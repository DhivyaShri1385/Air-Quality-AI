"""Inference utilities for next-calendar-day city AQI forecasts."""

import json
from datetime import date
from pathlib import Path

import joblib
import pandas as pd

from .aqi_classifier import classify_aqi
from .data_loader import load_city_daily_data
from .feature_engineering import MIN_HISTORY, build_feature_frame

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


def load_artifacts() -> tuple[object, dict]:
    model_path, metadata_path = MODEL_DIR / "aqi_model.joblib", MODEL_DIR / "metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Model artifacts are missing. Run `python -m src.train_model` first.")
    try:
        model = joblib.load(model_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, EOFError) as exc:
        raise ValueError(f"Saved model artifacts could not be loaded: {exc}") from exc
    if not metadata.get("feature_names") or not metadata.get("best_model"):
        raise ValueError("Model metadata is incomplete; retrain with `python -m src.train_model`.")
    return model, metadata


def load_aqi_only_artifacts() -> tuple[object, dict]:
    """Load the separate model trained only on city/date/AQI history."""
    model_path = MODEL_DIR / "aqi_only_model.joblib"
    metadata_path = MODEL_DIR / "aqi_only_metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("AQI-only artifacts are missing. Run `python -m src.train_aqi_only_model`.")
    try:
        model = joblib.load(model_path)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, EOFError) as exc:
        raise ValueError(f"Saved AQI-only artifacts could not be loaded: {exc}") from exc
    names = metadata.get("feature_names", [])
    if metadata.get("model_type") != "AQI-only city-level regression" or not names:
        raise ValueError("AQI-only model metadata is incomplete or has the wrong model type.")
    if any("PM" in name or name.startswith(("NO", "CO", "SO", "O3", "NH3", "Benzene", "Toluene", "Xylene")) for name in names):
        raise ValueError("AQI-only model metadata unexpectedly includes pollutant features.")
    return model, metadata


def predict_next(city: str, raw_data: pd.DataFrame | None = None) -> dict:
    model, metadata = load_artifacts()
    raw = load_city_daily_data() if raw_data is None else raw_data
    if raw is None or raw.empty:
        raise ValueError("No air-quality observations are available to forecast from.")
    features, available_names = build_feature_frame(raw)
    requested = str(city).strip()
    city_rows = features[features["City"].astype(str).str.strip() == requested].sort_values("Date")
    if city_rows.empty:
        raise ValueError(f"Unknown city or no usable AQI observations: {requested}.")
    latest = city_rows.iloc[-1]
    if int(latest["history_count"]) < MIN_HISTORY:
        raise ValueError(f"{requested} has only {int(latest['history_count'])} usable daily observations; at least {MIN_HISTORY} are required for forecasting.")
    names = list(metadata["feature_names"])
    missing = [name for name in names if name not in available_names]
    if missing:
        raise ValueError(f"Current feature pipeline does not match the saved model; missing features: {missing}. Retrain the model.")
    row = latest[names].to_frame().T
    expected = getattr(model, "n_features_in_", None)
    if expected is not None and int(expected) != len(names):
        raise ValueError("Saved model feature count does not match metadata. Retrain the model.")
    model_names = getattr(model, "feature_names_in_", None)
    if model_names is not None and list(model_names) != names:
        raise ValueError("Saved model feature order does not match metadata. Retrain the model.")
    prediction = max(0.0, float(model.predict(row)[0]))
    origin = pd.Timestamp(latest["Date"])
    target_date = origin + pd.Timedelta(days=1)
    return {
        "city": requested, "forecast_origin_date": origin, "target_date": target_date,
        "as_of": origin, "forecast_observation": target_date,
        "predicted_aqi": prediction, "predicted_category": classify_aqi(prediction),
        "model": metadata["best_model"], "persistence_baseline": float(latest["AQI"]),
    }


def predict_aqi_only(city: str, recent_data: pd.DataFrame) -> dict:
    """Forecast tomorrow from three consecutive recent city AQI observations."""
    model, metadata = load_aqi_only_artifacts()
    if recent_data is None or recent_data.empty:
        raise ValueError("No recent CPCB city AQI observations are available.")
    required = {"City", "Date", "AQI"}
    missing = required.difference(recent_data.columns)
    if missing:
        raise ValueError(f"Recent AQI history is missing columns: {sorted(missing)}")
    raw = recent_data[["City", "Date", "AQI"]].copy()
    features, available_names = build_feature_frame(raw, include_pollutants=False)
    requested = str(city).strip()
    city_rows = features[features["City"].astype(str).str.strip().str.casefold() == requested.casefold()].sort_values("Date")
    if city_rows.empty:
        raise ValueError(f"No recent AQI observations are available for {requested}.")
    if len(city_rows) < MIN_HISTORY:
        raise ValueError(f"{requested} has {len(city_rows)} recent daily AQI observation(s); 3 consecutive days are required before forecasting.")
    last_three = city_rows.tail(MIN_HISTORY)
    expected_dates = pd.date_range(end=pd.Timestamp(last_three.iloc[-1]["Date"]), periods=MIN_HISTORY, freq="D")
    if not pd.DatetimeIndex(last_three["Date"]).equals(expected_dates):
        raise ValueError(f"{requested} does not have 3 consecutive recent AQI dates; forecast withheld.")
    observation_age = (date.today() - pd.Timestamp(last_three.iloc[-1]["Date"]).date()).days
    if observation_age < 0 or observation_age > 1:
        raise ValueError(f"The latest CPCB AQI observation is {observation_age} day(s) from the current date; refresh the source before forecasting.")
    names = list(metadata["feature_names"])
    missing_features = [name for name in names if name not in available_names]
    if missing_features:
        raise ValueError(f"AQI-only inference features do not match the saved model: {missing_features}.")
    latest = city_rows.iloc[-1]
    row = latest[names].to_frame().T
    expected_count = getattr(model, "n_features_in_", None)
    model_names = getattr(model, "feature_names_in_", None)
    if expected_count is not None and int(expected_count) != len(names):
        raise ValueError("AQI-only model feature count does not match saved metadata.")
    if model_names is not None and list(model_names) != names:
        raise ValueError("AQI-only model feature order does not match saved metadata.")
    prediction = max(0.0, float(model.predict(row)[0]))
    origin = pd.Timestamp(latest["Date"])
    return {
        "city": requested,
        "forecast_origin_date": origin,
        "target_date": origin + pd.Timedelta(days=1),
        "as_of": origin,
        "forecast_observation": origin + pd.Timedelta(days=1),
        "predicted_aqi": prediction,
        "predicted_category": classify_aqi(prediction),
        "model": metadata["best_model"],
        "persistence_baseline": float(latest["AQI"]),
        "model_type": metadata["model_type"],
        "training_data_end_date": metadata["training_data_date_range"][1],
    }
