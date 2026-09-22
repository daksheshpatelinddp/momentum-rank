"""Download NSE index level history (Nifty 50, Nifty 200, etc.) so the index_sma200 filter in
backtest2.py can use the REAL index instead of its equal-weight-universe proxy.

Saves data/index_<name>.csv (date, close), one file per index named in INDEX_TYPES below.
Untested against NSE's live site from this environment - if the field names have changed,
this prints the raw keys it saw so the fix is a one-line change, not a guess.
"""
import io
import os
import sys
import time
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
import requests

URL = "https://www.nseindia.com/api/historical/indicesHistory"
INDEX_TYPES = {
    "nifty50": "NIFTY 50",
    "nifty100": "NIFTY 100",
    "nifty200": "NIFTY 200",
    "nifty500": "NIFTY 500",
    "niftymidcap100": "NIFTY MIDCAP 100",
    "niftysmallcap100": "NIFTY SMALLCAP 100",
}
DEFAULT_START = "2013-01-01"
CHUNK_DAYS = 360
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/reports-indices-historical-index-data",
}


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get("https://www.nseindia.com/", timeout=20)
    except requests.RequestException:
        pass
    return s


def _pick(row, *names):
    lut = {str(k).strip().lower().replace("_", "").replace(" ", ""): v for k, v in row.items()}
    for n in names:
        v = lut.get(n.strip().lower().replace("_", "").replace(" ", ""))
        if v is not None and str(v).strip() not in ("", "None", "nan", "-"):
            return v
    return None


def _rows_from_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "Data"):
            if isinstance(data.get(key), dict):
                for k2 in ("indexCloseOnlineRecords", "indexOnlyRecords", "indexTurnoverRecords"):
                    if isinstance(data[key].get(k2), list) and data[key][k2]:
                        return data[key][k2]
            if isinstance(data.get(key), list):
                return data[key]
    return []


def fetch_one(session, index_type, start, end, chunk_days=CHUNK_DAYS, pause=0.5):
    """Return (DataFrame[date, close], error_or_None, sample_record)."""
    rows, sample = [], None
    a = pd.Timestamp(start)
    end = pd.Timestamp(end)
    while a <= end:
        b = min(a + pd.Timedelta(days=chunk_days - 1), end)
        params = {"indexType": index_type, "from": a.strftime("%d-%m-%Y"), "to": b.strftime("%d-%m-%Y")}
        try:
            r = session.get(URL, params=params, timeout=60)
        except requests.RequestException as e:
            return pd.DataFrame(columns=["date", "close"]), f"{type(e).__name__}: {e}", sample
        if r.status_code != 200:
            return pd.DataFrame(columns=["date", "close"]), f"HTTP {r.status_code}", sample
        try:
            data = r.json()
        except ValueError:
            return pd.DataFrame(columns=["date", "close"]), "answer is not JSON (blocked?)", sample
        recs = _rows_from_json(data)
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            if sample is None:
                sample = {k: rec[k] for k in list(rec)[:10]}
            d = _pick(rec, "EOD_TIMESTAMP", "HistoricalDate", "Date", "TIMESTAMP")
            c = _pick(rec, "EOD_CLOSE_INDEX_VAL", "CLOSE", "Close", "closeIndexVal")
            if d is None or c is None:
                continue
            dd = pd.to_datetime(str(d), errors="coerce", dayfirst=True)
            cc = pd.to_numeric(str(c).replace(",", ""), errors="coerce")
            if pd.notna(dd) and pd.notna(cc):
                rows.append((dd.normalize(), float(cc)))
        time.sleep(pause)
        a = b + pd.Timedelta(days=1)
    df = pd.DataFrame(rows, columns=["date", "close"]).drop_duplicates("date").sort_values("date")
    if df.empty:
        return df, "no usable records found" + (f" (fields seen: {list(sample)})" if sample else ""), sample
    return df.reset_index(drop=True), None, sample


def main():
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    want = os.environ.get("INDEX_NAMES", "").strip()
    names = [n.strip() for n in want.split(",") if n.strip()] or list(INDEX_TYPES)
    start = os.environ.get("HISTORY_START", DEFAULT_START).strip()
    session = make_session()
    os.makedirs("data", exist_ok=True)
    any_ok, any_fail = False, False

    for name in names:
        idx_type = INDEX_TYPES.get(name)
        if idx_type is None:
            print(f"{name}: not a recognised index name, skipped.")
            continue
        path = f"data/index_{name}.csv"
        fetch_from = start
        existing = None
        if os.path.exists(path):
            existing = pd.read_csv(path, parse_dates=["date"])
            fetch_from = (existing["date"].max() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
            if pd.Timestamp(fetch_from) > pd.Timestamp(today):
                print(f"{name}: already up to date ({existing['date'].max().date()}).")
                any_ok = True
                continue
        df, err, sample = fetch_one(session, idx_type, fetch_from, today)
        if err:
            print(f"{name}: not usable - {err}")
            any_fail = True
            continue
        if existing is not None and len(existing):
            df = pd.concat([existing, df]).drop_duplicates("date").sort_values("date")
        df.to_csv(path, index=False)
        print(f"{name}: saved {path}, {len(df)} rows, {df['date'].min().date()} -> {df['date'].max().date()}")
        any_ok = True

    if any_fail and not any_ok:
        print("No index history could be downloaded. The index_sma200 filter will keep using "
             "the equal-weight-universe proxy until this works.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
