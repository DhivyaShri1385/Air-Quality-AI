import pandas as pd
import pytest

from src.feature_engineering import build_feature_frame, build_forecasting_frame
from src.preprocessing import chronological_split, clean_daily_data, fill_feature_missing_values


def sample_data():
    dates = pd.date_range("2020-01-01", periods=6)
    return pd.DataFrame({"City": ["A"] * 6, "Date": dates, "PM2.5": [10, None, 30, 40, 50, 60], "AQI": [20, 30, 40, 50, 60, 70]})


def test_cleaning_date_parsing_duplicates_and_invalid_values():
    data = pd.DataFrame({"City": [" A ", "A", "A"], "Date": ["2020-01-01", "2020-01-01", "bad"], "AQI": [10, 15, 20], "PM2.5": [1, -2, 3]})
    cleaned = clean_daily_data(data)
    assert len(cleaned) == 1
    assert cleaned.iloc[0]["City"] == "A"
    assert cleaned.iloc[0]["AQI"] == 15
    assert pd.isna(cleaned.iloc[0]["PM2.5"])


def test_fill_is_causal_and_city_scoped():
    frame = pd.DataFrame({"City": ["A", "A", "B"], "x": [None, 2.0, 9.0]})
    filled = fill_feature_missing_values(frame, ["x"])
    assert pd.isna(filled.loc[0, "x"])
    assert filled.loc[2, "x"] == 9.0


def test_chronological_split_keeps_whole_dates_together():
    frame = pd.DataFrame({"City": ["A", "B"] * 6, "Date": list(pd.date_range("2020-01-01", periods=6).repeat(2))})
    train, validation, test = chronological_split(frame, 0.5, 0.25)
    groups = [set(part["Date"]) for part in (train, validation, test)]
    assert not groups[0] & groups[1] and not groups[1] & groups[2]
    assert all(len(part.groupby("Date")) == len(part["Date"].unique()) for part in (train, validation, test))


def test_target_requires_exact_next_calendar_day():
    frame = pd.DataFrame({"City": ["A", "A", "A"], "Date": pd.to_datetime(["2020-01-01", "2020-01-03", "2020-01-04"]), "AQI": [10, 30, 40]})
    supervised, _ = build_forecasting_frame(frame)
    assert supervised["Date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-01-03"]
    assert supervised["target_date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-01-04"]
    assert supervised.iloc[0]["target_aqi"] == 40


def test_feature_frame_retains_latest_without_future_label_and_no_city_leakage():
    frame = pd.DataFrame({"City": ["A", "A", "A", "B", "B", "B"], "Date": list(pd.date_range("2020-01-01", periods=3)) * 2, "AQI": [10, 20, 30, 100, 110, 120], "PM2.5": [1, 2, 3, 20, 21, 22]})
    feature_frame, _ = build_feature_frame(frame)
    last_a = feature_frame[feature_frame["City"] == "A"].iloc[-1]
    assert last_a["Date"] == pd.Timestamp("2020-01-03")
    assert last_a["aqi_lag1"] == 20
    assert last_a["PM2.5_lag1"] == 2
    assert "target_aqi" not in feature_frame


def test_empty_or_small_date_splits_fail_clearly():
    with pytest.raises(ValueError, match="three distinct dates"):
        chronological_split(pd.DataFrame({"Date": [pd.Timestamp("2020-01-01")] * 2, "City": ["A", "B"]}))
