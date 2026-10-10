# Momentum ranking (data up to 2026-10-09)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MWL | 94.3 | 13.4 | 55.0 | 74.8 | 66.4 | 35.1 | 6.9 | 41.56 |  |
| 2 | PAYTM | 92.1 | 21.9 | 47.8 | 32.3 | 40.6 | 41.1 | 11.6 | 1636.0 |  |
| 3 | ROLEXRINGS | 86.0 | 19.9 | 29.6 | 26.4 | 29.4 | 47.5 | 13.9 | 169.14 |  |
| 4 | AEGISVOPAK | 79.8 | 0.6 | 51.4 | 2.9 | 5.5 | 47.9 | 10.5 | 284.8 |  |
| 5 | KAJARIACER | 71.2 | -0.2 | 8.2 | -2.1 | 0.2 | 24.6 | 3.7 | 1215.4 |  |
| 6 | GUJTHEM | 64.8 | -4.1 | 28.5 | -13.5 | 2.3 | 52.6 | 22.6 | 363.5 |  |
| 7 | GOLDIAM | 59.8 | -19.1 | 20.5 | 9.4 | 17.2 | 54.7 | 20.3 | 305.9 |  |
| 8 | PFOCUS | 59.5 | 1.7 | -22.6 | 55.3 | 86.4 | 51.5 | 27.0 | 261.1 |  |
| 9 | TRIVENI | 56.7 | -15.5 | 1.8 | 10.3 | 23.5 | 39.4 | 21.5 | 235.67 |  |
| 10 | VBL | 55.2 | -7.8 | 2.4 | -0.6 | -7.5 | 29.1 | 18.9 | 441.0 |  |
| 11 | GUJINJEC | 50.0 | -31.1 | 5.6 | 355.9 | 397.1 | 49.8 | 31.1 | 9.4 |  |
| 12 | SBIN | 46.4 | -7.4 | -9.8 | 8.9 | 14.7 | 22.0 | 21.9 | 959.1 |  |
| 13 | BRIGADE | 46.2 | -4.5 | -1.8 | -22.4 | -7.9 | 40.7 | 29.7 | 548.8 |  |
| 14 | ZFCVINDIA | 43.8 | -10.8 | -11.2 | -6.3 | 13.8 | 26.7 | 22.5 | 2082.2 |  |
| 15 | KFINTECH | 42.1 | -6.5 | -6.5 | -21.5 | -16.2 | 35.6 | 28.3 | 842.35 |  |
| 16 | HDFCAMC | 34.5 | -18.1 | -11.1 | -18.0 | -11.8 | 31.0 | 22.0 | 2262.5 |  |
| 17 | MINOLTAF | 33.1 | -20.0 | -13.7 | -11.1 | 2.2 | 42.4 | 30.2 | 1.2 | unverified |
| 18 | JIOFIN | 28.6 | -11.3 | -9.7 | -30.4 | -25.3 | 27.2 | 31.8 | 214.62 |  |
| 19 | INFY | 21.2 | -4.2 | -19.8 | -32.4 | -31.6 | 34.3 | 39.4 | 1023.4 |  |
| 20 | HDFCBANK | 20.5 | -14.3 | -11.0 | -27.9 | -29.3 | 22.3 | 29.9 | 707.25 |  |
| 21 | TEAMLEASE | 14.3 | -22.5 | -9.3 | -40.1 | -29.7 | 22.9 | 40.2 | 1068.0 |  |


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
| GUJENERGY | 2026-07-01 | 2026-10-09 | 71 | -25.1 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
