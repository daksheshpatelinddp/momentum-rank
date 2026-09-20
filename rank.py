"""Rank the stocks in symbols.txt by momentum, using bonus/split-adjusted NSE prices.

Reads  : symbols.txt, corporate_actions.csv, data/prices.csv
Writes : output/ranked.csv, output/ranked.md (and the GitHub run summary)
"""
import datetime as dt
import os
import re
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from adjust import raw_close_matrix, apply_events
from events import load_manual, gather_events, estimate_factor

STORE = "data/prices.csv"
BSE_STORE = "data/prices_bse.csv"
OUT_CSV = "output/ranked.csv"
OUT_MD = "output/ranked.md"
# Look-backs are calendar days, like Screener / Chartink: 3m = 90, 6m = 180, 1y = 365 days.
LOOKBACKS = {"m1": 30, "m3": 90, "m6": 180, "y1": 365}
DROP_FLAG = -0.15              # a 1-day fall bigger than this after adjustment -> "check chart"
JUMP_FLAG = 0.35               # a 1-day rise bigger than this after adjustment -> "check chart"

# Score = weighted average of percentile ranks (0 = worst, 1 = best) among your list.
WEIGHTS = {
    "r6_per_vol": 0.30,        # 6-month return divided by volatility
    "r12_1":      0.25,        # 12-month return skipping the latest month
    "r3":         0.25,        # 3-month return
    "near_high":  0.20,        # closeness to the 52-week high
}


def read_symbols(path="symbols.txt"):
    if not os.path.exists(path):
        raise SystemExit("symbols.txt not found. Create it with one NSE symbol per line.")
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.split("#")[0]
            for tok in re.split(r"[,\s;]+", line):
                tok = tok.strip().upper()
                if tok.startswith("NSE:"):
                    tok = tok[4:]
                if tok.endswith(".NS"):
                    tok = tok[:-3]
                if tok and tok not in out:
                    out.append(tok)
    if not out:
        raise SystemExit("symbols.txt is empty. Paste your Chartink symbols, one per line.")
    return out


def md_table(df):
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def write_reports(md_text, ranked_df):
    os.makedirs("output", exist_ok=True)
    ranked_df.to_csv(OUT_CSV, index=False)
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md_text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(md_text)


