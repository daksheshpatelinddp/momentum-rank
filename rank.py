#!/usr/bin/env python3
"""Rank the stocks in symbols.txt by momentum, using split/bonus-adjusted NSE closes.

Adjustment method: every bhavcopy row has today's close AND the previous close as NSE
sees it. On the ex-date of a split/bonus, NSE lowers the previous close, so
    factor = today's prev_close / yesterday's stored close
differs from 1. Every earlier price is multiplied by that factor.
"""
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "data"))
SYMBOLS_FILE = Path(os.environ.get("SYMBOLS_FILE", "symbols.txt"))
OUT_CSV = Path(os.environ.get("OUT_CSV", "ranked.csv"))
OUT_MD = Path(os.environ.get("OUT_MD", "ranked.md"))

EVENT_THRESHOLD = 0.03       # |factor-1| above this counts as a corporate action
GAP_EVENT_THRESHOLD = 0.25   # stricter threshold on days after a missing market-wide day
GAP_SHARE = 0.30             # share of stocks that "mismatch" that reveals a missing day
MIN_ROWS = 253               # trading days needed for the 12-1 month measure
WEIGHTS = {"ret_6m_per_vol": 0.30, "ret_12_1": 0.25, "ret_3m": 0.25, "near_high": 0.20}


def read_symbols(path):
    if not path.exists():
        sys.exit(f"ERROR: {path} not found.")
    out = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.split("#")[0].strip()
        for tok in re.split(r"[,\s;]+", line):
            tok = tok.strip().upper()
            if tok.startswith("NSE:"):
                tok = tok[4:]
            if tok.endswith(".NS"):
                tok = tok[:-3]
            if tok and tok not in ("SYMBOL", "SYMBOLS") and tok not in out:
                out.append(tok)
    return out


def load_prices():
    files = sorted(DATA_DIR.glob("*.csv.gz"))
    frames = []
    for f in files:
        try:
            date = pd.Timestamp(f.name[:10])
        except ValueError:
            continue
        df = pd.read_csv(f, usecols=["symbol", "close", "prev_close"])
        df["date"] = date
        frames.append(df)
    if not frames:
        sys.exit("ERROR: no price files in data/. Run fetch_bhav.py first.")
    data = pd.concat(frames, ignore_index=True).drop_duplicates(["date", "symbol"], keep="last")
    close = data.pivot(index="date", columns="symbol", values="close").sort_index()
    prev = data.pivot(index="date", columns="symbol", values="prev_close").reindex(close.index)
    return close, prev


def adjust_prices(close, prev):
    """Return (adjusted close, table of detected events, dates that follow a missing day)."""
    factor = prev / close.shift(1)
    mismatch = (factor - 1).abs()
    n_valid = mismatch.notna().sum(axis=1)
    share = (mismatch > 0.005).sum(axis=1) / n_valid.where(n_valid >= 50)
    gap_dates = share[share > GAP_SHARE].index

    threshold = pd.Series(EVENT_THRESHOLD, index=close.index)
    threshold[gap_dates] = GAP_EVENT_THRESHOLD
    is_event = mismatch.gt(threshold, axis=0)
    multiplier = factor.where(is_event, 1.0)
    # price on day t is scaled by every event that happens AFTER t
    after = multiplier.iloc[::-1].cumprod().iloc[::-1].shift(-1).fillna(1.0)
    return close * after, factor.where(is_event), gap_dates


