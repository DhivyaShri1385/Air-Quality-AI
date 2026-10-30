"""Leakage-safe next-calendar-day AQI feature construction."""

import pandas as pd

from .data_loader import pollutant_columns
from .preprocessing import clean_daily_data

TARGET = "target_aqi"
BASE_FEATURES = ["AQI"]
MIN_HISTORY = 3


def build_feature_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Create one row per observed city/date, including rows with no future target."""
    data = clean_daily_data(frame).sort_values(["City", "Date"]).copy()
    pollutants = pollutant_columns(data)
    feature_columns = list(BASE_FEATURES)
    for column in pollutants:
        data[f"{column}_current"] = data[column]
        data[f"{column}_lag1"] = data.groupby("City", sort=False)[column].shift(1)
        data[f"{column}_rolling3"] = data.groupby("City", sort=False)[column].transform(
            lambda values: values.shift(1).rolling(3, min_periods=1).mean()
        )
        feature_columns.extend([f"{column}_current", f"{column}_lag1", f"{column}_rolling3"])
    grouped_aqi = data.groupby("City", sort=False)["AQI"]
    data["aqi_lag1"] = grouped_aqi.shift(1)
    data["aqi_rolling3"] = grouped_aqi.transform(lambda values: values.shift(1).rolling(3, min_periods=1).mean())
    data["day_of_week"] = data["Date"].dt.dayofweek
    data["month"] = data["Date"].dt.month
    data["day_of_year"] = data["Date"].dt.dayofyear
    data["history_count"] = data.groupby("City", sort=False).cumcount() + 1
    feature_columns.extend(["aqi_lag1", "aqi_rolling3", "day_of_week", "month", "day_of_year"])
    return data[["City", "Date", "history_count", *feature_columns]].copy(), feature_columns


def build_forecasting_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Build supervised examples only when that city's next calendar day is observed."""
    features, feature_columns = build_feature_frame(frame)
    targets = clean_daily_data(frame)[["City", "Date", "AQI"]].rename(
        columns={"Date": "target_date", "AQI": TARGET}
    )
    features["target_date"] = features["Date"] + pd.Timedelta(days=1)
    result = features.merge(targets, on=["City", "target_date"], how="inner", validate="many_to_one")
    return result[["City", "Date", "target_date", "history_count", TARGET, *feature_columns]], feature_columns
