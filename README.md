# India Live Rainfall Monitor

A Streamlit dashboard combining:
1. Historical analysis of the supplied `precipitation-ind-csv-1.csv`.
2. Manually refreshed, model-based current weather and precipitation for representative city locations across India using the Open-Meteo Forecast API.

## Files
- `app.py`
- `requirements.txt`
- `precipitation-ind-csv-1.csv`

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud
1. Upload `app.py`, `requirements.txt`, and `precipitation-ind-csv-1.csv` to the root of your GitHub repository.
2. On Streamlit Community Cloud choose **Deploy a public app from GitHub**.
3. Repository: your GitHub repository URL.
4. Branch: `main` (or the actual default branch shown by GitHub).
5. Main file path: `app.py`.
6. Deploy.

## Important interpretation
The live panel queries Open-Meteo for 28 representative city coordinates. It is not a full India gridded rainfall map, radar feed, or official IMD gauge network. Current weather and forecasts are model estimates. The historical CSV has 32,000 rows, 76 station IDs, and 18 monthly dates from January 2010 to June 2011. Its supplied columns do not identify the measurement unit; values are therefore labelled as source values and station sums are not described as national-area rainfall.
