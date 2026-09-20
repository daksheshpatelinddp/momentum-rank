# Momentum ranking (data up to 2026-09-18)

Ranked **20** of 28 symbols. Score is 0-100 (percentile-based, relative to this list only).

- WARNING: corporate actions could not be checked for: ROLEXRINGS, MWL, MINOLTAF. A rights issue, demerger or bonus that is not in corporate_actions.csv would make their returns wrong.

| rank | symbol | score | ret_3m_% | ret_6m_% | ret_1y_% | ret_12m_ex1m_% | volatility_% | below_52w_high_% | close | flag |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | PAYTM | 94.2 | 69.8 | 78.7 | 57.1 | 38.6 | 43.4 | 0.0 | 1849.9 |  |
| 2 | MWL | 90.5 | 13.0 | 70.6 | 67.6 | 63.3 | 34.0 | 1.2 | 42.52 | unverified |
| 3 | AEGISVOPAK | 81.5 | 27.9 | 77.3 | 29.9 | 14.0 | 49.6 | 0.0 | 314.95 |  |
| 4 | ROLEXRINGS | 77.5 | 18.4 | 49.5 | 24.8 | 32.9 | 46.3 | 7.4 | 172.08 | unverified |
| 5 | PFOCUS | 76.8 | 53.4 | 11.5 | 87.1 | 61.4 | 52.7 | 1.5 | 344.35 |  |
| 6 | KAJARIACER | 69.0 | 3.2 | 33.2 | -0.2 | 0.3 | 29.4 | 4.7 | 1202.7 |  |
| 7 | GUJTHEM | 65.5 | 6.2 | 61.7 | 10.6 | -1.3 | 56.6 | 9.0 | 427.4 |  |
| 8 | GOLDIAM | 55.5 | -7.2 | 51.9 | 9.3 | 20.6 | 58.3 | 14.9 | 326.75 |  |
| 9 | BRIGADE | 54.8 | 16.1 | 28.4 | -11.6 | -9.1 | 42.6 | 20.4 | 621.7 |  |
| 10 | ZFCVINDIA | 52.0 | -8.2 | 8.6 | 8.2 | 20.6 | 28.5 | 11.1 | 2387.0 |  |
| 11 | GUJINJEC | 51.0 | -17.6 | 35.6 | 395.0 | 441.5 | 51.3 | 27.5 | 9.9 |  |
| 12 | TRIVENI | 49.0 | -5.7 | 6.9 | 10.0 | 36.0 | 43.3 | 20.4 | 238.8 |  |
| 13 | SBIN | 47.2 | -4.3 | -3.4 | 15.5 | 21.6 | 24.9 | 18.9 | 996.2 |  |
| 14 | MINOLTAF | 38.2 | -5.5 | -8.6 | 29.0 | 16.8 | 42.4 | 19.8 | 1.38 | unverified |
| 15 | HDFCAMC | 32.8 | -9.8 | 3.1 | -17.2 | -10.9 | 35.1 | 17.6 | 2425.0 |  |
| 16 | VBL | 29.8 | -17.7 | 8.7 | -11.1 | -9.3 | 31.1 | 22.4 | 421.95 |  |
| 17 | JIOFIN | 28.7 | -5.5 | -1.2 | -27.5 | -23.0 | 29.5 | 27.0 | 229.89 |  |
| 18 | INFY | 20.0 | -1.3 | -17.8 | -31.7 | -27.2 | 34.4 | 37.8 | 1051.4 |  |
| 19 | HDFCBANK | 20.0 | -7.0 | -4.4 | -24.4 | -24.8 | 25.1 | 27.6 | 731.0 |  |
| 20 | TEAMLEASE | 16.0 | -15.9 | 1.7 | -35.2 | -33.8 | 23.6 | 34.8 | 1219.0 |  |


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
- BSE announcements: VALIDATED - reproduced 5 of 5 known events, so it is used for every bonus, split, rights issue and demerger.
- Announced but NOT adjusted: ROLEXRINGS 2025-10-17 'Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per' (ratio not readable from the text). Add the exact factor to corporate_actions.csv.
- Announced but NOT adjusted: MWL 2026-07-10 'Face Value Split (Sub-Division) - From Rs 10/- Per Share To Re 1/- Per' (ratio not readable from the text). Add the exact factor to corporate_actions.csv.
- Announced but NOT adjusted: MINOLTAF 2026-07-17 'Right Issue of Equity Shares ' (ratio not readable from the text). Add the exact factor to corporate_actions.csv.


## Corporate-action adjustments applied

| symbol | ex-date | factor | source | announcement / note |
|---|---|---|---|---|
| HDFCBANK | 2025-08-26 | 0.5 | manual | 1:1 bonus |
| ROLEXRINGS | 2025-10-17 | 0.1 | bse-announcement | Stock  Split From Rs.10/- to Rs.1/- |
| HDFCAMC | 2025-11-26 | 0.5 | nse-announcement | Bonus 1:1 |
| BRIGADE | 2026-06-17 | 0.75 | manual | 1:3 bonus |
| ZFCVINDIA | 2026-06-24 | 0.1667 | nse-announcement | Bonus 5:1 |
| GUJINJEC | 2026-07-08 | 0.1 | manual | 10:1 split |
| GOLDIAM | 2026-07-10 | 0.75 | manual | 1:3 bonus |
| MWL | 2026-07-10 | 0.1 | bse-announcement | Stock  Split From Rs.10/- to Rs.1/- |
| TRIVENI | 2026-07-22 | 0.603 | manual | spin-off (checked against Screener returns) |


**Not found in NSE or BSE data** (typo, renamed, SME or not listed): KFINTEC, MRSS, 539229, KEDIACN, 508993


## Not ranked (not enough usable price history)

| symbol | first trade | last trade | trading days | return over that period % | why not ranked |
|---|---|---|---|---|---|
| INRADIA | 2025-08-06 | 2026-07-20 | 10 | 40.4 | stopped trading or very thin (last trade 2026-07-20) |
| JBCHEPHARM | 2025-06-16 | 2026-07-16 | 269 | 38.8 | stopped trading or very thin (last trade 2026-07-16) |
| GUJENERGY | 2026-07-01 | 2026-09-18 | 57 | -18.0 | listed less than a year ago |


*Research shortlist only, not investment advice. Returns look back 90 / 180 / 365 calendar days from today, like Screener, so small differences remain if another site used a different day. ret_12m_ex1m skips the latest month.*
