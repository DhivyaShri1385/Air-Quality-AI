"""Streamlit dashboard for the AI-based air-quality prediction system."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.alert_system import build_alert
from src.aqi_classifier import category_color
from src.data_loader import load_city_daily_data
from src.predict import load_artifacts, predict_next

st.set_page_config(page_title="Air Quality Prediction", page_icon="🌿", layout="wide")
st.markdown(
    """<style>
    .stApp { background: #f7faf9; }
    [data-testid="stSidebar"] { background: #0b2545; }
    [data-testid="stSidebar"] * { color: white; }
    .metric-card { background: white; border-left: 5px solid #2e7d32; padding: 1rem; border-radius: .5rem; box-shadow: 0 1px 5px #d5ded9; }
    </style>""",
    unsafe_allow_html=True,
)


@st.cache_data
def get_data():
    return load_city_daily_data()


def main():
    st.sidebar.title("🌿 Air Quality AI")
    page = st.sidebar.radio("Navigation", ["Environmental Overview", "AQI Prediction", "Pollution Analytics", "Model Performance", "Pollution Alerts", "Explainable AI", "About Project"])
    try:
        data = get_data()
        model, metadata = load_artifacts()
    except Exception as exc:
        st.error(str(exc))
        st.info("Run `python -m src.train_model` before opening the dashboard.")
        return

    cities = sorted(data["City"].unique())
    city = st.sidebar.selectbox("City", cities)
    city_data = data[data["City"] == city].sort_values("Date")
    result = predict_next(city, data)
    alert = build_alert(result["predicted_aqi"])

    if page == "Environmental Overview":
        st.title("AI-Based Air Quality Prediction and Pollution Alert System")
        st.write("Historical Indian air-quality observations with a leakage-safe next-observation AQI forecast.")
        a, b, c, d = st.columns(4)
        a.metric("Latest historical AQI", f"{city_data.iloc[-1]['AQI']:.1f}")
        b.metric("Predicted AQI", f"{result['predicted_aqi']:.1f}")
        c.metric("Category", alert["category"])
        d.metric("Observations", f"{len(city_data):,}")
        fig = px.line(city_data, x="Date", y="AQI", title=f"Historical AQI — {city}")
        st.plotly_chart(fig, use_container_width=True)
        st.warning(alert["message"]) if alert["severity"] != "info" else st.success(alert["message"])
    elif page == "AQI Prediction":
        st.title("AQI Prediction")
        st.subheader(f"Next available daily observation for {city}")
        st.metric("Predicted AQI", f"{result['predicted_aqi']:.2f}")
        st.markdown(f"**Category:** `{alert['category']}`  \n**Model:** {result['model']}  \n**Latest usable observation:** {result['as_of'].date()}  \n**Forecast observation:** {result['forecast_observation'].date()}")
        st.info("This is a next-available-observation forecast based on historical daily data; it is not a real-time prediction.")
    elif page == "Pollution Analytics":
        st.title("Pollution Analytics")
        numeric = [c for c in ["AQI", "PM2.5", "PM10", "NO2", "SO2", "CO", "O3"] if c in city_data]
        pollutant = st.selectbox("Trend variable", numeric)
        st.plotly_chart(px.line(city_data, x="Date", y=pollutant, title=f"{pollutant} trend — {city}"), use_container_width=True)
        st.plotly_chart(px.histogram(data, x="AQI", nbins=40, title="AQI distribution across all cities"), use_container_width=True)
        st.plotly_chart(px.imshow(data[numeric].corr(), text_auto=".2f", title="Pollutant correlation"), use_container_width=True)
    elif page == "Model Performance":
        st.title("Model Performance")
        st.dataframe(pd.read_csv(Path("models") / "metrics.csv"), use_container_width=True)
        actual = metadata["test_actual"]
        predicted = metadata["test_predictions"]
        comparison = pd.DataFrame({"Actual": actual, "Predicted": predicted})
        st.plotly_chart(px.scatter(comparison, x="Actual", y="Predicted", title="Untouched test-set predictions"), use_container_width=True)
        st.json(metadata["test_metrics"])
    elif page == "Pollution Alerts":
        st.title("Pollution Alerts")
        st.markdown(f"<div class='metric-card'><h2 style='color:{category_color(alert['category'])}'>{alert['category']}</h2><p>{alert['message']}</p><strong>Predicted AQI: {result['predicted_aqi']:.1f}</strong></div>", unsafe_allow_html=True)
        st.subheader("CPCB AQI categories")
        st.table(pd.DataFrame({"Range": ["0–50", "51–100", "101–200", "201–300", "301–400", "401–500"], "Category": ["Good", "Satisfactory", "Moderately Polluted", "Poor", "Very Poor", "Severe"]}))
    elif page == "Explainable AI":
        st.title("Explainable AI")
        estimator = model.named_steps["model"]
        if hasattr(estimator, "feature_importances_"):
            importance = pd.DataFrame({"Feature": metadata["feature_names"], "Importance": estimator.feature_importances_}).sort_values("Importance", ascending=False).head(15)
            st.plotly_chart(px.bar(importance.sort_values("Importance"), x="Importance", y="Feature", orientation="h", title="Model feature importance"), use_container_width=True)
            st.caption("Feature importance indicates model reliance, not scientific causation.")
        else:
            st.info("The selected model does not expose tree feature importance.")
    elif page == "About Project":
        st.title("About the Project")
        st.write("This academic system combines environmental data analytics, machine learning, CPCB AQI classification, explainability, and pollution alerts.")
        st.markdown("**Dataset:** supplied India Air Quality daily city observations.  \n**Models:** Linear Regression, Random Forest Regressor, and XGBoost Regressor.  \n**Limitations:** no meteorological variables are present, and forecasts cover the next available city observation.")


if __name__ == "__main__":
    main()
