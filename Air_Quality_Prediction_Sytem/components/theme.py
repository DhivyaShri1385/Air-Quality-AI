"""Centralized visual system for the Streamlit dashboard."""

import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "background": "#0B1220",
    "surface": "#111C2E",
    "card": "#17263B",
    "accent": "#00D4AA",
    "blue": "#38BDF8",
    "text": "#F8FAFC",
    "muted": "#CBD5E1",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "border": "#2A3B54",
}


def apply_theme() -> None:
    """Apply one idempotent stylesheet for all dashboard pages."""
    st.markdown(
        f"""
        <style>
        :root {{
            --aq-background: {COLORS["background"]};
            --aq-surface: {COLORS["surface"]};
            --aq-card: {COLORS["card"]};
            --aq-accent: {COLORS["accent"]};
            --aq-blue: {COLORS["blue"]};
            --aq-text: {COLORS["text"]};
            --aq-muted: {COLORS["muted"]};
            --aq-border: {COLORS["border"]};
        }}
        .stApp {{ background: var(--aq-background); color: var(--aq-text); }}
        [data-testid="stHeader"] {{ background: transparent; }}
        [data-testid="stSidebar"] {{
            background: var(--aq-surface);
            border-right: 1px solid var(--aq-border);
        }}
        [data-testid="stSidebar"] * {{ color: var(--aq-text); }}
        .block-container {{ padding-top: 2rem; padding-bottom: 3rem; }}
        h1, h2, h3, h4 {{ color: var(--aq-text) !important; letter-spacing: -0.02em; }}
        p, li, label, .stCaption {{ color: var(--aq-muted); }}
        [data-testid="stMetric"] {{
            background: var(--aq-card);
            border: 1px solid var(--aq-border);
            border-radius: 0.75rem;
            padding: 1rem;
        }}
        [data-testid="stMetricLabel"] {{ color: var(--aq-muted) !important; }}
        [data-testid="stMetricValue"] {{ color: var(--aq-text) !important; }}
        [data-testid="stSelectbox"] label, [data-testid="stRadio"] label {{ color: var(--aq-muted) !important; }}
        [data-baseweb="select"] > div {{
            background: var(--aq-card);
            border-color: var(--aq-border);
            color: var(--aq-text);
        }}
        [data-baseweb="select"] * {{ color: var(--aq-text) !important; }}
        [data-testid="stAlert"] {{ border-radius: 0.65rem; }}
        .aq-card {{
            background: var(--aq-card);
            border: 1px solid var(--aq-border);
            border-radius: 0.75rem;
            padding: 1.15rem 1.25rem;
            margin: 0.5rem 0 1rem;
        }}
        .aq-card h3 {{ margin: 0 0 0.45rem; color: var(--aq-text); }}
        .aq-card p {{ margin: 0; color: var(--aq-muted); }}
        .aq-kicker {{
            color: var(--aq-accent);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}
        .aq-empty {{
            background: var(--aq-surface);
            border: 1px dashed var(--aq-border);
            border-radius: 0.65rem;
            color: var(--aq-muted);
            padding: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str) -> None:
    st.markdown('<div class="aq-kicker">Air Quality AI</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(description)


def chart_layout(title: str) -> dict:
    return {
        "title": {"text": title, "font": {"color": COLORS["text"], "size": 20}},
        "paper_bgcolor": COLORS["card"],
        "plot_bgcolor": COLORS["card"],
        "font": {"color": COLORS["muted"]},
        "margin": {"l": 55, "r": 25, "t": 65, "b": 50},
        "legend": {"font": {"color": COLORS["muted"]}},
        "xaxis": {"gridcolor": COLORS["border"], "zerolinecolor": COLORS["border"]},
        "yaxis": {"gridcolor": COLORS["border"], "zerolinecolor": COLORS["border"]},
    }


def style_chart(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(**chart_layout(title), hovermode="x unified")
    return figure


def empty_state(message: str) -> None:
    st.markdown(f'<div class="aq-empty">{message}</div>', unsafe_allow_html=True)
