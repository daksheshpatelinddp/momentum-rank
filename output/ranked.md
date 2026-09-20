# Momentum ranking (data up to 2026-09-18)

Ranked **14** of 19 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF, GUJINJEC. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 93.6 | 69.8 | 78.7 | 57.1 | 38.6 | 43.4 | 0.0 | 1849.9 |  |
| 2 | MWL | 88.2 | 13.0 | 70.6 | 67.6 | 63.3 | 34.0 | 1.2 | 42.52 |  |
| 3 | AEGISVOPAK | 77.1 | 27.9 | 77.3 | 29.9 | 14.0 | 49.6 | 0.0 | 314.95 |  |
| 4 | PFOCUS | 75.0 | 53.4 | 11.5 | 87.1 | 61.4 | 52.7 | 1.5 | 344.35 |  |
| 5 | ROLEXRINGS | 71.8 | 18.4 | 49.5 | 24.8 | 32.9 | 46.3 | 7.4 | 172.08 |  |
| 6 | KAJARIACER | 61.1 | 3.2 | 33.2 | -0.2 | 0.3 | 29.4 | 4.7 | 1202.7 |  |
| 7 | GOLDIAM | 50.7 | -7.2 | 51.9 | 9.3 | 20.6 | 58.3 | 14.9 | 326.75 |  |
| 8 | BRIGADE | 49.3 | 16.1 | 28.4 | -11.6 | -9.1 | 42.6 | 20.4 | 621.7 |  |
| 9 | ZFCVINDIA | 47.9 | -8.1 | 8.6 | 8.2 | 20.6 | 28.5 | 11.1 | 2387.0 |  |
| 10 | TRIVENI | 46.8 | -5.7 | 6.9 | 10.0 | 36.0 | 43.3 | 20.4 | 238.8 |  |
| 11 | MINOLTAF | 37.9 | -5.5 | -8.6 | 29.0 | 16.8 | 43.3 | 19.8 | 1.38 | unverified |
| 12 | HDFCBANK | 25.0 | -7.0 | -4.4 | -24.4 | -24.8 | 25.1 | 27.6 | 731.0 |  |
| 13 | TEAMLEASE | 18.6 | -15.9 | 1.7 | -35.2 | -33.8 | 23.6 | 34.8 | 1219.0 |  |
| 14 | GUJINJEC | 7.1 | -91.8 | -86.4 | -50.5 | -45.8 | 139.6 | 92.5 | 9.9 | unverified; big 1-day drop: corporate action? |


## Corporate-action sources used in this run

- NSE daily file: NOT used - it reproduced only 0 of 4 known events (its previous close is not adjusted for corporate actions).
  - expected HDFCBANK 2025-08-26 factor 0.5, source showed no change
  - expected BRIGADE 2026-06-17 factor 0.75, source showed no change
  - expected GOLDIAM 2026-07-10 factor 0.75, source showed no change
  - expected TRIVENI 2026-07-22 factor 0.603, source showed no change
- NSE website API: not usable - JSONDecodeError: Expecting value: line 2 column 1 (char 1).
- BSE daily file: NOT used - it reproduced only 0 of 4 known events (its previous close is not adjusted for corporate actions).
  - expected HDFCBANK 2025-08-26 factor 0.5, source showed no change
  - expected BRIGADE 2026-06-17 factor 0.75, source showed no change
  - expected GOLDIAM 2026-07-10 factor 0.75, source showed no change
  - expected TRIVENI 2026-07-22 factor 0.603, source showed no change
- Prices for MINOLTAF, GUJINJEC come from BSE.
- Yahoo Finance (bonus/split only): checked 13 of 15 stocks; no Yahoo data for GUJINJEC, MINOLTAF.


## Corporate-action adjustments applied

| symbol | ex-date | factor | source |
|---|---|---|---|
| HDFCBANK | 2025-08-26 | 0.5 | manual |
| ROLEXRINGS | 2025-10-17 | 0.1 | yahoo |
| BRIGADE | 2026-06-17 | 0.75 | manual |
| ZFCVINDIA | 2026-06-24 | 0.1667 | yahoo |
| GOLDIAM | 2026-07-10 | 0.75 | manual |
| MWL | 2026-07-10 | 0.1 | yahoo |
| TRIVENI | 2026-07-22 | 0.603 | manual |


## Possible corporate actions not adjusted - please check

These stocks fell sharply in one day. If the announcement shows a spin-off, demerger, rights issue, bonus or split with that ex-date, add the line (or the exact factor instead of `auto`) to corporate_actions.csv. If it was a real price fall, ignore it.

| symbol | date | 1-day move % | estimated factor | line to add to corporate_actions.csv |
|---|---|---|---|---|
| GUJINJEC | 2026-07-08 | -89.7 | 0.1049 | GUJINJEC,2026-07-08,auto,check announcement |


**Not found in NSE or BSE data** (typo, renamed, SME or not listed): INDRADIA, JBCHEMPHARMA, MRSS, KEDIACN


**Skipped: less than about 12 months of history or not trading recently:** GUJENERGY


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
