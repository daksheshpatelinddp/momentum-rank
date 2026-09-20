"""Download BSE equity bhavcopy for the stocks in symbols.txt that are NOT on NSE.

Only the stocks you need are kept (data/prices_bse.csv), so the file stays small.
* First time a new BSE stock appears in symbols.txt: the last ~460 days are scanned once
  (about 10-15 minutes) and the stock is remembered in data/bse_meta.json.
* Later runs: only the days after the last stored day are downloaded.
Write each BSE stock in symbols.txt by its BSE Security ID (for example GOLDIAM) or by its
numeric scrip code (for example 526729), one per line.
"""
import io
import json
import os
import sys
import time
import zipfile
import datetime as dt
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

from events import load_manual
from fetch_bhav import fetch_day, NotAZip, WrongDate, BadFormat
from rank import read_symbols

URL = ("https://www.bseindia.com/download/BhavCopy/Equity/"
       "BhavCopy_BSE_CM_0_0_0_{d}_F_0000.CSV")
NSE_STORE = "data/prices.csv"
STORE = "data/prices_bse.csv"
META = "data/bse_meta.json"
BACKFILL_DAYS = 460
KEEP_DAYS = 500
STORE_COLS = ["date", "symbol", "code", "close", "prev_close"]
REQUIRED = ["TckrSymb", "ClsPric", "PrvsClsgPric"]
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
}


def parse_bse(content, day, drop_unpriced=True):
    """Bytes of a BSE bhavcopy (csv or zip) -> DataFrame [symbol, code, close, prev_close]."""
    if content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            names = [n for n in z.namelist() if n.lower().endswith(".csv")]
            if not names:
                raise BadFormat("no csv file inside the zip")
            content = z.read(names[0])
    text = content.decode("utf-8-sig", errors="replace")
    if "TckrSymb" not in text[:3000]:
        raise NotAZip("response is not a BSE bhavcopy")
    raw = pd.read_csv(io.StringIO(text), dtype=str)
    raw.columns = [str(c).strip() for c in raw.columns]
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        raise BadFormat(f"missing columns {missing}; file has {list(raw.columns)}")
    if "TradDt" in raw.columns:
        d = pd.to_datetime(raw["TradDt"], errors="coerce").dropna()
        if len(d) and d.iloc[0].date() != day:
            raise WrongDate(f"file says {d.iloc[0].date()}, expected {day}")

    out = pd.DataFrame({
        "symbol": raw["TckrSymb"].astype(str).str.strip().str.upper(),
        "code": raw["FinInstrmId"].astype(str).str.strip() if "FinInstrmId" in raw.columns else "",
        "close": pd.to_numeric(raw["ClsPric"], errors="coerce"),
        "series": raw["SctySrs"].astype(str).str.strip().str.upper() if "SctySrs" in raw.columns else "",
    })
    prev = pd.to_numeric(raw["PrvsClsgPric"], errors="coerce")
    out["prev_close"] = prev.where(prev > 0)
    if drop_unpriced:
        out = out[out["close"] > 0]
    out = out.drop_duplicates("symbol")
    if out.empty or not (out["close"] > 0).any():
        raise BadFormat("no priced rows in file")
    return out.reset_index(drop=True)


def make_session():
    s = requests.Session()
    s.headers.update(HEADERS)
    try:
        s.get("https://www.bseindia.com/", timeout=20)
    except requests.RequestException:
        pass
    return s


def load_meta():
    if os.path.exists(META):
        try:
            with open(META, encoding="utf-8") as f:
                m = json.load(f)
            return {"scanned": list(m.get("scanned", [])), "last_date": m.get("last_date"),
                    "diag": dict(m.get("diag", {}))}
        except (ValueError, OSError):
            pass
    return {"scanned": [], "last_date": None, "diag": {}}


def save_meta(meta):
    os.makedirs("data", exist_ok=True)
    with open(META, "w", encoding="utf-8") as f:
        json.dump({"scanned": sorted(set(meta["scanned"])), "last_date": meta["last_date"],
                   "diag": meta.get("diag", {})}, f, indent=1)


def load_store():
    if not os.path.exists(STORE):
        return pd.DataFrame(columns=STORE_COLS)
    df = pd.read_csv(STORE, parse_dates=["date"], dtype={"code": str})
    return df


def save_store(df, today):
    cutoff = pd.Timestamp(today - dt.timedelta(days=KEEP_DAYS))
    df = df[df["date"] >= cutoff].drop_duplicates(["date", "symbol"], keep="last")
    df = df.sort_values(["date", "symbol"])[STORE_COLS]
    os.makedirs("data", exist_ok=True)
    df.to_csv(STORE, index=False, date_format="%Y-%m-%d")
    return df


