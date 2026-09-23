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
from events import (load_manual, fetch_yahoo, align_event, build_events, derive_from_store,
                    validate, fetch_api_history, events_from_api, gather_events,
                    derive_from_bse, detect_price_events)
from announce import parse_purpose, resolve_actions, fetch_bse_actions, fetch_nse_actions
from fetch_bhav import parse_bhav, parse_sec, NotAZip, WrongDate, BadFormat
from fetch_bse import parse_bse
import backtest as bt
import backtest2 as bt2
import fetch_index_history as fih
import indicators as ind
import universe as uv


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


def test_auto_estimate():
    idx = pd.bdate_range("2026-01-01", periods=30)
    raw = pd.Series(100.0, index=idx)
    raw.iloc[15:] = 60.0                       # spin-off: -40 % overnight, market flat
    raw_px = pd.DataFrame({"AAA": raw})
    manual = pd.DataFrame([("AAA", idx[15], np.nan, "spin-off")],
                          columns=["symbol", "ex_date", "factor", "note"])
    mm = pd.Series(0.0, index=idx)
    ev, _ = build_events(raw_px, manual, pd.DataFrame(columns=["symbol", "date", "factor"]),
                         market_move=mm)
    check(len(ev) == 1 and abs(ev.iloc[0]["factor"] - 0.6) < 1e-6 and "estimated" in ev.iloc[0]["source"],
          "factor 'auto' is estimated from the ex-date price move")


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
            open("auto.csv", "w").write("symbol,ex_date,factor,note\nabc,2026-01-05,auto,spin-off\n")
            a = load_manual("auto.csv")
            check(len(a) == 1 and pd.isna(a.iloc[0]["factor"]), "factor 'auto' is accepted in corporate_actions.csv")
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



