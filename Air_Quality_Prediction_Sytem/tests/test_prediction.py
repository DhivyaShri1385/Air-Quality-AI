from src.data_loader import load_city_daily_data
from src.predict import predict_next


def test_prediction_output():
    data = load_city_daily_data()
    result = predict_next("Delhi", data)
    assert result["city"] == "Delhi"
    assert result["predicted_aqi"] >= 0
    assert result["forecast_observation"] > result["as_of"]
