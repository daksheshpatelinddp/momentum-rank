"""Stock universes for the backtest.

Two kinds, chosen per scenario in scenarios.csv:

1. Index membership: a plain text file in universe/<name>.txt, one NSE symbol per line
   (get these from NSE's index page -> "Download CSV", or reuse the existing nifty500.txt
   fetcher for the Nifty 500 itself). Recognised names: nifty50, nifty100, nifty200,
   nifty500, niftymidcap100, niftysmallcap100 -- or any file you add yourself.

2. Market-cap band: universe/marketcap.csv with columns symbol,marketcap_cr (crore rupees).
   You maintain this yourself (export from Screener.in or similar); it is a SNAPSHOT, so a
   band like "500-1000" is applied as if every stock's current market cap applied for the
   whole backtest. This is a real limitation -- see the caveat in backtest_config.README.

IMPORTANT LIMITATION (read before trusting results): both kinds use TODAY's membership or
market cap for the ENTIRE backtest period. The real Nifty 50 of 2016 held different
companies than today's. This biases every result upward (survivorship bias) exactly like
the plain "Nifty 500" backtest already warned about. Results across universes are still
comparable to EACH OTHER, which is what "various possible conditions" mostly needs.
"""
import os

import pandas as pd

DIR = "universe"
INDEX_ALIASES = {
    "nifty50": "nifty50.txt", "nifty 50": "nifty50.txt",
    "nifty100": "nifty100.txt", "nifty 100": "nifty100.txt",
    "nifty200": "nifty200.txt", "nifty 200": "nifty200.txt",
    "nifty500": "nifty500.txt", "nifty 500": "nifty500.txt",
    "niftymidcap100": "niftymidcap100.txt", "midcap100": "niftymidcap100.txt",
    "niftysmallcap100": "niftysmallcap100.txt", "smallcap100": "niftysmallcap100.txt",
}


def _read_list(path):
    out = []
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            for tok in line.split("#")[0].replace(",", " ").split():
                tok = tok.strip().upper()
                if tok.endswith(".NS"):
                    tok = tok[:-3]
                if tok and tok not in out and tok != "SYMBOL":
                    out.append(tok)
    return out


def load_index(name):
    """Symbols for a named index list. Raises SystemExit with a clear message if missing."""
    key = name.strip().lower()
    fname = INDEX_ALIASES.get(key, name if name.endswith(".txt") else name + ".txt")
    path = os.path.join(DIR, fname) if not os.path.isabs(fname) and "/" not in fname else fname
    if not os.path.exists(path) and os.path.exists(fname):
        path = fname
    if not os.path.exists(path):
        raise SystemExit(f"Universe file not found: {path}\n"
                         f"Create it (one NSE symbol per line) - e.g. download the constituent "
                         f"list from NSE's index page for '{name}' and save it as {path}.")
    syms = _read_list(path)
    if not syms:
        raise SystemExit(f"{path} has no symbols in it.")
    return syms


def load_marketcap():
    path = os.path.join(DIR, "marketcap.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    need = {"symbol", "marketcap_cr"}
    if not need.issubset(df.columns):
        raise SystemExit(f"{path} must have columns: symbol,marketcap_cr")
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["marketcap_cr"] = pd.to_numeric(df["marketcap_cr"], errors="coerce")
    return df.dropna().drop_duplicates("symbol").set_index("symbol")["marketcap_cr"]


def resolve(spec, min_mcap=None, max_mcap=None):
    """spec is either an index name (from load_index) or the literal 'marketcap'.
    Returns a plain list of symbols."""
    spec = str(spec).strip()
    if spec.lower() == "marketcap":
        mc = load_marketcap()
        if mc is None:
            raise SystemExit("universe = marketcap needs universe/marketcap.csv "
                             "(columns: symbol,marketcap_cr).")
        s = mc
        if min_mcap not in (None, "", 0):
            s = s[s >= float(min_mcap)]
        if max_mcap not in (None, ""):
            s = s[s <= float(max_mcap)]
        if s.empty:
            raise SystemExit(f"No stocks in universe/marketcap.csv between {min_mcap} and "
                             f"{max_mcap} crore.")
        return list(s.index)
    return load_index(spec)


NSE_INDEX_URLS = {
    "nifty50.txt": "https://nsearchives.nseindia.com/content/indices/ind_nifty50list.csv",
    "nifty100.txt": "https://nsearchives.nseindia.com/content/indices/ind_nifty100list.csv",
    "nifty200.txt": "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv",
    "nifty500.txt": "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv",
    "niftymidcap100.txt": "https://nsearchives.nseindia.com/content/indices/ind_niftymidcap100list.csv",
    "niftysmallcap100.txt": "https://nsearchives.nseindia.com/content/indices/ind_niftysmallcap100list.csv",
}


def fetch_index_lists(names=None, force=False):
    """Best-effort download of the standard NSE index lists into universe/. Existing files
    are left alone unless force=True (index membership does drift over time, so re-running
    this occasionally keeps it current -- but note the "today's membership applied to the
    whole backtest" limitation described at the top of this file either way)."""
    import requests
    os.makedirs(DIR, exist_ok=True)
    todo = {INDEX_ALIASES.get(n, n): u for n, u in
           ({k: NSE_INDEX_URLS[k] for k in names} if names else NSE_INDEX_URLS).items()}         if names else NSE_INDEX_URLS
    results = {}
    for fname, url in todo.items():
        path = os.path.join(DIR, fname)
        if os.path.exists(path) and not force:
            results[fname] = "already present"
            continue
        try:
            r = requests.get(url, timeout=60, headers={"User-Agent": "Mozilla/5.0",
                                                        "Referer": "https://www.nseindia.com/"})
            if r.status_code != 200:
                results[fname] = f"HTTP {r.status_code}"
                continue
            import io as _io
            df = pd.read_csv(_io.StringIO(r.text))
            col = [c for c in df.columns if c.strip().lower() == "symbol"]
            if not col:
                results[fname] = "no Symbol column in the response"
                continue
            syms = sorted(set(s.strip().upper() for s in df[col[0]].dropna().astype(str)))
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"# Downloaded from {url}\n" + "\n".join(syms) + "\n")
            results[fname] = f"{len(syms)} symbols"
        except Exception as e:
            results[fname] = f"{type(e).__name__}: {e}"
    return results


def all_symbols_needed(scenarios_df):
    """Union of every symbol any scenario's universe could need, for one shared download."""
    out = set()
    for r in scenarios_df.itertuples(index=False):
        out |= set(resolve(r.universe, getattr(r, "min_marketcap_cr", None),
                           getattr(r, "max_marketcap_cr", None)))
    return sorted(out)
