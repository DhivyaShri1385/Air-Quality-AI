"""Model evaluation helpers."""

from math import sqrt

import pandas as pd
import math

from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(actual, predicted) -> dict[str, float]:
    """Calculate regression metrics; R² is NaN when the target has <2 values or is constant."""
    if len(actual) == 0 or len(actual) != len(predicted):
        raise ValueError("Actual and predicted values must have the same non-zero length.")
    r2 = float(r2_score(actual, predicted)) if len(actual) >= 2 and len(set(actual)) > 1 else math.nan
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(sqrt(mean_squared_error(actual, predicted))),
        "R2": r2,
    }


def metrics_frame(results: dict[str, dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(results).T.rename_axis("Model").reset_index()
