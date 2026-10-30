"""Cleaning and chronological data preparation."""

import pandas as pd

from .data_loader import pollutant_columns


def clean_daily_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize types, remove invalid target rows, and sort chronologically."""
    cleaned = frame.copy()
    if not {"City", "Date", "AQI"}.issubset(cleaned.columns):
        raise ValueError("Daily data must contain City, Date, and AQI columns.")
    cleaned["City"] = cleaned["City"].astype("string").str.strip()
    cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce").dt.normalize()
    cleaned["AQI"] = pd.to_numeric(cleaned["AQI"], errors="coerce")
    cleaned = cleaned.dropna(subset=["City", "Date", "AQI"])
    cleaned = cleaned[(cleaned["City"] != "") & (cleaned["AQI"] >= 0)]
    cleaned = cleaned.sort_values(["City", "Date"], kind="stable")
    cleaned = cleaned.drop_duplicates(subset=["City", "Date"], keep="last")
    for column in pollutant_columns(cleaned):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
        cleaned.loc[cleaned[column] < 0, column] = float("nan")
    return cleaned.sort_values(["City", "Date"]).reset_index(drop=True)


def fill_feature_missing_values(frame: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Causally forward-fill within city; learned median filling belongs in a fitted pipeline."""
    result = frame.copy()
    for column in feature_columns:
        if column not in result:
            result[column] = 0.0
        result[column] = pd.to_numeric(result[column], errors="coerce")
        result[column] = result.groupby("City", sort=False)[column].transform("ffill")
    return result


def chronological_split(
    frame: pd.DataFrame, train_fraction: float = 0.70, validation_fraction: float = 0.15
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split whole distinct dates chronologically so same-day cities never cross partitions."""
    if train_fraction <= 0 or validation_fraction <= 0 or train_fraction + validation_fraction >= 1:
        raise ValueError("Split fractions must be positive and leave a test portion.")
    date_column = "target_date" if "target_date" in frame.columns else "Date"
    ordered = frame.sort_values([date_column, "City"] if "City" in frame.columns else [date_column]).reset_index(drop=True)
    dates = pd.Index(ordered[date_column].dropna().drop_duplicates().sort_values())
    if len(dates) < 3:
        raise ValueError("At least three distinct dates are required for chronological train/validation/test splits.")
    train_end = max(1, int(len(dates) * train_fraction))
    validation_end = max(train_end + 1, int(len(dates) * (train_fraction + validation_fraction)))
    if validation_end >= len(dates):
        validation_end = len(dates) - 1
    train_dates, validation_dates, test_dates = dates[:train_end], dates[train_end:validation_end], dates[validation_end:]
    if min(len(train_dates), len(validation_dates), len(test_dates)) < 1:
        raise ValueError("Chronological split produced an empty partition; provide more distinct dates.")
    return tuple(ordered[ordered[date_column].isin(part)].copy().reset_index(drop=True) for part in (train_dates, validation_dates, test_dates))