def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def main():
    symbols = read_symbols(SYMBOLS_FILE)
    if not symbols:
        sys.exit("ERROR: symbols.txt is empty. Paste your Chartink symbols, one per line.")

    close, prev = load_prices()
    if len(close) < MIN_ROWS:
        sys.exit(f"ERROR: only {len(close)} trading days stored, need {MIN_ROWS}. "
                 "Run the download step again (the first backfill may have been interrupted).")
    adj, events, gap_dates = adjust_prices(close, prev)

    last_date = close.index[-1]
    today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
    notes = []
    if (today - last_date.date()).days > 7:
        notes.append(f"WARNING: newest data is {last_date.date()}, more than 7 days old.")
    if len(gap_dates):
        notes.append("Days after a missing market-wide day (extra-strict event rule used): "
                     + ", ".join(d.strftime("%Y-%m-%d") for d in gap_dates))

    px = adj.ffill(limit=5)
    last = px.iloc[-1]
    daily_ret = px / px.shift(1) - 1
    metrics = pd.DataFrame({
        "close": close.iloc[-1],
        "ret_3m": last / px.iloc[-64] - 1,
        "ret_6m": last / px.iloc[-127] - 1,
        "ret_12_1": px.iloc[-22] / px.iloc[-253] - 1,
        "ann_vol": daily_ret.iloc[-126:].std() * np.sqrt(252),
        "near_high": last / px.iloc[-252:].max(),
    })
    metrics["ret_6m_per_vol"] = metrics["ret_6m"] / metrics["ann_vol"]
    metrics = metrics.replace([np.inf, -np.inf], np.nan)

    found = [s for s in symbols if s in metrics.index]
    not_found = [s for s in symbols if s not in metrics.index]
    traded = close.iloc[-1].notna()
    inactive = [s for s in found if not traded[s]]
    m = metrics.loc[[s for s in found if traded[s]]]
    ok = m[list(WEIGHTS) + ["close"]].notna().all(axis=1) & (m["ann_vol"] > 0)
    short_history = list(m.index[~ok])
    m = m[ok].copy()
    if m.empty:
        sys.exit("ERROR: none of your symbols could be ranked. "
                 f"Not found: {not_found[:20]} | short history: {short_history[:20]}")

    pct = m[list(WEIGHTS)].rank(pct=True)
    m["score"] = sum(w * pct[c] for c, w in WEIGHTS.items()) * 100
    m = m.sort_values("score", ascending=False)
    m["adj_events"] = events.notna().sum().reindex(m.index).fillna(0).astype(int)

    out = pd.DataFrame({
        "score": m["score"].round(1),
        "close": m["close"].round(2),
        "ret_3m_%": (m["ret_3m"] * 100).round(1),
        "ret_6m_%": (m["ret_6m"] * 100).round(1),
        "ret_12_1_%": (m["ret_12_1"] * 100).round(1),
        "ann_vol_%": (m["ann_vol"] * 100).round(1),
        "below_52w_high_%": ((m["near_high"] - 1) * 100).round(1),
        "adj_events": m["adj_events"],
    })
    out.insert(0, "symbol", out.index)
    out.insert(0, "rank", np.arange(1, len(out) + 1))
    out = out.reset_index(drop=True)
    out.to_csv(OUT_CSV, index=False)

    ev_lines = []
    for sym in m.index[m["adj_events"] > 0]:
        for d, f in events[sym].dropna().items():
            ev_lines.append(f"- {sym}: {d.date()} factor {f:.4f} (earlier prices multiplied by this)")

    md = [f"# Momentum ranking - data up to {last_date.date()}", "",
          f"Symbols in list: {len(symbols)} | ranked: {len(out)}", ""]
    md.append(md_table(out))
    md.append("")
    if ev_lines:
        md += ["## Corporate actions detected (check against a chart)"] + ev_lines + [""]
    for label, items in (("Not found in NSE data", not_found),
                         ("Did not trade on the latest date", inactive),
                         ("Not enough price history", short_history)):
        if items:
            md += [f"**{label}:** {', '.join(items)}", ""]
    if notes:
        md += notes + [""]
    md.append("_Ranking is a research shortlist, not investment advice._")
    text = "\n".join(md)
    OUT_MD.write_text(text + "\n", encoding="utf-8")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text + "\n")

    print(out.head(25).to_string(index=False))
    print(f"\nRanked {len(out)} of {len(symbols)} symbols. Data through {last_date.date()}.")
    for n in notes:
        print(n)
    if not_found:
        print("Not found:", ", ".join(not_found))
    if short_history:
        print("Not enough history:", ", ".join(short_history))


if __name__ == "__main__":
    main()
