"""AI-Based Air Quality Prediction and Pollution Alert System dashboard."""

from datetime import date
import math
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.theme import AQI_COLORS, COLORS, apply_theme, empty_state, forecast_hero, kpi_card, page_header, panel_heading, style_chart
from src.alert_system import build_alert
from src.aqi_classifier import classify_aqi
from src.data_loader import load_city_daily_data
from src.predict import load_artifacts, predict_next, predict_aqi_only

PROJECT_TITLE = "AI-Based Air Quality Prediction and Pollution Alert System"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dataset"

st.set_page_config(page_title=PROJECT_TITLE, page_icon="🌿", layout="wide")
apply_theme()


@st.cache_data(show_spinner="Loading city observations…")
def get_data() -> pd.DataFrame:
    return load_city_daily_data()


@st.cache_data(show_spinner=False)
def latest_city_rows(data: pd.DataFrame) -> pd.DataFrame:
    return data.sort_values(["City", "Date"]).groupby("City", as_index=False, sort=False).tail(1).copy()


def header(city: str, city_data: pd.DataFrame) -> None:
    left, right = st.columns([3.1, 1.1], gap="medium")
    with left:
        st.markdown(
            '<div class="aq-brand"><span class="aq-mark">AQ</span><span>Air Quality Intelligence</span></div>',
            unsafe_allow_html=True,
        )
    with right:
        options = sorted(city_data["City"].astype(str).unique())
        if city not in options:
            city = options[0]
        st.selectbox("Selected city", options, index=options.index(city), key="selected_city")


def current_context(city_data: pd.DataFrame) -> tuple[pd.Series | None, pd.Timestamp | None]:
    if city_data.empty:
        return None, None
    latest = city_data.sort_values("Date").iloc[-1]
    return latest, pd.Timestamp(latest["Date"]) + pd.Timedelta(days=1)


def safe_forecast(city: str, data: pd.DataFrame) -> tuple[dict | None, object | None, dict | None, str | None]:
    try:
        result = predict_next(city, data)
        model, metadata = load_artifacts()
        alert = build_alert(result["predicted_aqi"], "Forecast", result["target_date"].date())
        return result, model, metadata, None
    except (FileNotFoundError, ValueError, KeyError, OSError) as exc:
        return None, None, None, str(exc)


def render_kpis(latest: pd.Series, result: dict | None) -> None:
    row = st.columns(2, gap="medium")
    observed = float(latest["AQI"])
    observed_category = classify_aqi(observed)
    with row[0]:
        kpi_card("Latest historical AQI", f"{observed:.0f}", f"Observed {pd.Timestamp(latest['Date']).date()}", COLORS["blue"], observed_category)
    if result:
        predicted = float(result["predicted_aqi"])
        with row[1]:
            change = predicted - observed
            arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
            tint = COLORS["red"] if change > 0 else COLORS["green"]
            kpi_card("Historical forecast change", f"{arrow} {change:+.1f}", "Compared with latest dataset AQI", tint)
    else:
        with row[1]:
            kpi_card("Historical forecast change", "Unavailable", "Model or city history needs attention", COLORS["yellow"])


def add_aqi_bands(fig: go.Figure, ymax: float) -> None:
    bands = [(0, 50, "Good"), (50, 100, "Satisfactory"), (100, 200, "Moderately Polluted"),
             (200, 300, "Poor"), (300, 400, "Very Poor"), (400, 500, "Severe")]
    for low, high, category in bands:
        if low >= ymax:
            continue
        fig.add_hrect(y0=low, y1=min(high, ymax), fillcolor=AQI_COLORS[category], opacity=0.035, line_width=0, layer="below")
    for level in [50, 100, 200, 300, 400, 500]:
        if level < ymax:
            fig.add_hline(y=level, line_width=1, line_dash="dot", line_color=COLORS["border"], opacity=.9)


