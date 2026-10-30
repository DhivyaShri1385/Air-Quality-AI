# Runtime Validation Report

**Date:** 2026-10-30
**Environment:** Project `.venv`, Python 3.12.10.

## Stabilization

- Restored `app.py` to the last pre-recent-data dashboard implementation (`1974705`, after the calendar-day pipeline fix), then made historical-data labels explicit and removed the redundant standalone map page.
- Dashboard startup now reads only `dataset/city_day.csv` and the saved XGBoost artifacts. No CPCB or data.gov.in call is made. Recent-data code, files, tests, and artifacts were retained.
- The AQI-only model is not called or shown in the dashboard. The existing XGBoost model, metadata, metrics, and historical dataset were not retrained or modified.
- Backed up `app.py`, `README.md`, `requirements.txt`, and this report to `backups/pre-stabilization-20261030-221220/` before edits.

## Data and forecast check

- Source file: `dataset/city_day.csv` (29,531 source rows).
- Validated/cleaned records loaded: **24,850**.
- Date coverage: **2015-01-01 through 2020-07-01**.
- Saved estimator loaded: **XGBoost**, with 42 features.
- Verified Delhi forecast: origin **2020-07-01**, target **2020-07-02**, AQI **125.38**. It is labeled as historical and is not presented as current or real-time data.
- The dashboard uses only the original historical dataset. It does not present recent bulletin observations.

## Model results preserved

Saved chronological holdout target dates: **2019-09-04 through 2020-07-01**.

| Model/partition | MAE | RMSE | R² |
|---|---:|---:|---:|
| XGBoost validation | 28.8982 | 63.5062 | 0.8375 |
| Selected XGBoost held-out test | 19.3938 | 37.1834 | 0.8742 |
| Persistence held-out test | 23.1039 | 48.5682 | 0.7854 |

## Verification

| Check | Result |
|---|---|
| `python -m pytest -q` | Passed: **23 tests**. |
| Streamlit `AppTest`, all 7 pages | No page exceptions. A Windows temporary-directory `PermissionError` was printed during test harness shutdown after successful checks. |
| Streamlit server | Running at `http://127.0.0.1:18768`; `/_stcore/health` returned `ok`. |
| Model training | Not run; existing artifacts loaded and produced the expected next-calendar-day forecast. |

## Notes

The historical dataset ends in 2020. The model forecast is therefore also historical and should not be interpreted as a current AQI estimate. The recent-data parser and fetch code remain in the repository, but are not loaded by the dashboard. `pypdf` remains in requirements for the retained bulletin parser tests; the redundant direct `requests` pin was removed (Streamlit supplies it transitively).
