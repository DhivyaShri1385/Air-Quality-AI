"""Human-readable pollution alerts based on actual AQI predictions."""

from .aqi_classifier import classify_aqi


def build_alert(predicted_aqi: float) -> dict[str, str]:
    category = classify_aqi(predicted_aqi)
    messages = {
        "Good": "Air quality is satisfactory.",
        "Satisfactory": "Air quality is generally acceptable.",
        "Moderately Polluted": "Sensitive individuals should pay attention to air quality conditions.",
        "Poor": "Increased pollution risk. Consider reducing prolonged outdoor exertion.",
        "Very Poor": "High pollution levels. Take appropriate precautions.",
        "Severe": "Extremely poor air quality. Follow relevant public-health guidance.",
        "Above Standard Scale": "AQI exceeds the standard 0–500 scale. Avoid unnecessary outdoor exposure.",
        "Invalid": "The predicted AQI is invalid and requires review.",
    }
    severity = "info" if category in {"Good", "Satisfactory"} else "warning"
    if category in {"Very Poor", "Severe", "Above Standard Scale"}:
        severity = "critical"
    return {"category": category, "severity": severity, "message": messages[category]}