def render_trend(city_data: pd.DataFrame, result: dict | None, widget_key: str = "trend_range") -> None:
    if city_data.empty:
        empty_state("There are no AQI observations for this city.")
        return
    choices = ["7 days", "30 days", "90 days", "All"]
    selected = st.radio("History window", choices, index=2, horizontal=True, key=widget_key, label_visibility="collapsed")
    ordered = city_data.sort_values("Date").copy()
    if selected != "All":
        days = int(selected.split()[0])
        cutoff = pd.Timestamp(ordered["Date"].max()) - pd.Timedelta(days=days - 1)
        ordered = ordered[ordered["Date"] >= cutoff]
    if ordered.empty:
        empty_state(f"No observations fall within the selected {selected.lower()} window.")
        return
    fig = go.Figure()
    ymax = max(510.0, float(ordered["AQI"].max()) * 1.12, float(result["predicted_aqi"]) * 1.12 if result else 0)
    add_aqi_bands(fig, ymax)
    fig.add_trace(go.Scatter(x=ordered["Date"], y=ordered["AQI"], mode="lines", name="Observed AQI",
                             line={"color": COLORS["blue"], "width": 2.3},
                             hovertemplate="Observed<br>%{x|%d %b %Y}<br>AQI %{y:.0f}<extra></extra>"))
    if result:
        origin = pd.Timestamp(result["forecast_origin_date"])
        target = pd.Timestamp(result["target_date"])
        fig.add_vline(x=target, line_dash="dash", line_color=COLORS["accent"], line_width=1.5)
        fig.add_trace(go.Scatter(x=[target], y=[result["predicted_aqi"]], mode="markers", name=f"{result.get('model', 'Saved model')} forecast",
                                 marker={"size": 13, "color": COLORS["green"], "line": {"color": "#D8FFF5", "width": 1.5}},
                                 customdata=[[result["predicted_category"], str(target.date()), str(origin.date())]],
                                 hovertemplate=f"{result.get('model', 'Model')} · %{{customdata[0]}}<br>Target %{{customdata[1]}}<br>Origin %{{customdata[2]}}<br>AQI %{{y:.1f}}<extra></extra>"))
    fig.update_layout(yaxis={"title": "AQI", "range": [0, ymax]}, xaxis_title="Observation date", height=365,
                      margin={"l": 42, "r": 20, "t": 55, "b": 38})
    st.plotly_chart(style_chart(fig, "AQI trend and next-day forecast"), use_container_width=True, config={"displayModeBar": True, "scrollZoom": True})
    if result:
        st.caption(f"{result['model']} · origin {pd.Timestamp(result['forecast_origin_date']).date()} · target {pd.Timestamp(result['target_date']).date()}")


def city_comparison_chart(data: pd.DataFrame) -> go.Figure:
    latest = latest_city_rows(data).sort_values("AQI", ascending=True)
    latest["Category"] = latest["AQI"].map(classify_aqi)
    fig = go.Figure(go.Bar(
        x=latest["AQI"], y=latest["City"], orientation="h", text=latest["AQI"].round(0).astype(int),
        textposition="outside", cliponaxis=False,
        marker={"color": latest["Category"].map(AQI_COLORS).tolist(), "line": {"width": 0}},
        customdata=latest[["Category", "Date"]].assign(Date=latest["Date"].dt.strftime("%Y-%m-%d")).to_numpy(),
        hovertemplate="%{y}<br>AQI %{x:.0f}<br>%{customdata[0]}<br>Observed %{customdata[1]}<extra></extra>"))
    fig.update_layout(height=max(300, len(latest) * 23), xaxis_title="Latest available AQI", yaxis_title="", margin={"l": 10, "r": 38, "t": 12, "b": 34})
    return style_chart(fig, "Latest available AQI by city")


def category_distribution(data: pd.DataFrame) -> go.Figure | None:
    values = data["AQI"].dropna()
    if values.empty:
        return None
    categories = values.map(classify_aqi).value_counts().rename_axis("Category").reset_index(name="Observations")
    colors = [AQI_COLORS.get(category, COLORS["muted"]) for category in categories["Category"]]
    fig = px.pie(categories, names="Category", values="Observations", hole=.68,
                 color="Category", color_discrete_map=AQI_COLORS)
    fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>%{value:,} observations<br>%{percent}<extra></extra>",
                      marker={"line": {"color": COLORS["background"], "width": 2}})
    fig.update_layout(height=320, showlegend=True, legend={"orientation": "v", "x": 1, "y": .5})
    return style_chart(fig, "Observed AQI category mix")