def exchange_store(n_syms=60, n_days=80, adjusted=True, seed=2):
    """Store with the second daily file (adj_prev). Events: 1:3 bonus, rights issue, demerger."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2026-01-01", periods=n_days)
    plan = {"BON": (40, 0.75), "RIGHTS": (50, 0.93), "DEMERG": (60, 0.80)}
    names = list(plan) + [f"S{i:02d}" for i in range(n_syms)]
    rows = []
    for n in names:
        p = 200 * np.exp(np.cumsum(rng.normal(0, 0.01, n_days)))
        ev_day, f = plan.get(n, (None, 1.0))
        for t in range(n_days):
            nominal = p[t] / (f if (ev_day is not None and t < ev_day) else 1.0)
            prev = (p[t - 1] / (f if (ev_day is not None and t - 1 < ev_day) else 1.0)) if t else np.nan
            adj = prev * f if (adjusted and ev_day == t and t) else prev
            rows.append((dates[t], n, round(nominal, 2), prev, adj))
    return pd.DataFrame(rows, columns=["date", "symbol", "close", "prev_close", "adj_prev"]), dates


def test_exchange_sources():
    store, dates = exchange_store(adjusted=True)
    ev, note = derive_from_store(store)
    got = {(r.symbol, r.date): round(r.factor, 2) for r in ev.itertuples()}
    check(got == {("BON", dates[40]): 0.75, ("RIGHTS", dates[50]): 0.93, ("DEMERG", dates[60]): 0.8},
          "NSE daily file: bonus, rights issue and demerger all detected with exact factors")

    manual = pd.DataFrame([("BON", dates[40], 0.75, "1:3 bonus")], columns=["symbol", "ex_date", "factor", "note"])
    have = set(zip(store["date"], store["symbol"]))
    ok, hits, misses = validate(ev, manual, lambda s, d: (d, s) in have)
    check(ok and len(hits) == 1, "source that reproduces a known event is accepted")

    store_u, _ = exchange_store(adjusted=False)
    ev_u, _ = derive_from_store(store_u)
    ok, hits, misses = validate(ev_u, manual, lambda s, d: True)
    check(len(ev_u) == 0 and not ok, "unadjusted source is rejected")

    # full pipeline: file source validated -> rights + demerger applied automatically
    raw = raw_close_matrix(store, list(store["symbol"].unique()))
    events, rej, status, unver, _mm = gather_events(store, raw, ["BON", "RIGHTS", "DEMERG", "S00"], manual,
                                               skip_yahoo=True, skip_api=True, skip_announce=True)
    check(set(events["symbol"]) == {"BON", "RIGHTS", "DEMERG"} and not unver,
          "gather_events applies rights issue and demerger automatically")
    px = apply_events(raw[["RIGHTS"]], events)
    r = px["RIGHTS"].pct_change().abs().max()
    check(r < 0.06, f"rights-issue day no longer shows a fake drop (max 1-day move {r:.1%})")

    # file source unadjusted -> API source (fake) is validated and used
    def getter(sym, a, b):
        g = store[(store["symbol"] == sym) & (store["date"] >= pd.Timestamp(a)) & (store["date"] <= pd.Timestamp(b))]
        return [{"CH_TIMESTAMP": r.date.strftime("%Y-%m-%d"), "CH_PREVIOUS_CLS_PRICE": r.adj_prev,
                 "CH_CLOSING_PRICE": r.close} for r in g.itertuples() if not pd.isna(r.adj_prev)]
    store_x = store.copy()
    store_x["adj_prev"] = store_x["prev_close"]                     # daily file unadjusted
    events, rej, status, unver, _mm = gather_events(store_x, raw, ["BON", "RIGHTS", "S00"], manual,
                                               api_getter=getter, skip_yahoo=True, skip_announce=True)
    check("RIGHTS" in set(events["symbol"]) and any("website API: VALIDATED" in l for l in status),
          "NSE website API is used when the daily file is unadjusted")

    # both refused -> falls back, reports unverified
    def refused(sym, a, b):
        raise ConnectionError("HTTP 403")
    events, rej, status, unver, _mm = gather_events(store_x, raw, ["BON", "S00"], manual,
                                               api_getter=refused, skip_yahoo=True, skip_announce=True)
    check(unver == ["S00"] and list(events["symbol"]) == ["BON"],
          "when no source works, stocks are reported as unverified")


def test_parse_sec():
    text = ("SYMBOL, SERIES, DATE1, PREV_CLOSE, CLOSE_PRICE\n"
            "AAA, EQ, 05-Jan-2026, 99.5, 100\nBBB, BE, 05-Jan-2026, 50, 51\nCCC, N1, 05-Jan-2026, 5, 5\n")
    s = parse_sec(text, dt.date(2026, 1, 5))
    check(sorted(s.index) == ["AAA", "BBB"] and s["AAA"] == 99.5, "second daily file is parsed")
    try:
        parse_sec(text, dt.date(2026, 1, 6))
    except WrongDate:
        print("ok  - second daily file with the wrong date is rejected")
    else:
        check(False, "second daily file with the wrong date is rejected")


def test_bse():
    day = dt.date(2026, 1, 5)
    csv = ("TradDt,FinInstrmId,TckrSymb,SctySrs,ClsPric,PrvsClsgPric\n"
           "2026-01-05,532356,TRIVENI,A,240.5,239\n2026-01-05,540001,kediacn,B,150,0\n"
           "2026-01-05,540002,BADPRICE,B,-,10\n").encode()
    df = parse_bse(csv, day)
    check(sorted(df["symbol"]) == ["KEDIACN", "TRIVENI"], "BSE file: symbols read (upper-cased), bad prices dropped")
    check(pd.isna(df.loc[df.symbol == "KEDIACN", "prev_close"].iloc[0]), "BSE file: missing previous close kept as blank")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("x.CSV", csv)
    check(len(parse_bse(buf.getvalue(), day)) == 2, "BSE file: zipped version also accepted")
    for bad, exc, label in [(b"<html>error</html>", NotAZip, "BSE file: web page instead of data rejected"),
                            (csv, WrongDate, "BSE file: wrong date rejected")]:
        try:
            parse_bse(bad, dt.date(2026, 1, 6) if exc is WrongDate else day)
        except exc:
            print("ok  -", label)
        else:
            check(False, label)

    # BSE previous close adjusted on ex-date -> detected; a missing day is not mistaken for an event
    dates = pd.bdate_range("2026-01-01", periods=30)
    rows = []
    for t, d in enumerate(dates):
        if t == 12:
            continue                                   # BSE file missing for one day
        price = 100.0 / (0.5 if t < 20 else 1.0)
        prev = (100.0 / (0.5 if t - 1 < 20 else 1.0)) if t else np.nan
        if t == 20:
            prev = 100.0                               # adjusted base on the ex-date
        rows.append((d, "AAA", "1", price, prev))
    bse = pd.DataFrame(rows, columns=["date", "symbol", "code", "close", "prev_close"])
    ev = derive_from_bse(bse, dates)
    check(len(ev) == 1 and abs(ev.iloc[0]["factor"] - 0.5) < 1e-9 and ev.iloc[0]["date"] == dates[20],
          "BSE file: adjusted previous close gives the exact factor")


def test_auto_detection():
    idx = pd.bdate_range("2026-03-02", periods=60)
    rng = np.random.default_rng(4)
    base = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 60)))
    cols = {}
    a = base.copy(); a[30:] *= 0.1               # 10:1 split, consecutive days traded
    cols["SPLIT"] = a
    b = base.copy(); b[30:] *= 0.85              # a 15% fall: could be a real move -> not touched
    cols["FALL15"] = b
    c = base.copy(); c[30] *= 0.5                # one bad print that reverses next day
    cols["SPIKE"] = c
    d = base.copy(); d[30:] *= 0.3; d[29] = np.nan   # stock did not trade the day before: gap, not an event
    cols["GAP"] = d
    e = base.copy(); e[30:] *= 10                # 10:1 consolidation
    cols["REVERSE"] = e
    f = base.copy(); f[30:] *= 0.6               # already explained by another source
    cols["KNOWN"] = f
    raw = pd.DataFrame(cols, index=idx)
    known = pd.DataFrame([("KNOWN", idx[30], 0.6, "manual", "")], columns=["symbol", "date", "factor", "source", "note"])
    ev = detect_price_events(raw, known)
    got = {r.symbol: r.factor for r in ev.itertuples()}
    check(set(got) == {"SPLIT", "REVERSE"}, f"automatic check finds only real corporate-action moves (found {sorted(got)})")
    check(abs(got["SPLIT"] - 0.1) < 0.01 and got["REVERSE"] > 5, "automatic factors: 1/10 for the split, about 10 for the consolidation")
    px = apply_events(raw[["SPLIT"]], ev)
    check((px["SPLIT"].pct_change().abs().max()) < 0.06, "after the automatic adjustment the split day shows no fake drop")


def test_announcements():
    cases = [
        ("Bonus issue 1:3", None, "bonus", 0.75),
        ("Bonus 1:1", None, "bonus", 0.5),
        ("Stock Split From Rs.10/- To Rs.1/-", None, "split", 0.1),
        ("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Rs 2/- Per Share", None, "split", 0.2),
        ("Sub-division of equity shares of Rs.10/- each into 10 equity shares of Rs.1/- each", None, "split", 0.1),
        ("Consolidation from Rs.1/- to Rs.10/-", None, "split", 10.0),
        ("Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per Share", None, "split", 0.1),
        ("Bonus 5:1", None, "bonus", 1 / 6),
        ("Spin Off", None, "estimate", None),
        ("Final Dividend - Rs. - 1.2500", None, None, None),
        ("Bonus issue of debentures 1:10", None, None, None),
    ]
    for text, face, kind, factor in cases:
        p = parse_purpose(text, face)
        ok = p["kind"] == kind and (factor is None or abs(p["factor"] - factor) < 1e-9)
        check(ok, f"announcement text read correctly: {text[:48]}")
    r = parse_purpose("Rights 1:5 @ Premium Rs 30/-", 10)
    check(r["kind"] == "rights" and r["issue"] == 40.0 and r["ratio"] == (1, 5), "rights text: ratio and issue price (face value + premium)")

    idx = pd.bdate_range("2026-03-02", periods=40)
    price = pd.Series(100.0, index=idx)
    price.iloc[20:] = 75.0                                   # 1:3 bonus on day 20
    raw_px = pd.DataFrame({"AAA": price, "RGT": 100.0, "SPIN": 100.0}, index=idx)
    raw_px.loc[idx[25]:, "SPIN"] = 60.0                      # spin-off, day 25
    acts = pd.DataFrame([
        ("BSE", "AAA", "1", idx[20], "Bonus issue 1:3", np.nan),
        ("BSE", "RGT", "2", idx[10], "Rights 1:5 @ Premium Rs 30/-", 10.0),
        ("BSE", "RGT", "2", idx[12], "Rights 1:5 @ Premium Rs 30/-", np.nan),
        ("BSE", "SPIN", "3", idx[25], "Spin Off", np.nan),
        ("BSE", "AAA", "1", idx[30], "Final Dividend - Rs. - 2", np.nan),
    ], columns=["source", "symbol", "code", "ex_date", "purpose", "face"])
    ev, unres = resolve_actions(acts, raw_px, None)
    got = {(r.symbol, r.date): r.factor for r in ev.itertuples()}
    check(abs(got[("AAA", idx[20])] - 0.75) < 1e-9, "bonus announcement gives factor 0.75 on the ex-date")
    check(abs(got[("RGT", idx[10])] - (5 + 1 * 40 / 100) / 6) < 1e-3, "rights issue factor from theoretical ex-rights price")
    check(abs(got[("SPIN", idx[25])] - 0.6) < 1e-3, "spin-off: official date, factor estimated from the price move")
    check(len(unres) == 1 and unres[0][0] == "RGT", "rights issue without an issue price is reported, not guessed")

    # download functions: windows, JSON shapes, failures
    def bse_get(a, b):
        return {"Table": [{"scrip_code": 532356, "short_name": "trivenI", "Ex_date": "22 Jul 2026",
                           "Purpose": "Spin Off"}]} if a <= dt.date(2026, 7, 22) <= b else []
    df, note = fetch_bse_actions(pd.Timestamp("2026-06-01"), pd.Timestamp("2026-08-31"), get=bse_get, pause=0)
    check(len(df) == 1 and df.iloc[0]["symbol"] == "TRIVENI" and df.iloc[0]["ex_date"] == pd.Timestamp("2026-07-22"),
          "BSE announcements: rows read from the JSON answer")
    def nse_get(a, b):
        return [{"symbol": "GOLDIAM", "subject": "Bonus 1:3", "exDate": "10-Jul-2026", "faceVal": "10"}]
    df, note = fetch_nse_actions(pd.Timestamp("2026-06-01"), pd.Timestamp("2026-08-31"), get=nse_get, pause=0)
    check(len(df) >= 1 and df.iloc[0]["face"] == 10.0 and df.iloc[0]["ex_date"] == pd.Timestamp("2026-07-10"),
          "NSE announcements: rows and face value read")
    def odd(a, b):
        return [{"foo": "x", "bar": "y"}]
    df, note = fetch_bse_actions(pd.Timestamp("2026-06-01"), pd.Timestamp("2026-06-20"), get=odd, pause=0)
    check(df.empty and "field names seen" in note and "foo" in note,
          "unreadable announcement fields are reported with the field names seen")

    def blocked(a, b):
        raise ValueError("Expecting value: line 1 column 1")
    df, note = fetch_bse_actions(pd.Timestamp("2026-06-01"), pd.Timestamp("2026-08-31"), get=blocked, pause=0)
    check(df.empty and "ValueError" in note, "a blocked or non-JSON answer is reported as not usable")

    # full check: validated only when the announcements reproduce YOUR known events
    store, dates = exchange_store(adjusted=False)
    raw = raw_close_matrix(store, list(store["symbol"].unique()))
    manual = pd.DataFrame([("BON", dates[40], 0.75, "1:3 bonus")], columns=["symbol", "ex_date", "factor", "note"])
    good = lambda a, b: [{"scrip_code": 1, "short_name": "BON", "Ex_date": dates[40].strftime("%d %b %Y"),
                          "Purpose": "Bonus issue 1:3"},
                         {"scrip_code": 2, "short_name": "RIGHTS", "Ex_date": dates[50].strftime("%d %b %Y"),
                          "Purpose": "Spin Off"}]
    wrong = lambda a, b: [{"scrip_code": 1, "short_name": "BON", "Ex_date": dates[41].strftime("%d %b %Y"),
                           "Purpose": "Bonus issue 1:2"}]
    def refuse(a, b):
        raise ConnectionError("HTTP 403")
    events, rej, status, unver, _mm = gather_events(store, raw, ["BON", "RIGHTS", "S00"], manual,
                                                    skip_yahoo=True, skip_api=True,
                                                    announce_getters={"BSE": good, "NSE": refuse},
                                                    bse_ids={"BON", "RIGHTS", "S00"})
    check(any("BSE announcements: VALIDATED" in l for l in status) and "RIGHTS" in set(events["symbol"]) and not unver,
          "announcements that match your known events are used, and cover the stock")
    events, rej, status, unver, _mm = gather_events(store, raw, ["BON", "S00"], manual, skip_yahoo=True,
                                                    skip_api=True, announce_getters={"BSE": wrong, "NSE": refuse},
                                                    bse_ids={"BON", "S00"})
    check(any("BSE announcements: NOT used" in l for l in status),
          "announcements that contradict your known events are rejected")


def test_backtest():
    rng = np.random.default_rng(3)
    dates = pd.bdate_range("2018-01-01", "2022-12-31")
    n = 60
    rates = np.linspace(0.0001, 0.0018, n)                  # stock 59 is the best, ordering is stable
    r = rates + rng.normal(0, 2e-4, (len(dates), n))
    P = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=dates, columns=[f"S{i:02d}" for i in range(n)])
    ranks = bt.compute_ranks(P, None, 0)
    check(ranks.iloc[-1].idxmin() == "S59", "backtest: the fastest riser gets rank 1")
    res = bt.simulate(P, ranks, n=20, entry=20, exit_=40, cost_bps=0, cash_rate=0.0)
    top = [f"S{i:02d}" for i in range(40, 60)]
    exp = 100 * (P.loc[res["equity"].index[-1], top] / P.loc[res["equity"].index[0], top]).mean()
    check(abs(res["equity"].iloc[-1] / exp - 1) < 1e-6, "backtest: result equals buy-and-hold of the top 20 (known answer)")
    res2 = bt.simulate(P, ranks, n=20, entry=20, exit_=40, cost_bps=30, cash_rate=0.0)
    check(abs(res2["equity"].iloc[-1] / (exp * 0.997) - 1) < 1e-4, "backtest: trading cost is charged once per buy")
    t = ranks.index[30]
    P2 = P.copy()
    fut = P2.index > t
    P2.loc[fut] = P2.loc[fut] * np.random.default_rng(1).uniform(0.5, 1.5, P2.loc[fut].shape)
    check(bt.compute_ranks(P2, None, 0).loc[t].equals(ranks.loc[t]), "backtest: ranks use no future data")


def test_universe_and_backtest2():
    import tempfile
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            os.makedirs("universe")
            open("universe/nifty50.txt", "w").write("AAA\nBBB\nCCC\n")
            check(uv.load_index("nifty50") == ["AAA", "BBB", "CCC"], "universe: index list file is read")
            try:
                uv.load_index("doesnotexist")
            except SystemExit:
                print("ok  - universe: missing index file gives a clear error")
            else:
                check(False, "universe: missing index file gives a clear error")

            open("universe/marketcap.csv", "w").write("symbol,marketcap_cr\nAAA,2000\nBBB,8000\nCCC,50000\n")
            got = uv.resolve("marketcap", 1000, 10000)
            check(sorted(got) == ["AAA", "BBB"], "universe: marketcap band filters correctly")

            rng = np.random.default_rng(5)
            dates = pd.bdate_range("2020-01-01", periods=600)
            rates = np.linspace(0.0002, 0.0018, 20)
            P = pd.DataFrame(100 * np.exp(np.cumsum(rates + rng.normal(0, 0.015, (600, 20)), axis=0)),
                             index=dates, columns=[f"S{i:02d}" for i in range(20)])
            ranks = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0)
            check(ranks.iloc[-1].idxmin() == "S19", "backtest2: fastest riser ranks first (own compute_ranks)")

            # single-measure scenario: only w_r3 nonzero
            only_r3 = {"r3": 1.0, "r3_vol": 0, "r6": 0, "r6_vol": 0, "r12_1": 0, "r12_1_vol": 0, "near_high": 0}
            ranks_r3 = bt2.compute_ranks(P, only_r3, list(P.columns), min_turnover_cr=0)
            check(not ranks_r3.equals(ranks), "backtest2: a single nonzero weight (r3 only) gives a different ranking than the default mix")

            # a choppy climber should rank worse on r6_vol than a smooth one with the same total return
            dv = pd.bdate_range("2020-01-01", periods=400)
            smooth = 100 * np.exp(np.cumsum(np.full(400, 0.0012)))
            choppy = 100 * np.exp(np.cumsum(np.where(np.arange(400) % 2 == 0, 0.03, -0.0276)))
            Pv = pd.DataFrame({"SMOOTH": smooth, "CHOPPY": choppy,
                               **{f"F{i}": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 400))) for i in range(15)}}, index=dv)
            only_r6vol = {"r3": 0, "r3_vol": 0, "r6": 0, "r6_vol": 1.0, "r12_1": 0, "r12_1_vol": 0, "near_high": 0}
            rv = bt2.compute_ranks(Pv, only_r6vol, list(Pv.columns), min_turnover_cr=0)
            check(rv.iloc[-1]["SMOOTH"] < rv.iloc[-1]["CHOPPY"],
                  "backtest2: w_r6vol ranks the smoother climber ahead of the choppier one with similar total return")

            try:
                bt2.compute_ranks(P, {k: 0 for k in bt2.MEASURES}, list(P.columns), min_turnover_cr=0)
            except SystemExit:
                print("ok  - backtest2: all-zero weights is rejected with a clear error")
            else:
                check(False, "backtest2: all-zero weights is rejected with a clear error")

            gate = pd.Series(False, index=ranks.index)          # index filter always closed
            res = bt2.simulate(P, ranks, n=5, entry=5, exit_=10, cost_bps=0, buy_gate=gate)
            check(len(res["trades"]) == 0, "backtest2: buy_gate closed for the whole run makes zero trades")

            gate2 = pd.Series(True, index=ranks.index)
            res2 = bt2.simulate(P, ranks, n=5, entry=5, exit_=10, cost_bps=0, buy_gate=gate2)
            check(len(res2["trades"]) > 0, "backtest2: buy_gate open lets trades happen")

            windowed = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0,
                                         start=str(dates[300].date()))
            check(windowed.index.min() >= dates[300], "backtest2: start= actually restricts the ranking window")

            os.makedirs("data", exist_ok=True)
            open("data/index_test.csv", "w").write("date,close\n" + "\n".join(
                f"{d.date()},{100 + i}" for i, d in enumerate(dates[::20])))
            s_idx, src = bt2.load_index_series("test", P)
            check(src.startswith("file") and len(s_idx) > 0, "backtest2: a real data/index_<name>.csv is read, not the proxy")
        finally:
            os.chdir(cwd)


def test_scenario_weight_defaults():
    import tempfile
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            open("scenarios.csv", "w").write(
                "name,universe,entry,exit,w_r3\n"
                "all_default,nifty500,20,40,\n"          # every weight blank -> default mix
                "r3_only,nifty500,20,40,1\n")             # one weight set -> ONLY that measure
            df = bt2.load_scenarios("scenarios.csv")
            d = df.set_index("name")
            check(d.loc["all_default", "w_r6vol"] == bt2.DEFAULT_WEIGHTS["r6_vol"],
                  "scenarios.csv: a row with every weight blank gets the default mix")
            check(d.loc["r3_only", "w_r3"] == 1.0 and d.loc["r3_only", "w_r6vol"] == 0.0
                  and d.loc["r3_only", "w_r12_1"] == 0.0 and d.loc["r3_only", "w_nearhigh"] == 0.0,
                  "scenarios.csv: a row with only w_r3 set does NOT silently mix in the other defaults")
        finally:
            os.chdir(cwd)


def test_index_history_parsing():
    sample = {"data": {"indexCloseOnlineRecords": [
        {"EOD_TIMESTAMP": "01-Jan-2020", "EOD_CLOSE_INDEX_VAL": "12,168.45"},
        {"EOD_TIMESTAMP": "02-Jan-2020", "EOD_CLOSE_INDEX_VAL": "12,282.20"},
    ]}}
    rows = fih._rows_from_json(sample)
    check(len(rows) == 2, "index history: records found inside the nested BSE/NSE-style JSON shape")
    d = fih._pick(rows[0], "EOD_TIMESTAMP")
    c = fih._pick(rows[0], "EOD_CLOSE_INDEX_VAL")
    check(d == "01-Jan-2020" and c == "12,168.45", "index history: field lookup is case/underscore-insensitive")


def test_capital_slippage_tax_rebalance():
    rng = np.random.default_rng(21)
    dates = pd.bdate_range("2018-01-01", "2023-12-31")
    n = 30
    rates = np.linspace(0.0002, 0.0016, n)
    rng.shuffle(rates)
    P = pd.DataFrame(100 * np.exp(np.cumsum(rates + rng.normal(0, 0.015, (len(dates), n)), axis=0)),
                     index=dates, columns=[f"C{i:02d}" for i in range(n)])
    ranks = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0)

    r1 = bt2.simulate(P, ranks, n=10, entry=10, exit_=20, cost_bps=0, start_value=100)
    r2 = bt2.simulate(P, ranks, n=10, entry=10, exit_=20, cost_bps=0, start_value=100000)
    check(abs(r2["equity"].iloc[-1] / r1["equity"].iloc[-1] - 1000) < 0.5,
          "backtest2: result scales linearly with starting capital (Rs 100 vs Rs 100,000)")

    r_plain = bt2.simulate(P, ranks, n=10, entry=10, exit_=20, cost_bps=0, slippage_bps=0, start_value=100000)
    r_slip = bt2.simulate(P, ranks, n=10, entry=10, exit_=20, cost_bps=0, slippage_bps=100, start_value=100000)
    check(r_slip["equity"].iloc[-1] < r_plain["equity"].iloc[-1],
          "backtest2: slippage makes both buys and sells worse, lowering the result")

    r_notax = bt2.simulate(P, ranks, n=10, entry=10, exit_=20, cost_bps=0, start_value=100000, tax=False)
    r_tax = bt2.simulate(P, ranks, n=10, entry=10, exit_=20, cost_bps=0, start_value=100000, tax=True)
    end_notax = r_notax["equity"].iloc[-1]
    end_tax = r_tax["equity"].iloc[-1] - r_tax["pending_tax"]
    check(end_tax < end_notax and (r_tax["tax_paid"] + r_tax["pending_tax"]) > 0,
          "backtest2: tax=True actually removes money from the result")

    ts = r_notax["trade_stats"]
    check(ts["num_trades"] > 0 and 0 <= ts["win_rate"] <= 1 and pd.notna(ts["profit_factor"]),
          "backtest2: trade_stats (win rate, profit factor) are computed from real closed trades")

    ranks_w = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0, rebalance="weekly")
    ranks_d = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0, rebalance="daily")
    check(len(ranks_w) > len(ranks) and len(ranks_d) > len(ranks_w),
          "backtest2: weekly rebalance has more signal dates than monthly, daily more than weekly")


def test_indicator_filters():
    rng = np.random.default_rng(31)
    dates = pd.bdate_range("2019-01-01", "2023-12-31")
    n = 25
    rates = np.linspace(0.0002, 0.0015, n)
    rng.shuffle(rates)
    P = pd.DataFrame(100 * np.exp(np.cumsum(rates + rng.normal(0, 0.015, (len(dates), n)), axis=0)),
                     index=dates, columns=[f"D{i:02d}" for i in range(n)])
    V = pd.DataFrame(rng.uniform(1e5, 1e6, (len(dates), n)), index=dates, columns=P.columns)

    plain = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0)
    rsi_tight = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0,
                                  rsi_entry_min=60, rsi_entry_max=70)
    check(rsi_tight.notna().to_numpy().sum() < plain.notna().to_numpy().sum(),
          "backtest2: a tight RSI band eliminates some otherwise-eligible stocks")

    macd_on = bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0, macd_filter=True)
    check(macd_on.notna().to_numpy().sum() <= plain.notna().to_numpy().sum(),
          "backtest2: the MACD filter only keeps stocks whose MACD line is above its signal")

    try:
        bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=1e9, volume=V)
    except SystemExit:
        print("ok  - backtest2: a real turnover filter (with volume data) excludes everything when set absurdly high")
    else:
        check(False, "backtest2: a real turnover filter (with volume data) excludes everything when set absurdly high")

    try:
        bt2.compute_ranks(P, bt2.DEFAULT_WEIGHTS, list(P.columns), min_turnover_cr=0, volume=V,
                          vol_surge_entry=1000)
    except SystemExit:
        print("ok  - backtest2: an unreachable volume-surge requirement excludes everything")
    else:
        check(False, "backtest2: an unreachable volume-surge requirement excludes everything")


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
    test_auto_estimate()
    test_yahoo_handling()
    test_exchange_sources()
    test_parse_sec()
    test_bse()
    test_auto_detection()
    test_backtest()
    test_universe_and_backtest2()
    test_index_history_parsing()
    test_capital_slippage_tax_rebalance()
    test_indicator_filters()
    test_scenario_weight_defaults()
    test_announcements()
    test_parser()
    print("ALL SELFTESTS PASSED")
