"""Inference utilities for next-calendar-day city AQI forecasts."""

import json
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
