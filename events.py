"""Corporate actions (bonus / split) used to adjust NSE prices.

Two sources are combined:
  1. corporate_actions.csv  - your own list; always trusted, always wins
  2. Yahoo Finance splits   - fetched automatically for the symbols you rank, and only
                              accepted when NSE's own prices show the matching price drop
If Yahoo cannot be reached for a stock, that stock is reported as "unverified".
"""
import os
import time

import numpy as np
import pandas as pd

MANUAL_FILE = "corporate_actions.csv"
CONFIRM_TOL = 0.30            # |log(raw 1-day ratio / expected factor)| allowed when confirming
COLS = ["symbol", "date", "factor", "source", "note"]


def load_manual(path=MANUAL_FILE):
    empty = pd.DataFrame(columns=["symbol", "ex_date", "factor", "note"])
    if not os.path.exists(path):
        return empty
    try:
        df = pd.read_csv(path, comment="#", dtype=str, skipinitialspace=True)
    except pd.errors.EmptyDataError:
        return empty
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"symbol", "ex_date", "factor"}
    if not need.issubset(df.columns):
        raise SystemExit(f"{path} must have the columns: symbol,ex_date,factor,note")
    if "note" not in df.columns:
        df["note"] = ""
    df = df.dropna(subset=["symbol", "ex_date", "factor"]).copy()
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["ex_date"] = pd.to_datetime(df["ex_date"].str.strip(), errors="coerce")
    df["factor"] = pd.to_numeric(df["factor"].str.strip(), errors="coerce")
    df["note"] = df["note"].fillna("").str.strip()
    bad = df[df["ex_date"].isna() | df["factor"].isna() | (df["factor"] <= 0)]
    if len(bad):
        raise SystemExit(f"{path} has invalid rows for: {', '.join(bad['symbol'])}. "
                         "Use YYYY-MM-DD dates and a positive factor.")
    return df[["symbol", "ex_date", "factor", "note"]].reset_index(drop=True)


def _yahoo_splits(symbol):
    import yfinance as yf
    return yf.Ticker(symbol + ".NS").splits


def fetch_yahoo(symbols, since, get_splits=_yahoo_splits, pause=0.3):
    """Return (DataFrame[symbol, date, factor], {symbol: reason it failed})."""
    rows, failed = [], {}
    for s in symbols:
        try:
            sp = get_splits(s)
        except Exception as e:                       # network, rate limit, unknown symbol ...
            failed[s] = type(e).__name__
            time.sleep(pause)
            continue
        if sp is None:
            failed[s] = "no answer"
            continue
        for d, v in sp.items():
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v) or v <= 0 or abs(v - 1) < 1e-9:
                continue
            d = pd.Timestamp(d)
            if d.tzinfo is not None:
                d = d.tz_localize(None)
            d = d.normalize()
            if d >= since:
                rows.append((s, d, 1.0 / v))         # Yahoo ratio 4/3 (1:3 bonus) -> factor 0.75
        time.sleep(pause)
    return pd.DataFrame(rows, columns=["symbol", "date", "factor"]), failed


def align_event(series, date, factor, tol=CONFIRM_TOL, tie=0.03):
    """Find the trading day (the Yahoo date, the trading day before it, or the one after) on
    which the RAW NSE close really shows the event: the day whose 1-day price ratio is closest
    to `factor`. The Yahoo date is preferred only when it is practically as good as the best
    day. Returns None when NSE prices show no such drop (event not confirmed)."""
    s = series.dropna()
    if len(s) < 3:
        return None
    r = s / s.shift(1)
    pos = int(r.index.searchsorted(date))
    scores = {}
    for d in list(r.index[max(0, pos - 1): pos + 2]):
        v = r[d]
        if pd.isna(v) or v <= 0:
            continue
        scores[d] = abs(np.log(v / factor))
    if not scores:
        return None
    best_d = min(scores, key=scores.get)
    if scores[best_d] > tol:
        return None
    if date in scores and scores[date] <= scores[best_d] + tie:
        return date
    return best_d


def build_events(raw_px, manual, yahoo, dedupe_days=3):
    """Combine manual + confirmed Yahoo events. Returns (events, rejected_yahoo_events)."""
    out, rejected = [], []
    first, last = raw_px.index.min(), raw_px.index.max()

    for r in manual.itertuples(index=False):
        if r.symbol in raw_px.columns and first < r.ex_date <= last:
            out.append((r.symbol, r.ex_date, float(r.factor), "manual", r.note))

    manual_events = list(out)
    for r in yahoo.itertuples(index=False):
        if r.symbol not in raw_px.columns:
            continue
        if any(m[0] == r.symbol and abs((m[1] - r.date).days) <= dedupe_days
               for m in manual_events):
            continue
        d = align_event(raw_px[r.symbol], r.date, r.factor)
        if d is None:
            rejected.append((r.symbol, r.date, r.factor))
            continue
        out.append((r.symbol, d, float(r.factor), "yahoo", ""))

    ev = pd.DataFrame(out, columns=COLS).drop_duplicates(["symbol", "date"])
    ev = ev.sort_values(["date", "symbol"]).reset_index(drop=True)
    return ev, rejected
