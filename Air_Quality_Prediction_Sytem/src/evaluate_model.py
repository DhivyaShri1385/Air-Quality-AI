"""Model evaluation helpers."""

from math import sqrt

import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def regression_metrics(actual, predicted) -> dict[str, float]:
    return {
        "MAE": float(mean_absolute_error(actual, predicted)),
        "RMSE": float(sqrt(mean_squared_error(actual, predicted))),
        "R2": float(r2_score(actual, predicted)),
    }


def metrics_frame(results: dict[str, dict[str, float]]) -> pd.DataFrame:
    return pd.DataFrame(results).T.rename_axis("Model").reset_index()
