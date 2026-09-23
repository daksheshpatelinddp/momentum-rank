# n500_top20_exit40

Universe: **nifty500**, 501 symbols, 1 missing prices. Buy top **20**, hold up to **20**, exit below rank **40**, rebalance **monthly** (every 1 period(s)), starting capital Rs 500,000, cost 30 bps + slippage 0 bps, with tax.

Score uses: r3 (0.25), r6_vol (0.30), r12_1 (0.25), near_high (0.20). Extra filters: 20d/100d volume >= 1.2x; close > own 200-day SMA. New buys only while nifty50 is above its 200-day average. Index trend filter uses proxy (equal-weight average of the universe; no data/index_nifty50.csv found).

| Period | Starting capital | Ending value | CAGR | Total return | Volatility | Sharpe | Max drawdown |
|---|---|---|---|---|---|---|---|
| 2025-01-01 to 2026-09-21 (1.7y) | Rs 500,000 | Rs 461,952 | -4.3% | -7.3% | 19.4% | -0.48 | -25.2% |

## Trade statistics (Amibroker-style)

| Closed trades | Win rate | Avg win | Avg loss | Profit factor | Avg holding period | Max consecutive losses | Time invested | Yearly turnover | Avg holdings |
|---|---|---|---|---|---|---|---|---|---|
| 102 | 30.4% | Rs 3,086 | Rs -2,894 | 0.47 | 85 days | 21 | 100.0% | 622% | 16.1 |

Tax paid during the run: Rs 0. Tax owed on gains still open at the end (not yet paid): Rs 0 (subtracted from 'Ending value' above). Rough model: 20% short-term / 12.5% long-term (12+ months), netted per financial year - check current rates.


- No usable volume data for this scenario's universe/date range -> the turnover filter used price-only as an approximation, and any vol_surge_entry condition was skipped (treated as always passing).


## Year by year

| Year | Return |
|---|---|
| 2025 | -11.7% |
| 2026 | 4.9% |
