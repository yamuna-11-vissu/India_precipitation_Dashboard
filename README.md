# India Precipitation Analysis Dashboard

Interactive Streamlit dashboard for the supplied Indian TPCP precipitation dataset.

## Files
- `app.py` — Streamlit dashboard
- `requirements.txt` — Python packages
- `precipitation-ind-csv-1.csv` — source dataset

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy
Push these files to a GitHub repository, then deploy `app.py` from Streamlit Community Cloud.

## Data note
The supplied CSV has monthly observation dates (18 unique dates, January 2010 to June 2011), 32,000 records, and 76 station IDs. The source columns do not state a measurement unit, so the dashboard labels values as dataset values and avoids claiming national-area rainfall totals.
