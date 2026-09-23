"""Long-history NSE bhavcopy downloader, for backtesting only (data/history.csv).

Separate from fetch_bhav.py (which keeps ~500 days for live ranking): this one keeps
EVERY day back to --start and is resumable, because a decade of history needs more calls
than one GitHub Actions run's time limit reliably allows. Run the workflow again to
continue where it left off; it saves progress after every day.
"""
import os
import sys
import time
import datetime as dt
from zoneinfo import ZoneInfo

import pandas as pd

from fetch_bhav import fetch_day, parse_bhav, make_session

STORE = "data/history.csv"
DEFAULT_START = "2013-01-01"
STORE_COLS = ["date", "symbol", "close", "prev_close", "volume"]


def load_store():
    if not os.path.exists(STORE) or os.path.getsize(STORE) == 0:
        return pd.DataFrame(columns=STORE_COLS)
    try:
        df = pd.read_csv(STORE, parse_dates=["date"])
    except pd.errors.EmptyDataError:
        print(f"{STORE} exists but has no data in it; starting a fresh backfill.")
        return pd.DataFrame(columns=STORE_COLS)
    if "volume" not in df.columns:
        df["volume"] = float("nan")
    return df


def save_store(df):
    if "volume" not in df.columns:
        df["volume"] = float("nan")
    df = df[STORE_COLS]
    df = df.drop_duplicates(["date", "symbol"], keep="last").sort_values(["date", "symbol"])
    os.makedirs("data", exist_ok=True)
    df.to_csv(STORE, index=False, date_format="%Y-%m-%d")


def main():
    today = dt.datetime.now(ZoneInfo("Asia/Kolkata")).date()
    start_arg = os.environ.get("HISTORY_START", DEFAULT_START).strip()
    start_wanted = dt.date.fromisoformat(start_arg)
    store = load_store()

    if len(store) and store["date"].min().date() <= start_wanted:
        start = store["date"].max().date() + dt.timedelta(days=1)
        print(f"Resuming: history already covers {store['date'].min().date()} -> "
              f"{store['date'].max().date()}; fetching from {start}.")
    else:
        start = start_wanted
        print(f"Starting a fresh history from {start} (requested start {start_wanted}).")

    days = [start + dt.timedelta(days=n) for n in range((today - start).days + 1)]
    days = [d for d in days if d.weekday() < 5]
    if not days:
        print("Already up to date.")
        return 0

    session = make_session()
    frames, counts, saved_every = [], {"ok": 0, "none": 0, "denied": 0, "error": 0}, 40
    fatal = None
    deadline = time.time() + float(os.environ.get("HISTORY_TIME_BUDGET_S", 4800))  # ~80 min default

    for i, day in enumerate(days):
        if time.time() > deadline:
            print(f"Time budget reached after {i} days; stopping here so progress is saved. "
                  "Run the workflow again to continue.")
            break
        status, df, note = fetch_day(session, day, parser=parse_bhav)
        counts[status] += 1
        if status == "ok":
            frames.append(df)
        elif status == "error":
            fatal = f"{day}: {note} (server/network problem)."
            break
        elif status == "denied" and counts["ok"] == 0 and counts["denied"] >= 6:
            fatal = f"NSE refused {counts['denied']} requests in a row (last: {note})."
            break
        if (i + 1) % saved_every == 0:
            if frames:
                store = pd.concat(([store] if len(store) else []) + frames, ignore_index=True)
                store["date"] = pd.to_datetime(store["date"])
                save_store(store)
                frames = []
            print(f"  ...{i + 1}/{len(days)} days done, up to {day}", flush=True)
        time.sleep(0.5)

    if frames:
        store = pd.concat(([store] if len(store) else []) + frames, ignore_index=True)
        store["date"] = pd.to_datetime(store["date"])
    if len(store):
        save_store(store)
        print(f"Saved {STORE}: {len(store):,} rows, {store['date'].nunique()} trading days, "
              f"{store['date'].min().date()} -> {store['date'].max().date()}")
    print(f"Summary this run: {counts}")
    if fatal:
        print("ERROR:", fatal)
        return 1
    remaining = (today - (store['date'].max().date() if len(store) else start)).days
    if remaining > 3:
        print(f"NOTE: history is not yet complete up to today ({remaining} days remaining). "
              "Run the workflow again to continue the backfill.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
