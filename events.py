"""Corporate actions (bonus / split) used to adjust NSE prices.

Sources, in order of trust:
  1. corporate_actions.csv  - your own list; always trusted, always wins
  2. NSE's own adjusted previous close (bonus, split, rights, demerger, spin-off, anything):
       a. the second daily file (sec_bhavdata_full), stored by fetch_bhav.py as adj_prev
       b. NSE's website history API
     A source is used ONLY after it reproduces the known events in corporate_actions.csv.
  3. Yahoo Finance splits   - fallback for bonus/split, accepted only when NSE prices show the drop
Stocks that no source could check are reported as "unverified".
"""
import os
import time
from urllib.parse import quote

import numpy as np
import pandas as pd

MANUAL_FILE = "corporate_actions.csv"
CONFIRM_TOL = 0.30            # |log(raw 1-day ratio / expected factor)| allowed when confirming
COLS = ["symbol", "date", "factor", "source", "note"]
EVENT_TOL = 0.015             # ignore |factor - 1| below 1.5 % (rounding noise)
FACTOR_TOL = 0.03             # a source "reproduces" a known event if factors agree within 3 %


def load_manual(path=MANUAL_FILE):
    """Read corporate_actions.csv. factor may be a number or the word auto (= estimate it from
    NSE prices on the ex-date)."""
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
    raw_factor = df["factor"].str.strip().str.lower()
    is_auto = raw_factor == "auto"
    df["factor"] = pd.to_numeric(raw_factor.where(~is_auto), errors="coerce")
    df["note"] = df["note"].fillna("").str.strip()
    bad = df[df["ex_date"].isna() | (df["factor"].isna() & ~is_auto) | (df["factor"] <= 0)]
    if len(bad):
        raise SystemExit(f"{path} has invalid rows for: {', '.join(bad['symbol'])}. "
                         "Use YYYY-MM-DD dates and a positive factor (or the word auto).")
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


def estimate_factor(series, date, market_move=None):
    """Estimate the price factor of an event from NSE prices alone: the ex-date's raw 1-day
    price ratio with the market's typical move that day removed. Rough (a few %), exact
    factors from the announcement are better."""
    s = series.dropna()
    if date not in s.index:
        return None
    pos = s.index.get_loc(date)
    if pos == 0:
        return None
    ratio = float(s.iloc[pos] / s.iloc[pos - 1])
    m = 0.0
    if market_move is not None and date in market_move.index and pd.notna(market_move[date]):
        m = float(market_move[date])
    return round(ratio / (1.0 + m), 4)


def _near_existing(existing, symbol, date, days):
    return any(e[0] == symbol and abs((e[1] - date).days) <= days for e in existing)


def build_events(raw_px, manual, yahoo, exchange=None, dedupe_days=3, market_move=None):
    """Combine manual + exchange + confirmed Yahoo events. Returns (events, rejected_yahoo)."""
    out, rejected = [], []
    first, last = raw_px.index.min(), raw_px.index.max()

    for r in manual.itertuples(index=False):
        if r.symbol in raw_px.columns and first < r.ex_date <= last:
            if pd.isna(r.factor):                              # factor = auto
                f = estimate_factor(raw_px[r.symbol], r.ex_date, market_move)
                if f is None:
                    continue
                out.append((r.symbol, r.ex_date, f, "manual (estimated)", r.note))
            else:
                out.append((r.symbol, r.ex_date, float(r.factor), "manual", r.note))

    if exchange is not None:
        for r in exchange.itertuples(index=False):
            if r.symbol not in raw_px.columns or not (first < r.date <= last):
                continue
            if _near_existing(out, r.symbol, r.date, dedupe_days):
                continue
            out.append((r.symbol, r.date, float(r.factor), r.source, ""))

    trusted = list(out)
    for r in yahoo.itertuples(index=False):
        if r.symbol not in raw_px.columns:
            continue
        if _near_existing(trusted, r.symbol, r.date, dedupe_days):
            continue
        d = align_event(raw_px[r.symbol], r.date, r.factor)
        if d is None:
            rejected.append((r.symbol, r.date, r.factor))
            continue
        out.append((r.symbol, d, float(r.factor), "yahoo", ""))

    ev = pd.DataFrame(out, columns=COLS).drop_duplicates(["symbol", "date"])
    ev = ev.sort_values(["date", "symbol"]).reset_index(drop=True)
    return ev, rejected


