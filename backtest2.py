"""Multi-scenario backtest, driven by scenarios.csv, using NSE bhavcopy prices (data/history.csv)
adjusted the same way as the live ranking: corporate_actions.csv (exact, always wins) -> BSE and
NSE announcements (exact ratios, matched and validated) -> automatic price-jump detection
(estimated, for anything neither source explains).

Run: python backtest2.py
Needs: data/history.csv (built by fetch_history.py) and scenarios.csv.
"""
import os
import sys
import time
import datetime as dt

import numpy as np
import pandas as pd

from adjust import apply_events
from announce import fetch_bse_actions, fetch_nse_actions, resolve_actions
from events import detect_price_events, load_manual, build_events, estimate_factor
from fetch_bse import refresh_ids, make_session as bse_session
import universe as uv
from backtest import stats, pct, md_table, yearly, month_end_dates

HISTORY = "data/history.csv"
OUT_DIR = "output/scenarios"
SUMMARY = "output/backtest_summary.md"
# Seven selectable measures. Set a weight to 0 (or leave the column blank) to drop it from
# the score entirely -- so "use just one return" is simply one nonzero weight; "volatility
# adjust the 3-month return too" is putting weight on r3_vol instead of/as well as r3.
# The *_vol variants divide the plain return by the stock's trailing 6-month volatility
# (annualised), the same calculation already used for r6_vol -- a smoother climb outranks
# an equally-sized but choppier one.
MEASURES = ["r3", "r3_vol", "r6", "r6_vol", "r12_1", "r12_1_vol", "near_high"]
MEASURE_COL = {"r3": "w_r3", "r3_vol": "w_r3vol", "r6": "w_r6", "r6_vol": "w_r6vol",
              "r12_1": "w_r12_1", "r12_1_vol": "w_r12_1vol", "near_high": "w_nearhigh"}
DEFAULT_WEIGHTS = {"r3": 0.25, "r3_vol": 0.0, "r6": 0.0, "r6_vol": 0.30,
                   "r12_1": 0.25, "r12_1_vol": 0.0, "near_high": 0.20}
LOOKBACKS = {"m1": 30, "m3": 90, "m6": 180, "y1": 365}
CR = 1e7


# ---------------------------------------------------------------------------------------
# Data: load history, adjust for corporate actions (same precedence as the live ranking)
# ---------------------------------------------------------------------------------------
def load_history():
    if not os.path.exists(HISTORY):
        raise SystemExit(f"{HISTORY} not found. Run fetch_history.py first "
                         "(it can take several runs to backfill a decade).")
    df = pd.read_csv(HISTORY, parse_dates=["date"])
    if df.empty:
        raise SystemExit(f"{HISTORY} is empty.")
    return df


def build_price_panel(store, symbols, notes):
    """Raw close/volume-proxy panel, then adjusted for every corporate action we can find."""
    raw = store[store["symbol"].isin(symbols)]
    close = raw.pivot(index="date", columns="symbol", values="close").sort_index()
    turnover = raw.pivot(index="date", columns="symbol", values="close").sort_index()  # placeholder

    manual = load_manual()
    ok = store[(store["prev_close"] > 0) & (store["close"] > 0)]
    mm = (ok["close"] / ok["prev_close"] - 1).groupby(ok["date"]).median()

    start, end = close.index.min(), close.index.max()
    codes = {}
    try:
        codes = pd.read_csv("data/bse_ids.csv", dtype=str).set_index("symbol")["code"].to_dict()
    except (FileNotFoundError, KeyError):
        pass

    resolved_all = []
    for source, fetcher in (("BSE", fetch_bse_actions), ("NSE", fetch_nse_actions)):
        try:
            ann, note = fetcher(start, end)
        except Exception as e:
            notes.append(f"{source} announcements: not usable - {type(e).__name__}: {e}.")
            continue
        if note != "ok" or ann.empty:
            notes.append(f"{source} announcements: not usable - {note}.")
            continue
        ev, unresolved = resolve_actions(ann, close, market_move=mm, code_to_sym=codes)
        notes.append(f"{source} announcements: {len(ann)} read, {len(ev)} applied with an exact factor, "
                     f"{len(unresolved)} could not be given a factor automatically.")
        if len(ev):
            resolved_all.append(ev)

    announced = (pd.concat(resolved_all, ignore_index=True).drop_duplicates(["symbol", "date"])
                if resolved_all else pd.DataFrame(columns=["symbol", "date", "factor", "source", "note"]))
    events = build_events(close, manual, pd.DataFrame(columns=["symbol", "date", "factor"]),
                          exchange=announced if len(announced) else None, market_move=mm)[0]
    auto = detect_price_events(close, events, mm)
    if len(auto):
        notes.append(f"Automatic price check: {len(auto)} one-day move(s) too large for normal "
                     "trading, with no announcement confirming them, adjusted with an ESTIMATED factor.")
        events = pd.concat([events, auto], ignore_index=True)
    if len(events):
        close = apply_events(close, events)
    notes.append(f"Total corporate-action adjustments applied: {len(events)} "
                 f"({(events['source'].str.contains('estimated', case=False)).sum() if len(events) else 0} estimated).")
    return close, events


