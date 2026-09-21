# Multi-scenario backtest — setup

## 1. Add these files to the repo
- `fetch_history.py`, `universe.py`, `backtest2.py` — new
- `scenarios.csv` — new (edit this to define your scenarios)
- `.github/workflows/backtest2.yml` — new workflow
- `selftest.py` — replace with the updated one

## 2. Edit scenarios.csv
One row = one backtest. The comments at the top explain each column. Start from the seven
example rows and change/add/remove rows freely — no code changes needed.

- **universe**: `nifty50` / `nifty100` / `nifty200` / `nifty500` / `niftymidcap100` /
  `niftysmallcap100` / `marketcap`. The first six come from NSE's own index lists,
  downloaded automatically. `marketcap` needs `universe/marketcap.csv` — see below.
- **entry / exit**: your top-N / exit-below-rank rule.
- **stock_sma200**, **index_sma200**: `yes`/`no` trend filters, as you asked for.

## 3. Market-cap universes (optional)
If you use `universe = marketcap` in any row, create `universe/marketcap.csv` yourself:

```
symbol,marketcap_cr
RELIANCE,1900000
TCS,1400000
...
```

Screener.in's "Export to Excel" on a broad screen is one way to build this. There is no
free, automatable source for *historical* market cap by stock, so this file is a snapshot —
today's market cap is applied to the whole backtest. This is explained in every report.

## 4. Run it
**Actions → Multi-scenario backtest → Run workflow.**

The first run downloads years of NSE price history, which can take longer than one GitHub
Actions run allows. If the log says the history is incomplete, **just run the workflow
again** — it resumes from where it stopped. Once the history is built, later runs (to add
scenarios or update recent prices) are much faster.

## 5. Read the results
- `output/backtest_summary.md` — one row per scenario, side by side.
- `output/scenarios/<name>.md` — full detail (year-by-year, turnover, etc.) for each one.

## Notes and limits
- **NSE only** (no BSE-only stocks) — bhavcopy is the shared price source across every
  universe, which keeps the comparison fair.
- **Survivorship bias**: every universe uses today's index membership or market-cap
  snapshot for the whole period. Compare scenarios to each other, not to a "true" number.
- **Corporate actions** are adjusted the same way as the live ranking: your
  `corporate_actions.csv` first, then BSE/NSE announcements, then the automatic price-jump
  check for anything neither source explains.
- Research only, not investment advice.
