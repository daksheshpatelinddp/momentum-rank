# Momentum ranking (data up to 2026-11-13)

Ranked **21** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 95.2 | 21.0 | 75.5 | 49.3 | 31.8 | 41.1 | 0.0 | 1939.9 |  |
| 2 | ROLEXRINGS | 92.9 | 21.0 | 49.1 | 92.9 | 51.8 | 48.7 | 2.2 | 213.34 |  |
| 3 | AEGISVOPAK | 77.9 | 6.3 | 44.9 | 5.6 | 4.1 | 49.8 | 10.2 | 285.93 |  |
| 4 | SBIN | 69.8 | 1.2 | 15.0 | 11.6 | -0.8 | 19.7 | 12.0 | 1080.0 |  |
| 5 | KAJARIACER | 68.6 | -4.1 | 14.7 | 6.9 | 8.1 | 21.9 | 4.7 | 1201.9 |  |
| 6 | MWL | 65.5 | -4.0 | 8.3 | 84.9 | 89.4 | 35.7 | 11.2 | 39.62 |  |
| 7 | PFOCUS | 62.9 | 0.1 | 14.7 | 56.3 | 60.7 | 53.8 | 24.5 | 269.95 |  |
| 8 | KFINTECH | 60.2 | 1.2 | 16.9 | -12.3 | -17.5 | 34.4 | 13.7 | 950.9 |  |
| 9 | TRIVENI | 59.3 | -5.6 | 13.1 | 14.3 | 12.3 | 41.5 | 16.1 | 251.6 |  |
| 10 | HDFCAMC | 58.3 | 7.2 | 1.4 | -1.6 | -10.8 | 31.2 | 7.0 | 2663.0 |  |
| 11 | GUJTHEM | 56.7 | 11.4 | 11.9 | -13.0 | -17.2 | 51.0 | 14.3 | 388.65 |  |
| 12 | GOLDIAM | 49.5 | -14.3 | 12.9 | 10.0 | 8.7 | 49.6 | 18.4 | 313.3 |  |
| 13 | HDFCBANK | 46.4 | 10.6 | 4.6 | -18.8 | -26.6 | 22.9 | 20.4 | 804.0 |  |
| 14 | GUJINJEC | 44.0 | -15.2 | 2.2 | 312.7 | 268.8 | 52.2 | 21.4 | 10.73 |  |
| 15 | ZFCVINDIA | 38.1 | -11.5 | -2.5 | 10.3 | 2.1 | 28.1 | 13.2 | 2332.4 |  |
| 16 | BRIGADE | 36.0 | -7.2 | 10.4 | -22.5 | -17.9 | 40.3 | 22.9 | 549.15 |  |
| 17 | VBL | 35.5 | -0.5 | -15.4 | -5.8 | -6.6 | 29.0 | 20.4 | 432.8 |  |
| 18 | MINOLTAF | 32.1 | -0.8 | -18.7 | -0.8 | -3.3 | 44.4 | 29.1 | 1.22 | unverified |
| 19 | INFY | 27.1 | -2.4 | -0.1 | -24.0 | -26.1 | 34.7 | 32.4 | 1141.5 |  |
| 20 | JIOFIN | 19.3 | -8.7 | -2.2 | -27.8 | -30.5 | 25.9 | 27.8 | 227.5 |  |
| 21 | TEAMLEASE | 4.8 | -20.0 | -25.3 | -41.3 | -34.4 | 26.3 | 41.3 | 1003.8 |  |


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
- NSE announcements: not usable - JSONDecodeError: Expecting value: line 2 column 1 (char 1).
- BSE announcements: not usable - ConnectionError: HTTP 403.
- Yahoo Finance (bonus/split only): checked 20 of 24 stocks; no Yahoo data for GUJINJEC, INRADIA, JBCHEPHARM, MINOLTAF.


## Corporate-action adjustments applied

| symbol | ex-date | factor | source | announcement / note |
|---|---|---|---|---|
| HDFCBANK | 2025-08-26 | 0.5 | manual | 1:1 bonus |
| ROLEXRINGS | 2025-10-17 | 0.1 | yahoo |  |
| HDFCAMC | 2025-11-26 | 0.5 | yahoo |  |
| BRIGADE | 2026-06-17 | 0.75 | manual | 1:3 bonus |
| ZFCVINDIA | 2026-06-24 | 0.1667 | yahoo |  |
| GUJINJEC | 2026-07-08 | 0.1 | manual | 10:1 split |
| GOLDIAM | 2026-07-10 | 0.75 | manual | 1:3 bonus |
| MWL | 2026-07-10 | 0.1 | yahoo |  |
| TRIVENI | 2026-07-22 | 0.603 | manual | spin-off (checked against Screener returns) |


**Not found in NSE or BSE data** (typo, renamed, SME or not listed): MRSS, 539229, KEDIACN, 508993


## Not ranked (not enough usable price history)

| symbol | first trade | last trade | trading days | return over that period % | why not ranked |
|---|---|---|---|---|---|
| INRADIA | 2025-08-06 | 2026-07-20 | 10 | 40.4 | stopped trading or very thin (last trade 2026-07-20) |
| JBCHEPHARM | 2025-07-02 | 2026-07-16 | 257 | 46.8 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-11-13 | 95 | -31.8 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
