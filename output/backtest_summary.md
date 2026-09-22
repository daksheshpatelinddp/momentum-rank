# Backtest summary

> Every universe here uses TODAY's index membership or market-cap snapshot for the WHOLE backtest period (see universe.py's docstring) - a real form of survivorship bias, present in every row here, so use this table to compare rows against each other rather than to judge any one of them in isolation. Past results do not predict future returns.

| Scenario | Universe | Enter/Exit | CAGR | Max drawdown | Sharpe | Positive months | Yearly turnover | Avg holdings |
|---|---|---|---|---|---|---|---|---|
| n500_top20_exit40 | nifty500 | 20/40 | 2.0% | -27.4% | -0.13 | 65.0% | 760% | 20 |
| n500_top10_exit30 | nifty500 | 10/30 | -5.2% | -33.9% | -0.39 | 55.0% | 823% | 10 |
| n200_top20_exit40 | nifty200 | 20/40 | -5.7% | -24.5% | -0.52 | 60.0% | 554% | 20 |
| n50_top10_exit20 | nifty50 | 10/20 | -8.5% | -17.8% | -0.81 | 60.0% | 407% | 10 |
| midcap100_top15_exit30 | niftymidcap100 | 15/30 | 9.0% | -27.0% | 0.18 | 65.0% | 342% | 15 |
| n500_top20_exit40_trendfilter | nifty500 | 20/40 | -4.3% | -25.2% | -0.48 | 60.0% | 622% | 16 |

## Data notes

- BSE announcements: 6223 read, 73 applied with an exact factor, 11 could not be given a factor automatically.
- NSE announcements: 6355 read, 83 applied with an exact factor, 2 could not be given a factor automatically.
- Automatic price check: 13 one-day move(s) too large for normal trading, with no announcement confirming them, adjusted with an ESTIMATED factor.
- Total corporate-action adjustments applied: 96 (18 estimated).

Each scenario's own page (year-by-year returns, etc.) is in output/scenarios/.
