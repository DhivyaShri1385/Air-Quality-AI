"""Cleaning and chronological data preparation."""

import pandas as pd

from .data_loader import pollutant_columns


def clean_daily_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Normalize types, remove invalid target rows, and sort chronologically."""
    cleaned = frame.copy()
    cleaned["Date"] = pd.to_datetime(cleaned["Date"], errors="coerce")
    cleaned["AQI"] = pd.to_numeric(cleaned["AQI"], errors="coerce")
    cleaned = cleaned.dropna(subset=["City", "Date", "AQI"])
    cleaned = cleaned.drop_duplicates(subset=["City", "Date"], keep="last")
    for column in pollutant_columns(cleaned):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    return cleaned.sort_values(["City", "Date"]).reset_index(drop=True)


def fill_feature_missing_values(frame: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    """Fill feature gaps using training-safe forward/backward values then medians."""
    result = frame.copy()
    for column in feature_columns:
        if column not in result:
            result[column] = 0.0
        result[column] = pd.to_numeric(result[column], errors="coerce")
        result[column] = result.groupby("City", sort=False)[column].transform(
            lambda series: series.ffill().bfill()
        )
        result[column] = result[column].fillna(result[column].median()).fillna(0.0)
    return result


def chronological_split(
    frame: pd.DataFrame, train_fraction: float = 0.70, validation_fraction: float = 0.15
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split rows by timestamp, preserving time order."""
    if train_fraction <= 0 or validation_fraction <= 0 or train_fraction + validation_fraction >= 1:
        raise ValueError("Split fractions must be positive and leave a test portion.")
    ordered = frame.sort_values("Date").reset_index(drop=True)
    train_end = int(len(ordered) * train_fraction)
    validation_end = int(len(ordered) * (train_fraction + validation_fraction))
    return ordered.iloc[:train_end], ordered.iloc[train_end:validation_end], ordered.iloc[validation_end:]
