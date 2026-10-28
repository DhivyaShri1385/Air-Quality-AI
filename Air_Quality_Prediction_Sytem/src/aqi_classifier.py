"""CPCB National Air Quality Index classification."""


def classify_aqi(value: float) -> str:
    """Return the CPCB category, including explicit handling above 500."""
    value = float(value)
    if value < 0:
        return "Invalid"
    if value <= 50:
        return "Good"
    if value <= 100:
        return "Satisfactory"
    if value <= 200:
        return "Moderately Polluted"
    if value <= 300:
        return "Poor"
    if value <= 400:
        return "Very Poor"
    if value <= 500:
        return "Severe"
    return "Above Standard Scale"


def category_color(category: str) -> str:
    return {
        "Good": "#2e7d32",
        "Satisfactory": "#558b2f",
        "Moderately Polluted": "#f9a825",
        "Poor": "#ef6c00",
        "Very Poor": "#c62828",
        "Severe": "#6a1b9a",
        "Above Standard Scale": "#263238",
    }.get(category, "#455a64")
