"""Backtest of the momentum strategy:  rank the universe every month with the same score as
rank.py, buy the top ENTRY names, sell a holding when its rank falls below EXIT.

Data   : Yahoo Finance adjusted prices (splits, bonuses and dividends included) for the
         Nifty 500 list (nifty500.txt, or downloaded from NSE). Residual jumps that Yahoo
         did not adjust are repaired with the same automatic check the ranking uses.
Output : output/backtest.md, output/backtest_equity.csv, output/backtest_trades.csv,
         output/backtest_equity.png

Run    : python backtest.py --start 2014-01-01 --entry 20 --exit 40 --cost-bps 30
"""
import argparse
import io
import os
import sys
import time
import datetime as dt

import numpy as np
import pandas as pd

from adjust import apply_events
from events import detect_price_events
from rank import WEIGHTS, LOOKBACKS

OUT_DIR = "output"
NIFTY500_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
BENCH = {"Nifty 500 (price index)": "^CRSLDX", "Nifty 50 (price index)": "^NSEI"}
CR = 1e7                                   # one crore


# ---------------------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------------------
def load_universe(path="nifty500.txt"):
    """nifty500.txt if present, otherwise NSE's official list (then saved to nifty500.txt)."""
    if os.path.exists(path):
        syms = []
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                for tok in line.split("#")[0].replace(",", " ").split():
                    tok = tok.strip().upper()
                    if tok.endswith(".NS"):
                        tok = tok[:-3]
                    if tok and tok not in syms and tok != "SYMBOL":
                        syms.append(tok)
        if syms:
            return syms
    import requests
    r = requests.get(NIFTY500_URL, timeout=60, headers={
        "User-Agent": "Mozilla/5.0", "Referer": "https://www.nseindia.com/"})
    if r.status_code != 200:
        raise SystemExit(f"Could not download the Nifty 500 list (HTTP {r.status_code}). "
                         "Create nifty500.txt with one NSE symbol per line and run again.")
    df = pd.read_csv(io.StringIO(r.text))
    col = [c for c in df.columns if c.strip().lower() == "symbol"]
    if not col:
        raise SystemExit("NSE's Nifty 500 file has no Symbol column; create nifty500.txt yourself.")
    syms = [s.strip().upper() for s in df[col[0]].dropna().astype(str)]
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Nifty 500 constituents (downloaded from NSE). Edit freely.\n" + "\n".join(syms) + "\n")
    return syms


def download_prices(symbols, start, end=None, chunk=40, tries=3):
    """Adjusted close and volume from Yahoo. Returns (close, volume, missing_symbols)."""
    import yfinance as yf
    closes, vols, missing = [], [], []
    for i in range(0, len(symbols), chunk):
        part = symbols[i:i + chunk]
        tickers = [s + ".NS" for s in part]
        data = None
        for attempt in range(tries):
            try:
                data = yf.download(tickers, start=start, end=end, auto_adjust=True,
                                   progress=False, threads=True, group_by="column")
                if data is not None and len(data):
                    break
            except Exception as e:                       # rate limit, network ...
                print(f"  chunk {i // chunk + 1}: {type(e).__name__}, retrying", flush=True)
            time.sleep(5 * (attempt + 1))
        if data is None or data.empty:
            missing += part
            continue
        c, v = data["Close"], data["Volume"]
        if isinstance(c, pd.Series):                     # a single ticker
            c, v = c.to_frame(tickers[0]), v.to_frame(tickers[0])
        c.columns = [str(x).replace(".NS", "") for x in c.columns]
        v.columns = [str(x).replace(".NS", "") for x in v.columns]
        closes.append(c)
        vols.append(v)
        print(f"  downloaded {min(i + chunk, len(symbols))}/{len(symbols)}", flush=True)
    if not closes:
        raise SystemExit("Yahoo Finance returned no data. Try again later.")
    close = pd.concat(closes, axis=1).sort_index()
    volume = pd.concat(vols, axis=1).sort_index()
    close = close.loc[:, ~close.columns.duplicated()]
    volume = volume.loc[:, ~volume.columns.duplicated()]
    missing += [s for s in symbols if s not in close.columns or close[s].notna().sum() < 250]
    return close, volume, sorted(set(missing))


def download_benchmarks(start, end=None):
    import yfinance as yf
    out = {}
    for name, tk in BENCH.items():
        try:
            d = yf.download(tk, start=start, end=end, auto_adjust=True, progress=False)["Close"]
            if isinstance(d, pd.DataFrame):
                d = d.iloc[:, 0]
            d = d.dropna()
            if len(d) > 250:
                out[name] = d
        except Exception:
            pass
    return out


