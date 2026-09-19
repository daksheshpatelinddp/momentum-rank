# momentum-rank

Ranks the stocks in `symbols.txt` (your Chartink results) by momentum, using official NSE
bhavcopy prices that are automatically adjusted for splits and bonuses.

## Files
| File | Purpose |
|---|---|
| `symbols.txt` | Your Chartink symbols, one per line (edit weekly) |
| `fetch_bhav.py` | Downloads NSE daily files into `data/` |
| `rank.py` | Adjusts prices and writes `ranked.csv` / `ranked.md` |
| `.github/workflows/rank.yml` | Runs both on a schedule or on demand |
| `data/` | Created automatically (one small file per trading day) |

## Weekly routine
1. Run your Chartink scan after Friday's close.
2. Edit `symbols.txt` on GitHub, paste the symbols, commit.
3. Actions tab -> "Momentum rank" -> Run workflow (or wait for Saturday 5 PM IST).
4. Open `ranked.md` (or the run's Summary page). Top rows = strongest momentum.

## Score
Percentile average of: 6-month return / volatility (30%), 12-1 month return (25%),
3-month return (25%), closeness to 52-week high (20%). Change `WEIGHTS` in `rank.py` to taste.

## If NSE blocks GitHub's servers
Run the same scripts on any computer with Python 3.9+:
`pip install -r requirements.txt && python fetch_bhav.py && python rank.py`
then commit the new `data/` files and `ranked.*` to the repo.

## Repair
Actions -> Run workflow -> tick "rebuild" to delete stored data and download everything again.
