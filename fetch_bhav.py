#!/usr/bin/env python3
"""Download NSE cash-market bhavcopy files into data/ (one small file per trading day).

- Fetches every weekday in the last ~460 days that is not already stored, newest first.
  Holidays simply return "not found" and are skipped; they are re-checked cheaply each run,
  so a day missed by a glitch heals itself on the next run.
- Stops with a clear error if NSE blocks the requests or changes its file format.
"""
import datetime as dt
import io
import os
import sys
import time
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests

BASE_URL = os.environ.get("BHAV_BASE_URL", "https://nsearchives.nseindia.com/content/cm").rstrip("/")
FILE_FMT = "BhavCopy_NSE_CM_0_0_0_{ymd}_F_0000.csv.zip"
DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
PAUSE = float(os.environ.get("BHAV_PAUSE", "0.7"))          # polite delay between requests
RETRY_SLEEP = float(os.environ.get("BHAV_RETRY_SLEEP", "3"))

HISTORY_DAYS = 460          # calendar days of history to keep available
KEEP_DAYS = 540             # older files are deleted
SERIES = {"EQ", "BE"}       # normal and trade-to-trade equity series
MIN_ROWS_PER_DAY = 300      # a real file has ~2000 rows; fewer means a bad/partial file
NEEDED = ["TckrSymb", "SctySrs", "ClsPric", "PrvsClsgPric"]

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}


class FormatChanged(Exception):
    """NSE changed the file layout: needs a human to update the script."""


def get_day(session, day):
    """Return the zip bytes for `day`, or None if NSE has no file (holiday / not yet published)."""
    url = f"{BASE_URL}/{FILE_FMT.format(ymd=day.strftime('%Y%m%d'))}"
    err = "unknown error"
    for attempt in range(1, 5):
        try:
            r = session.get(url, timeout=(10, 60))
        except requests.RequestException as exc:
            err = repr(exc)
        else:
            if r.status_code == 200:
                return r.content
            if r.status_code == 404:
                return None
            if r.status_code == 403 and attempt >= 2:
                return None          # NSE's archive answers 403 for some missing files
            err = f"HTTP {r.status_code}"
        time.sleep(RETRY_SLEEP * attempt)
    raise RuntimeError(f"{day}: giving up after 4 tries ({err})")


def parse_bhav(content, day):
    """Turn a bhavcopy zip into a DataFrame [symbol, close, prev_close]."""
    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise FormatChanged(f"{day}: no CSV inside the zip file")
        with zf.open(names[0]) as fh:
            raw = pd.read_csv(fh)
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in NEEDED if c not in raw.columns]
    if missing:
        raise FormatChanged(f"{day}: columns {missing} not found. Header is: {list(raw.columns)}")

    if "TradDt" in raw.columns and len(raw):
        file_day = pd.to_datetime(str(raw["TradDt"].iloc[0]).strip(), format="%Y-%m-%d", errors="coerce")
        if pd.notna(file_day) and file_day.date() != day:
            raise ValueError(f"file contains {file_day.date()} instead of {day}")

    raw = raw[raw["SctySrs"].astype(str).str.strip().isin(SERIES)]
    out = pd.DataFrame({
        "symbol": raw["TckrSymb"].astype(str).str.strip().str.upper(),
        "close": pd.to_numeric(raw["ClsPric"], errors="coerce"),
        "prev_close": pd.to_numeric(raw["PrvsClsgPric"], errors="coerce"),
    })
    out = out.dropna()
    out = out[(out["close"] > 0) & (out["prev_close"] > 0)]
    return out.drop_duplicates("symbol", keep="first").reset_index(drop=True)


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    window_start = today - dt.timedelta(days=HISTORY_DAYS)
    have = {p.name[:10] for p in DATA_DIR.glob("*.csv.gz")}

    todo, d = [], today
    while d >= window_start:                      # newest first
        if d.weekday() < 5 and d.isoformat() not in have:
            todo.append(d)
        d -= dt.timedelta(days=1)
    print(f"Stored days: {len(have)} | weekdays to check: {len(todo)}")

    session = requests.Session()
    session.headers.update(HEADERS)
    saved = absent_streak = 0

    def check_blocked():
        if saved == 0 and absent_streak >= 15 and len(have) < 200:
            sys.exit("ERROR: the first 15 requests returned nothing usable. NSE is probably blocking "
                     "this server (or the URL changed). See the README 'If NSE blocks' section.")

    for day in todo:
        content = get_day(session, day)
        if content is None:
            absent_streak += 1
            check_blocked()
            time.sleep(PAUSE)
            continue
        try:
            df = parse_bhav(content, day)
        except FormatChanged as exc:
            sys.exit(f"ERROR: NSE file format changed - {exc}")
        except (zipfile.BadZipFile, ValueError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
            print(f"WARNING: {day} skipped ({exc}); it will be retried next run")
            absent_streak += 1
            check_blocked()
            time.sleep(PAUSE)
            continue
        if len(df) < MIN_ROWS_PER_DAY:
            print(f"WARNING: {day} has only {len(df)} rows; skipped, will be retried next run")
            time.sleep(PAUSE)
            continue
        df.to_csv(DATA_DIR / f"{day.isoformat()}.csv.gz", index=False, compression="gzip")
        saved += 1
        absent_streak = 0
        have.add(day.isoformat())
        if saved % 25 == 0:
            print(f"  ...{saved} days downloaded")
        time.sleep(PAUSE)

    cutoff = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
    removed = 0
    for p in DATA_DIR.glob("*.csv.gz"):
        if p.name[:10] < cutoff:
            p.unlink()
            removed += 1

    dates = sorted(p.name[:10] for p in DATA_DIR.glob("*.csv.gz"))
    print(f"Downloaded {saved} new day(s), removed {removed} old file(s). "
          f"Stored: {len(dates)} days ({dates[0] if dates else '-'} to {dates[-1] if dates else '-'})")
    if not dates or (today - dt.date.fromisoformat(dates[-1])).days > 7:
        sys.exit("ERROR: no recent data (newest file is older than 7 days). "
                 "NSE may be blocking requests or the URL/format changed.")


if __name__ == "__main__":
    main()