def pollutant_table(latest: pd.Series) -> pd.DataFrame:
    units = {"PM2.5": "µg/m³", "PM10": "µg/m³", "NO": "µg/m³", "NO2": "µg/m³", "NOx": "µg/m³",
             "NH3": "µg/m³", "CO": "mg/m³", "SO2": "µg/m³", "O3": "µg/m³", "Benzene": "µg/m³",
             "Toluene": "µg/m³", "Xylene": "µg/m³"}
    records = []
    for name, unit in units.items():
        if name in latest.index and pd.notna(latest[name]):
            records.append({"Pollutant": name, "Observed": f"{float(latest[name]):.2f}", "Unit": unit})
    return pd.DataFrame(records)


def recent_table(city_data: pd.DataFrame) -> pd.DataFrame:
    rows = city_data.sort_values("Date", ascending=False).head(12).copy()
    rows["Category"] = rows["AQI"].map(classify_aqi)
    selected = [column for column in ["City", "Date", "AQI", "Category"] if column in rows]
    rows["Date"] = rows["Date"].dt.strftime("%Y-%m-%d")
    rows["AQI"] = rows["AQI"].round(0).astype("Int64")
    return rows[selected]


def coordinates_for_map(data: pd.DataFrame) -> pd.DataFrame:
    path = DATA_DIR / "city_coordinates.csv"
    if not path.exists():
        return pd.DataFrame()
    coords = pd.read_csv(path)
    required = {"City", "Latitude", "Longitude", "GeoNameId"}
    if not required.issubset(coords.columns):
        return pd.DataFrame()
    if coords["City"].duplicated().any():
        return pd.DataFrame()
    coords["Latitude"] = pd.to_numeric(coords["Latitude"], errors="coerce")
    coords["Longitude"] = pd.to_numeric(coords["Longitude"], errors="coerce")
    coords = coords.dropna(subset=["Latitude", "Longitude"])
    coords = coords[coords["Latitude"].between(5, 38) & coords["Longitude"].between(67, 98)]
    latest = latest_city_rows(data)[["City", "Date", "AQI"]].copy()
    latest["Category"] = latest["AQI"].map(classify_aqi)
    return coords.merge(latest, on="City", how="inner", validate="one_to_one")


def india_map(data: pd.DataFrame) -> go.Figure | None:
    points = coordinates_for_map(data)
    if points.empty:
        return None
    fig = go.Figure()
    for category, group in points.groupby("Category", sort=False):
        fig.add_trace(go.Scattergeo(
            lon=group["Longitude"], lat=group["Latitude"], text=group["City"], name=category,
            customdata=group[["AQI", "Date"]].assign(Date=group["Date"].dt.strftime("%Y-%m-%d")).to_numpy(),
            mode="markers", marker={"size": 11, "color": AQI_COLORS.get(category, COLORS["muted"]), "opacity": .92,
                                      "line": {"color": "#E9F7FA", "width": .7}},
            hovertemplate="%{text}<br>%{customdata[0]:.0f} AQI · %{customdata[1]}<br>" + category + "<extra></extra>"))
    fig.update_geos(scope="asia", projection_type="mercator", center={"lat": 22.5, "lon": 79.5},
                    lataxis_range=[5, 38], lonaxis_range=[67, 98], showland=True,
                    landcolor="#13232B", showocean=True, oceancolor=COLORS["background"],
                    showlakes=True, lakecolor=COLORS["background"], showcountries=True,
                    countrycolor=COLORS["border"], countrywidth=.7, showcoastlines=True,
                    coastlinecolor=COLORS["border"], coastlinewidth=.6, showframe=False,
                    bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=390, margin={"l": 0, "r": 0, "t": 10, "b": 0},
                      legend={"title": {"text": "AQI category"}, "orientation": "h", "y": -.04})
    return style_chart(fig, "Latest available city observations · India")


