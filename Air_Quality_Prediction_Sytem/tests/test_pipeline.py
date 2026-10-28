import pandas as pd

from src.feature_engineering import build_forecasting_frame
from src.preprocessing import chronological_split, clean_daily_data


def sample_data():
    return pd.DataFrame(
        {
            "City": ["A"] * 5,
            "Date": pd.date_range("2020-01-01", periods=5),
            "PM2.5": [10, 20, 30, 40, 50],
            "AQI": [20, 30, 40, 50, 60],
        }
    )


def test_cleaning_and_chronological_split():
    cleaned = clean_daily_data(sample_data())
    train, validation, test = chronological_split(cleaned, 0.6, 0.2)
    assert len(cleaned) == 5
    assert train["Date"].max() < validation["Date"].min()
    assert validation["Date"].max() < test["Date"].min()


def test_target_is_next_observation_and_no_future_feature():
    frame, features = build_forecasting_frame(sample_data())
    first = frame.iloc[0]
    assert first["target_aqi"] == 30
    assert first["target_date"] == pd.Timestamp("2020-01-02")
    assert "target_aqi" not in features
    assert "target_date" not in features
    assert first["PM2.5_current"] == 10