def main():
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    tokens = read_symbols()
    nse = set()
    if os.path.exists(NSE_STORE):
        nse = set(pd.read_csv(NSE_STORE, usecols=["symbol"])["symbol"].unique())
    cand = [t for t in tokens if t not in nse]
    if not cand:
        print("Every symbol in symbols.txt is on NSE; nothing to fetch from BSE.")
        return 0

    watch = set(cand) | set(load_manual()["symbol"])     # manual-event stocks help validate BSE data
    meta = load_meta()
    store = load_store()
    need = sorted(watch - set(meta["scanned"]))
    in_store = (set(store["symbol"]) | set(store["code"].astype(str))) if len(store) else set()
    unknown = [t for t in cand if t not in in_store and t not in meta["diag"]]
    if unknown and not need:
        need = unknown                     # scanned before, but we never learned WHY there were no rows
    backfill = bool(need) or meta["last_date"] is None

    if backfill:
        start = today - dt.timedelta(days=BACKFILL_DAYS)
        keep = watch | set(meta["scanned"])
        store = pd.DataFrame(columns=STORE_COLS)
        print(f"Scanning BSE from {start} for: {', '.join(need) or 'all watched stocks'}")
    else:
        start = pd.Timestamp(meta["last_date"]).date() + dt.timedelta(days=1)
        keep = set(meta["scanned"])
        print(f"BSE data ends {meta['last_date']} -> fetching from {start}")

    days = [start + dt.timedelta(days=n) for n in range((today - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    session = make_session()
    frames, counts = [], {"ok": 0, "none": 0, "denied": 0, "error": 0}
    last_ok, fatal = None, None
    tokset, listed, shown_groups = set(cand), set(), False
    parse_all = lambda content, d: parse_bse(content, d, drop_unpriced=False)

    for day in days:
        status, df, note = fetch_day(session, day, url_tmpl=URL, parser=parse_all,
                                     retry_sleep=2)
        counts[status] += 1
        if status == "ok":
            last_ok = day
            listed |= set(df.loc[df["symbol"].isin(tokset), "symbol"])
            listed |= set(df.loc[df["code"].isin(tokset), "code"])
            if not shown_groups:
                shown_groups = True
                grp = df["series"].value_counts().head(12)
                print("BSE file security groups: " + ", ".join(f"{k}:{v}" for k, v in grp.items()))
            df = df[df["close"] > 0]
            sel = df[df["symbol"].isin(keep) | df["code"].isin(keep)].copy()
            sel.insert(0, "date", pd.Timestamp(day))
            frames.append(sel)
            print(f"{day}  ok      {len(df)} BSE symbols, {len(sel)} kept", flush=True)
        elif status == "error":
            fatal = f"{day}: {note} (server/network problem)."
            break
        elif status == "denied" and counts["ok"] == 0 and counts["denied"] >= 6:
            fatal = (f"BSE refused {counts['denied']} requests in a row with no success "
                     f"(last: {note}). GitHub's servers are probably blocked by BSE.")
            break
        time.sleep(0.5)

    if backfill and not fatal and counts["ok"] == 0:
        fatal = ("BSE returned no bhavcopy file for any day (its download address may have "
                 "changed). Nothing saved.")
    if backfill and fatal:
        print("Backfill incomplete; nothing saved. Run again later.")
    else:
        if frames:
            parts = ([store] if len(store) else []) + frames
            store = pd.concat(parts, ignore_index=True)
            store["date"] = pd.to_datetime(store["date"])
        if len(store):
            store = save_store(store, today)
            print(f"Saved {STORE}: {len(store):,} rows, {store['symbol'].nunique()} stocks, "
                  f"{store['date'].min().date()} -> {store['date'].max().date()}")
        if backfill:
            meta["scanned"] = sorted(set(meta["scanned"]) | watch)
        if last_ok is not None:
            meta["last_date"] = str(last_ok)
        elif backfill and meta["last_date"] is None:
            meta["last_date"] = None
        if last_ok is not None or backfill:
            save_meta(meta)
        found = (set(store["symbol"]) | set(store["code"].astype(str))) if len(store) else set()
        lost = [c for c in cand if c not in found]
        for t in cand:
            if t in found:
                meta["diag"].pop(t, None)
            elif t in listed:
                meta["diag"][t] = "listed"
            elif backfill or t not in meta["diag"]:
                meta["diag"][t] = "absent"
        if lost:
            print("No BSE price rows for: " + ", ".join(lost))
            for t in lost:
                if meta["diag"].get(t) == "listed":
                    print(f"  {t}: listed in BSE's file, but with no closing price on any day "
                          "(it did not trade in the scanned period).")
                else:
                    print(f"  {t}: not in BSE's daily file at all (wrong ID, or a segment this "
                          "file does not include, such as SME).")
        save_meta(meta)

    print(f"Summary: {counts}")
    if fatal:
        print("ERROR:", fatal)
        return 1
    if not frames:
        print("No new BSE files (weekend, holiday, or today's file not published yet).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
