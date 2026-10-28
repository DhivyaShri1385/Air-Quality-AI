"""Inference utilities for the Streamlit dashboard."""

import json
from pathlib import Path

import joblib
import pandas as pd

from .data_loader import load_city_daily_data
from .feature_engineering import build_forecasting_frame

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


def load_artifacts() -> tuple[object, dict]:
    model_path = MODEL_DIR / "aqi_model.joblib"
    metadata_path = MODEL_DIR / "metadata.json"
    if not model_path.exists() or not metadata_path.exists():
        raise FileNotFoundError("Model artifacts are missing. Run `python -m src.train_model` first.")
    return joblib.load(model_path), json.loads(metadata_path.read_text(encoding="utf-8"))


def predict_next(city: str, raw_data: pd.DataFrame | None = None) -> dict:
    model, metadata = load_artifacts()
    raw = load_city_daily_data() if raw_data is None else raw_data
    frame, feature_names = build_forecasting_frame(raw)
    city_rows = frame[frame["City"] == city].sort_values("Date")
    if city_rows.empty:
        raise ValueError(f"No usable historical data is available for {city}.")
    latest = city_rows.iloc[[-1]]
    prediction = float(model.predict(latest[feature_names])[0])
    return {
        "city": city,
        "as_of": latest["Date"].iloc[0],
        "forecast_observation": latest["target_date"].iloc[0],
        "predicted_aqi": max(0.0, prediction),
        "model": metadata["best_model"],
    }
