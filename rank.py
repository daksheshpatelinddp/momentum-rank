"""Rank the stocks in symbols.txt by momentum, using split/bonus-adjusted NSE prices.

Reads  : symbols.txt, data/prices.csv
Writes : output/ranked.csv, output/ranked.md (and the GitHub run summary)
"""
import datetime as dt
import os
import re
import sys
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from adjust import adjusted_close

STORE = "data/prices.csv"
OUT_CSV = "output/ranked.csv"
OUT_MD = "output/ranked.md"
MIN_ROWS = 253                 # trading days needed for the 12-1 return
JUMP_FLAG = 0.35               # a 1-day move above 35 % after adjustment -> "check chart"

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


def main():
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

    px, events, gap_dates = adjusted_close(store, symbols)
    if gap_dates:
        notes.append("WARNING: these dates look like they follow a missing trading day, so "
                     "corporate actions on them were ignored: "
                     + ", ".join(d.strftime("%Y-%m-%d") for d in gap_dates[-10:]))

    px = px.reindex(all_dates)                 # one row per market day, same for every stock
    if len(px) < MIN_ROWS:
        raise SystemExit(f"Only {len(px)} trading days of history; need {MIN_ROWS}. "
                         "Run the workflow with 'rebuild' ticked.")
    px = px.ffill(limit=3)

    not_found = [s for s in symbols if s not in px.columns]
    have = [s for s in symbols if s in px.columns]
    px = px[have]

    pts = px.iloc[[-1, -22, -64, -127, -253]]
    good = pts.notna().all()
    short = [s for s in have if not good[s]]
    px = px.loc[:, good[good].index]

    if px.shape[1] == 0:
        md = ("# Momentum ranking\n\nNo stock in symbols.txt had enough price history.\n\n"
              f"Not found in NSE data: {', '.join(not_found) or 'none'}\n\n"
              f"Too little history or not trading recently: {', '.join(short) or 'none'}\n")
        write_reports(md, pd.DataFrame(columns=["rank", "symbol", "score"]))
        print(md)
        return 1

    last = px.iloc[-1]
    daily = px / px.shift(1) - 1
    vol = daily.iloc[-126:].std() * np.sqrt(252)
    vol = vol.where(vol > 0)
    r3 = last / px.iloc[-64] - 1
    r6 = last / px.iloc[-127] - 1
    r12_1 = px.iloc[-22] / px.iloc[-253] - 1
    hi52 = px.iloc[-252:].max()
    near_high = last / hi52
    max_jump = daily.iloc[-252:].abs().max()

    m = pd.DataFrame({"r3": r3, "r6": r6, "r12_1": r12_1, "r6_per_vol": r6 / vol,
                      "near_high": near_high, "vol": vol, "close": last,
                      "max_jump": max_jump})
    bad = m.index[m[list(WEIGHTS)].isna().any(axis=1)].tolist()
    m = m.drop(index=bad)

    pct = m[list(WEIGHTS)].rank(pct=True)
    m["score"] = sum(w * pct[k] for k, w in WEIGHTS.items())
    m = m.sort_values("score", ascending=False)

    ranked = pd.DataFrame({
        "rank": range(1, len(m) + 1),
        "symbol": m.index,
        "score": (m["score"] * 100).round(1).to_numpy(),
        "ret_3m_%": (m["r3"] * 100).round(1).to_numpy(),
        "ret_6m_%": (m["r6"] * 100).round(1).to_numpy(),
        "ret_12m_ex1m_%": (m["r12_1"] * 100).round(1).to_numpy(),
        "volatility_%": (m["vol"] * 100).round(1).to_numpy(),
        "below_52w_high_%": ((1 - m["near_high"]) * 100).round(1).to_numpy(),
        "close": m["close"].round(2).to_numpy(),
        "flag": np.where(m["max_jump"].to_numpy() > JUMP_FLAG, "check chart", ""),
    })

    ev = events[events["symbol"].isin(ranked["symbol"])].copy()
    ev = ev[ev["date"] >= pd.Timestamp(all_dates[-253])]

    md = [f"# Momentum ranking (data up to {as_of.date()})\n",
          f"Ranked **{len(ranked)}** of {len(symbols)} symbols. "
          "Score is 0-100 (percentile-based, relative to this list only).\n"]
    if notes:
        md.append("\n".join(f"- {n}" for n in notes) + "\n")
    md.append(md_table(ranked) + "\n")
    if len(ev):
        evt = pd.DataFrame({
            "date": ev["date"].dt.strftime("%Y-%m-%d"),
            "symbol": ev["symbol"],
            "adjustment factor": ev["factor"].round(4),
            "meaning": np.where(ev["factor"] < 1, "split/bonus (older prices scaled down)",
                                "reverse split (older prices scaled up)"),
        })
        md.append("\n## Corporate actions detected and adjusted\n\n" + md_table(evt) + "\n")
    if not_found:
        md.append("\n**Not found in NSE data** (typo, renamed, SME or not listed): "
                  + ", ".join(not_found) + "\n")
    if short:
        md.append("\n**Skipped: less than about 12 months of history or not trading "
                  "recently:** " + ", ".join(short) + "\n")
    if bad:
        md.append("\n**Skipped: metrics could not be computed:** " + ", ".join(bad) + "\n")
    md.append("\n*Research shortlist only, not investment advice. "
              "'check chart' = a 1-day move above 35% remains after adjustment; verify it.*\n")

    text = "\n".join(md)
    write_reports(text, ranked)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
