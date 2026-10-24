# Momentum ranking (data up to 2026-10-23)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 94.3 | 25.9 | 42.8 | 25.6 | 34.8 | 41.3 | 12.6 | 1616.1 |  |
| 2 | MWL | 90.7 | 4.3 | 24.6 | 57.3 | 83.7 | 37.7 | 15.8 | 37.56 |  |
| 3 | ROLEXRINGS | 87.1 | 11.0 | 4.6 | 22.3 | 43.1 | 42.7 | 21.0 | 155.03 |  |
| 4 | PFOCUS | 68.3 | -5.7 | -14.2 | 52.9 | 78.6 | 52.5 | 23.7 | 272.85 |  |
| 5 | KAJARIACER | 62.9 | -6.4 | -8.1 | -6.0 | 1.1 | 24.5 | 9.9 | 1136.6 |  |
| 6 | GUJINJEC | 62.6 | -13.6 | 1.2 | 371.5 | 344.2 | 51.1 | 27.8 | 9.85 |  |
| 7 | TRIVENI | 57.1 | -8.5 | -9.3 | 5.9 | 11.8 | 40.8 | 24.2 | 227.52 |  |
| 8 | ZFCVINDIA | 57.1 | -8.1 | -14.1 | -0.7 | 9.2 | 26.0 | 20.6 | 2132.7 |  |
| 9 | AEGISVOPAK | 56.2 | -17.1 | 22.4 | -13.4 | 3.2 | 48.4 | 23.8 | 242.7 |  |
| 10 | GOLDIAM | 56.0 | -16.9 | 0.2 | 8.9 | 20.7 | 51.1 | 24.4 | 290.35 |  |
| 11 | SBIN | 54.8 | -5.6 | -13.8 | 6.0 | 8.2 | 22.0 | 21.9 | 958.6 |  |
| 12 | BRIGADE | 53.8 | 4.2 | -7.2 | -27.0 | -19.2 | 40.9 | 29.9 | 547.6 |  |
| 13 | INFY | 50.0 | 10.8 | -1.4 | -24.4 | -33.5 | 34.3 | 31.7 | 1153.8 |  |
| 14 | GUJTHEM | 45.5 | -10.1 | -9.6 | -28.4 | -9.3 | 51.6 | 31.0 | 324.0 |  |
| 15 | HDFCAMC | 40.5 | -10.2 | -18.4 | -18.8 | -14.1 | 30.4 | 21.4 | 2250.0 |  |
| 16 | MINOLTAF | 37.6 | 4.5 | -32.0 | -22.5 | -12.6 | 43.5 | 32.0 | 1.17 | unverified |
| 17 | KFINTECH | 34.8 | -6.8 | -16.8 | -30.5 | -21.9 | 36.1 | 32.0 | 799.0 |  |
| 18 | HDFCBANK | 33.6 | -6.7 | -12.3 | -30.4 | -26.7 | 22.1 | 31.4 | 692.8 |  |
| 19 | VBL | 28.8 | -13.6 | -23.9 | -14.4 | -6.5 | 28.1 | 27.4 | 395.1 |  |
| 20 | JIOFIN | 18.1 | -12.6 | -19.2 | -33.0 | -25.7 | 26.2 | 34.9 | 205.03 |  |
| 21 | TEAMLEASE | 10.2 | -19.6 | -15.5 | -38.9 | -31.0 | 24.5 | 39.1 | 1056.3 |  |


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
| JBCHEPHARM | 2025-06-16 | 2026-07-16 | 269 | 38.8 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-10-23 | 80 | -28.2 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