def repair_prices(close):
    """Fix jumps Yahoo did not adjust (same rule as the live ranking). Returns (panel, events)."""
    close = close.copy()
    ok = (close / close.shift(1) - 1)
    mm = ok.median(axis=1)
    ev = detect_price_events(close, pd.DataFrame(columns=["symbol", "date", "factor", "source", "note"]), mm)
    if len(ev):
        close = apply_events(close, ev)
    return close, ev


# ---------------------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------------------
def month_end_dates(index):
    s = pd.Series(index, index=index)
    return list(s.groupby([index.year, index.month]).max().values)


def compute_ranks(close, volume=None, min_turnover_cr=5.0, weights=WEIGHTS):
    """Rank table: rows = month-end signal dates, columns = stocks, value = rank (1 = best)
    or NaN when the stock was not eligible that day. Uses only data up to each date."""
    P = close.ffill(limit=5)
    R = P / P.shift(1) - 1
    idx = P.index
    T = None
    if volume is not None:
        T = (close * volume.reindex(index=close.index, columns=close.columns))
    lb = LOOKBACKS
    out = {}
    for t in month_end_dates(idx):
        pos = idx.get_loc(t)

        def at(days):
            p = idx.searchsorted(t - pd.Timedelta(days=days), side="right") - 1
            return P.iloc[p] if p >= 0 else pd.Series(np.nan, index=P.columns)

        p_now, p1m, p3m, p6m, p1y = P.iloc[pos], at(lb["m1"]), at(lb["m3"]), at(lb["m6"]), at(lb["y1"])
        if idx[0] > t - pd.Timedelta(days=lb["y1"]):
            continue
        s6 = idx.searchsorted(t - pd.Timedelta(days=lb["m6"]), side="right") - 1
        s1y = idx.searchsorted(t - pd.Timedelta(days=lb["y1"]), side="right") - 1
        rr = R.iloc[s6 + 1:pos + 1]
        vol = rr.std() * np.sqrt(252)
        vol = vol.where((rr.count() >= 60) & (vol > 0))
        hi = P.iloc[s1y:pos + 1].max()
        m = pd.DataFrame({
            "r3": p_now / p3m - 1,
            "r6_per_vol": (p_now / p6m - 1) / vol,
            "r12_1": p1m / p1y - 1,
            "near_high": p_now / hi,
        })
        ok = m.notna().all(axis=1)
        if T is not None and min_turnover_cr > 0:
            med = T.iloc[max(0, pos - 125):pos + 1].median()
            ok &= (med >= min_turnover_cr * CR).reindex(m.index).fillna(False)
        m = m[ok]
        if len(m) < 30:
            continue
        pct = m[list(weights)].rank(pct=True)
        score = sum(w * pct[k] for k, w in weights.items())
        out[t] = score.rank(ascending=False, method="first")
    return pd.DataFrame(out).T.reindex(columns=close.columns).sort_index()


