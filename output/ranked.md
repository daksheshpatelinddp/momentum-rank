# Momentum ranking (data up to 2026-11-27)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 87.9 | 5.5 | 59.1 | 31.9 | 27.7 | 42.6 | 10.2 | 1741.9 |  |
| 2 | MWL | 83.8 | 9.8 | 15.3 | 74.9 | 53.0 | 36.3 | 2.7 | 43.41 |  |
| 3 | SBIN | 82.4 | 7.3 | 17.8 | 14.8 | -0.7 | 20.2 | 8.5 | 1123.9 |  |
| 4 | ROLEXRINGS | 78.6 | 4.6 | 37.2 | 85.2 | 65.7 | 48.9 | 13.4 | 188.9 |  |
| 5 | AEGISVOPAK | 73.8 | 5.4 | 47.5 | 9.2 | -9.3 | 49.7 | 10.6 | 284.47 |  |
| 6 | KAJARIACER | 70.0 | -0.8 | 9.4 | 12.9 | 3.3 | 22.2 | 4.4 | 1205.3 |  |
| 7 | HDFCBANK | 64.3 | 19.0 | 15.4 | -14.9 | -32.2 | 23.7 | 14.9 | 857.25 |  |
| 8 | HDFCAMC | 62.4 | 5.3 | 3.9 | 1.2 | -13.3 | 31.0 | 5.5 | 2706.0 |  |
| 9 | KFINTECH | 60.5 | 4.1 | 17.0 | -6.4 | -18.6 | 35.9 | 10.2 | 989.0 |  |
| 10 | GUJINJEC | 54.8 | -7.6 | -2.8 | 278.0 | 296.7 | 51.3 | 21.7 | 10.69 |  |
| 11 | BRIGADE | 54.0 | -3.8 | 24.8 | -8.0 | -20.8 | 41.1 | 13.3 | 617.85 |  |
| 12 | TRIVENI | 50.5 | -16.1 | 8.0 | 11.0 | 9.1 | 42.1 | 20.6 | 238.18 |  |
| 13 | PFOCUS | 41.2 | -19.3 | 4.1 | 40.0 | 72.4 | 53.9 | 33.5 | 237.65 |  |
| 14 | ZFCVINDIA | 39.0 | -14.8 | -8.5 | -0.6 | -4.4 | 29.6 | 18.6 | 2187.1 |  |
| 15 | GOLDIAM | 37.4 | -16.8 | -5.7 | -2.9 | -0.1 | 49.4 | 24.5 | 289.85 |  |
| 16 | VBL | 34.3 | 2.6 | -19.1 | -11.8 | -13.9 | 28.8 | 21.9 | 424.9 |  |
| 17 | MINOLTAF | 32.9 | -4.5 | -18.5 | 5.8 | -6.6 | 44.5 | 25.6 | 1.28 | unverified |
| 18 | INFY | 31.9 | 0.6 | -4.3 | -26.2 | -26.5 | 35.1 | 31.9 | 1151.3 |  |
| 19 | GUJTHEM | 30.2 | -15.9 | -13.3 | -15.2 | -7.8 | 42.8 | 23.8 | 345.6 |  |
| 20 | JIOFIN | 24.3 | -6.6 | -5.3 | -27.3 | -32.4 | 26.5 | 27.3 | 222.6 |  |
| 21 | TEAMLEASE | 6.0 | -18.5 | -24.9 | -37.1 | -36.9 | 28.0 | 38.6 | 1036.7 |  |


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
| JBCHEPHARM | 2025-07-16 | 2026-07-16 | 247 | 45.5 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-11-27 | 104 | -19.4 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