# ---------------------------------------------------------------------------------------
# Exchange-derived events
# ---------------------------------------------------------------------------------------
def _ratio_events(df, prev_col, close_col, source, tol=EVENT_TOL):
    """df: columns symbol, date, close_col, prev_col (sorted by symbol/date)."""
    prev_row = df.groupby("symbol")[close_col].shift(1)
    ratio = (df[prev_col] / prev_row).replace([np.inf, -np.inf], np.nan)
    is_ev = ratio.notna() & ((ratio - 1).abs() > tol) & (ratio > 0.005) & (ratio < 200)
    # data-gap guard: a missing trading day makes EVERY stock look like it had an event
    n_all = df.groupby("date")["symbol"].transform("size")
    n_ev = is_ev.astype(int).groupby(df["date"]).transform("sum")
    gap = (n_ev >= 30) & (n_ev / n_all > 0.05)
    keep = is_ev & ~gap
    ev = df.loc[keep, ["symbol", "date"]].copy()
    ev["factor"] = ratio[keep].to_numpy()
    ev["source"] = source
    ev["note"] = ""
    return ev.reset_index(drop=True)


def derive_from_store(store, min_coverage=0.9):
    """Events from NSE's second daily file (column adj_prev). Returns (events|None, note)."""
    if "adj_prev" not in store.columns:
        return None, "the stored data has no adjusted-previous-close column yet"
    df = store[["date", "symbol", "close", "adj_prev"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    all_days = df["date"].nunique()
    with_alt = df.loc[df["adj_prev"].notna(), "date"].nunique()
    cov = with_alt / max(all_days, 1)
    if cov < min_coverage:
        return None, f"file available for only {cov:.0%} of stored days"
    df = df.drop_duplicates(["date", "symbol"], keep="last")
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    return _ratio_events(df, "adj_prev", "close", "nse-file"), "ok"


def _api_rows(session, sym, a, b):
    url = ("https://www.nseindia.com/api/historical/cm/equity?symbol="
           f"{quote(sym)}&series=[%22EQ%22]&from={a:%d-%m-%Y}&to={b:%d-%m-%Y}")
    r = session.get(url, timeout=40)
    if r.status_code != 200:
        raise ConnectionError(f"HTTP {r.status_code}")
    return r.json().get("data", [])


def _api_session():
    import requests
    s = requests.Session()
    s.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
        "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/report-detail/eq_security"})
    try:
        s.get("https://www.nseindia.com/", timeout=20)
    except Exception:
        pass
    return s


def fetch_api_history(symbols, start, end, getter=None, chunk_days=90, pause=0.4):
    """NSE website history API: per stock, date + previous close + close.
    Returns ({symbol: DataFrame[date, prev, close]}, {symbol: reason}). Stops early when the
    very first request is refused (GitHub blocked)."""
    if getter is None:
        session = _api_session()
        getter = lambda sym, a, b: _api_rows(session, sym, a, b)
    frames, failed = {}, {}
    n_ok, n_fail = 0, 0
    for sym in symbols:
        rows, err = [], None
        a = start
        while a <= end:
            b = min(a + pd.Timedelta(days=chunk_days - 1), end)
            try:
                rows += list(getter(sym, a.date(), b.date()))
                n_ok += 1
            except Exception as e:
                err = f"{type(e).__name__}: {e}"
                n_fail += 1
                break
            time.sleep(pause)
            a = b + pd.Timedelta(days=1)
        if err:
            failed[sym] = err
            if n_ok == 0 and n_fail >= 2:                # refused from the very start
                for rest in symbols:
                    failed.setdefault(rest, err)
                break
            continue
        recs = []
        for x in rows:
            try:
                recs.append((pd.Timestamp(x["CH_TIMESTAMP"]).normalize(),
                             float(x["CH_PREVIOUS_CLS_PRICE"]), float(x["CH_CLOSING_PRICE"])))
            except (KeyError, TypeError, ValueError):
                continue
        if recs:
            df = pd.DataFrame(recs, columns=["date", "prev", "close"])
            frames[sym] = df.drop_duplicates("date").sort_values("date").reset_index(drop=True)
        else:
            failed[sym] = "empty answer"
    return frames, failed


def events_from_api(frames):
    parts = []
    for sym, df in frames.items():
        d = df.copy()
        d["symbol"] = sym
        parts.append(d)
    if not parts:
        return pd.DataFrame(columns=COLS)
    big = pd.concat(parts, ignore_index=True).sort_values(["symbol", "date"]).reset_index(drop=True)
    return _ratio_events(big, "prev", "close", "nse-api")