# ---------------------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------------------
def simulate(close, ranks, n=20, entry=20, exit_=40, cost_bps=30.0, lag=1, step=1,
             cash_rate=0.05, tax=False, start_value=100.0):
    """Buy the best `entry` ranked names (up to n holdings), sell when rank > exit_ or the
    stock is no longer eligible. Trades happen at the close `lag` trading days after the
    signal date. Cost is charged on every buy and sell. Returns dict with equity, trades..."""
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
        raise SystemExit("Not enough history to run the backtest.")
    first = min(exec_map)
    days = [d for d in idx if d >= first]
    fee = cost_bps / 1e4
    daily_cash = (1 + cash_rate) ** (1 / 252)

    cash, hold, trades = float(start_value), {}, []
    fy = {"short": 0.0, "long": 0.0}
    tax_paid, traded_value = 0.0, 0.0
    equity, count, prev_day = [], [], None

    def price(sym, di):
        return arr[di, cpos[sym]]

    for d in days:
        di = idx.get_loc(d)
        cash *= daily_cash
        if tax and prev_day is not None and prev_day.month == 3 and d.month == 4:
            due = 0.20 * max(fy["short"], 0) + 0.125 * max(fy["long"], 0)
            cash -= due
            tax_paid += due
            fy = {"short": 0.0, "long": 0.0}
        if d in exec_map:
            rk = ranks.loc[exec_map[d]]
            for sym in list(hold):
                r = rk.get(sym, np.nan)
                if pd.isna(r) or r > exit_:
                    h = hold.pop(sym)
                    px = price(sym, di)
                    proceeds = h["shares"] * px * (1 - fee)
                    cash += proceeds
                    traded_value += h["shares"] * px
                    gain = proceeds - h["basis"]
                    if (d - h["date"]).days >= 365:
                        fy["long"] += gain
                    else:
                        fy["short"] += gain
                    trades.append((d, sym, "SELL", px, proceeds, None if pd.isna(r) else int(r), gain))
            slots = n - len(hold)
            cands = [s for s in rk[rk <= entry].sort_values().index if s not in hold]
            buys = [s for s in cands if not np.isnan(price(s, di))][:max(slots, 0)]
            if buys:
                total = cash + sum(h["shares"] * price(s, di) for s, h in hold.items())
                alloc = min(total / n, cash / len(buys))
                if alloc > 0:
                    for s in buys:
                        px = price(s, di)
                        hold[s] = {"shares": alloc * (1 - fee) / px, "date": d, "basis": alloc}
                        cash -= alloc
                        traded_value += alloc
                        trades.append((d, s, "BUY", px, alloc, int(rk[s]), None))
        value = cash + sum(h["shares"] * price(s, di) for s, h in hold.items())
        equity.append(value)
        count.append(len(hold))
        prev_day = d

    eq = pd.Series(equity, index=days)
    pending = 0.0
    if tax:
        pending = 0.20 * max(fy["short"], 0) + 0.125 * max(fy["long"], 0)
    tr = pd.DataFrame(trades, columns=["date", "symbol", "side", "price", "value", "rank", "gain"])
    years = max((days[-1] - days[0]).days / 365.25, 1e-9)
    return {"equity": eq, "trades": tr, "holdings": pd.Series(count, index=days),
            "turnover": traded_value / eq.mean() / years, "tax_paid": tax_paid,
            "pending_tax": pending, "years": years}


def equal_weight_universe(close, ranks, lag=1, start=None):
    """Control group: every eligible stock, equal weight, rebalanced monthly (no costs)."""
    P = close.ffill(limit=5)
    R = (P / P.shift(1) - 1)
    idx = P.index
    sig = list(ranks.index)
    ret = pd.Series(np.nan, index=idx)
    for k, t in enumerate(sig):
        p = idx.get_loc(t)
        a = p + lag
        b = idx.get_loc(sig[k + 1]) + lag if k + 1 < len(sig) else len(idx) - 1
        b = min(b, len(idx) - 1)
        if a + 1 > b:
            continue
        members = ranks.loc[t].dropna().index
        seg = R.iloc[a + 1:b + 1][members]
        ret.iloc[a + 1:b + 1] = seg.mean(axis=1).to_numpy()
    ret = ret.dropna()
    if start is not None:
        ret = ret[ret.index >= start]
    return (1 + ret).cumprod() * 100


# ---------------------------------------------------------------------------------------
# Statistics and report
# ---------------------------------------------------------------------------------------
def stats(eq, rf=0.05):
    eq = eq.dropna()
    yrs = max((eq.index[-1] - eq.index[0]).days / 365.25, 1e-9)
    total = eq.iloc[-1] / eq.iloc[0] - 1
    cagr = (eq.iloc[-1] / eq.iloc[0]) ** (1 / yrs) - 1
    r = eq.pct_change().dropna()
    vol = r.std() * np.sqrt(252)
    dd = (eq / eq.cummax() - 1).min()
    m = eq.resample("ME").last().pct_change().dropna()
    return {"Total return": total, "CAGR": cagr, "Volatility": vol,
            "Sharpe (rf 5%)": (cagr - rf) / vol if vol > 0 else np.nan,
            "Max drawdown": dd, "Worst month": m.min() if len(m) else np.nan,
            "Positive months": (m > 0).mean() if len(m) else np.nan}


def pct(x):
    return "" if pd.isna(x) else f"{x * 100:.1f}%"


def md_table(df):
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for row in df.itertuples(index=False):
        lines.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(lines)


def yearly(eq):
    y = eq.resample("YE").last()
    first = pd.Series([eq.iloc[0]], index=[eq.index[0]])
    y = pd.concat([first, y]).pct_change().dropna()
    y.index = y.index.year
    return y


