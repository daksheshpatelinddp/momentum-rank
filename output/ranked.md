# Momentum ranking (data up to 2026-09-18)

Ranked **15** of 20 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: INRADIA, JBCHEPHARM, MINOLTAF, GUJINJEC. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 94.0 | 69.8 | 78.7 | 57.1 | 38.6 | 43.4 | 0.0 | 1849.9 |  |
| 2 | MWL | 89.0 | 13.0 | 70.6 | 67.6 | 63.3 | 34.0 | 1.2 | 42.52 |  |
| 3 | AEGISVOPAK | 77.0 | 27.9 | 77.3 | 29.9 | 14.0 | 49.6 | 0.0 | 314.95 |  |
| 4 | PFOCUS | 76.7 | 53.4 | 11.5 | 87.1 | 61.4 | 52.7 | 1.5 | 344.35 |  |
| 5 | ROLEXRINGS | 73.7 | 18.4 | 49.5 | 24.8 | 32.9 | 46.3 | 7.4 | 172.08 |  |
| 6 | KAJARIACER | 62.0 | 3.2 | 33.2 | -0.2 | 0.3 | 29.4 | 4.7 | 1202.7 |  |
| 7 | GOLDIAM | 50.7 | -7.2 | 51.9 | 9.3 | 20.6 | 58.3 | 14.9 | 326.75 |  |
| 8 | BRIGADE | 49.7 | 16.1 | 28.4 | -11.6 | -9.1 | 42.6 | 20.4 | 621.7 |  |
| 9 | ZFCVINDIA | 48.0 | -8.1 | 8.6 | 8.2 | 20.6 | 28.5 | 11.1 | 2387.0 |  |
| 10 | TRIVENI | 47.3 | -5.7 | 6.9 | 10.0 | 36.0 | 43.3 | 20.4 | 238.8 |  |
| 11 | SBIN | 47.3 | -4.3 | -3.4 | 15.5 | 21.6 | 24.9 | 18.9 | 996.2 |  |
| 12 | MINOLTAF | 35.3 | -5.5 | -8.6 | 29.0 | 16.8 | 43.3 | 19.8 | 1.38 | unverified |
| 13 | HDFCBANK | 23.3 | -7.0 | -4.4 | -24.4 | -24.8 | 25.1 | 27.6 | 731.0 |  |
| 14 | TEAMLEASE | 19.3 | -15.9 | 1.7 | -35.2 | -33.8 | 23.6 | 34.8 | 1219.0 |  |
| 15 | GUJINJEC | 6.7 | -91.8 | -86.4 | -50.5 | -45.8 | 139.6 | 92.5 | 9.9 | unverified; big 1-day drop: corporate action? |


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
- Prices for INRADIA, MINOLTAF, GUJINJEC come from BSE.
- Yahoo Finance (bonus/split only): checked 14 of 18 stocks; no Yahoo data for GUJINJEC, INRADIA, JBCHEPHARM, MINOLTAF.


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


**Not found in NSE or BSE data** (typo, renamed, SME or not listed): MRSS, KEDIACN


**Skipped: less than about 12 months of history or not trading recently:** INRADIA, JBCHEPHARM, GUJENERGY


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
