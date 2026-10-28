from src.aqi_classifier import classify_aqi


def test_cpcb_boundaries():
    assert classify_aqi(0) == "Good"
    assert classify_aqi(50) == "Good"
    assert classify_aqi(51) == "Satisfactory"
    assert classify_aqi(200) == "Moderately Polluted"
    assert classify_aqi(301) == "Very Poor"
    assert classify_aqi(500) == "Severe"
    assert classify_aqi(501) == "Above Standard Scale"