def main(get_splits=None, api_getter=None):
    symbols = read_symbols()
    if not os.path.exists(STORE):
        raise SystemExit(f"{STORE} not found. fetch_bhav.py must run first.")
    store = pd.read_csv(STORE, parse_dates=["date"])
    if store.empty:
        raise SystemExit(f"{STORE} is empty.")

    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    as_of = store["date"].max()
    all_dates = sorted(store["date"].unique())
    notes = []

    age = (today - as_of.date()).days
    if age > 6:
        notes.append(f"WARNING: latest price data is {age} days old ({as_of.date()}).")

    bse, bse_syms, tickers = None, [], {}
    if os.path.exists(BSE_STORE):
        bse = pd.read_csv(BSE_STORE, parse_dates=["date"], dtype={"code": str})
        if len(bse):                                   # numeric scrip codes -> BSE Security IDs
            code_to_sym = bse.drop_duplicates("code", keep="last").set_index("code")["symbol"]
            symbols = list(dict.fromkeys(code_to_sym.get(t, t) if t.isdigit() else t for t in symbols))
    raw = raw_close_matrix(store, symbols)
    if bse is not None and len(bse):
        todo = [s for s in symbols if s not in raw.columns]
        rb = raw_close_matrix(bse, todo)
        bse_syms = list(rb.columns)
        raw = raw.join(rb, how="outer")
        codes = bse.drop_duplicates("symbol", keep="last").set_index("symbol")["code"]
        tickers = {s: (f"{codes[s]}.BO" if str(codes.get(s, "")).strip() not in ("", "nan")
                       else f"{s}.BO") for s in bse_syms}
    ref = max(pd.Timestamp(today), as_of)          # reference date for the look-backs
    d = {k: ref - pd.Timedelta(days=n) for k, n in LOOKBACKS.items()}
    if pd.Timestamp(all_dates[0]) > d["y1"]:
        raise SystemExit(f"Price history starts {pd.Timestamp(all_dates[0]).date()}, but 1 year "
                         f"before {ref.date()} is needed. Run the workflow with 'rebuild' ticked.")
    raw = raw.reindex(all_dates)               # one row per market day, same for every stock

    not_found = [s for s in symbols if s not in raw.columns]
    have = [s for s in symbols if s in raw.columns]

    # ---- corporate actions -------------------------------------------------------------
    manual = load_manual()
    events, rejected, ca_status, unverified, mm = gather_events(
        store, raw[have], have, manual, get_splits=get_splits, api_getter=api_getter,
        skip_yahoo=os.environ.get("SKIP_YAHOO", "").strip() == "1",
        skip_api=os.environ.get("SKIP_API", "").strip() == "1",
        bse=bse, bse_symbols=bse_syms, calendar=all_dates, yahoo_tickers=tickers)
    px = apply_events(raw[have], events)
    # BSE stocks can trade only on some days: carry the last traded price forward, but only
    # for stocks that traded within the last 30 days.
    unfilled = px.copy()
    traded = px.loc[d["y1"]:].notna().sum()
    last_trade = px.apply(lambda c: c.last_valid_index())
    filled = px.ffill(limit=3)
    bse_have = [s for s in bse_syms if s in px.columns]
    if bse_have:
        filled[bse_have] = px[bse_have].ffill()
    px = filled
    stale = [s for s in bse_have
             if pd.isna(last_trade.get(s)) or last_trade[s] < as_of - pd.Timedelta(days=30)]

    def at(date):
        """Last close on or before `date` (NaN if the stock was not trading then)."""
        return px.loc[:date].iloc[-1]

    p_now, p1m, p3m, p6m, p1y = px.iloc[-1], at(d["m1"]), at(d["m3"]), at(d["m6"]), at(d["y1"])
    good = pd.concat([p_now, p1m, p3m, p6m, p1y], axis=1).notna().all(axis=1)
    for st in stale:
        good[st] = False
    short = [s for s in have if not good.get(s, False)]
    px = px.loc[:, good[good].index]
    p_now, p1m, p3m, p6m, p1y = (x[px.columns] for x in (p_now, p1m, p3m, p6m, p1y))

    if px.shape[1] == 0:
        md = ("# Momentum ranking\n\nNo stock in symbols.txt had enough price history.\n\n"
              f"Not found in NSE or BSE data: {', '.join(not_found) or 'none'}\n\n"
              f"Too little history or not trading recently: {', '.join(short) or 'none'}\n")
        write_reports(md, pd.DataFrame(columns=["rank", "symbol", "score"]))
        print(md)
        return 1

    daily = px / px.shift(1) - 1
    vol = daily.loc[d["m6"]:].std() * np.sqrt(252)
    vol = vol.where(vol > 0)
    r3 = p_now / p3m - 1
    r6 = p_now / p6m - 1
    r12_1 = p1m / p1y - 1
    r1y = p_now / p1y - 1
    near_high = p_now / px.loc[d["y1"]:].max()
    worst_day = daily.loc[d["y1"]:].min()
    worst_date = daily.loc[d["y1"]:].idxmin()
    best_day = daily.loc[d["y1"]:].max()
    last = p_now

    m = pd.DataFrame({"r3": r3, "r6": r6, "r12_1": r12_1, "r1y": r1y,
                      "r6_per_vol": r6 / vol, "near_high": near_high, "vol": vol,
                      "close": last, "worst_day": worst_day, "best_day": best_day,
                      "worst_date": worst_date})
    bad = m.index[m[list(WEIGHTS)].isna().any(axis=1)].tolist()
    m = m.drop(index=bad)

    pct = m[list(WEIGHTS)].rank(pct=True)
    m["score"] = sum(w * pct[k] for k, w in WEIGHTS.items())
    m = m.sort_values("score", ascending=False)

    def flag_for(sym, row):
        f = []
        if sym in unverified:
            f.append("unverified")
        if row.worst_day <= DROP_FLAG:
            f.append("big 1-day drop: corporate action?")
        if sym in traded.index and traded[sym] < 60:
            f.append(f"thin trading ({int(traded[sym])} days in a year)")
        if row.best_day >= JUMP_FLAG:
            f.append("big 1-day jump: check")
        return "; ".join(f)

    ranked = pd.DataFrame({
        "rank": range(1, len(m) + 1),
        "symbol": m.index,
        "score": (m["score"] * 100).round(1).to_numpy(),
        "ret_3m_%": (m["r3"] * 100).round(1).to_numpy(),
        "ret_6m_%": (m["r6"] * 100).round(1).to_numpy(),
        "ret_1y_%": (m["r1y"] * 100).round(1).to_numpy(),
        "ret_12m_ex1m_%": (m["r12_1"] * 100).round(1).to_numpy(),
        "volatility_%": (m["vol"] * 100).round(1).to_numpy(),
        "below_52w_high_%": ((1 - m["near_high"]) * 100).round(1).to_numpy(),
        "close": m["close"].round(2).to_numpy(),
        "flag": [flag_for(s, r) for s, r in zip(m.index, m.itertuples())],
    })

    unver_ranked = [u for u in unverified if u in set(ranked["symbol"])]
    if unver_ranked:
        notes.append("WARNING: corporate actions could not be checked for: "
                     + ", ".join(unver_ranked) + ". A rights issue, demerger or bonus that is not "
                     "in corporate_actions.csv would make their returns wrong.")
    ev = events[events["symbol"].isin(ranked["symbol"])]
    if len(ev) and ev["source"].astype(str).str.startswith("auto").any():
        notes.append("Adjustments marked 'auto (estimated)' come from price behaviour alone, so their "
                     "factors are estimates. Check the announcement and, for an exact factor, add it "
                     "to corporate_actions.csv.")
    md = [f"# Momentum ranking (data up to {as_of.date()})\n",
          f"Ranked **{len(ranked)}** of {len(symbols)} symbols. "
          "Score is 0-100 (percentile-based, relative to this list only).\n"]
    if notes:
        md.append("\n".join(f"- {n}" for n in notes) + "\n")
    md.append(md_table(ranked) + "\n")

    md.append("\n## Corporate-action sources used in this run\n\n"
              + "\n".join(f"- {line}" if not line.startswith("   ") else f"  - {line.strip()}"
                          for line in ca_status) + "\n")
    if len(ev):
        evt = pd.DataFrame({
            "symbol": ev["symbol"],
            "ex-date": ev["date"].dt.strftime("%Y-%m-%d"),
            "factor": ev["factor"].round(4),
            "source": ev["source"],
        })
        md.append("\n## Corporate-action adjustments applied\n\n" + md_table(evt) + "\n")
    else:
        md.append("\nNo corporate-action adjustments were needed for these stocks.\n")
    sus = m[m["worst_day"] <= DROP_FLAG]
    if len(sus):
        rows = []
        for sym, r in sus.iterrows():
            est = estimate_factor(raw[sym], pd.Timestamp(r["worst_date"]), mm)
            rows.append((sym, pd.Timestamp(r["worst_date"]).strftime("%Y-%m-%d"),
                         f"{r['worst_day'] * 100:.1f}", est if est is not None else "",
                         f"{sym},{pd.Timestamp(r['worst_date']).strftime('%Y-%m-%d')},auto,check announcement"))
        sg = pd.DataFrame(rows, columns=["symbol", "date", "1-day move %", "estimated factor",
                                         "line to add to corporate_actions.csv"])
        md.append("\n## Possible corporate actions not adjusted - please check\n\n"
                  "These stocks fell sharply in one day. If the announcement shows a spin-off, "
                  "demerger, rights issue, bonus or split with that ex-date, add the line (or the "
                  "exact factor instead of `auto`) to corporate_actions.csv. If it was a real "
                  "price fall, ignore it.\n\n" + md_table(sg) + "\n")
    if rejected:
        rj = pd.DataFrame([(s, d.strftime("%Y-%m-%d"), round(f, 4)) for s, d, f in rejected],
                          columns=["symbol", "Yahoo date", "factor"])
        md.append("\n**Yahoo reported these events but NSE prices do not show the drop, so they "
                  "were NOT applied (check the chart):**\n\n" + md_table(rj) + "\n")
    if not_found:
        md.append("\n**Not found in NSE or BSE data** (typo, renamed, SME or not listed): "
                  + ", ".join(not_found) + "\n")
    if short:
        rows = []
        for sym in short:
            col = unfilled[sym].dropna() if sym in unfilled.columns else pd.Series(dtype=float)
            if col.empty:
                rows.append((sym, "-", "-", 0, "-", "no prices in the period"))
                continue
            first, last, n = col.index[0], col.index[-1], len(col)
            since = (col.iloc[-1] / col.iloc[0] - 1) * 100
            if last < as_of - pd.Timedelta(days=5):
                reason = f"stopped trading or very thin (last trade {last.date()})"
            elif first > d["y1"]:
                reason = "listed less than a year ago"
            else:
                reason = "price missing on a date needed for the returns"
            rows.append((sym, first.date(), last.date(), n, f"{since:.1f}", reason))
        nr = pd.DataFrame(rows, columns=["symbol", "first trade", "last trade", "trading days",
                                          "return over that period %", "why not ranked"])
        md.append("\n## Not ranked (not enough usable price history)\n\n" + md_table(nr) + "\n")
    if bad:
        md.append("\n**Skipped: metrics could not be computed:** " + ", ".join(bad) + "\n")
    md.append("\n*Research shortlist only, not investment advice. Returns look back 90 / 180 / "
              "365 calendar days from today, like Screener, so small differences remain if another "
              "site used a different day. ret_12m_ex1m skips the latest month.*\n")

    text = "\n".join(md)
    write_reports(text, ranked)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