def validate(found, manual, checkable):
    """Does this source reproduce the events you listed in corporate_actions.csv?"""
    hits, misses = [], []
    for m in manual.itertuples(index=False):
        if pd.isna(m.factor) or not checkable(m.symbol, m.ex_date):
            continue
        near = found[(found["symbol"] == m.symbol) &
                     ((found["date"] - m.ex_date).abs() <= pd.Timedelta(days=4))]
        seen = [round(float(x), 4) for x in near["factor"]]
        rec = (m.symbol, m.ex_date.strftime("%Y-%m-%d"), float(m.factor), seen)
        if any(abs(x / m.factor - 1) <= FACTOR_TOL for x in seen):
            hits.append(rec)
        else:
            misses.append(rec)
    passed = len(hits) >= 1 and len(hits) >= len(misses)
    return passed, hits, misses


def _describe(name, passed, hits, misses):
    total = len(hits) + len(misses)
    lines = []
    if passed:
        lines.append(f"{name}: VALIDATED - reproduced {len(hits)} of {total} known events, "
                     "so it is used for every bonus, split, rights issue and demerger.")
    else:
        lines.append(f"{name}: NOT used - it reproduced only {len(hits)} of {total} known events "
                     "(its previous close is not adjusted for corporate actions).")
    for sym, d, f, seen in misses:
        lines.append(f"   expected {sym} {d} factor {f}, source showed {seen or 'no change'}")
    return lines


def gather_events(store, raw_px, symbols, manual, get_splits=None, api_getter=None,
                  skip_yahoo=False, skip_api=False):
    """Return (events, rejected_yahoo, status_lines, unverified_symbols)."""
    status = []
    exchange = None
    covered = set()
    have = [s for s in symbols if s in raw_px.columns]

    # (a) NSE second daily file, stored by fetch_bhav.py
    evA, noteA = derive_from_store(store)
    if evA is None:
        status.append(f"NSE daily file (adjusted previous close): not usable - {noteA}.")
    else:
        rows = store.loc[store["symbol"].isin(manual["symbol"]), ["date", "symbol", "adj_prev"]].dropna()
        have_alt = set(zip(pd.to_datetime(rows["date"]), rows["symbol"]))
        checkable = lambda s, d: (d, s) in have_alt
        passed, hits, misses = validate(evA, manual, checkable)
        if hits or misses:
            status += _describe("NSE daily file", passed, hits, misses)
        else:
            status.append("NSE daily file: cannot be validated (no known event in "
                          "corporate_actions.csv falls inside the stored data) - not used.")
        if passed:
            exchange, covered = evA[evA["symbol"].isin(have)], set(have)

    # (b) NSE website API, only if (a) did not work
    if not covered and not skip_api:
        first = pd.Timestamp(raw_px.index.min())
        last = pd.Timestamp(raw_px.index.max())
        man_syms = [s for s in manual["symbol"].unique() if s in raw_px.columns]
        todo = list(dict.fromkeys(have + man_syms))
        frames, failed = fetch_api_history(todo, first, last, getter=api_getter)
        if not frames:
            why = next(iter(failed.values()), "no answer")
            status.append(f"NSE website API: not usable - {why}.")
        else:
            evB = events_from_api(frames)
            checkable = lambda s, d: s in frames and frames[s]["date"].min() < d <= frames[s]["date"].max()
            passed, hits, misses = validate(evB, manual, checkable)
            if hits or misses:
                status += _describe("NSE website API", passed, hits, misses)
            else:
                status.append("NSE website API: cannot be validated - not used.")
            if passed:
                exchange = evB[evB["symbol"].isin(have)]
                covered = {s for s in have if s in frames}
                if failed:
                    status.append("NSE website API failed for: " + ", ".join(sorted(
                        s for s in failed if s in have)) + " (Yahoo fallback used)")

    # (c) Yahoo for whatever the exchange sources did not cover
    rest = [s for s in have if s not in covered]
    yahoo = pd.DataFrame(columns=["symbol", "date", "factor"])
    y_failed = {}
    if rest and not skip_yahoo:
        kw = {"get_splits": get_splits} if get_splits else {}
        yahoo, y_failed = fetch_yahoo(rest, since=pd.Timestamp(raw_px.index.min()), **kw)
        n_ok = len(rest) - len(y_failed)
        status.append(f"Yahoo Finance (bonus/split only): checked {n_ok} of {len(rest)} stocks"
                      + (f"; failed for {', '.join(sorted(y_failed))}" if y_failed else "") + ".")
    elif rest:
        y_failed = {s: "skipped" for s in rest}

    ok_rows = store[(store["prev_close"] > 0) & (store["close"] > 0)]
    mm = (ok_rows["close"] / ok_rows["prev_close"] - 1).groupby(pd.to_datetime(ok_rows["date"])).median()
    events, rejected = build_events(raw_px[have], manual, yahoo, exchange, market_move=mm)
    manual_syms = set(manual["symbol"])
    unverified = [s for s in rest if s in y_failed and s not in manual_syms]
    return events, rejected, status, unverified, mm
