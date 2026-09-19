"""Offline self-test (no internet). Fails the workflow if the logic is broken."""
import datetime as dt
import io
import os
import sys
import tempfile
import zipfile

import numpy as np
import pandas as pd

from adjust import raw_close_matrix, apply_events
from events import load_manual, fetch_yahoo, align_event, build_events
from fetch_bhav import parse_bhav, NotAZip, WrongDate, BadFormat


def check(cond, msg):
    if not cond:
        print("SELFTEST FAILED:", msg)
        sys.exit(1)
    print("ok  -", msg)


def synthetic(n_days=300, seed=1):
    """NSE-style data: closes are as traded (NOT adjusted), and prev_close is the plain
    previous close, exactly like the real bhavcopy."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2025-01-01", periods=n_days)
    truth, rows = {}, []
    actions = {"BONUS": {150: 0.5}, "SPLIT": {100: 0.2}, "MULTI": {60: 0.5, 220: 0.75},
               "REVERSE": {180: 10.0}, "PLAIN": {}}
    for name, ev in actions.items():
        p = 500 * np.exp(np.cumsum(rng.normal(0.0004, 0.018, n_days)))   # adjusted basis
        truth[name] = pd.Series(p, index=dates)
        closes = [round(p[t] / (np.prod([f for e, f in ev.items() if e > t]) if ev else 1.0), 2)
                  for t in range(n_days)]
        for t in range(n_days):
            rows.append((dates[t], name, closes[t], closes[t - 1] if t else np.nan))
    store = pd.DataFrame(rows, columns=["date", "symbol", "close", "prev_close"])
    ev_rows = [(s, dates[t], f, "manual", "") for s, ev in actions.items() for t, f in ev.items()]
    events = pd.DataFrame(ev_rows, columns=["symbol", "date", "factor", "source", "note"])
    return store, truth, events, dates


def test_adjustment():
    store, truth, events, dates = synthetic()
    raw = raw_close_matrix(store, list(truth))
    px = apply_events(raw, events)
    for name in truth:
        err = (px[name] / truth[name] - 1).abs().max()
        check(err < 0.005, f"{name}: adjusted prices match the true series (max err {err:.3%})")


def test_alignment():
    idx = pd.bdate_range("2026-06-01", periods=30)
    base = pd.Series(100.0, index=idx)
    # 1:3 bonus (factor 0.75) on day 15, hidden by a +20% upper-circuit move (raw ratio 0.9)
    raw = base.copy()
    raw.iloc[15:] = 100 * 0.9
    d = idx[15]
    check(align_event(raw, d, 0.75) == d, "bonus hidden by a +20% move is confirmed on the exact day")
    check(align_event(raw, idx[14], 0.75) == d, "Yahoo date one day early is moved to the real day")
    check(align_event(raw, idx[16], 0.75) == d, "Yahoo date one day late is moved to the real day")
    check(align_event(base, idx[15], 0.5) is None, "event not visible in NSE prices is rejected")

    raw_px = pd.DataFrame({"AAA": raw})
    yahoo = pd.DataFrame([("AAA", idx[14], 0.75), ("AAA", idx[3], 0.5)],
                         columns=["symbol", "date", "factor"])
    manual = pd.DataFrame(columns=["symbol", "ex_date", "factor", "note"])
    ev, rej = build_events(raw_px, manual, yahoo)
    check(len(ev) == 1 and ev.iloc[0]["date"] == d and len(rej) == 1,
          "build_events keeps the confirmed event and reports the rejected one")

    manual = pd.DataFrame([("AAA", d, 0.75, "1:3 bonus")], columns=["symbol", "ex_date", "factor", "note"])
    ev, _ = build_events(raw_px, manual, yahoo[yahoo["date"] == idx[14]])
    check(len(ev) == 1 and ev.iloc[0]["source"] == "manual",
          "manual entry wins and is not double counted")


def test_manual_file():
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            open("ok.csv", "w").write("# c\nsymbol,ex_date,factor,note\nabc,2026-01-05,0.75,1:3 bonus\n")
            df = load_manual("ok.csv")
            check(len(df) == 1 and df.iloc[0]["symbol"] == "ABC" and df.iloc[0]["factor"] == 0.75,
                  "corporate_actions.csv is read correctly")
            open("bad.csv", "w").write("symbol,ex_date,factor,note\nABC,notadate,0.75,x\n")
            try:
                load_manual("bad.csv")
            except SystemExit:
                print("ok  - invalid corporate_actions.csv row is rejected")
            else:
                check(False, "invalid corporate_actions.csv row is rejected")
            open("empty.csv", "w").write("# only comments\n")
            check(load_manual("empty.csv").empty, "comment-only corporate_actions.csv is fine")
        finally:
            os.chdir(cwd)


def test_yahoo_handling():
    def fake(sym):
        if sym == "GOOD":
            return pd.Series([4 / 3], index=pd.DatetimeIndex([pd.Timestamp("2026-06-17", tz="Asia/Kolkata")]))
        if sym == "NONE":
            return pd.Series([], dtype=float, index=pd.DatetimeIndex([]))
        raise ConnectionError("down")
    df, failed = fetch_yahoo(["GOOD", "NONE", "BAD"], since=pd.Timestamp("2025-01-01"),
                             get_splits=fake, pause=0)
    check(len(df) == 1 and abs(df.iloc[0]["factor"] - 0.75) < 1e-9, "Yahoo 4/3 bonus becomes factor 0.75")
    check(list(failed) == ["BAD"], "a Yahoo failure is reported per symbol, not hidden")


def make_zip(rows, header=None, name="bhav.csv"):
    header = header or ["TradDt", "TckrSymb", "SctySrs", "ClsPric", "PrvsClsgPric"]
    text = ",".join(header) + "\n" + "\n".join(",".join(map(str, r)) for r in rows)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, text)
    return buf.getvalue()


def test_parser():
    day = dt.date(2026, 1, 5)
    data = make_zip([
        ("2026-01-05", "AAA", "EQ", "100.5", "99"),
        ("2026-01-05", "BBB", "BE", "50", "0"),
        ("2026-01-05", "BBB", "EQ", "51", "50"),
        ("2026-01-05", "CCC", "N1", "1000", "1000"),
        ("2026-01-05", "DDD", "EQ", "-", "10"),
    ])
    df = parse_bhav(data, day)
    check(sorted(df["symbol"]) == ["AAA", "BBB"], "parser keeps only valid equity rows")
    check(float(df.loc[df.symbol == "BBB", "close"].iloc[0]) == 51.0, "parser prefers EQ over BE")
    for bad, exc, label in [
        (b"<html>denied</html>", NotAZip, "non-zip answer rejected"),
        (make_zip([("2026-01-02", "AAA", "EQ", "1", "1")]), WrongDate, "wrong-date file rejected"),
        (make_zip([("AAA", "EQ", "1")], header=["TckrSymb", "SctySrs", "ClsPric"]),
         BadFormat, "changed column layout rejected"),
    ]:
        try:
            parse_bhav(bad, day)
        except exc:
            print("ok  -", label)
        else:
            check(False, label)


if __name__ == "__main__":
    test_adjustment()
    test_alignment()
    test_manual_file()
    test_yahoo_handling()
    test_parser()
    print("ALL SELFTESTS PASSED")