def load_index_series(name, close_panel):
    """A reference index level series for the trend filter. Uses a saved
    data/index_<name>.csv if present; otherwise falls back to an equal-weight average of
    the price panel (a rough proxy - a real index file gives a truer signal)."""
    path = f"data/index_{name}.csv"
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["date"])
        s = df.set_index("date")["close"].sort_index()
        return s, f"file ({path}, {s.index.min().date()} to {s.index.max().date()})"
    proxy = (close_panel / close_panel.iloc[0]).mean(axis=1)
    return proxy, "proxy (equal-weight average of the universe; no data/index_%s.csv found)" % name


# ---------------------------------------------------------------------------------------
# Ranking and simulation (extends backtest.py's ideas with universe + trend filters)
# ---------------------------------------------------------------------------------------
def compute_ranks(close, weights, universe_syms, min_turnover_cr=5.0, stock_sma200=False,
                  vol_window=180, start=None, end=None):
    """weights: dict of measure -> weight, keys from MEASURES. A measure with weight 0 (or
    missing) is dropped from the score entirely, so picking "just r3" is one nonzero weight,
    and "volatility-adjust r3 too" is putting weight on r3_vol alongside or instead of r3."""
    P = close[[c for c in universe_syms if c in close.columns]].ffill(limit=5)
    if start is not None:
        P = P[P.index >= pd.Timestamp(start)]
    if end is not None:
        P = P[P.index <= pd.Timestamp(end)]
    if P.shape[1] < 10:
        raise SystemExit(f"Only {P.shape[1]} of this universe's symbols have price history in "
                         "this date range; check the universe file, data/history.csv, and start/end.")
    used = {k for k, w in weights.items() if w}
    if not used:
        raise SystemExit("Every weight is 0 - at least one w_* column must be non-zero.")
    R = P / P.shift(1) - 1
    idx = P.index
    out = {}
    for t in month_end_dates(idx):
        pos = idx.get_loc(t)

        def at(days):
            p = idx.searchsorted(t - pd.Timedelta(days=days), side="right") - 1
            return P.iloc[p] if p >= 0 else pd.Series(np.nan, index=P.columns)

        p_now, p1m, p3m, p6m, p1y = P.iloc[pos], at(30), at(90), at(180), at(365)
        if idx[0] > t - pd.Timedelta(days=365):
            continue
        sV = idx.searchsorted(t - pd.Timedelta(days=vol_window), side="right") - 1
        s1y = idx.searchsorted(t - pd.Timedelta(days=365), side="right") - 1
        rr = R.iloc[sV + 1:pos + 1]
        vol = rr.std() * np.sqrt(252)
        vol = vol.where((rr.count() >= max(20, vol_window // 5)) & (vol > 0))
        hi = P.iloc[s1y:pos + 1].max()

        r3, r6, r12_1 = p_now / p3m - 1, p_now / p6m - 1, p1m / p1y - 1
        avail = {"r3": r3, "r3_vol": r3 / vol, "r6": r6, "r6_vol": r6 / vol,
                "r12_1": r12_1, "r12_1_vol": r12_1 / vol, "near_high": p_now / hi}
        m = pd.DataFrame({k: avail[k] for k in used})
        ok = m.notna().all(axis=1)
        if min_turnover_cr > 0:
            med = P.iloc[max(0, pos - 60):pos + 1].median()   # price only: true turnover needs
            ok &= med.notna()                                  # volume, which bhavcopy close alone lacks
        if stock_sma200:
            s200 = idx.searchsorted(t - pd.Timedelta(days=200 * 1.45), side="right") - 1
            sma = P.iloc[max(0, s200):pos + 1].mean()
            ok &= (p_now > sma)
        m = m[ok]
        if len(m) < 10:
            continue
        pct_ = m.rank(pct=True)
        score = sum(weights[k] * pct_[k] for k in used)
        out[t] = score.rank(ascending=False, method="first")
    if not out:
        raise SystemExit("No rebalance date had enough eligible stocks for this scenario.")
    return pd.DataFrame(out).T.reindex(columns=P.columns).sort_index()


def index_ok_mask(index_series, ranks_index):
    s = index_series.reindex(index_series.index.union(ranks_index)).sort_index().ffill()
    sma = s.rolling(200, min_periods=100).mean()
    ok = (s > sma)
    return ok.reindex(ranks_index).fillna(False)


def simulate(close, ranks, n, entry, exit_, cost_bps, step=1, buy_gate=None, cash_rate=0.05,
            start_value=100.0, lag=1):
    Pv = close.ffill()
    idx, cols = Pv.index, list(Pv.columns)
    arr = Pv.to_numpy()
    cpos = {c: i for i, c in enumerate(cols)}
    sig = list(ranks.index[::step])
    exec_map = {}
    for t in sig:
        p = idx.get_loc(t)
        if p + lag < len(idx):
            exec_map[idx[p + lag]] = t
    if not exec_map:
        raise SystemExit("Not enough history to run this scenario.")
    days = [d for d in idx if d >= min(exec_map)]
    fee = cost_bps / 1e4
    daily_cash = (1 + cash_rate) ** (1 / 252)
    cash, hold, trades = float(start_value), {}, []
    equity, count = [], []

    def price(sym, di):
        return arr[di, cpos[sym]]

    for d in days:
        di = idx.get_loc(d)
        cash *= daily_cash
        if d in exec_map:
            t = exec_map[d]
            rk = ranks.loc[t]
            gate_ok = True if buy_gate is None else bool(buy_gate.get(t, True))
            for sym in list(hold):
                r = rk.get(sym, np.nan)
                if pd.isna(r) or r > exit_:
                    h = hold.pop(sym)
                    px = price(sym, di)
                    proceeds = h["shares"] * px * (1 - fee)
                    cash += proceeds
                    trades.append((d, sym, "SELL", px, proceeds))
            if gate_ok:
                slots = n - len(hold)
                cands = [s for s in rk[rk <= entry].sort_values().index if s not in hold]
                buys = [s for s in cands if not np.isnan(price(s, di))][:max(slots, 0)]
                if buys:
                    total = cash + sum(h["shares"] * price(s, di) for s, h in hold.items())
                    alloc = min(total / n, cash / len(buys))
                    if alloc > 0:
                        for s in buys:
                            px = price(s, di)
                            hold[s] = {"shares": alloc * (1 - fee) / px}
                            cash -= alloc
                            trades.append((d, s, "BUY", px, alloc))
        value = cash + sum(h["shares"] * price(s, di) for s, h in hold.items())
        equity.append(value)
        count.append(len(hold))
    eq = pd.Series(equity, index=days)
    tr = pd.DataFrame(trades, columns=["date", "symbol", "side", "price", "value"])
    years = max((days[-1] - days[0]).days / 365.25, 1e-9)
    turnover = tr["value"].sum() / eq.mean() / years if len(tr) else 0.0
    return {"equity": eq, "trades": tr, "holdings": pd.Series(count, index=days),
            "turnover": turnover, "years": years}


# ---------------------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------------------
def load_scenarios(path="scenarios.csv"):
    if not os.path.exists(path):
        raise SystemExit(f"{path} not found.")
    df = pd.read_csv(path, comment="#", skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    need = {"name", "universe", "entry", "exit"}
    if not need.issubset(df.columns):
        raise SystemExit(f"scenarios.csv must have at least the columns: {sorted(need)}")
    if "n" not in df.columns:
        df["n"] = np.nan
    df["n"] = pd.to_numeric(df["n"], errors="coerce").fillna(df["entry"]).astype(int)
    if "step" not in df.columns:
        df["step"] = np.nan
    df["step"] = pd.to_numeric(df["step"], errors="coerce").fillna(1).astype(int)
    if "cost_bps" not in df.columns:
        df["cost_bps"] = np.nan
    df["cost_bps"] = pd.to_numeric(df["cost_bps"], errors="coerce").fillna(30).astype(float)
    if "min_turnover_cr" not in df.columns:
        df["min_turnover_cr"] = np.nan
    df["min_turnover_cr"] = pd.to_numeric(df["min_turnover_cr"], errors="coerce").fillna(5).astype(float)
    for c in ("stock_sma200", "index_sma200"):
        if c not in df.columns:
            df[c] = "no"
        df[c] = df[c].fillna("no").astype(str).str.strip().str.lower().isin(("yes", "y", "true", "1"))
    if "index" not in df.columns:
        df["index"] = "nifty50"
    df["index"] = df["index"].fillna("nifty50")
    # Weight defaults only apply as a WHOLE SET, when a row leaves every weight column blank
    # (the default mix). The moment a row fills in ANY weight, every other blank weight in
    # that row means 0 (dropped), not "use its individual default" -- otherwise "just w_r3"
    # would silently keep the default r6_vol/r12_1/near_high mixed in too.
    wcols = ["w_r3", "w_r3vol", "w_r6", "w_r6vol", "w_r12_1", "w_r12_1vol", "w_nearhigh"]
    for c in wcols:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")
    row_touched = df[wcols].notna().any(axis=1)
    for c in wcols:
        default_key = {"w_r3": "r3", "w_r3vol": "r3_vol", "w_r6": "r6", "w_r6vol": "r6_vol",
                       "w_r12_1": "r12_1", "w_r12_1vol": "r12_1_vol", "w_nearhigh": "near_high"}[c]
        df[c] = np.where(row_touched, df[c].fillna(0.0),
                        DEFAULT_WEIGHTS[default_key])
    for c in ("min_marketcap_cr", "max_marketcap_cr"):
        if c not in df.columns:
            df[c] = np.nan
    for c in ("start", "end"):
        if c not in df.columns:
            df[c] = np.nan
        else:
            df[c] = df[c].replace("", np.nan)
    if "vol_adjust" not in df.columns:
        df["vol_adjust"] = "r6"
    df["vol_adjust"] = df["vol_adjust"].fillna("r6").astype(str)
    return df


def run_scenario(row, close_full, index_cache, notes_all):
    syms = uv.resolve(row.universe, row.min_marketcap_cr, row.max_marketcap_cr)
    weights = {k: getattr(row, MEASURE_COL[k]) for k in MEASURES}
    close = close_full[[c for c in syms if c in close_full.columns]]
    missing = [s for s in syms if s not in close_full.columns]
    start = None if pd.isna(row.start) else str(row.start)
    end = None if pd.isna(row.end) else str(row.end)
    ranks = compute_ranks(close, weights, syms, row.min_turnover_cr, row.stock_sma200,
                          start=start, end=end)

    buy_gate = None
    idx_note = ""
    if row.index_sma200:
        if row.index not in index_cache:
            index_cache[row.index] = load_index_series(row.index, close)
        idx_series, source = index_cache[row.index]
        buy_gate = index_ok_mask(idx_series, ranks.index)
        idx_note = f" Index trend filter uses {source}."

    res = simulate(close, ranks, n=row.n, entry=row.entry, exit_=row.exit, cost_bps=row.cost_bps,
                   step=row.step, buy_gate=buy_gate)
    st = stats(res["equity"])
    os.makedirs(OUT_DIR, exist_ok=True)
    used_str = ", ".join(f"{k} ({v:.2f})" for k, v in weights.items() if v)
    md = [f"# {row.name}\n",
          f"Universe: **{row.universe}**"
          + (f", data from {start}" if start else "") + (f" to {end}" if end else "")
          + (f" ({row.min_marketcap_cr or '-'} to {row.max_marketcap_cr or '-'} Rs crore)"
             if row.universe == "marketcap" else f", {len(syms)} symbols, {len(missing)} missing prices")
          + f". Buy top **{row.entry}**, hold up to **{row.n}**, exit below rank **{row.exit}**, "
          f"rebalance every {row.step} month(s), cost {row.cost_bps:.0f} bps."
          + f" Score uses: {used_str}."
          + (" Stock must be above its own 200-day average to be bought/held." if row.stock_sma200 else "")
          + (f" New buys only while {row.index} is above its 200-day average.{idx_note}" if row.index_sma200 else "")
          + "\n",
          md_table(pd.DataFrame([[
              f"{res['equity'].index[0].date()} to {res['equity'].index[-1].date()} ({res['years']:.1f}y)",
              pct(st["CAGR"]), pct(st["Total return"]), pct(st["Volatility"]), f"{st['Sharpe (rf 5%)']:.2f}",
              pct(st["Max drawdown"]), pct(st["Positive months"]), f"{res['turnover'] * 100:.0f}%",
              f"{res['holdings'].mean():.1f}"]],
              columns=["Period", "CAGR", "Total return", "Volatility", "Sharpe", "Max drawdown",
                       "Positive months", "Yearly turnover", "Avg holdings"])),
          "\n## Year by year\n",
          md_table(yearly(res["equity"]).apply(pct).reset_index().rename(
              columns={"index": "Year", 0: "Return"}))]
    with open(os.path.join(OUT_DIR, f"{row.name}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")
    return st, res


def main():
    scenarios = load_scenarios()
    notes = []
    store = load_history()

    try:
        refresh_ids(bse_session(), dt.date.today())
    except Exception as e:
        notes.append(f"BSE Security-ID list refresh failed ({type(e).__name__}); BSE announcement "
                     "matching by name only may miss some stocks.")

    all_syms = uv.all_symbols_needed(scenarios)
    print(f"Universes need {len(all_syms)} symbols in total; adjusting prices for corporate actions "
         "(this reads BSE/NSE announcements once for the whole period) ...", flush=True)
    close, events = build_price_panel(store, all_syms, notes)

    index_cache = {}
    rows = []
    for r in scenarios.itertuples(index=False):
        print(f"Running scenario: {r.name} ...", flush=True)
        try:
            st, res = run_scenario(r, close, index_cache, notes)
        except SystemExit as e:
            rows.append([r.name, r.universe, f"{r.entry}/{r.exit}", "FAILED", str(e), "", "", "", ""])
            print(f"  FAILED: {e}")
            continue
        rows.append([r.name, r.universe, f"{r.entry}/{r.exit}", pct(st["CAGR"]), pct(st["Max drawdown"]),
                    f"{st['Sharpe (rf 5%)']:.2f}", pct(st["Positive months"]), f"{res['turnover'] * 100:.0f}%",
                    f"{res['holdings'].mean():.0f}"])

    summary = pd.DataFrame(rows, columns=["Scenario", "Universe", "Enter/Exit", "CAGR", "Max drawdown",
                                          "Sharpe", "Positive months", "Yearly turnover", "Avg holdings"])
    md = ["# Backtest summary\n",
          "> Every universe here uses TODAY's index membership or market-cap snapshot for the "
          "WHOLE backtest period (see universe.py's docstring) - a real form of survivorship "
          "bias, present in every row here, so use this table to compare rows against each "
          "other rather than to judge any one of them in isolation. Past results do not predict "
          "future returns.\n",
          md_table(summary), "\n## Data notes\n\n" + "\n".join(f"- {n}" for n in notes),
          "\nEach scenario's own page (year-by-year returns, etc.) is in output/scenarios/."]
    os.makedirs("output", exist_ok=True)
    text = "\n".join(md) + "\n"
    with open(SUMMARY, "w", encoding="utf-8") as f:
        f.write(text)
    ghs = os.environ.get("GITHUB_STEP_SUMMARY")
    if ghs:
        with open(ghs, "a", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0 if not summary["CAGR"].eq("FAILED").any() else 1


if __name__ == "__main__":
    sys.exit(main())
