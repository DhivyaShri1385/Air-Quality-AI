"""Leakage-safe next-calendar-day AQI feature construction."""

import pandas as pd

from .data_loader import pollutant_columns
from .preprocessing import clean_daily_data

TARGET = "target_aqi"
BASE_FEATURES = ["AQI"]
MIN_HISTORY = 3


def build_feature_frame(frame: pd.DataFrame, include_pollutants: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Create one row per observed city/date, including rows with no future target."""
    data = clean_daily_data(frame).sort_values(["City", "Date"]).copy()
    if not include_pollutants:
        return _build_aqi_only_feature_frame(data)
    pollutants = pollutant_columns(data) if include_pollutants else []
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


def _build_aqi_only_feature_frame(data: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Compute AQI lags against calendar days, leaving missing days missing."""
    feature_columns = ["AQI", "aqi_lag1", "aqi_rolling3", "day_of_week", "month", "day_of_year"]
    city_frames = []
    for city, observations in data.groupby("City", sort=False):
        observations = observations[["Date", "AQI"]].sort_values("Date")
        calendar = pd.DataFrame({"Date": pd.date_range(observations["Date"].min(), observations["Date"].max(), freq="D")})
        calendar = calendar.merge(observations, on="Date", how="left", validate="one_to_one")
        calendar.insert(0, "City", city)
        previous = calendar.groupby("City", sort=False)["AQI"]
        calendar["aqi_lag1"] = previous.shift(1)
        calendar["aqi_rolling3"] = previous.transform(lambda values: values.shift(1).rolling(3, min_periods=1).mean())
        calendar["day_of_week"] = calendar["Date"].dt.dayofweek
        calendar["month"] = calendar["Date"].dt.month
        calendar["day_of_year"] = calendar["Date"].dt.dayofyear
        calendar["history_count"] = calendar.groupby("City", sort=False)["AQI"].transform(lambda values: values.notna().cumsum())
        city_frames.append(calendar[calendar["AQI"].notna()])
    result = pd.concat(city_frames, ignore_index=True) if city_frames else pd.DataFrame()
    return result[["City", "Date", "history_count", *feature_columns]].copy(), feature_columns


def build_forecasting_frame(frame: pd.DataFrame, include_pollutants: bool = True) -> tuple[pd.DataFrame, list[str]]:
    """Build supervised examples only when that city's next calendar day is observed."""
    features, feature_columns = build_feature_frame(frame, include_pollutants=include_pollutants)
    targets = clean_daily_data(frame)[["City", "Date", "AQI"]].rename(
        columns={"Date": "target_date", "AQI": TARGET}
    )
    features["target_date"] = features["Date"] + pd.Timedelta(days=1)
    result = features.merge(targets, on=["City", "target_date"], how="inner", validate="many_to_one")
    return result[["City", "Date", "target_date", "history_count", TARGET, *feature_columns]], feature_columns


def build_aqi_only_forecasting_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Build next-day examples using only city/date/AQI data.

    This schema is suitable for CPCB city AQI bulletins. Prominent-pollutant
    labels are not numerical measurements and never enter this feature set.
    """
    required = {"City", "Date", "AQI"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"AQI-only data is missing required columns: {sorted(missing)}")
    return build_forecasting_frame(frame[["City", "Date", "AQI"]], include_pollutants=False)
