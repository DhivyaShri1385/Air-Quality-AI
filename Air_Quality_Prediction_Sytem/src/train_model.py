"""Train, compare, and persist the next-observation AQI models."""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor

from .data_loader import DATA_PATH, load_city_daily_data
from .evaluate_model import metrics_frame, regression_metrics
from .feature_engineering import build_forecasting_frame
from .preprocessing import chronological_split

MODEL_DIR = Path(__file__).resolve().parents[1] / "models"


def make_models() -> dict[str, Pipeline]:
    return {
        "Linear Regression": Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler()), ("model", LinearRegression())]
        ),
        "Random Forest": Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("model", RandomForestRegressor(n_estimators=180, random_state=42, n_jobs=-1, min_samples_leaf=2))]
        ),
        "XGBoost": Pipeline(
            [("imputer", SimpleImputer(strategy="median")), ("model", XGBRegressor(n_estimators=350, max_depth=6, learning_rate=0.05, subsample=0.85, colsample_bytree=0.85, objective="reg:squarederror", random_state=42, n_jobs=4))]
        ),
    }


def train() -> dict:
    raw = load_city_daily_data(DATA_PATH)
    prepared, feature_names = build_forecasting_frame(raw)
    train_frame, validation_frame, test_frame = chronological_split(prepared)
    x_train, y_train = train_frame[feature_names], train_frame["target_aqi"]
    x_validation, y_validation = validation_frame[feature_names], validation_frame["target_aqi"]
    x_test, y_test = test_frame[feature_names], test_frame["target_aqi"]

    validation_results = {}
    models = make_models()
    for name, model in models.items():
        model.fit(x_train, y_train)
        validation_results[name] = regression_metrics(y_validation, model.predict(x_validation))
    best_name = min(validation_results, key=lambda name: validation_results[name]["MAE"])
    best_model = models[best_name]
    best_model.fit(pd.concat([x_train, x_validation]), pd.concat([y_train, y_validation]))
    test_predictions = best_model.predict(x_test)
    test_results = regression_metrics(y_test, test_predictions)

    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(best_model, MODEL_DIR / "aqi_model.joblib")
    metadata = {
        "dataset": str(DATA_PATH),
        "target": "next available AQI observation per city",
        "best_model": best_name,
        "feature_names": feature_names,
        "validation_metrics": validation_results,
        "test_metrics": test_results,
        "test_dates": [test_frame["Date"].min().isoformat(), test_frame["Date"].max().isoformat()],
        "test_predictions": test_predictions.tolist(),
        "test_actual": y_test.tolist(),
        "test_cities": test_frame["City"].tolist(),
    }
    (MODEL_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    metrics_frame(validation_results).to_csv(MODEL_DIR / "metrics.csv", index=False)
    return metadata


if __name__ == "__main__":
    result = train()
    print(f"Best model: {result['best_model']}")
    print("Validation metrics:")
    print(metrics_frame(result["validation_metrics"]).to_string(index=False))
    print("Untouched test metrics:")
    print(result["test_metrics"])
