# Momentum ranking (data up to 2026-11-06)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ROLEXRINGS | 95.0 | 28.4 | 34.6 | 76.2 | 49.0 | 47.7 | 2.2 | 201.17 |  |
| 2 | PAYTM | 93.1 | 24.5 | 50.0 | 33.3 | 21.9 | 40.7 | 3.0 | 1794.4 |  |
| 3 | KAJARIACER | 78.6 | 1.1 | 7.8 | 5.0 | 7.6 | 21.6 | 6.4 | 1180.7 |  |
| 4 | MWL | 71.4 | -9.1 | 10.0 | 67.4 | 77.5 | 34.7 | 13.8 | 38.45 |  |
| 5 | TRIVENI | 63.8 | 2.9 | 1.6 | 10.4 | 9.4 | 41.8 | 20.0 | 240.01 |  |
| 6 | SBIN | 58.8 | -7.2 | 4.6 | 6.6 | -1.7 | 20.2 | 17.0 | 1018.5 |  |
| 7 | PFOCUS | 58.1 | -0.8 | -2.2 | 64.9 | 57.2 | 54.4 | 20.2 | 285.2 |  |
| 8 | GUJTHEM | 56.9 | 6.8 | -1.4 | -15.5 | -18.3 | 52.0 | 16.1 | 380.2 |  |
| 9 | HDFCAMC | 56.9 | 4.1 | -3.5 | -2.4 | -17.3 | 31.6 | 7.5 | 2649.8 |  |
| 10 | HDFCBANK | 55.2 | 7.8 | 3.2 | -19.8 | -29.5 | 23.3 | 21.9 | 788.25 |  |
| 11 | AEGISVOPAK | 53.8 | -13.6 | 16.1 | -5.2 | 9.6 | 47.9 | 22.6 | 246.5 |  |
| 12 | GUJINJEC | 51.4 | -1.5 | -7.2 | 309.5 | 275.8 | 52.0 | 24.4 | 10.32 |  |
| 13 | GOLDIAM | 51.0 | -15.1 | 1.5 | 19.0 | 14.9 | 51.2 | 17.5 | 316.65 |  |
| 14 | KFINTECH | 50.5 | -2.2 | 2.8 | -17.6 | -24.6 | 35.0 | 17.6 | 915.8 |  |
| 15 | ZFCVINDIA | 40.0 | -13.1 | -5.8 | 8.4 | 0.1 | 28.5 | 14.7 | 2292.3 |  |
| 16 | VBL | 39.8 | -0.9 | -12.6 | -6.8 | -8.1 | 29.7 | 19.5 | 438.0 |  |
| 17 | INFY | 37.6 | 0.5 | 0.4 | -20.0 | -32.5 | 35.3 | 30.1 | 1181.4 |  |
| 18 | BRIGADE | 36.7 | -4.1 | -0.7 | -24.1 | -25.6 | 40.8 | 24.1 | 558.15 |  |
| 19 | MINOLTAF | 25.0 | -8.5 | -24.2 | -4.0 | -3.2 | 44.5 | 30.8 | 1.19 | unverified |
| 20 | JIOFIN | 21.7 | -10.0 | -3.8 | -22.8 | -29.5 | 27.0 | 26.6 | 231.2 |  |
| 21 | TEAMLEASE | 4.8 | -19.5 | -25.3 | -41.6 | -37.7 | 25.8 | 41.6 | 1009.3 |  |


## Corporate-action sources used in this run

- NSE daily file: NOT used - it reproduced only 0 of 4 known events (its previous close is not adjusted for corporate actions).
  - expected HDFCBANK 2025-08-26 factor 0.5, source showed no change
  - expected BRIGADE 2026-06-17 factor 0.75, source showed no change
  - expected GOLDIAM 2026-07-10 factor 0.75, source showed no change
  - expected TRIVENI 2026-07-22 factor 0.603, source showed no change
- NSE website API: not usable - JSONDecodeError: Expecting value: line 2 column 1 (char 1).
- BSE daily file: NOT used - it reproduced only 0 of 5 known events (its previous close is not adjusted for corporate actions).
  - expected HDFCBANK 2025-08-26 factor 0.5, source showed no change
  - expected BRIGADE 2026-06-17 factor 0.75, source showed no change
  - expected GOLDIAM 2026-07-10 factor 0.75, source showed no change
  - expected TRIVENI 2026-07-22 factor 0.603, source showed no change
  - expected GUJINJEC 2026-07-08 factor 0.1, source showed no change
- Prices for INRADIA, MINOLTAF, GUJINJEC come from BSE.
- NSE announcements: VALIDATED - reproduced 4 of 5 known events, so it is used for every bonus, split, rights issue and demerger.
  - expected GUJINJEC 2026-07-08 factor 0.1, source showed no change
- BSE announcements: not usable - ConnectionError: HTTP 403.
- Yahoo Finance (bonus/split only): checked 0 of 3 stocks; no Yahoo data for GUJINJEC, INRADIA, MINOLTAF.


## Corporate-action adjustments applied

| symbol | ex-date | factor | source | announcement / note |
|---|---|---|---|---|
| HDFCBANK | 2025-08-26 | 0.5 | manual | 1:1 bonus |
| ROLEXRINGS | 2025-10-17 | 0.1 | nse-announcement | Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per |
| HDFCAMC | 2025-11-26 | 0.5 | nse-announcement | Bonus 1:1 |
| BRIGADE | 2026-06-17 | 0.75 | manual | 1:3 bonus |
| ZFCVINDIA | 2026-06-24 | 0.1667 | nse-announcement | Bonus 5:1 |
| GUJINJEC | 2026-07-08 | 0.1 | manual | 10:1 split |
| GOLDIAM | 2026-07-10 | 0.75 | manual | 1:3 bonus |
| MWL | 2026-07-10 | 0.1 | nse-announcement | Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per |
| TRIVENI | 2026-07-22 | 0.603 | manual | spin-off (checked against Screener returns) |


**Not found in NSE or BSE data** (typo, renamed, SME or not listed): MRSS, 539229, KEDIACN, 508993


## Not ranked (not enough usable price history)

| symbol | first trade | last trade | trading days | return over that period % | why not ranked |
|---|---|---|---|---|---|
| INRADIA | 2025-08-06 | 2026-07-20 | 10 | 40.4 | stopped trading or very thin (last trade 2026-07-20) |
| JBCHEPHARM | 2025-06-25 | 2026-07-16 | 262 | 34.0 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-11-06 | 90 | -27.6 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
