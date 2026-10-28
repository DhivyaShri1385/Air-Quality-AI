# AI-Based Air Quality Prediction and Pollution Alert System

The project loads real Indian air-quality observations, trains three regression
models for next-observation daily AQI forecasting, classifies predictions using
CPCB categories, and presents analytics and alerts in Streamlit.

## Phase 1 decisions

### Python and package baseline

- **Python 3.12.x** is the recommended runtime. It is installed and available
  in this workspace as Python 3.12.10.
- The package versions in `requirements.txt` are pinned for repeatable
  installation on Windows 10/11.
- The application will use Streamlit, pandas, NumPy, scikit-learn, XGBoost,
  Plotly, Matplotlib, and joblib. No sensor or IoT hardware is required.

### Dataset

The supplied CSV files are the genuine **India Air Quality Data** dataset
(Kaggle/Indian government monitoring data lineage), provided as city-level and
station-level observations:

- `dataset/city_day.csv`: daily city observations with `City`, `Date`, pollutant
  measurements, `AQI`, and `AQI_Bucket`.
- `dataset/city_hour.csv`: hourly city observations with `City`, `Datetime`,
  pollutant measurements, `AQI`, and `AQI_Bucket`.
- `dataset/station_day.csv`: daily monitoring-station observations.
- `dataset/station_hour.csv`: hourly monitoring-station observations.
- `dataset/stations.csv`: station-to-city/state metadata.

The supplied files contain pollutant concentrations but do not contain
temperature, humidity, or wind speed. Those variables will not be fabricated or
used as model inputs. The initial implementation will use the available
pollutants and time-derived variables only.

The preferred first training source is `city_day.csv` because it provides a
consistent city/date grain and is suitable for a next-day forecast. The hourly
files remain available for a later next-hour mode if data sufficiency and
continuity checks pass.

### Forecasting contract

The first model will predict **the next available city's daily AQI**:

1. Sort observations by city and date.
2. Create lagged AQI and pollutant values plus trailing rolling statistics.
3. Shift the target so row `t` predicts AQI at the next available date after
   row `t`.
4. Build all lag and rolling features from observations at or before `t`.
5. Split chronologically into train, validation, and untouched test sets.

Current/future target AQI and future pollutant measurements will not be input
features. If a city has gaps, “next day” means the next available observation;
the UI will label this as a next-observation daily forecast rather than
claiming a real-time forecast.

AQI labels will use the CPCB categories:
Good (0–50), Satisfactory (51–100), Moderately Polluted (101–200), Poor
(201–300), Very Poor (301–400), and Severe (401–500). Values above 500 will be
reported as above the standard scale.

## Exact Windows PowerShell setup

Run these commands from the project directory:

```powershell
cd C:\Users\loges\Downloads\Air_Quality_Prediction_Sytem
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If PowerShell script activation is permitted, activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If activation is blocked by execution policy, continue to use the explicit
interpreter path:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

In VS Code, select `.venv\Scripts\python.exe` with **Python: Select
Interpreter**. The project dataset is already present under `dataset\`; do not
download or invent replacement measurements.

## Train the models

```powershell
.\.venv\Scripts\python.exe -m src.train_model
```

Training writes the selected model, metadata, validation metrics, and untouched
test-set predictions to `models\`.

## Run the application

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Open the displayed local URL, normally `http://localhost:8501`.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Dataset verification

Verify the environment and dataset headers:

```powershell
.\.venv\Scripts\python.exe --version
Get-ChildItem .\dataset\*.csv
Get-Content .\dataset\city_day.csv -TotalCount 2
```

The implemented pipeline uses `city_day.csv`, creates historical pollutant
lags and rolling statistics, uses chronological train/validation/test splits,
and does not use future target values as features.