def render_city_map(data: pd.DataFrame) -> None:
    fig = india_map(data)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, config={"scrollZoom": True, "displayModeBar": True}, key="india_city_aqi_map")
        return
    st.warning("Map unavailable: validated city coordinates are missing.")
    st.plotly_chart(city_comparison_chart(data), use_container_width=True, key="city_map_fallback_comparison")


def render_dashboard(city: str, data: pd.DataFrame, city_data: pd.DataFrame, latest: pd.Series,
                     result: dict | None, metadata: dict | None, alert: dict | None) -> None:
    page_header("Dashboard", "City AQI, pollutant levels, and model output.")
    if result:
        forecast_hero(
            result["predicted_aqi"], str(pd.Timestamp(result["target_date"]).date()),
            result["predicted_category"], result["model"], f"Historical {result['model']} demonstration",
            f"{city} · city-level model output",
        )
    render_kpis(latest, result)
    if result is None:
        st.warning("Historical forecast unavailable: " + (metadata if isinstance(metadata, str) else "Check model artifacts or city history."))
    top_left, top_right = st.columns([1.15, .95], gap="large")
    with top_left:
        panel_heading("India AQI map")
        render_city_map(data)
    with top_right:
        panel_heading("AQI trend")
        render_trend(city_data, result, "dashboard_trend_range")
    left, right = st.columns([1.15, .85], gap="large")
    with left:
        panel_heading("Latest AQI by city")
        st.plotly_chart(city_comparison_chart(data), use_container_width=True, key="dashboard_city_comparison")
    with right:
        panel_heading("AQI categories")
        distribution = category_distribution(data)
        if distribution is not None:
            st.plotly_chart(distribution, use_container_width=True)
        else:
            empty_state("No valid AQI observations are available.")
    lower_left, lower_right = st.columns([.9, 1.1], gap="large")
    with lower_left:
        panel_heading("Latest pollutants", str(pd.Timestamp(latest["Date"]).date()))
        pollutants = pollutant_table(latest)
        if pollutants.empty:
            empty_state("No pollutant measurements are available for this observation.")
        else:
            st.dataframe(pollutants, hide_index=True, use_container_width=True)
    with lower_right:
        panel_heading("Recent observations")
        st.dataframe(recent_table(city_data), hide_index=True, use_container_width=True)
    if alert:
        color = AQI_COLORS.get(alert["category"], COLORS["muted"])
        st.markdown(f'<div class="aq-card"><div class="aq-kicker">Historical forecast · {pd.Timestamp(result["target_date"]).date()}</div><h3 style="color:{color}">{alert["category"]} · AQI {result["predicted_aqi"]:.0f}</h3><p>{alert["message"]}</p><small>{result["model"]} · origin {pd.Timestamp(result["forecast_origin_date"]).date()} · city_day.csv</small></div>', unsafe_allow_html=True)


def render_prediction(city: str, city_data: pd.DataFrame, result: dict | None, error: str | None) -> None:
    page_header("AQI Prediction", "AQI-only baseline and historical XGBoost output.")
    render_recent_aqi_forecast(city)
    st.divider()
    historical_model = str(result["model"]) if result else "XGBoost"
    panel_heading(f"Historical {historical_model} Demonstration", "Historical only · not live")
    if result is None:
        st.error(f"Historical prediction unavailable: {error or 'No valid model result.'}")
        return
    columns = st.columns(3, gap="medium")
    cards = [
        (f"{result['model']} AQI", f"{result['predicted_aqi']:.0f}", result["predicted_category"], COLORS["green"], result["predicted_category"]),
        ("Forecast date", str(pd.Timestamp(result["target_date"]).date()), "Historical target", COLORS["blue"], None),
        ("Model", result["model"], "Historical demonstration", COLORS["accent"], None),
    ]
    for col, (label, value, meta, accent, category) in zip(columns, cards):
        with col:
            kpi_card(label, value, meta, accent, category)
    panel_heading("Observed history and forecast")
    render_trend(city_data, result, "prediction_trend_range")


