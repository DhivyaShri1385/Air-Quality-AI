"""Human-readable guidance for observed AQI and forecast alerts."""

from .aqi_classifier import classify_aqi


def build_alert(aqi: float, status: str = "Forecast", date=None) -> dict[str, str]:
    category = classify_aqi(aqi)
    messages = {
        "Good": "Air quality is in the Good category. Continue to follow local air-quality updates.",
        "Satisfactory": "Air quality is generally acceptable; unusually sensitive people may prefer to check local guidance.",
        "Moderately Polluted": "People sensitive to air pollution may consider reducing prolonged or strenuous outdoor activity if they notice symptoms.",
        "Poor": "Consider limiting prolonged or strenuous outdoor activity, especially for sensitive groups.",
        "Very Poor": "Reduce prolonged outdoor exertion and follow current public-health guidance.",
        "Severe": "Limit outdoor exertion where practical and follow current public-health guidance.",
        "Above Standard Scale": "AQI is above the 0–500 scale; treat this result cautiously and consult a reliable local source.",
        "Invalid": "The AQI value is invalid and requires data review.",
    }
    severity = "info" if category in {"Good", "Satisfactory"} else "warning"
    if category in {"Very Poor", "Severe", "Above Standard Scale"}:
        severity = "critical"
    return {"category": category, "severity": severity, "message": messages[category], "status": status, "date": "" if date is None else str(date)}
