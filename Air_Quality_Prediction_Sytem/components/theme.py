"""Shared navy and teal dashboard theme and reusable presentation helpers."""

from html import escape

import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "background": "#071321", "surface": "#0B1B2D", "card": "#10243A",
    "card_alt": "#0D2034", "accent": "#24D6C2", "blue": "#42B8F5",
    "green": "#38D996", "yellow": "#F6C85F", "orange": "#FF965A",
    "red": "#FB6573", "text": "#EDF6FC", "muted": "#91A8BB", "border": "#1B3851",
}

AQI_COLORS = {
    "Good": COLORS["green"], "Satisfactory": "#92C95B",
    "Moderately Polluted": COLORS["yellow"], "Poor": COLORS["orange"],
    "Very Poor": COLORS["red"], "Severe": "#C95787",
    "Above Standard Scale": "#A5AFBA", "Invalid": "#A5AFBA",
}


def apply_theme() -> None:
    """Inject consistent, responsive styling without replacing Streamlit controls."""
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme: dark; --aq-bg:{COLORS['background']}; --aq-surface:{COLORS['surface']};
          --aq-card:{COLORS['card']}; --aq-accent:{COLORS['accent']}; --aq-text:{COLORS['text']};
          --aq-muted:{COLORS['muted']}; --aq-border:{COLORS['border']}; }}
        .stApp {{ background: radial-gradient(ellipse at 48% -30%, #12314a 0%, var(--aq-bg) 52%); color:var(--aq-text); }}
        [data-testid="stHeader"] {{ background:rgba(7,19,33,.84); }}
        [data-testid="stSidebar"] {{ background:#081827; border-right:1px solid var(--aq-border); }}
        [data-testid="stSidebar"] > div {{ padding-top:1.15rem; }}
        [data-testid="stSidebar"] * {{ color:var(--aq-text); }}
        .block-container {{ max-width:1540px; padding:1.6rem clamp(1rem, 2.7vw, 2.8rem) 3rem; }}
        h1,h2,h3,h4 {{ color:var(--aq-text) !important; letter-spacing:-.025em; }}
        p,li,label,.stCaption {{ color:var(--aq-muted); }}
        [data-testid="stRadio"] > div {{ gap:.18rem; }}
        [data-testid="stRadio"] label {{ border-radius:.55rem; padding:.48rem .65rem; margin:0; }}
        [data-testid="stRadio"] label:hover {{ background:#102a40; }}
        [data-testid="stSelectbox"] label {{ color:var(--aq-muted) !important; font-size:.8rem; }}
        [data-baseweb="select"] > div {{ background:#10243A; border-color:var(--aq-border); min-height:2.6rem; }}
        [data-baseweb="select"] * {{ color:var(--aq-text) !important; }}
        [data-testid="stMetric"] {{ background:var(--aq-card); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.1rem; box-shadow:0 12px 28px rgba(0,0,0,.12); }}
        [data-testid="stMetricLabel"] {{ color:var(--aq-muted) !important; font-size:.78rem; }}
        [data-testid="stMetricValue"] {{ color:var(--aq-text) !important; font-size:1.55rem; }}
        [data-testid="stAlert"] {{ border-radius:12px; }}
        [data-testid="stDataFrame"] {{ border:1px solid var(--aq-border); border-radius:12px; overflow:hidden; }}
        .aq-brand {{ display:flex; align-items:center; gap:.65rem; color:var(--aq-text); font-weight:700; font-size:.93rem; line-height:1.25; }}
        .aq-mark {{ width:31px; height:31px; border-radius:10px; display:grid; place-items:center; background:rgba(36,214,194,.12); color:var(--aq-accent); border:1px solid rgba(36,214,194,.24); font-size:18px; }}
        .aq-side-label {{ color:#68849b; text-transform:uppercase; letter-spacing:.14em; font-size:.68rem; font-weight:700; margin:1.45rem .4rem .45rem; }}
        .aq-hero {{ display:flex; justify-content:space-between; align-items:flex-end; gap:1rem; padding:.25rem 0 1.2rem; border-bottom:1px solid var(--aq-border); margin-bottom:1.2rem; }}
        .aq-eyebrow {{ color:var(--aq-accent); text-transform:uppercase; letter-spacing:.15em; font-size:.69rem; font-weight:750; margin-bottom:.55rem; }}
        .aq-title {{ color:var(--aq-text); font-weight:740; font-size:clamp(1.55rem, 2.3vw, 2.25rem); letter-spacing:-.045em; line-height:1.14; margin:0; }}
        .aq-subtitle {{ color:var(--aq-muted); font-size:.9rem; margin:.55rem 0 0; }}
        .aq-live {{ color:#91a8bb; font-size:.73rem; border:1px solid var(--aq-border); border-radius:999px; padding:.45rem .7rem; white-space:nowrap; }}
        .aq-kpi {{ min-height:132px; height:100%; box-sizing:border-box; background:linear-gradient(145deg, rgba(19,45,67,.98), rgba(13,32,51,.98)); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.05rem .95rem; position:relative; overflow:hidden; }}
        .aq-kpi:before {{ content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--kpi-accent, var(--aq-accent)); }}
        .aq-kpi-label {{ color:#9bb1c3; font-size:.77rem; font-weight:650; }}
        .aq-kpi-value {{ color:var(--aq-text); font-size:1.65rem; font-weight:760; letter-spacing:-.04em; margin:.55rem 0 .25rem; }}
        .aq-kpi-meta {{ color:#849caf; font-size:.73rem; }}
        .aq-pill {{ display:inline-flex; margin-left:.35rem; border-radius:999px; padding:.18rem .48rem; color:#071321; font-size:.67rem; font-weight:750; vertical-align:.15rem; }}
        .aq-panel {{ background:linear-gradient(155deg, rgba(15,36,57,.98), rgba(11,28,45,.98)); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.05rem; }}
        .aq-panel-title {{ color:var(--aq-text); font-size:.96rem; font-weight:700; margin:0 0 .2rem; }}
        .aq-panel-note {{ color:#829bae; font-size:.73rem; margin:0; }}
        .aq-card {{ background:var(--aq-card); border:1px solid var(--aq-border); border-radius:14px; padding:1rem 1.15rem; }}
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
        "xaxis": {"gridcolor": "#19344C", "zerolinecolor": "#19344C", "linecolor": COLORS["border"]},
        "yaxis": {"gridcolor": "#19344C", "zerolinecolor": "#19344C", "linecolor": COLORS["border"]},
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