RECENT_RESULT_KEY = "recent_aqi_forecast_payload"


def recent_forecast_chart(dates: list, values: list[float], target_date: pd.Timestamp, predicted: float,
                          model_name: str) -> go.Figure:
    ymax = max(120.0, max(values + [predicted]) * 1.3)
    fig = go.Figure()
    add_aqi_bands(fig, ymax)
    fig.add_trace(go.Scatter(x=dates, y=values, mode="lines+markers", name="Entered readings (observed)",
                             line={"color": COLORS["blue"], "width": 2.6}, marker={"size": 9},
                             hovertemplate="Observed<br>%{x|%d %b %Y}<br>AQI %{y:.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[dates[-1], target_date], y=[values[-1], predicted], mode="lines+markers", name=f"{model_name} forecast",
                             line={"color": COLORS["accent"], "width": 2.4, "dash": "dash"},
                             marker={"size": [0, 13], "color": COLORS["accent"], "symbol": "diamond"},
                             hovertemplate=f"{model_name} forecast<br>%{{x|%d %b %Y}}<br>AQI %{{y:.1f}}<extra></extra>"))
    fig.update_layout(yaxis={"title": "AQI", "range": [0, ymax]}, xaxis={"title": "Date", "tickformat": "%d %b", "dtick": 86400000},
                      height=330, margin={"l": 42, "r": 20, "t": 55, "b": 38})
    return style_chart(fig, "Entered readings and next-day forecast")


def show_recent_result(payload: dict) -> None:
    result, target_date, values, dates = payload["result"], payload["target_date"], payload["values"], payload["dates"]
    forecast_hero(
        result["predicted_aqi"], str(target_date.date()), result["predicted_category"],
        result["model"], "Manual AQI Forecast (Baseline)",
        f"{payload['city']} · AQI-only model",
    )
    st.plotly_chart(recent_forecast_chart(dates, values, target_date, float(result["predicted_aqi"]), str(result["model"])), use_container_width=True, key="recent_forecast_chart")
    alert = build_alert(result["predicted_aqi"], "Forecast", target_date.date())
    st.warning(f"Forecast · {alert['category']} · {target_date.date()} · {alert['message']}")
    st.caption("AQI-only baseline from manual readings · not a live reading or official CPCB alert.")


def render_recent_aqi_forecast(city: str) -> None:
    """Forecast the next day from three manually supplied consecutive AQI readings."""
    panel_heading("Manual AQI Forecast (Baseline)", f"City · {city}")
    latest_date = st.date_input("Date of the latest observation", value=date.today(), max_value=date.today(), key="manual_aqi_latest_date")
    dates = [latest_date - pd.Timedelta(days=2), latest_date - pd.Timedelta(days=1), latest_date]
    with st.form("manual_recent_aqi_forecast"):
        columns = st.columns(3, gap="medium")
        raw_values = [
            columns[index].text_input(
                f"AQI on {observation_date}",
                placeholder="Enter recorded AQI",
                key=f"manual_aqi_value_{index}",
            )
            for index, observation_date in enumerate(dates)
        ]
        submitted = st.form_submit_button("Forecast next day")
    if submitted:
        st.session_state.pop(RECENT_RESULT_KEY, None)
        missing_dates = [str(observation_date) for observation_date, value in zip(dates, raw_values) if not value.strip()]
        if missing_dates:
            st.warning("Forecast unavailable: enter all 3 consecutive daily AQI values. "
                       f"Missing values for {', '.join(missing_dates)}; no values were filled in.")
            return
        try:
            values = [float(value.strip()) for value in raw_values]
        except ValueError:
            st.warning("Forecast unavailable: each AQI value must be a number.")
            return
        if any(not math.isfinite(value) or value < 0 or value > 500 for value in values):
            st.warning("Forecast unavailable: each AQI value must be between 0 and 500.")
            return
        recent_data = pd.DataFrame({"City": [city] * 3, "Date": dates, "AQI": values})
        try:
            result = predict_aqi_only(city, recent_data)
        except (FileNotFoundError, ValueError, KeyError, OSError) as exc:
            st.warning(f"Forecast unavailable: {exc}")
            return
        target_date = pd.Timestamp(latest_date) + pd.Timedelta(days=1)
        if pd.Timestamp(result["target_date"]).normalize() != target_date.normalize():
            st.warning("Forecast unavailable: the model result did not match the next calendar day.")
            return
        st.session_state[RECENT_RESULT_KEY] = {"city": city, "result": result, "values": values,
                                               "dates": [pd.Timestamp(d) for d in dates], "target_date": target_date}
    payload = st.session_state.get(RECENT_RESULT_KEY)
    if payload and payload["city"] == city:
        show_recent_result(payload)


