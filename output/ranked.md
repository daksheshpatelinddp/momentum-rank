# Momentum ranking (data up to 2026-10-01)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MWL | 93.3 | 14.7 | 65.1 | 82.7 | 65.6 | 34.3 | 3.4 | 43.13 |  |
| 2 | ROLEXRINGS | 91.0 | 38.3 | 63.8 | 51.3 | 34.7 | 46.7 | 0.0 | 196.36 |  |
| 3 | PAYTM | 90.0 | 35.6 | 60.9 | 41.8 | 40.2 | 41.9 | 10.5 | 1656.0 |  |
| 4 | AEGISVOPAK | 75.2 | 12.9 | 70.9 | 2.6 | 1.2 | 49.4 | 8.7 | 290.75 |  |
| 5 | KAJARIACER | 74.3 | 1.9 | 23.8 | 1.6 | 4.5 | 26.6 | 2.9 | 1225.1 |  |
| 6 | PFOCUS | 70.5 | 27.8 | -13.7 | 70.9 | 65.3 | 51.9 | 15.6 | 301.55 |  |
| 7 | GUJTHEM | 62.4 | -1.1 | 46.2 | -9.7 | 0.5 | 53.0 | 18.7 | 381.8 |  |
| 8 | BRIGADE | 60.0 | 10.8 | 9.9 | -15.3 | 5.9 | 41.2 | 27.1 | 569.55 |  |
| 9 | GOLDIAM | 58.8 | -13.7 | 37.7 | 6.3 | 16.5 | 57.0 | 19.1 | 310.8 |  |
| 10 | ZFCVINDIA | 55.7 | -7.3 | -2.2 | -0.9 | 11.6 | 27.7 | 16.6 | 2241.0 |  |
| 11 | TRIVENI | 49.0 | -16.5 | -2.4 | 9.5 | 33.0 | 38.9 | 23.0 | 230.92 |  |
| 12 | GUJINJEC | 46.2 | -29.9 | 9.1 | 358.8 | 428.7 | 50.6 | 32.7 | 9.18 |  |
| 13 | SBIN | 43.6 | -8.3 | -7.6 | 10.0 | 18.0 | 22.7 | 22.3 | 954.1 |  |
| 14 | VBL | 41.0 | -17.5 | 6.1 | -4.1 | -8.2 | 29.5 | 21.8 | 425.3 |  |
| 15 | KFINTECH | 33.6 | -5.5 | -9.5 | -22.0 | -13.1 | 35.5 | 29.2 | 832.0 |  |
| 16 | HDFCAMC | 32.4 | -17.6 | -3.3 | -17.4 | -10.2 | 33.5 | 20.5 | 2308.1 |  |
| 17 | MINOLTAF | 30.0 | -17.1 | -13.7 | -11.3 | 2.1 | 42.8 | 26.7 | 1.26 | unverified |
| 18 | HDFCBANK | 26.0 | -10.0 | -6.5 | -25.3 | -26.8 | 23.8 | 28.6 | 721.2 |  |
| 19 | TEAMLEASE | 24.8 | -17.0 | -1.3 | -33.1 | -29.1 | 21.9 | 34.4 | 1179.4 |  |
| 20 | INFY | 21.4 | -1.2 | -20.8 | -28.5 | -21.9 | 34.4 | 38.8 | 1035.0 |  |
| 21 | JIOFIN | 21.0 | -11.2 | -9.7 | -29.6 | -21.3 | 28.3 | 32.5 | 212.5 |  |


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
| GUJENERGY | 2026-07-01 | 2026-10-01 | 66 | -22.9 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
