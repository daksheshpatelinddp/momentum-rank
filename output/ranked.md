# Momentum ranking (data up to 2026-09-18)

Ranked **9** of 12 symbols. Score is 0-100 (percentile-based, relative to this list only).

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 90.0 | 69.8 | 78.7 | 57.1 | 38.6 | 43.4 | 0.0 | 1849.9 |  |
| 2 | MWL | 84.4 | 13.0 | 70.6 | 67.6 | 63.3 | 34.0 | 1.2 | 42.52 |  |
| 3 | AEGISVOPAK | 75.6 | 27.9 | 77.3 | 29.9 | 14.0 | 49.6 | 0.0 | 314.95 |  |
| 4 | PFOCUS | 71.1 | 53.4 | 11.5 | 87.1 | 61.4 | 52.7 | 1.5 | 344.35 |  |
| 5 | GOLDIAM | 56.1 | -7.2 | 51.9 | 9.3 | 20.6 | 58.3 | 14.9 | 326.75 |  |
| 6 | BRIGADE | 53.3 | 16.1 | 28.4 | -11.6 | -9.1 | 42.6 | 20.4 | 621.7 |  |
| 7 | HDFCBANK | 30.0 | -7.0 | -4.4 | -24.4 | -24.8 | 25.1 | 27.6 | 731.0 |  |
| 8 | TEAMLEASE | 22.8 | -15.9 | 1.7 | -35.2 | -33.8 | 23.6 | 34.8 | 1219.0 |  |
| 9 | TRIVENI | 16.7 | -43.1 | -35.5 | -33.7 | -18.0 | 74.0 | 50.0 | 238.8 | big 1-day drop: bonus/split? |


## Corporate-action sources used in this run

- NSE daily file: NOT used - it reproduced only 0 of 3 known events (its previous close is not adjusted for corporate actions).
  - expected HDFCBANK 2025-08-26 factor 0.5, source showed no change
  - expected BRIGADE 2026-06-17 factor 0.75, source showed no change
  - expected GOLDIAM 2026-07-10 factor 0.75, source showed no change
- NSE website API: not usable - JSONDecodeError: Expecting value: line 2 column 1 (char 1).
- Yahoo Finance (bonus/split only): checked 9 of 9 stocks.


## Corporate-action adjustments applied

| symbol | ex-date | factor | source |
|---|---|---|---|
| HDFCBANK | 2025-08-26 | 0.5 | manual |
| BRIGADE | 2026-06-17 | 0.75 | manual |
| GOLDIAM | 2026-07-10 | 0.75 | manual |
| MWL | 2026-07-10 | 0.1 | yahoo |


**Not found in NSE data** (typo, renamed, SME or not listed): INDRADIA, JBCHEMPHARMA, MINOLTAF


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