def render_analytics(data: pd.DataFrame, city: str, city_data: pd.DataFrame) -> None:
    page_header("Pollution Analytics", "Pollutant trends, distributions, and city comparisons.")
    available = [name for name in ["AQI", "PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene"]
                 if name in city_data and city_data[name].notna().any()]
    if not available:
        empty_state("No populated numeric pollution measures are available.")
        return
    selector, _ = st.columns([.48, .52])
    with selector:
        pollutant = st.selectbox("Trend measure", available)
    fig = px.line(city_data.dropna(subset=[pollutant]), x="Date", y=pollutant, labels={"Date": "Observation date", pollutant: pollutant})
    st.plotly_chart(style_chart(fig, f"{pollutant} history · {city}"), use_container_width=True)
    left, right = st.columns(2, gap="large")
    with left:
        panel_heading("Pollutant distributions")
        distribution_columns = [col for col in available if col != "AQI"]
        if distribution_columns:
            selected_dist = st.selectbox("Pollutant distribution", distribution_columns, key="pollutant_distribution")
            st.plotly_chart(style_chart(px.histogram(city_data.dropna(subset=[selected_dist]), x=selected_dist, nbins=35), f"{selected_dist} distribution · {city}"), use_container_width=True)
        else:
            empty_state("No pollutant columns are available.")
    with right:
        panel_heading("Pollutant correlation")
        corr = [col for col in available if city_data[col].notna().sum() > 1]
        if len(corr) > 1:
            fig = px.imshow(city_data[corr].corr(), text_auto=".2f", color_continuous_scale=[[0, "#315A78"], [.5, "#101D22"], [1, COLORS["accent"]]], zmin=-1, zmax=1)
            st.plotly_chart(style_chart(fig, "Pollutant correlation"), use_container_width=True)
        else:
            empty_state("At least two populated measures are needed.")
    panel_heading("Latest AQI by city")
    st.plotly_chart(city_comparison_chart(data), use_container_width=True)


