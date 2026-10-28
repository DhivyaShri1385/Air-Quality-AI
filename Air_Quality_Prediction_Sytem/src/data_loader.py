"""Dataset loading and validation helpers."""

from pathlib import Path
from typing import Final

import pandas as pd

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DATA_PATH: Final[Path] = PROJECT_ROOT / "dataset" / "city_day.csv"
REQUIRED_COLUMNS: Final[set[str]] = {"City", "Date", "AQI"}


def load_city_daily_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Load the daily city dataset and validate its minimum schema."""
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Dataset file was not found: {csv_path}")
    frame = pd.read_csv(csv_path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    if frame.empty:
        raise ValueError(f"Dataset is empty: {csv_path}")
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    frame["AQI"] = pd.to_numeric(frame["AQI"], errors="coerce")
    frame = frame.dropna(subset=["City", "Date", "AQI"]).copy()
    frame["City"] = frame["City"].astype(str).str.strip()
    return frame.sort_values(["Date", "City"]).reset_index(drop=True)


def pollutant_columns(frame: pd.DataFrame) -> list[str]:
    """Return numeric pollutant columns present in the supplied frame."""
    excluded = {"AQI"}
    return [
        column
        for column in frame.columns
        if column not in excluded
        and column not in {"City", "Date", "AQI_Bucket"}
        and pd.api.types.is_numeric_dtype(frame[column])
    ]
