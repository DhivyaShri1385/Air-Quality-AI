# AI-Based Air Quality Prediction and Pollution Alert System

This Streamlit application explores the supplied Indian city-level air-quality observations and forecasts AQI for the next calendar day. It labels historical measurements and model forecasts separately. Forecasts are not live readings, official alerts, or guaranteed outcomes.

## Problem and workflow

Daily city observations are cleaned and deduplicated by city/date. The feature pipeline creates current readings, city-scoped lags, trailing means, and calendar fields using data available on or before the forecast origin. A supervised target is created only when the same city has a valid AQI record on exactly the following calendar day. Missing target dates are omitted from supervised training and do not prevent inference for the latest observed date.

The system splits examples by distinct target dates into chronological train, validation, and test partitions. It compares a persistence baseline, Linear Regression, Random Forest, and XGBoost when installed; chooses by validation MAE; refits the selected estimator with train plus validation data; then evaluates once on the held-out test partition. Median imputation is fitted inside each model pipeline using training data and is reused for later partitions and inference.

## Data files

- `dataset/city_day.csv`: city/date AQI and pollutant readings used for modeling.
- `dataset/city_hour.csv`: supplied hourly city data; not used by the daily forecasting model.
- `dataset/station_day.csv` and `dataset/station_hour.csv`: supplied station-level observations; not used by this city-level model.
- `dataset/stations.csv`: station metadata. It has no latitude/longitude columns, so station-level plotting is unavailable; the dashboard uses separately sourced city reference coordinates for its city-level map.
- `dataset/city_coordinates.csv`: state-matched GeoNames reference points for the 26 city labels in `city_day.csv`. These are city reference locations, not monitoring-station coordinates. See `dataset/CITY_COORDINATES_SOURCES.md` for matching rules, source IDs, retrieval date, and attribution; the original India gazetteer and state-code lookup are retained alongside it.

The supplied city dataset has 29,531 rows before cleaning. Meteorological variables are not confirmed in the data and are not used. The map uses attributed GeoNames city reference points with historical AQI readings; it is not a station map or live map.

## Features

- Environmental overview with latest observed AQI, date, coverage, pollutant summary, history, and a separately labeled next-day forecast.
- Next-calendar-day forecast, origin and target dates, model name, predicted CPCB category, persistence comparison, and feature-family descriptions.
- Historical AQI/pollutant trends, distributions, correlations, and city comparisons.
- India-centered, interactive city AQI map using state-checked GeoNames reference coordinates, plus a city-comparison fallback if coordinate records are unavailable.
- Validation comparison, held-out test metrics, actual-versus-predicted view, residuals, and global feature importance when supported by the selected model.
- General category-based precautions. These are informational and are not medical advice or official communications.

## Measured model results

Results from the current run use target dates **2019-09-04 through 2020-07-01** for the untouched test set. Model selection used validation MAE only.

| Model/partition | MAE | RMSE | R² |
|---|---:|---:|---:|
| Persistence, validation | 34.03 | 80.63 | 0.738 |
| Linear Regression, validation | 29.48 | 62.97 | 0.840 |
| Random Forest, validation | 29.10 | 64.32 | 0.833 |
| XGBoost, validation (selected) | 28.90 | 63.51 | 0.838 |
| Selected XGBoost, held-out test | 19.39 | 37.18 | 0.874 |
| Persistence, held-out test | 23.10 | 48.57 | 0.785 |

These metrics describe this dataset split and do not establish future performance. R² is not a guarantee of forecast accuracy. No prediction interval is currently implemented.

## Windows setup

From PowerShell in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The validated environment is Python 3.12.10 with the versions pinned in `requirements.txt`. Select `.venv\Scripts\python.exe` in VS Code.

## Train, test, launch

```powershell
.\.venv\Scripts\python.exe -m src.train_model
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the default Streamlit port is occupied, choose another one, for example:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 18765
```

The application will print its local URL. The trained estimator, metadata, and comparison metrics are saved under `models/`.

## Project structure

```text
app.py                         Streamlit dashboard
components/theme.py            Shared visual theme
dataset/                       Supplied air-quality CSV files
models/                        Trained model, metadata, and metrics
src/data_loader.py             Dataset validation and pollutant selection
src/preprocessing.py           Cleaning and date-based splitting
src/feature_engineering.py     Features and exact next-day targets
src/train_model.py             Model selection, evaluation, and saving
src/predict.py                 Forecast inference and artifact validation
src/evaluate_model.py          Regression metrics
src/aqi_classifier.py          Central AQI category mapping
src/alert_system.py            Category guidance
tests/                         Synthetic and saved-artifact tests
runtime-validation-report.md   Observed commands and validation results
```

## Troubleshooting

- **Missing or mismatched artifacts:** run `python -m src.train_model` from the project root using the selected virtual environment.
- **Unknown city or too little history:** choose a city with at least three valid daily AQI observations. Pollutant gaps are handled by the fitted imputation pipeline.
- **No map:** `stations.csv` does not contain latitude and longitude; no station coordinates are inferred.
- **XGBoost unavailable:** training can continue with the remaining estimators and reports whether XGBoost was available.
- **Port already in use:** pass `--server.port` with an available local port.

## Limitations and future scope

The forecast horizon is one calendar day, and a historical target is used only if the following day's AQI exists. This is a supervised city-level dataset, not a live monitoring feed. The project does not include confirmed meteorological fields, usable station coordinates, uncertainty intervals, or an external alert integration. Future work could add verified weather inputs, coordinate metadata, temporally calibrated intervals, and validated live sources.