def render_performance(metadata: dict | None, error: str | None) -> None:
    page_header("Model Performance", "Saved validation and held-out test results.")
    path = BASE_DIR / "models" / "metrics.csv"
    if metadata is None or not path.exists():
        st.error(f"Saved evaluation metrics are unavailable: {error or 'metrics.csv is missing.'}")
        return
    metrics = pd.read_csv(path)
    test_rows = metrics[metrics["Partition"] == "Held-out Test"]
    selected = test_rows[test_rows["Model"] == "Selected Model"]
    baseline = test_rows[test_rows["Model"] == "Persistence Baseline"]
    if selected.empty or baseline.empty:
        st.error("Held-out selected-model or persistence metrics are missing from metrics.csv.")
        return
    test = selected.iloc[0]
    base = baseline.iloc[0]
    columns = st.columns(4, gap="medium")
    with columns[0]:
        kpi_card("Selected model MAE", f"{test['MAE']:.2f}", metadata["best_model"] + " · held-out test", COLORS["accent"])
    with columns[1]:
        kpi_card("Persistence MAE", f"{base['MAE']:.2f}", "Held-out test baseline", COLORS["blue"])
    with columns[2]:
        kpi_card("Selected RMSE", f"{test['RMSE']:.2f}", "Held-out test", COLORS["yellow"])
    with columns[3]:
        kpi_card("Selected R²", f"{test['R2']:.3f}", "Held-out test", COLORS["green"])
    dates = metadata.get("date_ranges", {}).get("test", ["unknown", "unknown"])
    st.caption(f"Test period {dates[0]}–{dates[1]} · {len(metadata.get('test_actual', [])):,} city-date rows · selected by validation MAE")
    left, right = st.columns(2, gap="large")
    with left:
        comparison = pd.DataFrame({"Actual AQI": metadata["test_actual"], "Selected model": metadata["test_predictions"], "Persistence baseline": metadata["test_baseline_predictions"]})
        fig = px.scatter(comparison, x="Actual AQI", y="Selected model", opacity=.58, color_discrete_sequence=[COLORS["accent"]])
        low = min(comparison["Actual AQI"].min(), comparison["Selected model"].min())
        high = max(comparison["Actual AQI"].max(), comparison["Selected model"].max())
        fig.add_trace(go.Scatter(x=[low, high], y=[low, high], name="Ideal", mode="lines", line={"color": COLORS["muted"], "dash": "dash"}))
        st.plotly_chart(style_chart(fig, "Held-out test · actual vs predicted"), use_container_width=True)
    with right:
        residuals = comparison["Actual AQI"] - comparison["Selected model"]
        fig = px.histogram(x=residuals, nbins=36, labels={"x": "Actual − predicted AQI"}, color_discrete_sequence=[COLORS["blue"]])
        st.plotly_chart(style_chart(fig, "Held-out test · residual distribution"), use_container_width=True)
    model_rows = metrics[metrics["Partition"] == "Validation"].copy()
    if not model_rows.empty:
        fig = px.bar(model_rows.sort_values("MAE"), x="Model", y="MAE", color="Model", color_discrete_sequence=[COLORS["accent"], COLORS["blue"], COLORS["yellow"], COLORS["orange"]])
        st.plotly_chart(style_chart(fig, "Validation MAE comparison · lower is better"), use_container_width=True)
    st.dataframe(metrics, hide_index=True, use_container_width=True)


def render_alerts(city: str, latest: pd.Series, result: dict | None, alert: dict | None, error: str | None) -> None:
    page_header("Pollution Alerts", "Observed AQI and dated model guidance.")
    observed_category = classify_aqi(float(latest["AQI"]))
    left, right = st.columns(2, gap="large")
    with left:
        color = AQI_COLORS.get(observed_category, COLORS["muted"])
        guidance = build_alert(float(latest["AQI"]), "Observed", pd.Timestamp(latest["Date"]).date())
        st.markdown(f'<div class="aq-card"><div class="aq-kicker">Observed · {pd.Timestamp(latest["Date"]).date()}</div><h3 style="color:{color}">{observed_category} · AQI {float(latest["AQI"]):.0f}</h3><p>{guidance["message"]}</p><small>{city} · city_day.csv</small></div>', unsafe_allow_html=True)
    with right:
        if result and alert:
            color = AQI_COLORS.get(alert["category"], COLORS["muted"])
            st.markdown(f'<div class="aq-card"><div class="aq-kicker">Historical forecast · {pd.Timestamp(result["target_date"]).date()}</div><h3 style="color:{color}">{alert["category"]} · AQI {result["predicted_aqi"]:.0f}</h3><p>{alert["message"]}</p><small>{result["model"]} · origin {pd.Timestamp(result["forecast_origin_date"]).date()}</small></div>', unsafe_allow_html=True)
        else:
            st.warning(f"Forecast alert unavailable: {error or 'No model output.'}")
    st.caption("Historical guidance · not an official CPCB alert or live monitoring.")


