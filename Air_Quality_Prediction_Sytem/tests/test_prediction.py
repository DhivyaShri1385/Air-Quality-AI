import pandas as pd
import pytest
from pathlib import Path

from src import predict
from src.feature_engineering import build_feature_frame
from src.predict import predict_next


class DummyModel:
    def __init__(self, value=42.0):
        self.value = value

    def predict(self, frame):
        self.seen = frame.copy()
        return [self.value]


def data(dates=None, city="A"):
    dates = dates or pd.date_range("2020-01-01", periods=3)
    return pd.DataFrame({"City": [city] * len(dates), "Date": dates, "AQI": [10 + i for i in range(len(dates))]})


def install_dummy(monkeypatch, frame, value=42.0):
    _, names = build_feature_frame(frame)
    model = DummyModel(value)
    monkeypatch.setattr(predict, "load_artifacts", lambda: (model, {"feature_names": names, "best_model": "Dummy"}))
    return model


def test_prediction_uses_latest_origin_without_future_label(monkeypatch):
    raw = data()
    model = install_dummy(monkeypatch, raw)
    result = predict_next("A", raw)
    assert result["forecast_origin_date"] == pd.Timestamp("2020-01-03")
    assert result["target_date"] == pd.Timestamp("2020-01-04")
    assert result["predicted_aqi"] == 42
    assert result["predicted_category"] == "Good"
    assert result["persistence_baseline"] == 12
    assert model.seen.iloc[0]["AQI"] == 12


def test_unknown_city_and_insufficient_history(monkeypatch):
    raw = data()
    install_dummy(monkeypatch, raw)
    with pytest.raises(ValueError, match="Unknown city"):
        predict_next("Missing", raw)
    one = raw.iloc[:1]
    install_dummy(monkeypatch, one)
    with pytest.raises(ValueError, match="at least 3"):
        predict_next("A", one)


def test_negative_model_output_is_clamped_and_classified(monkeypatch):
    raw = data()
    install_dummy(monkeypatch, raw, value=-5.0)
    result = predict_next("A", raw)
    assert result["predicted_aqi"] == 0
    assert result["predicted_category"] == "Good"


def test_missing_model_artifacts_error(monkeypatch):
    monkeypatch.setattr(predict, "MODEL_DIR", Path("models") / "nonexistent-test-dir")
    with pytest.raises(FileNotFoundError, match="Run `python -m src.train_model`"):
        predict.load_artifacts()


def test_prediction_pipeline_with_saved_artifacts():
    from src.data_loader import load_city_daily_data

    raw = load_city_daily_data()
    result = predict_next("Delhi", raw)
    assert result["city"] == "Delhi"
    assert result["predicted_aqi"] >= 0
    assert result["target_date"] == result["forecast_origin_date"] + pd.Timedelta(days=1)
