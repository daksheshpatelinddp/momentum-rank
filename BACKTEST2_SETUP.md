# Multi-scenario backtest — setup

## Two separate workflows now
- **"Download backtest price data"** — downloads/updates NSE price history, index level
  history, and the Nifty index lists. Run this **first**, and again whenever you want fresh
  data. It resumes rather than re-downloading, so after the first run it's quick.
- **"Multi-scenario backtest"** — reads whatever is already saved and runs every row in
  `scenarios.csv`. It does **no downloading at all**. Run this as often as you like while
  editing `scenarios.csv` — it's fast every time.

## 1. Add/replace these files in the repo
- New: `fetch_history.py`, `fetch_index_history.py`, `universe.py`, `indicators.py`
- Replace: `backtest2.py`, `scenarios.csv`, `selftest.py`
- Workflows: add `.github/workflows/data.yml`, replace `.github/workflows/backtest2.yml`

## 2. First run
**Actions → Download backtest price data → Run workflow.** May need a couple of runs to
finish a decade of history (it saves progress and resumes). Once `data/history.csv` exists
and is reasonably up to date, you don't need to run this again except to refresh.

## 3. Edit scenarios.csv and run the backtest
Every column is documented in the comments at the top of the file. Highlights covering what
you asked for:

- **Starting capital & slippage**: `capital` (rupees), `cost_bps` (brokerage/statutory),
  `slippage_bps` (assumed adverse fill). Results are shown in real ₹, not just an index.
- **Daily / weekly / monthly**: `rebalance` column.
- **With/without expenses and tax**: `cost_bps`/`slippage_bps` to 0 for a frictionless run;
  `tax` yes/no for the rough Indian capital-gains model. Run the same row both ways to see
  the difference.
- **RSI / MACD / volume conditions**: `rsi_entry_min`/`max`, `macd_filter`,
  `vol_surge_entry` — a stock failing any of these is excluded from that rebalance (forcing
  an exit if held), so these work as combined entry+exit filters.

Then: **Actions → Multi-scenario backtest → Run workflow.**

## 4. Read the results (Amibroker-style)
- `output/backtest_summary.md` — all scenarios side by side.
- `output/scenarios/<name>.md` — starting/ending capital, CAGR, Sharpe, max drawdown, **and
  a trade-statistics block**: number of closed trades, win rate, average win/loss, profit
  factor, average holding period, max consecutive losing trades, time invested, turnover.
- `output/scenarios/<name>_trades.csv` — every buy and sell, with price, shares, gain, and
  holding days, if you want to dig in yourself or check it against another tool.

## Notes and limits
- **Survivorship bias**: every universe uses today's index membership or market-cap snapshot
  for the whole period. Compare scenarios to each other, not to a "true" number.
- **Slippage is a flat assumption**, not a real market-impact model (that needs order-book
  data this backtest doesn't have). Use it as a stress test, and use `min_turnover_cr` plus
  the report's turnover/exposure figures as a capacity sanity check.
- **Tax is a rough model** (20% short-term / 12.5% long-term, netted per financial year) —
  check current rates before relying on it.
- **RSI/MACD/volume filters** need enough price (and, for volume, volume) history — a
  scenario with too few eligible stocks on every rebalance date fails cleanly and is marked
  `FAILED` in the summary; the other rows still run.
- Research only, not investment advice.