def render_explainability(model: object | None, metadata: dict | None, error: str | None) -> None:
    page_header("Explainable AI", "Feature importance for the saved estimator.")
    if model is None or metadata is None:
        st.error(f"Model explanation unavailable: {error or 'Model artifacts are missing.'}")
        return
    estimator = getattr(model, "named_steps", {}).get("model", model)
    importances = getattr(estimator, "feature_importances_", None)
    if importances is None:
        empty_state("The selected estimator does not expose global feature importance.")
        return
    if len(importances) != len(metadata["feature_names"]):
        st.error("Saved feature names do not match estimator importance dimensions.")
        return
    table = pd.DataFrame({"Feature": metadata["feature_names"], "Importance": importances}).sort_values("Importance", ascending=False).head(18)
    fig = px.bar(table.sort_values("Importance"), x="Importance", y="Feature", orientation="h", color_discrete_sequence=[COLORS["accent"]])
    st.plotly_chart(style_chart(fig, "Global feature importance"), use_container_width=True)
    st.caption("Global feature importance · not a local or causal explanation.")


def render_about() -> None:
    page_header("About Project", "Scope, data, and forecasting method.")
    for title, body in {
        "Purpose": "City AQI analysis and next-day model estimates.",
        "Data": "city_day.csv · daily AQI and pollutant measures · 2015-01-01 to 2020-07-01.",
        "Method": "City-scoped lags and rolling features · exact next-day targets · chronological train/validation/test splits · validation-MAE selection.",
        "Models": "Persistence baseline, Linear Regression, Random Forest, and XGBoost when available.",
        "Limits": "Historical only. No live monitoring, confirmed weather features, station coordinates, or calibrated uncertainty.",
        "Next": "Verified recent pollutant data and temporal uncertainty calibration.",
    }.items():
        st.markdown(f'<div class="aq-panel"><div class="aq-panel-title">{title}</div><p>{body}</p></div>', unsafe_allow_html=True)


def main() -> None:
    pages = ["Dashboard", "AQI Prediction", "Pollution Analytics", "Model Performance", "Pollution Alerts", "Explainable AI", "About Project"]
    try:
        data = get_data()
    except (FileNotFoundError, ValueError, OSError) as exc:
        st.error(f"Dataset setup error: {exc}")
        return
    if data.empty:
        empty_state("The dataset contains no valid city/date/AQI records.")
        return
    cities = sorted(data["City"].astype(str).unique())
    default_city = st.session_state.get("selected_city", cities[0])
    if default_city not in cities:
        default_city = cities[0]
    header(default_city, data)
    page = st.radio("Navigation", pages, horizontal=True, label_visibility="collapsed", key="navigation")
    dataset_end = pd.Timestamp(data["Date"].max()).date()
    city = st.session_state.get("selected_city", default_city)
    city_data = data[data["City"].astype(str) == city].sort_values("Date").copy()
    latest, _ = current_context(city_data)
    if latest is None:
        empty_state(f"No usable historical observations are available for {city}.")
        return
    st.caption(f"city_day.csv through {dataset_end} · {city} latest {pd.Timestamp(latest['Date']).date()} · historical data")
    result = model = metadata = alert = error = None
    if page in {"Dashboard", "AQI Prediction", "Pollution Alerts"}:
        result, model, metadata, error = safe_forecast(city, data)
        if result:
            alert = build_alert(result["predicted_aqi"], "Forecast", result["target_date"].date())
    elif page in {"Model Performance", "Explainable AI"}:
        try:
            model, metadata = load_artifacts()
        except (FileNotFoundError, ValueError, OSError) as exc:
            error = str(exc)
    if page == "Dashboard":
        render_dashboard(city, data, city_data, latest, result, metadata if result else error, alert)
    elif page == "AQI Prediction":
        render_prediction(city, city_data, result, error)
    elif page == "Pollution Analytics":
        render_analytics(data, city, city_data)
    elif page == "Model Performance":
        render_performance(metadata, error)
    elif page == "Pollution Alerts":
        render_alerts(city, latest, result, alert, error)
    elif page == "Explainable AI":
        render_explainability(model, metadata, error)
    else:
        render_about()


if __name__ == "__main__":
    main()
