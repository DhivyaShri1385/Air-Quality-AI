"""Air Quality AI Streamlit dashboard."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.theme import COLORS, apply_theme, empty_state, page_header, style_chart
from src.alert_system import build_alert
from src.aqi_classifier import category_color
from src.data_loader import load_city_daily_data
from src.predict import load_artifacts, predict_next

st.set_page_config(page_title="Air Quality AI", page_icon="🌿", layout="wide")
apply_theme()


@st.cache_data
def get_data() -> pd.DataFrame:
    return load_city_daily_data()


def render_overview(data: pd.DataFrame, city: str, city_data: pd.DataFrame, result: dict, alert: dict) -> None:
    page_header("Environmental Overview", "Evidence-based historical air-quality intelligence and a next-observation AQI forecast.")
    latest = city_data.iloc[-1]
    columns = st.columns(4)
    columns[0].metric("Observed AQI", f"{latest['AQI']:.1f}", help="Latest recorded AQI in the selected city.")
    columns[1].metric("Predicted AQI", f"{result['predicted_aqi']:.1f}", help="Model estimate for the next available observation.")
    columns[2].metric("Classification", alert["category"])
    columns[3].metric("City observations", f"{len(city_data):,}")
    st.caption(f"Selected city: {city} · Observed on {latest['Date'].date()} · Forecast observation: {result['forecast_observation'].date()}")
    figure = px.line(city_data, x="Date", y="AQI", labels={"Date": "Observation date", "AQI": "AQI"})
    st.plotly_chart(style_chart(figure, f"Historical AQI — {city}"), use_container_width=True)
    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("Pollutant summary")
        pollutant_names = ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"]
        available = [name for name in pollutant_names if name in city_data.columns]
        if available:
            summary = pd.DataFrame({"Pollutant": available, "Latest observed value": [latest[name] for name in available]})
            st.dataframe(summary, hide_index=True, use_container_width=True)
        else:
            empty_state("No supported pollutant columns are available for this city.")
    with right:
        st.markdown(
            f'<div class="aq-card"><h3 style="color:{category_color(alert["category"])}">Pollution warning</h3>'
            f'<p>{alert["message"]}</p><p><strong>Predicted AQI:</strong> {result["predicted_aqi"]:.1f}</p></div>',
            unsafe_allow_html=True,
        )
    st.subheader("Recent environmental observations")
    st.dataframe(city_data.tail(10).sort_values("Date", ascending=False), hide_index=True, use_container_width=True)


def render_prediction(city: str, city_data: pd.DataFrame, result: dict, alert: dict) -> None:
    page_header("AQI Prediction", "A transparent next-observation estimate based only on historical observations available at prediction time.")
    st.info("Forecast horizon: the next available daily observation for the selected city. This is not a real-time forecast.")
    st.caption(f"{city} has {len(city_data):,} usable historical observations from {city_data['Date'].min().date()} to {city_data['Date'].max().date()}.")
    columns = st.columns(4)
    columns[0].metric("Predicted AQI", f"{result['predicted_aqi']:.2f}")
    columns[1].metric("AQI category", alert["category"])
    columns[2].metric("Forecast date", str(result["forecast_observation"].date()))
    columns[3].metric("Alert severity", alert["severity"].title())
    figure = px.line(city_data.tail(90), x="Date", y="AQI", labels={"Date": "Observation date", "AQI": "Observed AQI"})
    figure.add_trace(go.Scatter(x=[result["forecast_observation"]], y=[result["predicted_aqi"]], mode="markers", name="Predicted AQI", marker={"size": 12, "color": COLORS["accent"]}))
    st.plotly_chart(style_chart(figure, f"Observed AQI and forecast point — {city}"), use_container_width=True)
    st.markdown(f'<div class="aq-card"><h3>How to interpret this result</h3><p>The {result["model"]} model uses historical AQI and pollutant lag/rolling features. Feature importance describes model reliance, not causation. The forecast is labeled separately from observed values.</p></div>', unsafe_allow_html=True)
    if alert["severity"] == "info":
        st.success(alert["message"])
    elif alert["severity"] == "critical":
        st.error(alert["message"])
    else:
        st.warning(alert["message"])


def render_analytics(data: pd.DataFrame, city: str, city_data: pd.DataFrame) -> None:
    page_header("Pollution Analytics", "Explore historical pollutant levels, AQI distributions, and relationships in the supplied dataset.")
    numeric = [column for column in ["AQI", "PM2.5", "PM10", "NO2", "SO2", "CO", "O3"] if column in city_data.columns and city_data[column].notna().any()]
    if not numeric:
        empty_state("No numeric pollution measures are available for analytics.")
        return
    pollutant = st.selectbox("Trend variable", numeric)
    figure = px.line(city_data, x="Date", y=pollutant, labels={"Date": "Observation date", pollutant: pollutant})
    st.plotly_chart(style_chart(figure, f"{pollutant} trend — {city}"), use_container_width=True)
    left, right = st.columns(2)
    with left:
        st.plotly_chart(style_chart(px.histogram(data.dropna(subset=["AQI"]), x="AQI", nbins=40), "AQI distribution across cities"), use_container_width=True)
    with right:
        correlation = data[numeric].corr()
        st.plotly_chart(style_chart(px.imshow(correlation, text_auto=".2f", color_continuous_scale="Teal"), "Pollutant correlation"), use_container_width=True)
    if "City" in data.columns:
        comparison = data.groupby("City", as_index=False)["AQI"].mean().dropna().sort_values("AQI", ascending=False)
        st.plotly_chart(style_chart(px.bar(comparison, x="City", y="AQI"), "Mean AQI by city"), use_container_width=True)


def render_performance(metadata: dict) -> None:
    page_header("Model Performance", "Metrics below come from chronological validation and an untouched test set.")
    metrics_path = Path(__file__).resolve().parent / "models" / "metrics.csv"
    if not metrics_path.exists():
        empty_state("Model comparison metrics are unavailable. Train the models first.")
        return
    st.dataframe(pd.read_csv(metrics_path), hide_index=True, use_container_width=True)
    comparison = pd.DataFrame({"Actual AQI": metadata["test_actual"], "Predicted AQI": metadata["test_predictions"]})
    figure = px.scatter(comparison, x="Actual AQI", y="Predicted AQI")
    figure.add_trace(go.Scatter(x=[comparison["Actual AQI"].min(), comparison["Actual AQI"].max()], y=[comparison["Actual AQI"].min(), comparison["Actual AQI"].max()], mode="lines", name="Ideal"))
    st.plotly_chart(style_chart(figure, "Untouched test-set predictions"), use_container_width=True)
    st.json(metadata["test_metrics"])


def render_alerts(result: dict, alert: dict) -> None:
    page_header("Pollution Alerts", "Warnings are generated from the actual model prediction and CPCB AQI classification.")
    color = category_color(alert["category"])
    st.markdown(f'<div class="aq-card"><div class="aq-kicker">{alert["severity"]} alert</div><h3 style="color:{color}">{alert["category"]}</h3><p>{alert["message"]}</p><p><strong>Predicted AQI:</strong> {result["predicted_aqi"]:.1f}</p></div>', unsafe_allow_html=True)
    st.subheader("CPCB AQI classification")
    st.dataframe(pd.DataFrame({"Range": ["0–50", "51–100", "101–200", "201–300", "301–400", "401–500"], "Category": ["Good", "Satisfactory", "Moderately Polluted", "Poor", "Very Poor", "Severe"]}), hide_index=True, use_container_width=True)


def render_explainability(model, metadata: dict) -> None:
    page_header("Explainable AI", "Understand which historical inputs the selected tree model relied on most.")
    estimator = model.named_steps.get("model")
    if not hasattr(estimator, "feature_importances_"):
        empty_state("The selected model does not expose feature importance.")
        return
    importance = pd.DataFrame({"Feature": metadata["feature_names"], "Importance": estimator.feature_importances_}).sort_values("Importance", ascending=False).head(15)
    st.plotly_chart(style_chart(px.bar(importance.sort_values("Importance"), x="Importance", y="Feature", orientation="h"), "Top model feature importance"), use_container_width=True)
    st.caption("Feature importance indicates predictive reliance. It does not prove that a feature scientifically causes pollution.")


def render_about() -> None:
    page_header("About the Project", "An academic environmental intelligence application built from real Indian air-quality observations.")
    for heading, text in {
        "Problem statement": "Air pollution varies across locations and time. Historical data can support transparent risk awareness and environmental decision support.",
        "Methodology": "The system validates daily city data, creates lag and rolling features, uses chronological splits, compares three regressors, and applies CPCB classification to predictions.",
        "Technology stack": "Python, Streamlit, pandas, NumPy, scikit-learn, XGBoost, Plotly, Matplotlib, and joblib.",
        "Limitations and future scope": "The supplied dataset has no meteorological variables. Future work can add validated weather data, uncertainty intervals, and a dedicated hourly model without claiming real-time sensing.",
    }.items():
        st.subheader(heading)
        st.write(text)


def main() -> None:
    st.sidebar.title("🌿 Air Quality AI")
    pages = ["Environmental Overview", "AQI Prediction", "Pollution Analytics", "Model Performance", "Pollution Alerts", "Explainable AI", "About Project"]
    page = st.sidebar.radio("Navigation", pages)
    try:
        data = get_data()
        model, metadata = load_artifacts()
    except (FileNotFoundError, ValueError, OSError) as exc:
        st.error(f"Application setup error: {exc}")
        st.info("Run `python -m src.train_model` to create the model artifacts.")
        return
    if data.empty:
        empty_state("The dataset contains no usable records.")
        return
    city = st.sidebar.selectbox("City", sorted(data["City"].unique()))
    city_data = data[data["City"] == city].sort_values("Date").copy()
    try:
        result = predict_next(city, data)
        alert = build_alert(result["predicted_aqi"])
    except (ValueError, KeyError, OSError) as exc:
        st.error(f"Prediction unavailable: {exc}")
        return
    if page == "Environmental Overview":
        render_overview(data, city, city_data, result, alert)
    elif page == "AQI Prediction":
        render_prediction(city, city_data, result, alert)
    elif page == "Pollution Analytics":
        render_analytics(data, city, city_data)
    elif page == "Model Performance":
        render_performance(metadata)
    elif page == "Pollution Alerts":
        render_alerts(result, alert)
    elif page == "Explainable AI":
        render_explainability(model, metadata)
    else:
        render_about()


if __name__ == "__main__":
    main()
