# AI-Based Air Quality Prediction and Pollution Alert System

Streamlit dashboard for historical Indian city air-quality observations and a next-calendar-day AQI forecast from the saved XGBoost pipeline. The project uses its supplied historical dataset; readings and forecasts are not current or real-time.

## Data and forecast

- `dataset/city_day.csv` is the original model dataset, with 29,531 source rows from **2015-01-01 through 2020-07-01**. The loader keeps 24,850 valid city/date/AQI rows after validation and deduplication. The file includes AQI and pollutant measurements.
- `models/aqi_model.joblib`, `models/metadata.json`, and `models/metrics.csv` are the existing trained model, feature metadata, and evaluation results. The dashboard does not retrain the model.
- The feature pipeline builds city-scoped historical lags and rolling values and predicts AQI for the calendar day after the latest observation. It preserves missing dates and never treats a prominent-pollutant label as a concentration.
- CPCB integration code and separately stored recent observations are retained for reference, but the dashboard does not load, refresh, or require them. The AQI-only pipeline is not used by the app.

## Existing XGBoost evaluation

The selected model was chosen by validation MAE. Results below use the saved untouched chronological test set, covering **2019-09-04 through 2020-07-01**.

| Model/partition | MAE | RMSE | R² |
|---|---:|---:|---:|
| XGBoost validation | 28.90 | 63.51 | 0.838 |
| Selected XGBoost held-out test | 19.39 | 37.18 | 0.874 |
| Persistence held-out test | 23.10 | 48.57 | 0.785 |

These are historical split results, not a guarantee of future performance.

## Dashboard pages

- **Dashboard:** historical AQI summary, next-day forecast, city map, trend, comparisons, distributions, pollutant measurements, and recent rows.
- **AQI Prediction:** forecast origin and target dates with the observed history.
- **Pollution Analytics:** historical pollutant trends, distributions, correlations, and city comparisons.
- **Model Performance:** saved validation and held-out test metrics.
- **Pollution Alerts:** dated historical observations and model forecast guidance.
- **Explainable AI:** saved XGBoost feature importance.
- **About Project:** dataset and method summary.

## Setup and run

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Run the existing test suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

The saved model can be reproduced with `python -m src.train_model` when retraining is intended. It is not required to run the dashboard.
