"""Automatic split / bonus adjustment using NSE's own previous-close figure.

On the ex-date of a split or bonus, NSE's bhavcopy shows a PrevClose that is
already on the new price basis. So

    factor = PrevClose(today) / Close(previous stored day)

is 1.0 on normal days and e.g. 0.5 on a 1:1 bonus. Every price BEFORE that day
is multiplied by the factor to put the whole history on today's basis.
"""
import numpy as np
import pandas as pd

EVENT_TOL = 0.015      # ignore |factor - 1| below 1.5 % (rounding noise)
GAP_SHARE = 0.05       # if > 5 % of all symbols "have an event" on one date ...
GAP_MIN_COUNT = 30     # ... (and at least 30 symbols), the date follows a missing day


def _prepare(store):
    df = store[["date", "symbol", "close", "prev_close"]].copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.drop_duplicates(["date", "symbol"], keep="last")
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    return df


def compute_factors(store):
    """Return (df, factor, gap_dates). factor is 1.0 where nothing happened."""
    df = _prepare(store)
    prev_row_close = df.groupby("symbol")["close"].shift(1)
    ratio = df["prev_close"] / prev_row_close
    ratio = ratio.replace([np.inf, -np.inf], np.nan)

    is_event = (ratio.notna()
                & ((ratio - 1).abs() > EVENT_TOL)
                & (ratio > 0.005) & (ratio < 200))

    # Safety net: if a whole trading day is missing from the store, EVERY stock
    # looks like it had an "event" on the next day. Real corporate actions hit
    # only a few stocks per day, so a market-wide pattern means a data gap.
    n_all = df.groupby("date")["symbol"].transform("size")
    n_ev = is_event.astype(int).groupby(df["date"]).transform("sum")
    gap_day = (n_ev >= GAP_MIN_COUNT) & (n_ev / n_all > GAP_SHARE)

    factor = ratio.where(is_event & ~gap_day, 1.0).fillna(1.0)
    gap_dates = sorted(pd.Timestamp(d) for d in df.loc[gap_day, "date"].unique())
    return df, factor, gap_dates


def _product_after(s):
    """For each row: product of the values that come AFTER it (1.0 for the last)."""
    a = s.to_numpy(dtype=float)
    cp = np.cumprod(a[::-1])[::-1]
    out = np.ones_like(a)
    out[:-1] = cp[1:]
    return pd.Series(out, index=s.index)


def adjusted_close(store, symbols=None):
    """Return (px, events, gap_dates).

    px      : DataFrame, index = date, columns = symbol, adjusted close
    events  : DataFrame [date, symbol, factor] of detected corporate actions
    """
    df, factor, gap_dates = compute_factors(store)
    df["factor"] = factor.to_numpy()
    if symbols is not None:
        df = df[df["symbol"].isin(list(symbols))].copy()

    df["cum"] = df.groupby("symbol")["factor"].transform(_product_after)
    df["adj"] = df["close"] * df["cum"]

    px = df.pivot(index="date", columns="symbol", values="adj").sort_index()
    events = (df.loc[df["factor"] != 1.0, ["date", "symbol", "factor"]]
              .sort_values(["date", "symbol"]).reset_index(drop=True))
    return px, events, gap_dates
