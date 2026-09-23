# Backtest summary

> Every universe here uses TODAY's index membership or market-cap snapshot for the WHOLE backtest period (see universe.py's docstring) - a real form of survivorship bias, present in every row here, so use this table to compare rows against each other rather than to judge any one of them in isolation. Past results do not predict future returns.

| Scenario | Universe | Enter/Exit | CAGR | Max drawdown | Sharpe | Win rate | Profit factor | Yearly turnover | Ending value |
|---|---|---|---|---|---|---|---|---|---|
| n500_top20_exit40 | nifty500 | 20/40 | -4.3% | -25.2% | -0.48 | 30.4% | 0.47 | 622% | Rs 461,952 |

## Data notes

- Volume data covers only 0% of prices (bhavcopy rows fetched before volume capture was added have none). Turnover-based liquidity filtering and the volume-surge indicator fall back to a price-only approximation until you rebuild data/history.csv. Bonus/split-adjusted returns are unaffected.
- BSE announcements: 6223 read, 73 applied with an exact factor, 11 could not be given a factor automatically.
- NSE announcements: 6355 read, 83 applied with an exact factor, 2 could not be given a factor automatically.
- Automatic price check: 13 one-day move(s) too large for normal trading, with no announcement confirming them, adjusted with an ESTIMATED factor.
- Total corporate-action adjustments applied: 96 (18 estimated).

Each scenario's own page (year-by-year returns, etc.) is in output/scenarios/.
