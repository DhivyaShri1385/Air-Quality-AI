"""Centralized CPCB National Air Quality Index category boundaries."""

from math import isfinite

CATEGORY_BOUNDARIES = (
    (50, "Good"), (100, "Satisfactory"), (200, "Moderately Polluted"),
    (300, "Poor"), (400, "Very Poor"), (500, "Severe"),
)


def classify_aqi(value: float) -> str:
    """Return the CPCB category, including explicit handling above 500."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Invalid"
    if not isfinite(value) or value < 0:
        return "Invalid"
    for upper_bound, category in CATEGORY_BOUNDARIES:
        if value <= upper_bound:
            return category
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
