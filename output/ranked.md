# Momentum ranking (data up to 2026-10-16)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 94.0 | 25.6 | 45.8 | 31.8 | 37.2 | 40.9 | 8.5 | 1693.5 |  |
| 2 | MWL | 93.3 | 7.1 | 43.3 | 65.1 | 66.7 | 35.4 | 10.8 | 39.79 |  |
| 3 | ROLEXRINGS | 86.9 | 9.7 | 24.1 | 37.3 | 34.7 | 47.7 | 11.8 | 173.14 |  |
| 4 | AEGISVOPAK | 77.9 | 1.8 | 40.0 | -1.3 | 11.1 | 47.5 | 13.3 | 276.0 |  |
| 5 | PFOCUS | 67.4 | 0.3 | -11.4 | 73.2 | 99.8 | 53.0 | 18.8 | 290.3 |  |
| 6 | KAJARIACER | 64.8 | -2.3 | 2.0 | -2.6 | -2.1 | 24.1 | 4.0 | 1211.0 |  |
| 7 | GUJTHEM | 63.3 | 1.0 | 12.1 | -13.5 | -2.6 | 52.3 | 20.5 | 373.4 |  |
| 8 | GOLDIAM | 63.1 | -7.3 | 4.9 | 19.3 | 21.2 | 50.7 | 16.6 | 320.35 |  |
| 9 | TRIVENI | 53.6 | -12.1 | 5.6 | 16.9 | 8.5 | 40.6 | 16.6 | 250.35 |  |
| 10 | GUJINJEC | 52.9 | -22.8 | 7.8 | 379.7 | 361.6 | 50.3 | 28.1 | 9.81 |  |
| 11 | BRIGADE | 50.0 | 1.5 | -1.1 | -21.8 | -15.6 | 40.8 | 26.4 | 575.15 |  |
| 12 | VBL | 43.8 | -7.1 | -7.7 | -6.7 | -10.0 | 28.4 | 20.9 | 430.5 |  |
| 13 | KFINTECH | 42.1 | -0.1 | -9.0 | -21.1 | -20.2 | 35.3 | 24.5 | 887.0 |  |
| 14 | MINOLTAF | 41.4 | 2.5 | -17.9 | -17.3 | -8.0 | 42.9 | 27.9 | 1.24 | unverified |
| 15 | ZFCVINDIA | 39.3 | -10.5 | -13.9 | -0.5 | 12.8 | 26.4 | 19.7 | 2157.0 |  |
| 16 | INFY | 39.3 | 5.9 | -11.5 | -19.4 | -26.5 | 35.5 | 31.3 | 1161.2 |  |
| 17 | SBIN | 36.2 | -7.8 | -13.1 | 8.3 | 11.2 | 22.1 | 21.6 | 962.6 |  |
| 18 | HDFCAMC | 35.0 | -9.5 | -13.4 | -16.1 | -16.4 | 30.2 | 16.2 | 2398.6 |  |
| 19 | JIOFIN | 22.6 | -11.0 | -8.8 | -30.1 | -25.9 | 27.0 | 31.3 | 216.25 |  |
| 20 | HDFCBANK | 21.4 | -11.1 | -8.4 | -27.3 | -28.9 | 22.1 | 27.8 | 728.85 |  |
| 21 | TEAMLEASE | 11.7 | -19.8 | -9.3 | -35.1 | -30.5 | 24.0 | 35.1 | 1145.4 |  |


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
| GUJENERGY | 2026-07-01 | 2026-10-16 | 76 | -25.4 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
