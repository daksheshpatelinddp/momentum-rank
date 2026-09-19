"""Download NSE cash-market bhavcopy files and keep them in data/prices.csv.

* First run (or REBUILD=true): downloads about 460 calendar days of history.
* Later runs: downloads only the days after the last stored date.
* 404 = no file for that day (weekend / holiday / not published yet) -> skipped.
* Any real error stops the run but keeps everything downloaded so far.
"""
import io
import os
import sys
import time
import zipfile
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd
import requests

URL = ("https://nsearchives.nseindia.com/content/cm/"
       "BhavCopy_NSE_CM_0_0_0_{d}_F_0000.csv.zip")
STORE = "data/prices.csv"
BACKFILL_DAYS = 460
KEEP_DAYS = 500
SERIES_PRIORITY = {"EQ": 0, "BE": 1, "BZ": 2}
REQUIRED = ["TckrSymb", "SctySrs", "ClsPric", "PrvsClsgPric"]
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/all-reports",
}


class NotAZip(ValueError):
    pass


class BadFormat(ValueError):
    pass


class WrongDate(ValueError):
    pass


def parse_bhav(content, day):
    """Turn the bytes of a bhavcopy zip into a DataFrame [date, symbol, close, prev_close]."""
    if content[:2] != b"PK":
        raise NotAZip("response is not a zip file")
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise BadFormat("no csv file inside the zip")
        with z.open(names[0]) as f:
            raw = pd.read_csv(f, dtype=str)
    raw.columns = [str(c).strip() for c in raw.columns]

    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise BadFormat(f"missing columns {missing}; file has {list(raw.columns)}")

    if "TradDt" in raw.columns:
        d = pd.to_datetime(raw["TradDt"], errors="coerce").dropna()
        if len(d) and d.iloc[0].date() != day:
            raise WrongDate(f"file says {d.iloc[0].date()}, expected {day}")

    raw["SctySrs"] = raw["SctySrs"].str.strip().str.upper()
    raw = raw[raw["SctySrs"].isin(SERIES_PRIORITY)].copy()
    if raw.empty:
        raise BadFormat("no EQ/BE/BZ rows in file")

    raw["symbol"] = raw["TckrSymb"].str.strip().str.upper()
    raw["close"] = pd.to_numeric(raw["ClsPric"], errors="coerce")
    prev = pd.to_numeric(raw["PrvsClsgPric"], errors="coerce")
    raw["prev_close"] = prev.where(prev > 0)
    raw["prio"] = raw["SctySrs"].map(SERIES_PRIORITY)

    raw = raw[raw["close"] > 0]
    raw = raw.sort_values("prio").drop_duplicates("symbol")
    out = raw[["symbol", "close", "prev_close"]].copy()
    out.insert(0, "date", pd.Timestamp(day))
    return out.reset_index(drop=True)


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    try:                                    # warm-up request for cookies; failure is fine
        s.get("https://www.nseindia.com/", timeout=20)
    except requests.RequestException:
        pass
    return s


def fetch_day(session, day):
    """Return (status, DataFrame|None, note).

    status: ok      -> DataFrame returned
            none    -> NSE has no file for that day (404, or file for another date)
            denied  -> 403 or a non-zip answer (missing file OR NSE blocking us)
            error   -> server / network trouble even after retries
    """
    url = URL.format(d=day.strftime("%Y%m%d"))
    note = ""
    denied_tries = 0
    for attempt in range(4):
        try:
            r = session.get(url, timeout=40)
        except requests.RequestException as e:
            note = type(e).__name__
            time.sleep(4 * (attempt + 1))
            continue

        if r.status_code == 404:
            return "none", None, ""
        if r.status_code == 200:
            try:
                return "ok", parse_bhav(r.content, day), ""
            except WrongDate as e:
                return "none", None, str(e)
            except NotAZip:
                denied_tries += 1
                note = "200 but not a zip (NSE block page?)"
            except BadFormat as e:
                raise SystemExit(f"{day}: NSE file format changed -> {e}")
        elif r.status_code == 403:
            denied_tries += 1
            note = "HTTP 403"
        else:
            note = f"HTTP {r.status_code}"

        if denied_tries >= 2:
            return "denied", None, note
        time.sleep(4 * (attempt + 1))
    return "error", None, note


def load_store():
    if not os.path.exists(STORE):
        return None
    df = pd.read_csv(STORE, parse_dates=["date"])
    need = {"date", "symbol", "close", "prev_close"}
    if not need.issubset(df.columns):
        raise SystemExit(f"{STORE} has unexpected columns {list(df.columns)}; "
                         "run the workflow with 'rebuild' ticked.")
    return df


def save_store(df, today):
    cutoff = pd.Timestamp(today - dt.timedelta(days=KEEP_DAYS))
    df = df[df["date"] >= cutoff]
    df = df.drop_duplicates(["date", "symbol"], keep="last")
    df = df.sort_values(["date", "symbol"])
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    df.to_csv(STORE, index=False, date_format="%Y-%m-%d")
    return df


def main():
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    rebuild = os.environ.get("REBUILD", "false").strip().lower() == "true"
    store = None if rebuild else load_store()

    if store is None or store.empty:
        store = pd.DataFrame(columns=["date", "symbol", "close", "prev_close"])
        start = today - dt.timedelta(days=BACKFILL_DAYS)
        print(f"No stored history -> backfilling from {start}")
    else:
        start = store["date"].max().date() + dt.timedelta(days=1)
        print(f"Stored history ends {store['date'].max().date()} -> fetching from {start}")

    days = [start + dt.timedelta(days=n) for n in range((today - start).days + 1)]
    if not days:
        print("Already up to date.")
        return 0

    session = make_session()
    frames = []
    counts = {"ok": 0, "none": 0, "denied": 0, "error": 0}
    fatal = None

    for day in days:
        status, df, note = fetch_day(session, day)
        counts[status] += 1
        if status == "ok":
            frames.append(df)
            print(f"{day}  ok      {len(df)} symbols", flush=True)
        elif status == "error":
            fatal = f"{day}: {note} (server/network problem). Progress so far is saved; re-run later."
            break
        elif status == "denied" and counts["ok"] == 0 and counts["denied"] >= 6:
            fatal = (f"NSE refused {counts['denied']} requests in a row with no success "
                     f"(last: {note}). GitHub's servers are probably blocked by NSE.")
            break
        time.sleep(0.7)

    if frames:
        parts = ([store] if len(store) else []) + frames
        store = pd.concat(parts, ignore_index=True)
        store["date"] = pd.to_datetime(store["date"])

    if len(store):
        store = save_store(store, today)
        print(f"Saved {STORE}: {len(store):,} rows, {store['date'].nunique()} trading days, "
              f"{store['date'].min().date()} -> {store['date'].max().date()}")

    print(f"Summary: {counts}")
    if fatal:
        print("ERROR:", fatal)
        return 1
    if not frames:
        print("No new files (weekend, holiday, or today's file not published yet). "
              "That is normal.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
