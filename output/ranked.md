# Momentum ranking (data up to 2026-09-25)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MWL | 92.1 | 16.1 | 69.8 | 90.1 | 76.6 | 34.7 | 3.5 | 43.07 |  |
| 2 | PAYTM | 91.0 | 48.8 | 74.6 | 48.8 | 49.2 | 42.7 | 9.5 | 1674.0 |  |
| 3 | ROLEXRINGS | 88.8 | 31.9 | 76.0 | 47.2 | 35.9 | 47.5 | 0.0 | 195.35 |  |
| 4 | AEGISVOPAK | 77.6 | 23.3 | 77.9 | 18.1 | 8.2 | 50.2 | 9.7 | 287.5 |  |
| 5 | GUJTHEM | 70.5 | 6.0 | 83.8 | 4.3 | 3.1 | 55.5 | 11.3 | 417.0 |  |
| 6 | KAJARIACER | 70.5 | 1.8 | 32.4 | 3.0 | 1.5 | 28.7 | 3.4 | 1218.1 |  |
| 7 | PFOCUS | 66.2 | 50.3 | -4.2 | 72.0 | 61.2 | 51.8 | 11.7 | 315.45 |  |
| 8 | GOLDIAM | 61.2 | -6.8 | 61.3 | 17.7 | 27.8 | 58.1 | 15.4 | 325.05 |  |
| 9 | TRIVENI | 60.2 | 0.2 | 8.2 | 21.5 | 38.5 | 39.3 | 17.5 | 247.55 |  |
| 10 | BRIGADE | 56.4 | 13.8 | 22.5 | -11.9 | -3.3 | 42.0 | 23.4 | 597.9 |  |
| 11 | ZFCVINDIA | 47.4 | -10.0 | 2.6 | 12.3 | 22.6 | 27.9 | 12.4 | 2354.2 |  |
| 12 | GUJINJEC | 46.2 | -23.1 | 20.8 | 371.1 | 506.7 | 51.3 | 30.8 | 9.45 |  |
| 13 | SBIN | 41.4 | -6.0 | 0.4 | 14.7 | 21.7 | 23.9 | 19.9 | 983.0 |  |
| 14 | VBL | 39.0 | -14.4 | 13.2 | -2.2 | -5.8 | 30.2 | 20.1 | 434.8 |  |
| 15 | HDFCAMC | 38.1 | -10.3 | 7.3 | -15.4 | -8.4 | 34.2 | 18.0 | 2378.0 |  |
| 16 | KFINTECH | 35.7 | 1.7 | 1.4 | -17.0 | -10.6 | 35.6 | 24.3 | 888.8 |  |
| 17 | JIOFIN | 30.5 | -5.2 | 1.3 | -23.3 | -19.5 | 28.8 | 27.9 | 227.0 |  |
| 18 | MINOLTAF | 27.1 | -9.6 | -12.6 | -1.5 | -4.5 | 42.5 | 23.3 | 1.32 | unverified |
| 19 | HDFCBANK | 22.6 | -7.6 | 0.6 | -22.2 | -24.8 | 24.0 | 27.1 | 735.6 |  |
| 20 | INFY | 19.0 | -3.9 | -20.0 | -31.0 | -23.3 | 34.2 | 40.8 | 1000.2 |  |
| 21 | TEAMLEASE | 18.3 | -19.1 | 3.9 | -34.5 | -30.1 | 22.0 | 34.8 | 1173.0 |  |


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
| GUJENERGY | 2026-07-01 | 2026-09-25 | 62 | -20.9 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
