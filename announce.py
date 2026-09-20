"""Corporate-action ANNOUNCEMENTS from BSE and NSE (official ex-dates and ratios).

* fetch_bse_actions / fetch_nse_actions download every announced action in a date range.
* parse_purpose turns the announcement text into an exact price factor where the text gives
  one (bonus a:b, split/consolidation from Rs X to Rs Y, rights issue with issue price).
* resolve_actions matches announcements to your stocks and price data. For spin-offs,
  demergers and capital reductions the text has no ratio, so the factor is estimated from the
  price move on the OFFICIAL ex-date.
Nothing here is trusted until events.gather_events has checked it against the events in
corporate_actions.csv.
"""
import re
import time

import numpy as np
import pandas as pd

BSE_URL = "https://api.bseindia.com/BseIndiaAPI/api/DefaultData/w"
NSE_URL = "https://www.nseindia.com/api/corporates-corporateActions"
ACTION_COLS = ["source", "symbol", "code", "ex_date", "purpose", "face"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


# ---------------------------------------------------------------------------------------
# Reading the announcement text
# ---------------------------------------------------------------------------------------
_NUM = r"(\d+(?:\.\d+)?)"
_RS = r"(?:rs\.?|inr)?\s*"


def parse_purpose(text, face=None):
    """Return dict(kind, factor, ratio, issue).

    kind: bonus | split | rights | estimate | unresolved | None
    factor: exact price factor when the text gives it (bonus, split, consolidation)
    """
    t = " ".join(str(text).lower().replace("\u20b9", "rs").split())
    out = {"kind": None, "factor": None, "ratio": None, "issue": None}
    if not t:
        return out

    if "bonus" in t and "debenture" not in t and "preference" not in t:
        m = re.search(r"(\d+)\s*:\s*(\d+)", t)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            if a > 0 and b > 0:
                out.update(kind="bonus", factor=b / (a + b), ratio=(a, b))
                return out
        out["kind"] = "unresolved"
        return out

    if any(w in t for w in ("split", "sub-division", "subdivision", "sub division",
                            "consolidation", "consolidated")):
        m = re.search(r"from\s*" + _RS + _NUM + r"\D+?to\s*" + _RS + _NUM, t)
        if not m:
            m = re.search(r"(?:rs\.?|inr)\s*" + _NUM + r"\D*?each\D*?into.*?(?:rs\.?|inr)\s*" + _NUM, t)
        if m:
            old, new = float(m.group(1)), float(m.group(2))
            if old > 0 and new > 0 and old != new:
                out.update(kind="split", factor=new / old)
                return out
        out["kind"] = "unresolved"
        return out

    if re.search(r"\brights?\b", t):
        m = re.search(r"(\d+)\s*:\s*(\d+)", t)
        if not m:
            out["kind"] = "unresolved"
            return out
        out["ratio"] = (int(m.group(1)), int(m.group(2)))
        prem = re.search(r"premium\D{0,20}?" + _NUM, t)
        price = re.search(r"@\s*" + _RS + _NUM, t)
        if prem and face:
            out["issue"] = float(face) + float(prem.group(1))
        elif price and not prem:
            out["issue"] = float(price.group(1))
        out["kind"] = "rights"
        return out

    if any(w in t for w in ("spin off", "spin-off", "spinoff", "demerger", "de-merger",
                            "capital reduction", "reduction of capital",
                            "scheme of arrangement")):
        out["kind"] = "estimate"
        return out
    return out


def resolve_actions(actions, raw_px, market_move=None, code_to_sym=None, window_days=5):
    """Match announcements to price data. Returns (events, unresolved).

    events     : DataFrame [symbol, date, factor, source, note]
    unresolved : list of (symbol, date, text, reason) that are real events but got no factor
    """
    from events import COLS, estimate_factor

    out, unresolved = [], []
    idx = raw_px.index
    for a in actions.itertuples(index=False):
        sym = a.symbol
        if sym not in raw_px.columns and code_to_sym and str(a.code) in code_to_sym:
            sym = code_to_sym[str(a.code)]
        if sym not in raw_px.columns or pd.isna(a.ex_date):
            continue
        p = parse_purpose(a.purpose, a.face if pd.notna(a.face) else None)
        if p["kind"] is None:
            continue
        pos = int(idx.searchsorted(pd.Timestamp(a.ex_date)))
        if pos <= 0 or pos >= len(idx) or (idx[pos] - pd.Timestamp(a.ex_date)).days > window_days:
            continue
        d = idx[pos]
        s = raw_px[sym]
        label = f"{str(a.source).lower()}-announcement"
        note = str(a.purpose)[:70]

        if p["kind"] in ("bonus", "split"):
            factor = p["factor"]
        elif p["kind"] == "rights":
            before = s.iloc[:pos].dropna()
            if p["issue"] is None or before.empty:
                unresolved.append((sym, d, note, "rights issue: issue price or face value not given"))
                continue
            (na, nb), cum = p["ratio"], float(before.iloc[-1])
            factor = (nb + na * p["issue"] / cum) / (na + nb)
            if abs(factor - 1) < 0.005:
                continue
        elif p["kind"] == "estimate":
            est = estimate_factor(s, d, market_move)
            if est is None or abs(est - 1) < 0.03:
                unresolved.append((sym, d, note, "no visible price effect on the ex-date"))
                continue
            factor, label = est, label + " (estimated)"
        else:
            unresolved.append((sym, d, note, "ratio not readable from the text"))
            continue
        out.append((sym, d, round(float(factor), 4), label, note))

    ev = pd.DataFrame(out, columns=COLS)
    if len(ev):
        ev["date"] = pd.to_datetime(ev["date"])
        ev = ev.drop_duplicates(["symbol", "date"]).sort_values(["date", "symbol"])
    return ev.reset_index(drop=True), unresolved


# ---------------------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------------------
def _rows_from_json(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []


def _ts(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return pd.NaT
    return pd.to_datetime(str(x), dayfirst=True, errors="coerce")


def _pick(row, *names):
    low = {str(k).lower(): v for k, v in row.items()}
    for n in names:
        v = low.get(n.lower())
        if v not in (None, ""):
            return v
    return None


def _norm_bse(rows):
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        sym = _pick(r, "short_name", "scrip_name", "symbol")
        out.append(("BSE", str(sym).strip().upper() if sym else "",
                    str(_pick(r, "scrip_code", "scripcode") or "").strip(),
                    _ts(_pick(r, "Ex_date", "exdate", "ex_date")),
                    str(_pick(r, "Purpose", "purpose_name") or ""), np.nan))
    return out


def _norm_nse(rows):
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        sym = _pick(r, "symbol")
        try:
            face = float(_pick(r, "faceVal", "face_value"))
        except (TypeError, ValueError):
            face = np.nan
        out.append(("NSE", str(sym).strip().upper() if sym else "", "",
                    _ts(_pick(r, "exDate", "ex_date")),
                    str(_pick(r, "subject", "purpose") or ""), face))
    return out


def _windows(start, end, days):
    a = pd.Timestamp(start)
    while a <= end:
        b = min(a + pd.Timedelta(days=days - 1), end)
        yield a, b
        a = b + pd.Timedelta(days=1)


def _collect(start, end, get, norm, days, pause):
    rows, n_raw, first_keys = [], 0, None
    for a, b in _windows(start, end, days):
        try:
            data = get(a.date(), b.date())
        except Exception as e:
            return pd.DataFrame(columns=ACTION_COLS), f"{type(e).__name__}: {e}"
        raw = _rows_from_json(data)
        n_raw += len(raw)
        if first_keys is None and raw and isinstance(raw[0], dict):
            first_keys = list(raw[0].keys())[:14]
        rows += norm(raw)
        time.sleep(pause)
    df = pd.DataFrame(rows, columns=ACTION_COLS)
    df = df[(df["symbol"] != "") | (df["code"] != "")]
    df = df[df["ex_date"].notna()]
    if len(df):
        return df.reset_index(drop=True), "ok"
    if n_raw:
        return df.reset_index(drop=True), (f"answered with {n_raw} records but none could be read "
                                           f"(field names seen: {first_keys})")
    return df.reset_index(drop=True), "answered, but with no announcements"


def fetch_bse_actions(start, end, get=None, chunk_days=31, pause=0.4):
    """Every equity corporate action BSE announced with an ex-date in [start, end]."""
    if get is None:
        import requests
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept": "application/json, text/plain, */*",
                          "Referer": "https://www.bseindia.com/", "Origin": "https://www.bseindia.com"})

        def get(a, b):
            r = s.get(BSE_URL, params={
                "Fdate": f"{a:%Y%m%d}", "TDate": f"{b:%Y%m%d}", "Purposecode": "",
                "ddlcategory": "E", "ddlindustries": "", "scripcode": "", "segment": "0",
                "strSearch": "S"}, timeout=40)
            if r.status_code != 200:
                raise ConnectionError(f"HTTP {r.status_code}")
            return r.json()
    return _collect(start, end, get, _norm_bse, chunk_days, pause)


def fetch_nse_actions(start, end, get=None, chunk_days=90, pause=0.4):
    """Every equity corporate action NSE announced with an ex-date in [start, end]."""
    if get is None:
        import requests
        s = requests.Session()
        s.headers.update({"User-Agent": UA, "Accept": "application/json, text/plain, */*",
                          "Accept-Language": "en-US,en;q=0.9",
                          "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-actions"})
        for warm in ("https://www.nseindia.com/",
                     "https://www.nseindia.com/companies-listing/corporate-filings-actions"):
            try:
                s.get(warm, timeout=20)
            except Exception:
                pass

        def get(a, b):
            r = s.get(NSE_URL, params={"index": "equities", "from_date": f"{a:%d-%m-%Y}",
                                       "to_date": f"{b:%d-%m-%Y}"}, timeout=40)
            if r.status_code != 200:
                raise ConnectionError(f"HTTP {r.status_code}")
            return r.json()
    return _collect(start, end, get, _norm_nse, chunk_days, pause)
