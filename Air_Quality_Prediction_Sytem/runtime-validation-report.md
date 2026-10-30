# Runtime Validation Report

**Date:** 2026-10-30
**Environment:** Windows, project `.venv`, Python 3.12.10; NumPy 2.1.3, pandas 2.2.3, scikit-learn 1.6.1, XGBoost 2.1.4, Plotly 5.24.1, Matplotlib 3.10.0, joblib 1.4.2, Streamlit 1.41.1, pytest 8.3.4.

## Completed checklist

- [x] Inspected project, environment, dataset schemas, station metadata, tests, and existing artifacts.
- [x] Backed up source, tests, docs, components, and model artifacts to `backups/pre-audit-20261030-202042/` before edits.
- [x] Cleaned city/date/AQI and known pollutant fields; deduplicated city/date records; rejected invalid and negative AQI; avoided backward filling.
- [x] Split by distinct chronological target dates, keeping same-date cities together.
- [x] Built city-scoped features and an exact next-calendar-day target; feature generation retains latest rows without a future label.
- [x] Compared persistence, Linear Regression, Random Forest, and XGBoost; selected by validation MAE only and evaluated on held-out dates.
- [x] Saved a consistent fitted model pipeline, feature names, model configuration, metadata, and metrics.
- [x] Updated inference categories/dates, alerts, dashboard pages, README, and tests.
- [x] Verified dashboard page flows and an HTTP startup response.
- [x] Redesigned the dashboard UI with a compact sidebar, project header/city selector, four data-driven KPI cards, interactive map/trend, AQI distribution, pollutant panels, recent observations, and separate analytical pages.
- [x] Added city reference coordinates with GeoNames IDs and state matching; documented source/license and retained the source extract.

## Commands and outcomes

| Command/check | Result |
|---|---|
| `\.venv\Scripts\python.exe -m compileall src app.py components tests` | Passed. |
| `\.venv\Scripts\python.exe -m src.train_model` | Passed. Trained and saved XGBoost; XGBoost was available. |
| `\.venv\Scripts\python.exe -m pytest -q` | Passed: **14 tests**. |
| `\.venv\Scripts\python.exe -m pip check` | Passed: no broken requirements. |
| Streamlit `AppTest` on all 8 pages | Each page rendered without Streamlit exceptions. The harness emitted a temporary-directory cleanup `PermissionError` during interpreter shutdown despite exit code 0. |
| Coordinate validation | Passed: 26 unique dataset cities matched to GeoNames places and checked against station-metadata states; coordinate ranges fall within India. The coordinates identify city reference points, not monitoring stations. |
| `\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 18765` | Started; `urllib` request returned **HTTP 200**. Process was stopped after the check. |
| Streamlit ports 8502 and 8503 | Reported already in use; startup was verified on 18765 instead. |
| `python -m pip install -r requirements.txt` | Not run; the existing project virtual environment already had the pinned dependencies installed. |

## Model results

Validation target dates: **2018-11-07 to 2019-09-03**. The selected model was chosen only by validation MAE.

| Model/partition | MAE | RMSE | R² |
|---|---:|---:|---:|
| Persistence, validation | 34.0307 | 80.6282 | 0.7381 |
| Linear Regression, validation | 29.4777 | 62.9727 | 0.8402 |
| Random Forest, validation | 29.0985 | 64.3183 | 0.8333 |
| XGBoost, validation (selected) | 28.8982 | 63.5062 | 0.8375 |

Held-out test target dates: **2019-09-04 to 2020-07-01**.

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| Selected XGBoost | 19.3938 | 37.1834 | 0.8742 |
| Persistence baseline | 23.1039 | 48.5682 | 0.7854 |

No interval coverage is reported because a defensible temporal calibration interval has not been implemented.

## Dataset findings and limitations

- `city_day.csv` has 29,531 source rows and the expected daily AQI/pollutant columns.
- `stations.csv` contains `StationId`, `StationName`, `City`, `State`, and `Status`; it has no latitude/longitude fields. A station map is unavailable and the dashboard presents city-level comparisons.
- `city_coordinates.csv` stores city-level GeoNames coordinates, IDs, source URL, license, and retrieval date. Matches are state-checked against station metadata; `Brajrajnagar` is matched to the GeoNames spelling `Brajarajnagar`. GeoNames coordinates are not station coordinates.
- Weather variables, live government feeds, and official CPCB certification are not included or claimed.
- The training target exists only where AQI is recorded exactly one calendar day after the origin. Inference predicts one calendar day after the latest eligible observation, even when that future target is absent.
- Metrics reflect this dataset and split only; they are not a guarantee of future accuracy.

## Dashboard redesign validation

- The dashboard default route renders four values from the data/artifact: latest observed AQI, next-day forecast AQI, forecast change, and selected model.
- Date-window controls filter the observed trend while retaining a single point on the actual next-calendar-day target date.
- The India map is generated from the 26 attributed city reference coordinate rows and latest available city AQI; hover includes city, AQI category, and observation date.
- Model Performance, Pollution Analytics, Geospatial Analytics, Pollution Alerts, Explainable AI, and About Project all rendered in `AppTest` without exceptions.

## Start the dashboard

From the project directory:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

If the default port is unavailable, the verified alternative was:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.headless true --server.address 127.0.0.1 --server.port 18765
```
