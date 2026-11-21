# Momentum ranking (data up to 2026-11-20)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 88.1 | 6.6 | 58.6 | 37.5 | 31.3 | 42.6 | 10.3 | 1740.0 |  |
| 2 | MWL | 86.9 | 5.8 | 18.5 | 75.1 | 57.7 | 36.0 | 1.7 | 43.86 |  |
| 3 | SBIN | 86.0 | 11.1 | 20.2 | 19.8 | -0.3 | 19.9 | 5.1 | 1165.1 |  |
| 4 | ROLEXRINGS | 81.7 | 5.7 | 34.9 | 88.6 | 50.0 | 48.9 | 11.2 | 193.81 |  |
| 5 | KAJARIACER | 76.7 | -0.7 | 12.2 | 11.4 | 7.6 | 22.1 | 4.8 | 1200.5 |  |
| 6 | AEGISVOPAK | 75.5 | 5.1 | 39.7 | 11.3 | -2.8 | 49.9 | 8.8 | 290.33 |  |
| 7 | HDFCBANK | 59.5 | 16.4 | 7.5 | -15.2 | -30.5 | 23.4 | 16.2 | 846.0 |  |
| 8 | GUJINJEC | 56.9 | -3.5 | -2.5 | 287.2 | 262.7 | 52.2 | 23.4 | 10.45 |  |
| 9 | HDFCAMC | 56.2 | 3.3 | -2.2 | 0.0 | -15.7 | 31.0 | 5.8 | 2697.0 |  |
| 10 | KFINTECH | 50.0 | -4.6 | 12.7 | -12.2 | -20.9 | 34.8 | 15.1 | 934.9 |  |
| 11 | PFOCUS | 48.3 | -14.9 | 2.5 | 50.9 | 62.0 | 53.4 | 29.3 | 252.7 |  |
| 12 | BRIGADE | 46.2 | -9.5 | 15.2 | -14.2 | -17.3 | 40.1 | 18.8 | 578.35 |  |
| 13 | TRIVENI | 43.8 | -21.2 | 2.2 | 6.7 | 7.6 | 41.9 | 22.5 | 232.65 |  |
| 14 | VBL | 39.8 | -0.6 | -19.4 | -4.5 | -10.5 | 28.6 | 21.4 | 427.5 |  |
| 15 | GOLDIAM | 38.3 | -18.1 | -3.6 | 0.7 | 3.1 | 49.6 | 23.2 | 295.05 |  |
| 16 | MINOLTAF | 37.9 | 0.8 | -16.0 | -5.3 | -12.0 | 44.3 | 26.7 | 1.26 | unverified |
| 17 | GUJTHEM | 36.2 | -7.5 | -9.4 | -14.5 | -14.4 | 51.6 | 22.2 | 352.7 |  |
| 18 | ZFCVINDIA | 34.8 | -17.7 | -12.3 | 1.4 | -0.8 | 29.2 | 18.4 | 2191.8 |  |
| 19 | INFY | 29.8 | -2.1 | -6.0 | -28.9 | -25.3 | 34.1 | 35.0 | 1098.0 |  |
| 20 | JIOFIN | 21.7 | -7.8 | -6.9 | -25.9 | -30.6 | 26.1 | 27.0 | 224.97 |  |
| 21 | TEAMLEASE | 6.0 | -18.1 | -26.9 | -38.5 | -34.0 | 27.8 | 40.3 | 1019.4 |  |


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
| JBCHEPHARM | 2025-07-09 | 2026-07-16 | 252 | 47.5 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-11-20 | 100 | -24.2 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
