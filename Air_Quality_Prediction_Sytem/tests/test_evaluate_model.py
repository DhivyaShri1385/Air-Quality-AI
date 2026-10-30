import math

import pytest

from src.evaluate_model import regression_metrics


def test_regression_metrics_and_constant_target_r2():
    result = regression_metrics([10, 10], [8, 12])
    assert result["MAE"] == 2
    assert result["RMSE"] == 2
    assert math.isnan(result["R2"])


def test_regression_metrics_reject_empty_or_mismatched_inputs():
    with pytest.raises(ValueError):
        regression_metrics([], [])
    with pytest.raises(ValueError):
        regression_metrics([1], [1, 2])
