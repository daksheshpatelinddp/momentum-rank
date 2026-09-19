"""Price matrix and split/bonus adjustment.

IMPORTANT: NSE's bhavcopy does NOT adjust the "previous close" on ex-dates (checked on
real data: HDFCBANK 1:1 bonus, Goldiam and Brigade 1:3 bonus), so corporate actions
cannot be detected from the price file itself. They come from events.py.
"""
import pandas as pd


def raw_close_matrix(store, symbols):
    """Unadjusted closes: index = date, columns = symbol."""
    df = store[["date", "symbol", "close"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["symbol"].isin(list(symbols))]
    df = df.drop_duplicates(["date", "symbol"], keep="last")
    return df.pivot(index="date", columns="symbol", values="close").sort_index()


def apply_events(raw_px, events):
    """Multiply every close BEFORE an ex-date by the event's factor.

    factor = 0.75 for a 1:3 bonus, 0.5 for a 1:1 bonus or 1:2 split, 10 for a 10:1
    reverse split. Several events on one stock compound.
    """
    px = raw_px.copy()
    for e in events.itertuples(index=False):
        if e.symbol in px.columns:
            px.loc[px.index < e.date, e.symbol] = px.loc[px.index < e.date, e.symbol] * e.factor
    return px
