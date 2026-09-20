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

import numpy as np
import pandas as pd
import requests

URL = ("https://nsearchives.nseindia.com/content/cm/"
       "BhavCopy_NSE_CM_0_0_0_{d}_F_0000.csv.zip")
SEC_URL = ("https://nsearchives.nseindia.com/products/content/"
           "sec_bhavdata_full_{d}.csv")
STORE = "data/prices.csv"
STORE_COLS = ["date", "symbol", "close", "prev_close", "adj_prev"]
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


def fetch_day(session, day, url_tmpl=URL, parser=None, datefmt="%Y%m%d", retry_sleep=4):
    """Return (status, DataFrame|None, note).

    status: ok      -> DataFrame returned
            none    -> NSE has no file for that day (404, or file for another date)
            denied  -> 403 or a non-zip answer (missing file OR NSE blocking us)
            error   -> server / network trouble even after retries
    """
    parser = parser or parse_bhav
    url = url_tmpl.format(d=day.strftime(datefmt))
    note = ""
    denied_tries = 0
    for attempt in range(4):
        try:
            r = session.get(url, timeout=40)
        except requests.RequestException as e:
            note = type(e).__name__
            time.sleep(retry_sleep * (attempt + 1))
            continue

        if r.status_code == 404:
            return "none", None, ""
        if r.status_code == 200:
            try:
                return "ok", parser(r.content, day), ""
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
        time.sleep(retry_sleep * (attempt + 1))
    return "error", None, note


def parse_sec(text, day):
    """NSE's second daily file. Returns Series symbol -> PREV_CLOSE (the value that may be
    adjusted for corporate actions on ex-dates)."""
    df = pd.read_csv(io.StringIO(text), skipinitialspace=True, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    for c in ("SYMBOL", "SERIES", "PREV_CLOSE"):
        if c not in df.columns:
            raise BadFormat(f"sec_bhavdata_full: missing column {c}")
    if "DATE1" in df.columns:
        d = pd.to_datetime(df["DATE1"].astype(str).str.strip(), format="%d-%b-%Y",
                           errors="coerce").dropna()
        if len(d) and d.iloc[0].date() != day:
            raise WrongDate(f"file says {d.iloc[0].date()}, expected {day}")
    df["SERIES"] = df["SERIES"].astype(str).str.strip().str.upper()
    df = df[df["SERIES"].isin(SERIES_PRIORITY)].copy()
    df["symbol"] = df["SYMBOL"].astype(str).str.strip().str.upper()
    df["prev"] = pd.to_numeric(df["PREV_CLOSE"].astype(str).str.strip(), errors="coerce")
    df["prio"] = df["SERIES"].map(SERIES_PRIORITY)
    df = df[df["prev"] > 0].sort_values("prio").drop_duplicates("symbol")
    if df.empty:
        raise BadFormat("sec_bhavdata_full: no usable rows")
    return df.set_index("symbol")["prev"]


def fetch_sec_prev(session, day):
    """Best-effort download of the second daily file. Returns Series or None (never raises)."""
    url = SEC_URL.format(d=day.strftime("%d%m%Y"))
    for attempt in range(2):
        try:
            r = session.get(url, timeout=40)
        except requests.RequestException:
            time.sleep(3)
            continue
        if r.status_code == 200:
            try:
                return parse_sec(r.text, day)
            except ValueError:
                return None
        if r.status_code in (403, 404):
            return None
        time.sleep(3)
    return None


class AltFetcher:
    """Wraps fetch_sec_prev and switches itself off if NSE keeps refusing."""

    def __init__(self, session):
        self.session, self.ok, self.fail, self.off = session, 0, 0, False

    def get(self, day):
        if self.off:
            return None
        s = fetch_sec_prev(self.session, day)
        if s is None:
            self.fail += 1
            if self.ok == 0 and self.fail >= 6:
                self.off = True
                print("NOTE: NSE's second daily file is not available; skipping it.")
        else:
            self.ok += 1
        time.sleep(0.5)
        return s


def fill_adj_prev(store, alt):
    """Add the adj_prev column for stored days that do not have it yet."""
    dates = sorted(store["date"].unique())
    parts = []
    for i, d in enumerate(dates):
        s = alt.get(pd.Timestamp(d).date())
        if s is not None:
            parts.append(pd.DataFrame({"date": pd.Timestamp(d), "symbol": s.index,
                                       "adj_prev2": s.to_numpy()}))
        if alt.off:
            break
        if (i + 1) % 50 == 0:
            print(f"  filled {i + 1}/{len(dates)} days", flush=True)
    store = store.copy()
    if "adj_prev" not in store.columns:
        store["adj_prev"] = np.nan
    if parts:
        add = pd.concat(parts, ignore_index=True)
        store = store.merge(add, on=["date", "symbol"], how="left")
        store["adj_prev"] = store["adj_prev"].fillna(store["adj_prev2"])
        store = store.drop(columns=["adj_prev2"])
    return store


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
    if "adj_prev" not in df.columns:
        df["adj_prev"] = np.nan
    df = df[STORE_COLS]
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    df.to_csv(STORE, index=False, date_format="%Y-%m-%d")
    return df


def main():
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    rebuild = os.environ.get("REBUILD", "false").strip().lower() == "true"
    store = None if rebuild else load_store()

    if store is None or store.empty:
        store = pd.DataFrame(columns=STORE_COLS)
        start = today - dt.timedelta(days=BACKFILL_DAYS)
        print(f"No stored history -> backfilling from {start}")
    else:
        start = store["date"].max().date() + dt.timedelta(days=1)
        print(f"Stored history ends {store['date'].max().date()} -> fetching from {start}")

    days = [start + dt.timedelta(days=n) for n in range((today - start).days + 1)]
    session = make_session()
    alt = AltFetcher(session)

    if len(store) and "adj_prev" not in store.columns:
        print("Adding NSE's adjusted previous close to the stored days (one-time, slow) ...")
        store = fill_adj_prev(store, alt)
        store = save_store(store, today)

    if not days:
        print("Already up to date.")
        return 0

    frames = []
    counts = {"ok": 0, "none": 0, "denied": 0, "error": 0}
    fatal = None

    for day in days:
        status, df, note = fetch_day(session, day)
        counts[status] += 1
        if status == "ok":
            a = alt.get(day)
            df["adj_prev"] = df["symbol"].map(a) if a is not None else np.nan
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
