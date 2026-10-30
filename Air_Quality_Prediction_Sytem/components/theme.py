"""Shared white and red dashboard theme and reusable presentation helpers."""

from html import escape

import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "background": "#F7F8FA", "surface": "#FFFFFF", "card": "#FFFFFF",
    "card_alt": "#FFF5F5", "accent": "#C62828", "blue": "#D94A4A",
    "green": "#2E7D32", "yellow": "#B7791F", "orange": "#D97706",
    "red": "#B91C1C", "text": "#1F2937", "muted": "#667085", "border": "#E5E7EB",
}

AQI_COLORS = {
    "Good": COLORS["green"], "Satisfactory": "#547D21",
    "Moderately Polluted": "#8A5A00", "Poor": "#B45309",
    "Very Poor": COLORS["red"], "Severe": "#C95787",
    "Above Standard Scale": "#626D7A", "Invalid": "#626D7A",
}


def apply_theme() -> None:
    """Inject consistent, responsive styling without replacing Streamlit controls."""
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: light; --aq-bg:{COLORS['background']}; --aq-surface:{COLORS['surface']};
          --aq-card:{COLORS['card']}; --aq-accent:{COLORS['accent']}; --aq-text:{COLORS['text']};
          --aq-muted:{COLORS['muted']}; --aq-border:{COLORS['border']}; }}
        .stApp {{ background:var(--aq-bg); color:var(--aq-text); }}
        [data-testid="stHeader"] {{ background:rgba(255,255,255,.94); }}
        [data-testid="stSidebar"] {{ background:#FFFFFF; border-right:1px solid var(--aq-border); }}
        [data-testid="stSidebar"] > div {{ padding-top:1.15rem; }}
        [data-testid="stSidebar"] * {{ color:var(--aq-text); }}
        .block-container {{ max-width:1540px; padding:1.6rem clamp(1rem, 2.7vw, 2.8rem) 3rem; }}
        h1,h2,h3,h4 {{ color:var(--aq-text) !important; letter-spacing:-.025em; }}
        p,li,label,.stCaption {{ color:var(--aq-muted); }}
        [data-testid="stRadio"] > div {{ gap:.18rem; }}
        [data-testid="stRadio"] label {{ border-radius:.55rem; padding:.48rem .65rem; margin:0; }}
        [data-testid="stRadio"] label:hover {{ background:#FFF1F1; }}
        [data-testid="stSelectbox"] label {{ color:var(--aq-muted) !important; font-size:.8rem; }}
        [data-baseweb="select"] > div {{ background:#FFFFFF; border-color:var(--aq-border); min-height:2.6rem; }}
        [data-baseweb="select"] * {{ color:var(--aq-text) !important; }}
        [data-testid="stMetric"] {{ background:var(--aq-card); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.1rem; box-shadow:0 8px 22px rgba(31,41,55,.06); }}
        [data-testid="stMetricLabel"] {{ color:var(--aq-muted) !important; font-size:.78rem; }}
        [data-testid="stMetricValue"] {{ color:var(--aq-text) !important; font-size:1.55rem; }}
        [data-testid="stAlert"] {{ border-radius:12px; }}
        [data-testid="stDataFrame"] {{ border:1px solid var(--aq-border); border-radius:12px; overflow:hidden; }}
        .aq-brand {{ display:flex; align-items:center; gap:.65rem; color:var(--aq-text); font-weight:700; font-size:.93rem; line-height:1.25; }}
        .aq-mark {{ width:31px; height:31px; border-radius:10px; display:grid; place-items:center; background:#FEECEC; color:var(--aq-accent); border:1px solid #F5CACA; font-size:18px; }}
        .aq-side-label {{ color:#8B3030; text-transform:uppercase; letter-spacing:.14em; font-size:.68rem; font-weight:700; margin:1.45rem .4rem .45rem; }}
        .aq-hero {{ display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; padding:.25rem 0 1.2rem; border-bottom:1px solid var(--aq-border); margin-bottom:1.2rem; }}
        .aq-eyebrow {{ color:var(--aq-accent); text-transform:uppercase; letter-spacing:.15em; font-size:.69rem; font-weight:750; margin-bottom:.55rem; }}
        .aq-title {{ color:var(--aq-text); font-weight:740; font-size:clamp(1.55rem, 2.3vw, 2.25rem); letter-spacing:-.045em; line-height:1.14; margin:0; }}
        .aq-subtitle {{ color:var(--aq-muted); font-size:.9rem; margin:.55rem 0 0; }}
        .aq-live {{ color:var(--aq-muted); font-size:.73rem; border:1px solid var(--aq-border); border-radius:999px; padding:.45rem .7rem; white-space:nowrap; }}
        .aq-kpi {{ min-height:132px; height:100%; box-sizing:border-box; background:linear-gradient(145deg, #FFFFFF, #FFF8F8); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.05rem .95rem; position:relative; overflow:hidden; box-shadow:0 8px 22px rgba(31,41,55,.05); }}
        .aq-kpi:before {{ content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--kpi-accent, var(--aq-accent)); }}
        .aq-kpi-label {{ color:var(--aq-muted); font-size:.77rem; font-weight:650; }}
        .aq-kpi-value {{ color:var(--aq-text); font-size:1.65rem; font-weight:760; letter-spacing:-.04em; margin:.55rem 0 .25rem; }}
        .aq-kpi-meta {{ color:var(--aq-muted); font-size:.73rem; }}
        .aq-pill {{ display:inline-flex; margin-left:.35rem; border-radius:999px; padding:.18rem .48rem; color:#FFFFFF; font-size:.67rem; font-weight:750; vertical-align:.15rem; }}
        .aq-panel {{ background:#FFFFFF; border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.05rem; box-shadow:0 8px 22px rgba(31,41,55,.04); }}
        .aq-panel-title {{ color:var(--aq-text); font-size:.96rem; font-weight:700; margin:0 0 .2rem; }}
        .aq-panel-note {{ color:var(--aq-muted); font-size:.73rem; margin:0; }}
        .aq-card {{ background:var(--aq-card); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.15rem; box-shadow:0 8px 22px rgba(31,41,55,.04); }}
        .aq-kicker {{ color:var(--aq-accent); font-size:.7rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; }}
        .aq-empty {{ background:var(--aq-surface); border:1px dashed var(--aq-border); border-radius:12px; color:var(--aq-muted); padding:1rem; }}
        hr {{ border-color:var(--aq-border); }}
        @media(max-width:760px) {{ .aq-hero {{ align-items:flex-start; flex-direction:column; }} .aq-kpi {{ min-height:112px; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str) -> None:
    st.markdown(
        f'<div class="aq-hero"><div><div class="aq-eyebrow">Environmental intelligence</div>'
        f'<h1 class="aq-title">{escape(title)}</h1><p class="aq-subtitle">{escape(description)}</p></div></div>',
        unsafe_allow_html=True,
    )


def chart_layout(title: str) -> dict:
    return {
        "title": {"text": title, "font": {"color": COLORS["text"], "size": 15}, "x": 0.02},
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": COLORS["muted"], "family": "Inter, Segoe UI, sans-serif", "size": 11},
        "margin": {"l": 42, "r": 20, "t": 52, "b": 38},
        "legend": {"font": {"color": COLORS["muted"], "size": 10}, "orientation": "h", "y": 1.08},
        "xaxis": {"gridcolor": "#E9EDF2", "zerolinecolor": "#D7DCE3", "linecolor": COLORS["border"]},
        "yaxis": {"gridcolor": "#E9EDF2", "zerolinecolor": "#D7DCE3", "linecolor": COLORS["border"]},
        "hoverlabel": {"bgcolor": COLORS["card"], "bordercolor": COLORS["border"], "font": {"color": COLORS["text"]}},
    }


def style_chart(figure: go.Figure, title: str) -> go.Figure:
    figure.update_layout(**chart_layout(title), hovermode="closest", showlegend=True)
    return figure


def kpi_card(label: str, value: str, meta: str, accent: str, category: str | None = None) -> None:
    badge = ""
    if category:
        color = AQI_COLORS.get(category, COLORS["muted"])
        badge = f'<span class="aq-pill" style="background:{color}">{escape(category)}</span>'
    st.markdown(
        f'<div class="aq-kpi" style="--kpi-accent:{accent}"><div class="aq-kpi-label">{escape(label)}</div>'
        f'<div class="aq-kpi-value">{escape(value)}{badge}</div><div class="aq-kpi-meta">{escape(meta)}</div></div>',
        unsafe_allow_html=True,
    )


def panel_heading(title: str, note: str = "") -> None:
    st.markdown(f'<div class="aq-panel-title">{escape(title)}</div><p class="aq-panel-note">{escape(note)}</p>', unsafe_allow_html=True)


def empty_state(message: str) -> None:
    st.markdown(f'<div class="aq-empty">{escape(message)}</div>', unsafe_allow_html=True)
