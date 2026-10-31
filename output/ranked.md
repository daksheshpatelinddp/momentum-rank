# Momentum ranking (data up to 2026-10-30)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 95.2 | 21.7 | 46.5 | 25.4 | 27.1 | 41.9 | 11.7 | 1634.3 |  |
| 2 | GUJINJEC | 89.5 | 11.0 | 6.0 | 375.5 | 291.1 | 51.7 | 18.2 | 11.16 |  |
| 3 | ROLEXRINGS | 89.5 | 18.7 | 10.8 | 33.2 | 61.0 | 42.9 | 17.2 | 162.54 |  |
| 4 | MWL | 86.4 | 3.4 | 3.3 | 63.7 | 89.8 | 34.2 | 16.6 | 37.21 |  |
| 5 | PFOCUS | 68.1 | 0.3 | -5.3 | 58.4 | 65.8 | 53.5 | 19.4 | 288.1 |  |
| 6 | KAJARIACER | 65.5 | -7.4 | 0.4 | -8.1 | 1.4 | 24.2 | 12.0 | 1109.2 |  |
| 7 | TRIVENI | 58.3 | 1.7 | -10.9 | 4.6 | 7.3 | 41.2 | 24.9 | 225.29 |  |
| 8 | GUJTHEM | 55.0 | 1.4 | -2.4 | -21.9 | -17.9 | 52.5 | 21.9 | 363.2 |  |
| 9 | INFY | 53.3 | 4.9 | 1.4 | -20.1 | -30.2 | 34.8 | 29.9 | 1185.0 |  |
| 10 | SBIN | 53.3 | -6.4 | -10.0 | 2.7 | 1.8 | 21.9 | 21.7 | 961.85 |  |
| 11 | AEGISVOPAK | 52.1 | -23.9 | 13.9 | -20.8 | 4.2 | 48.6 | 30.6 | 220.95 |  |
| 12 | KFINTECH | 47.1 | -9.3 | -1.5 | -22.5 | -24.2 | 35.1 | 23.4 | 850.9 |  |
| 13 | GOLDIAM | 46.0 | -24.0 | -4.6 | 6.4 | 15.7 | 51.2 | 25.6 | 285.7 |  |
| 14 | ZFCVINDIA | 42.1 | -13.1 | -14.5 | 1.5 | 8.2 | 26.0 | 21.8 | 2101.5 |  |
| 15 | HDFCAMC | 40.5 | -11.7 | -16.1 | -14.1 | -14.2 | 30.1 | 19.3 | 2309.5 |  |
| 16 | MINOLTAF | 39.0 | 2.6 | -28.0 | -14.5 | -8.7 | 43.9 | 31.4 | 1.18 | unverified |
| 17 | HDFCBANK | 32.6 | -7.4 | -11.1 | -29.8 | -27.0 | 22.1 | 31.4 | 692.8 |  |
| 18 | BRIGADE | 32.4 | -9.2 | -11.2 | -32.3 | -26.8 | 40.8 | 32.5 | 527.1 |  |
| 19 | VBL | 28.1 | -11.4 | -22.6 | -16.5 | -9.4 | 28.6 | 27.9 | 392.0 |  |
| 20 | TEAMLEASE | 16.2 | -12.5 | -15.0 | -35.7 | -29.8 | 24.5 | 37.5 | 1080.4 |  |
| 21 | JIOFIN | 9.5 | -20.3 | -19.1 | -33.3 | -30.7 | 25.7 | 35.1 | 204.5 |  |


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
| JBCHEPHARM | 2025-06-18 | 2026-07-16 | 267 | 40.0 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-10-30 | 85 | -30.3 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