def run(args):
    os.makedirs(OUT_DIR, exist_ok=True)
    notes = []
    if args.prices:
        close = pd.read_csv(args.prices, index_col=0, parse_dates=True)
        volume, missing, bench = None, [], {}
    else:
        symbols = load_universe()
        print(f"Universe: {len(symbols)} symbols; downloading from {args.start} ...", flush=True)
        close, volume, missing = download_prices(symbols, args.start)
        bench = download_benchmarks(args.start)
    close = close.dropna(how="all")
    close, repairs = repair_prices(close)
    if len(repairs):
        notes.append(f"{len(repairs)} unadjusted jumps in Yahoo prices (fall over 20% or rise over 60% in one day) "
                     "were repaired automatically.")
    if missing:
        notes.append(f"No usable Yahoo data for {len(missing)} symbols (excluded): " + ", ".join(missing[:40])
                     + (" ..." if len(missing) > 40 else ""))
    ranks = compute_ranks(close, volume, min_turnover_cr=args.min_turnover_cr)
    if ranks.empty:
        raise SystemExit("No rebalance date had enough eligible stocks; use an earlier --start.")
    print(f"{len(ranks)} monthly rankings, {ranks.notna().sum(axis=1).median():.0f} eligible stocks on average", flush=True)

    base = simulate(close, ranks, n=args.n, entry=args.entry, exit_=args.exit, cost_bps=args.cost_bps,
                    step=args.step, cash_rate=args.cash_rate, tax=False)
    taxed = simulate(close, ranks, n=args.n, entry=args.entry, exit_=args.exit, cost_bps=args.cost_bps,
                     step=args.step, cash_rate=args.cash_rate, tax=True)
    start = base["equity"].index[0]
    ew = equal_weight_universe(close, ranks, start=start)
    ew = ew / ew.iloc[0] * 100

    series = {"Strategy (after costs)": base["equity"]}
    tx = taxed["equity"].copy()
    tx.iloc[-1] -= taxed["pending_tax"]
    series["Strategy (after costs and tax)"] = tx
    series["All eligible stocks, equal weight"] = ew
    for name, s in bench.items():
        s = s[s.index >= start]
        if len(s) > 100:
            series[name] = s / s.iloc[0] * 100
    rows = []
    for name, s in series.items():
        st = stats(s)
        rows.append([name] + [pct(st["CAGR"]), pct(st["Total return"]), pct(st["Volatility"]),
                              f"{st['Sharpe (rf 5%)']:.2f}", pct(st["Max drawdown"]),
                              pct(st["Worst month"]), pct(st["Positive months"])])
    res = pd.DataFrame(rows, columns=["", "CAGR", "Total return", "Volatility", "Sharpe", "Max drawdown",
                                      "Worst month", "Positive months"])

    yr = pd.DataFrame({k: yearly(v) for k, v in series.items()})
    yr = yr.map(pct) if hasattr(yr, "map") else yr.applymap(pct)
    yr.insert(0, "Year", yr.index)

    grid = []
    for (en, ex, stp) in [(10, 30, 1), (20, 40, 1), (20, 60, 1), (30, 60, 1), (20, 40, 3), (20, 60, 3), (20, 20, 1)]:
        r = simulate(close, ranks, n=max(args.n, en), entry=en, exit_=ex, cost_bps=args.cost_bps, step=stp,
                     cash_rate=args.cash_rate)
        s = stats(r["equity"])
        grid.append([f"top {en}, exit below {ex}, every {stp} month(s)" + ("  <- your rule" if (en, ex, stp) == (20, 40, 1) else ""),
                     pct(s["CAGR"]), pct(s["Max drawdown"]), f"{s['Sharpe (rf 5%)']:.2f}", f"{r['turnover'] * 100:.0f}%"])
    grid = pd.DataFrame(grid, columns=["Rule", "CAGR", "Max drawdown", "Sharpe", "Yearly turnover"])

    costs = []
    for bps in (0, 15, 30, 60, 100):
        r = simulate(close, ranks, n=args.n, entry=args.entry, exit_=args.exit, cost_bps=bps, step=args.step,
                     cash_rate=args.cash_rate)
        s = stats(r["equity"])
        costs.append([f"{bps} bps per trade", pct(s["CAGR"]), pct(s["Max drawdown"]), f"{s['Sharpe (rf 5%)']:.2f}"])
    costs = pd.DataFrame(costs, columns=["Trading cost", "CAGR", "Max drawdown", "Sharpe"])

    tr = base["trades"]
    sells = tr[tr["side"] == "SELL"]
    per_year = len(tr) / base["years"]
    hold_days = []
    open_ = {}
    for r in tr.itertuples(index=False):
        if r.side == "BUY":
            open_[r.symbol] = r.date
        elif r.symbol in open_:
            hold_days.append((r.date - open_.pop(r.symbol)).days)
    win = (sells["gain"] > 0).mean() if len(sells) else np.nan
    info = pd.DataFrame([
        ["Period", f"{base['equity'].index[0].date()} to {base['equity'].index[-1].date()} ({base['years']:.1f} years)"],
        ["Rule", f"buy the top {args.entry}, hold up to {args.n}, sell when rank is below {args.exit}"],
        ["Rebalance", f"month-end signal, trade at the next day's close, every {args.step} month(s)"],
        ["Trading cost", f"{args.cost_bps:.0f} bps on every buy and every sell"],
        ["Average holdings", f"{base['holdings'].mean():.1f}"],
        ["Yearly turnover (buys + sells)", f"{base['turnover'] * 100:.0f}% of the portfolio"],
        ["Trades per year", f"{per_year:.0f}"],
        ["Average holding period", f"{np.mean(hold_days):.0f} days" if hold_days else "-"],
        ["Winning sales", pct(win)],
        ["Tax paid (approx.)", f"{taxed['tax_paid'] + taxed['pending_tax']:.1f} on a start of 100"],
    ], columns=["", ""])

    md = ["# Backtest: momentum top-%d / exit below rank %d\n" % (args.entry, args.exit),
          "> **Read this first.** The stock list is *today's* Nifty 500, so it contains only stocks that survived "
          "and grew into the index. That flatters every result. The row *All eligible stocks, equal weight* is the "
          "fair yardstick: it suffers the same bias, so only the **gap** between the strategy and that row says "
          "anything about the momentum rule. Past results do not predict future returns.\n",
          md_table(info), "\n## Results\n", md_table(res),
          "\nTax is a rough model: 20% on short-term gains, 12.5% on long-term gains (held 12+ months), netted per "
          "financial year with no exemption. Check current rates.\n",
          "\n## Year by year\n", md_table(yr.reset_index(drop=True)),
          "\n## Is the rule robust? (same data, other settings)\n",
          "A good rule works across neighbouring settings. If only one setting looks good, it is probably luck.\n",
          md_table(grid), "\n## How much do trading costs matter?\n", md_table(costs)]
    if notes:
        md.append("\n## Data notes\n\n" + "\n".join(f"- {n}" for n in notes))
    if len(repairs):
        rp = repairs.assign(date=repairs["date"].dt.strftime("%Y-%m-%d"))[["symbol", "date", "factor"]].head(25)
        md.append("\n<details><summary>Repaired jumps (first 25)</summary>\n\n" + md_table(rp) + "\n\n</details>")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 5))
        for name, s in series.items():
            ax.plot(s.index, s.values, label=name, lw=1.6 if "Strategy" in name else 1.0)
        ax.set_yscale("log")
        ax.set_title("Growth of 100 (log scale)")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(OUT_DIR, "backtest_equity.png"), dpi=110)
        md.insert(3, "\n![equity curve](backtest_equity.png)\n")
    except Exception as e:                                      # picture is optional
        notes.append(f"Chart not drawn ({type(e).__name__}).")
    text = "\n".join(md) + "\n"
    with open(os.path.join(OUT_DIR, "backtest.md"), "w", encoding="utf-8") as f:
        f.write(text)
    pd.DataFrame(series).to_csv(os.path.join(OUT_DIR, "backtest_equity.csv"), float_format="%.4f")
    tr.to_csv(os.path.join(OUT_DIR, "backtest_trades.csv"), index=False)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(text)
    print(text)
    return 0


def parse_args(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2014-01-01")
    ap.add_argument("--n", type=int, default=20, help="maximum number of holdings")
    ap.add_argument("--entry", type=int, default=20, help="buy only stocks ranked this well or better")
    ap.add_argument("--exit", type=int, default=40, help="sell when the rank is worse than this")
    ap.add_argument("--cost-bps", type=float, default=30.0, help="cost per buy or sell, in basis points")
    ap.add_argument("--step", type=int, default=1, help="rebalance every N months")
    ap.add_argument("--min-turnover-cr", type=float, default=5.0, help="minimum median daily traded value, Rs crore")
    ap.add_argument("--cash-rate", type=float, default=0.05, help="yearly return on idle cash")
    ap.add_argument("--prices", default=None, help="CSV of adjusted closes (date index, one column per stock)")
    return ap.parse_args(argv)


if __name__ == "__main__":
    sys.exit(run(parse_args()))
