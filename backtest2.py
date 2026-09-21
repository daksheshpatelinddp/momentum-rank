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
DEFAULT_WEIGHTS = {"r6_per_vol": 0.30, "r12_1": 0.25, "r3": 0.25, "near_high": 0.20}
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
        s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        return s, "file"
    proxy = (close_panel / close_panel.iloc[0]).mean(axis=1)
    return proxy, "proxy (equal-weight average of the universe; no data/index_%s.csv found)" % name


# ---------------------------------------------------------------------------------------
# Ranking and simulation (extends backtest.py's ideas with universe + trend filters)
# ---------------------------------------------------------------------------------------
def compute_ranks(close, weights, universe_syms, min_turnover_cr=5.0, stock_sma200=False):
    P = close[[c for c in universe_syms if c in close.columns]].ffill(limit=5)
    if P.shape[1] < 10:
        raise SystemExit(f"Only {P.shape[1]} of this universe's symbols have price history; "
                         "check the universe file and data/history.csv.")
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
        s6 = idx.searchsorted(t - pd.Timedelta(days=180), side="right") - 1
        s1y = idx.searchsorted(t - pd.Timedelta(days=365), side="right") - 1
        rr = R.iloc[s6 + 1:pos + 1]
        vol = rr.std() * np.sqrt(252)
        vol = vol.where((rr.count() >= 60) & (vol > 0))
        hi = P.iloc[s1y:pos + 1].max()
        m = pd.DataFrame({"r3": p_now / p3m - 1, "r6_per_vol": (p_now / p6m - 1) / vol,
                          "r12_1": p1m / p1y - 1, "near_high": p_now / hi})
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
        pct_ = m[list(weights)].rank(pct=True)
        score = sum(w * pct_[k] for k, w in weights.items())
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
    df["n"] = df.get("n", df["entry"]).fillna(df["entry"]).astype(int)
    df["step"] = df.get("step", 1).fillna(1).astype(int)
    df["cost_bps"] = df.get("cost_bps", 30).fillna(30).astype(float)
    df["min_turnover_cr"] = df.get("min_turnover_cr", 5).fillna(5).astype(float)
    for c in ("stock_sma200", "index_sma200"):
        df[c] = df.get(c, "no").fillna("no").astype(str).str.strip().str.lower().isin(("yes", "y", "true", "1"))
    df["index"] = df.get("index", "nifty50").fillna("nifty50")
    for c, dflt in [("w_r3", 0.25), ("w_r6vol", 0.30), ("w_r12_1", 0.25), ("w_nearhigh", 0.20)]:
        df[c] = pd.to_numeric(df.get(c), errors="coerce").fillna(dflt)
    for c in ("min_marketcap_cr", "max_marketcap_cr"):
        if c not in df.columns:
            df[c] = np.nan
    return df


def run_scenario(row, close_full, index_cache, notes_all):
    syms = uv.resolve(row.universe, row.min_marketcap_cr, row.max_marketcap_cr)
    weights = {"r3": row.w_r3, "r6_per_vol": row.w_r6vol, "r12_1": row.w_r12_1, "near_high": row.w_nearhigh}
    close = close_full[[c for c in syms if c in close_full.columns]]
    missing = [s for s in syms if s not in close_full.columns]
    ranks = compute_ranks(close, weights, syms, row.min_turnover_cr, row.stock_sma200)

    buy_gate = None
    idx_note = ""
    if row.index_sma200:
        if row.index not in index_cache:
            index_cache[row.index] = load_index_series(row.index, close)
        s, source = index_cache[row.index]
        buy_gate = index_ok_mask(s, ranks.index)
        idx_note = f" Index trend filter uses {source}."

    res = simulate(close, ranks, n=row.n, entry=row.entry, exit_=row.exit, cost_bps=row.cost_bps,
                   step=row.step, buy_gate=buy_gate)
    st = stats(res["equity"])
    os.makedirs(OUT_DIR, exist_ok=True)
    md = [f"# {row.name}\n",
          f"Universe: **{row.universe}**"
          + (f" ({row.min_marketcap_cr or '-'} to {row.max_marketcap_cr or '-'} Rs crore)"
             if row.universe == "marketcap" else f", {len(syms)} symbols, {len(missing)} missing prices")
          + f". Buy top **{row.entry}**, hold up to **{row.n}**, exit below rank **{row.exit}**, "
          f"rebalance every {row.step} month(s), cost {row.cost_bps:.0f} bps."
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
