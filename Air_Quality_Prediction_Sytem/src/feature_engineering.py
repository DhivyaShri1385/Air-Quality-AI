"""Leakage-safe next-observation AQI feature construction."""

import pandas as pd

from .data_loader import pollutant_columns
from .preprocessing import clean_daily_data

TARGET = "target_aqi"
BASE_FEATURES = ["AQI"] 


def build_forecasting_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Create features at time t and target AQI at the next available city row."""
    data = clean_daily_data(frame)
    pollutants = pollutant_columns(data)
    data = data.sort_values(["City", "Date"]).copy()
    feature_columns = list(BASE_FEATURES)
    for column in pollutants:
        data[f"{column}_current"] = data[column]
        data[f"{column}_lag1"] = data.groupby("City")[column].shift(1)
        data[f"{column}_rolling3"] = data.groupby("City")[column].transform(
            lambda series: series.shift(1).rolling(3, min_periods=1).mean()
        )
        feature_columns.extend(
            [f"{column}_current", f"{column}_lag1", f"{column}_rolling3"]
        )
    data["aqi_lag1"] = data.groupby("City")["AQI"].shift(1)
    data["aqi_rolling3"] = data.groupby("City")["AQI"].transform(
        lambda series: series.shift(1).rolling(3, min_periods=1).mean()
    )
    data["day_of_week"] = data["Date"].dt.dayofweek
    data["month"] = data["Date"].dt.month
    data["day_of_year"] = data["Date"].dt.dayofyear
    data["target_aqi"] = data.groupby("City")["AQI"].shift(-1)
    data["target_date"] = data.groupby("City")["Date"].shift(-1)
    feature_columns.extend(["aqi_lag1", "aqi_rolling3", "day_of_week", "month", "day_of_year"])
    result = data.dropna(subset=[TARGET]).copy()
    result = result[["City", "Date", "target_date", "target_aqi", *feature_columns]]
    return result, feature_columns
