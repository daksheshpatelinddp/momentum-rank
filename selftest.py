"""Offline self-test (no internet). Fails the workflow if the adjustment logic is broken."""
import datetime as dt
import io
import sys
import zipfile

import numpy as np
import pandas as pd

from adjust import adjusted_close
from fetch_bhav import parse_bhav, NotAZip, WrongDate, BadFormat


def synthetic_store(n_days=300, n_syms=120, seed=1):
    """Build fake bhavcopy-style data with known corporate actions and one missing day."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2025-01-01", periods=n_days)
    truth, rows = {}, []
    actions = {                       # symbol -> {day index: factor}
        "BONUS": {150: 0.5},          # 1:1 bonus
        "SPLIT": {100: 0.2},          # 1:5 split
        "MULTI": {60: 0.5, 220: 0.8}, # bonus then 1:4 bonus
        "REVERSE": {180: 10.0},       # 10:1 consolidation
    }
    names = ["BONUS", "SPLIT", "MULTI", "REVERSE"] + [f"S{i:03d}" for i in range(n_syms)]
    for name in names:
        p = 500 * np.exp(np.cumsum(rng.normal(0.0004, 0.018, n_days)))   # adjusted basis
        truth[name] = pd.Series(p, index=dates)
        ev = actions.get(name, {})
        for t in range(n_days):
            after = np.prod([f for e, f in ev.items() if e > t]) if ev else 1.0
            close = round(p[t] / after, 2)
            if t == 0:
                prev = np.nan
            else:
                after_prev_basis = np.prod([f for e, f in ev.items() if e > t]) if ev else 1.0
                prev = round(p[t - 1] / after_prev_basis, 2)
            rows.append((dates[t], name, close, prev))
    store = pd.DataFrame(rows, columns=["date", "symbol", "close", "prev_close"])
    return store, truth, dates


def check(cond, msg):
    if not cond:
        print("SELFTEST FAILED:", msg)
        sys.exit(1)
    print("ok  -", msg)


def test_adjustment():
    store, truth, dates = synthetic_store()
    px, events, gaps = adjusted_close(store)
    check(not gaps, "no false data-gap on clean data")
    for name in ["BONUS", "SPLIT", "MULTI", "REVERSE", "S000", "S050"]:
        err = (px[name] / truth[name] - 1).abs().max()
        check(err < 0.005, f"{name}: adjusted series matches true series (max err {err:.4%})")
    check(len(events) == 5, f"5 corporate actions detected (found {len(events)})")

    # a whole missing trading day must NOT be mistaken for corporate actions
    gap_date = dates[200]
    store2 = store[store["date"] != gap_date]
    px2, events2, gaps2 = adjusted_close(store2)
    check(len(gaps2) == 1 and gaps2[0] == dates[201], "missing day detected as data gap")
    check(len(events2) == 5, f"only real actions kept after a gap (found {len(events2)})")
    err = (px2["S010"] / truth["S010"].drop(gap_date) - 1).abs().max()
    check(err < 0.005, "ordinary stock unaffected by a missing day")


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
        ("2026-01-05", "BBB", "EQ", "51", "50"),      # duplicate symbol: EQ wins
        ("2026-01-05", "CCC", "N1", "1000", "1000"),   # bond, ignored
        ("2026-01-05", "DDD", "EQ", "-", "10"),        # bad price, ignored
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
    test_parser()
    print("ALL SELFTESTS PASSED")
