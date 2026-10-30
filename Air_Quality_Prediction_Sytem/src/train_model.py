"""Chronologically train, compare, and persist next-calendar-day AQI models."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .data_loader import DATA_PATH, load_city_daily_data
from .evaluate_model import metrics_frame, regression_metrics
from .feature_engineering import build_forecasting_frame
from .preprocessing import chronological_split

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"
RANDOM_SEED = 42


class PersistenceRegressor(BaseEstimator, RegressorMixin):
    """Persistence baseline: next-day AQI equals the forecast-origin AQI."""

    def fit(self, X, y=None):
        self.n_features_in_ = X.shape[1]
        self.feature_names_in_ = np.asarray(X.columns, dtype=object) if hasattr(X, "columns") else None
        return self

    def predict(self, X):
        if hasattr(X, "columns") and "AQI" in X.columns:
            values = X["AQI"].to_numpy(dtype=float)
        else:
            values = np.asarray(X, dtype=float)[:, 0]
        return values


def make_models() -> dict[str, Pipeline]:
    models = {
        "Linear Regression": Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True)), ("scaler", StandardScaler()), ("model", LinearRegression())]),
        "Random Forest": Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True)), ("model", RandomForestRegressor(n_estimators=180, random_state=RANDOM_SEED, n_jobs=1, min_samples_leaf=2))]),
    }
    try:
        from xgboost import XGBRegressor
        models["XGBoost"] = Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True)), ("model", XGBRegressor(n_estimators=350, max_depth=6, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, objective="reg:squarederror", random_state=RANDOM_SEED, n_jobs=1))])
    except ImportError:
        pass
    return models


def train() -> dict:
    raw = load_city_daily_data(DATA_PATH)
    prepared, feature_names = build_forecasting_frame(raw)
    if prepared.empty:
        raise ValueError("No next-calendar-day AQI targets exist in the dataset.")
    train_frame, validation_frame, test_frame = chronological_split(prepared)
    if min(len(train_frame), len(validation_frame), len(test_frame)) < 2:
        raise ValueError("Each chronological partition needs at least two supervised examples.")
    x_train, y_train = train_frame[feature_names], train_frame["target_aqi"]
    x_validation, y_validation = validation_frame[feature_names], validation_frame["target_aqi"]
    x_test, y_test = test_frame[feature_names], test_frame["target_aqi"]
    models = make_models()
    validation_results = {"Persistence Baseline": regression_metrics(y_validation, x_validation["AQI"])}
    for name, model in models.items():
        model.fit(x_train, y_train)
        validation_results[name] = regression_metrics(y_validation, model.predict(x_validation))
    best_name = min(validation_results, key=lambda name: validation_results[name]["MAE"])
    best_model = PersistenceRegressor() if best_name == "Persistence Baseline" else models[best_name]
    if best_name == "Persistence Baseline":
        best_model.fit(pd.concat([x_train, x_validation]), pd.concat([y_train, y_validation]))
    else:
        best_model.fit(pd.concat([x_train, x_validation]), pd.concat([y_train, y_validation]))
    best_predictions = np.asarray(best_model.predict(x_test), dtype=float)
    baseline_predictions = x_test["AQI"].to_numpy(dtype=float)
    test_results = regression_metrics(y_test, best_predictions)
    test_baseline = regression_metrics(y_test, baseline_predictions)
    metric_rows = []
    for name, values in validation_results.items():
        metric_rows.append({"Model": name, "Partition": "Validation", **values})
    metric_rows.extend([
        {"Model": "Selected Model", "Partition": "Held-out Test", **test_results},
        {"Model": "Persistence Baseline", "Partition": "Held-out Test", **test_baseline},
    ])
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(best_model, MODEL_DIR / "aqi_model.joblib")
    metadata = {
        "dataset": str(DATA_PATH), "target": "AQI on the next calendar day after forecast origin",
        "forecast_horizon_days": 1, "best_model": best_name, "feature_names": feature_names,
        "training_config": {"random_seed": RANDOM_SEED, "split": "chronological distinct target dates", "train_fraction": 0.70, "validation_fraction": 0.15, "selection_metric": "validation MAE"},
        "xgboost_available": "XGBoost" in models,
        "date_ranges": {"train": [str(train_frame.target_date.min().date()), str(train_frame.target_date.max().date())], "validation": [str(validation_frame.target_date.min().date()), str(validation_frame.target_date.max().date())], "test": [str(test_frame.target_date.min().date()), str(test_frame.target_date.max().date())]},
        "validation_metrics": validation_results, "test_metrics": test_results, "test_persistence_metrics": test_baseline,
        "test_dates": test_frame["target_date"].dt.strftime("%Y-%m-%d").tolist(),
        "test_predictions": best_predictions.tolist(), "test_actual": y_test.tolist(),
        "test_baseline_predictions": baseline_predictions.tolist(), "test_cities": test_frame["City"].tolist(),
    }
    (MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, allow_nan=True), encoding="utf-8")
    pd.DataFrame(metric_rows).to_csv(MODEL_DIR / "metrics.csv", index=False)
    return metadata


if __name__ == "__main__":
    result = train()
    print(f"Best model (validation MAE): {result['best_model']}")
    print("Validation metrics:")
    print(metrics_frame(result["validation_metrics"]).to_string(index=False))
    print("Held-out test metrics:", result["test_metrics"])
    print("Held-out persistence metrics:", result["test_persistence_metrics"])
