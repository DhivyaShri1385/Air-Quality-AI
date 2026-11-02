"""Shared dark environmental theme and reusable dashboard components."""

from html import escape

import plotly.graph_objects as go
import streamlit as st

COLORS = {
    "background": "#05080B", "surface": "#0B1218", "card": "#101C24",
    "card_alt": "#162832", "accent": "#35D6D0", "blue": "#62B7F5",
    "green": "#54D99F", "yellow": "#F5C95E", "orange": "#FF9966",
    "red": "#FF687D", "text": "#F5F7FA", "muted": "#A8B3BF", "border": "#2B3D48",
}

AQI_COLORS = {
    "Good": COLORS["green"], "Satisfactory": "#A8D96D",
    "Moderately Polluted": COLORS["yellow"], "Poor": COLORS["orange"],
    "Very Poor": COLORS["red"], "Severe": "#BF91FF",
    "Above Standard Scale": "#91A6B8", "Invalid": "#91A6B8",
}


def apply_theme() -> None:
    """Apply the responsive black dashboard theme with colorful accents."""
    st.markdown(
        f"""
        <style>
        :root {{ color-scheme:dark; --aq-bg:{COLORS['background']}; --aq-surface:{COLORS['surface']};
          --aq-card:{COLORS['card']}; --aq-accent:{COLORS['accent']}; --aq-text:{COLORS['text']};
          --aq-muted:{COLORS['muted']}; --aq-border:{COLORS['border']}; }}
        html,body,[data-testid="stAppViewContainer"] {{ background:var(--aq-bg); color:var(--aq-text); }}
        *,*::before,*::after {{ box-sizing:border-box; }}
        html,body {{ overflow-x:hidden; }}
        .stApp {{ background:radial-gradient(ellipse at 12% 0%, rgba(53,214,208,.08), transparent 34%),
          radial-gradient(ellipse at 92% 8%, rgba(98,183,245,.07), transparent 30%),var(--aq-bg); color:var(--aq-text); overflow-x:hidden; }}
        [data-testid="stHeader"] {{ background:rgba(5,8,11,.92); }}
        [data-testid="stSidebar"] {{ display:none; }}
        .block-container {{ width:100%; max-width:1420px; padding:1.1rem clamp(.9rem, 2.5vw, 2.4rem) 2.4rem; }}
        h1,h2,h3,h4 {{ color:var(--aq-text) !important; letter-spacing:-.025em; }}
        p,li,label,.stCaption {{ color:var(--aq-muted); line-height:1.45; }}
        [data-testid="stSelectbox"] label,[data-testid="stDateInput"] label,[data-testid="stTextInput"] label {{ color:var(--aq-muted) !important; font-size:.8rem; }}
        [data-baseweb="select"] > div,[data-baseweb="input"] > div,[data-baseweb="base-input"] {{ background:#11151A; border-color:var(--aq-border); min-height:2.65rem; }}
        [data-baseweb="select"] *,[data-baseweb="input"] input,[data-baseweb="base-input"] input {{ color:var(--aq-text) !important; }}
        input::placeholder {{ color:#71819A !important; }}
        [data-testid="stButton"] button,[data-testid="stFormSubmitButton"] button {{ background:linear-gradient(120deg,#35D6D0,#62B7F5); color:#061114; border:0; border-radius:10px; font-weight:750; min-height:2.65rem; }}
        [data-testid="stButton"] button:hover,[data-testid="stFormSubmitButton"] button:hover {{ filter:brightness(1.08); color:#061114; border:0; }}
        [data-testid="stRadio"] {{ margin:.45rem 0 1.4rem; }}
        [data-testid="stRadio"] > div[role="radiogroup"] {{ display:flex; flex-wrap:wrap; gap:.3rem; width:100%; padding:.38rem; background:rgba(11,18,24,.94); border:1px solid var(--aq-border); border-radius:14px; }}
        [data-testid="stRadio"] label {{ flex:1 1 auto; justify-content:center; border-radius:10px; padding:.58rem .78rem; margin:0; color:var(--aq-muted); transition:background .16s ease,color .16s ease; }}
        [data-testid="stRadio"] label:hover {{ background:#16272D; color:var(--aq-text); }}
        [data-testid="stRadio"] label:has(input:checked) {{ background:linear-gradient(120deg,rgba(53,214,208,.2),rgba(98,183,245,.15)); color:var(--aq-text); box-shadow:inset 0 0 0 1px rgba(53,214,208,.45); }}
        [data-testid="stMetric"] {{ background:var(--aq-card); border:1px solid var(--aq-border); border-radius:15px; padding:1rem 1.1rem; box-shadow:0 12px 32px rgba(0,0,0,.18); }}
        [data-testid="stMetricLabel"] {{ color:var(--aq-muted) !important; font-size:.78rem; }}
        [data-testid="stMetricValue"] {{ color:var(--aq-text) !important; font-size:1.55rem; }}
        [data-testid="stAlert"] {{ background:#171B20; color:var(--aq-text); border:1px solid var(--aq-border); border-radius:12px; }}
        [data-testid="stDataFrame"] {{ border:1px solid var(--aq-border); border-radius:12px; overflow:hidden; }}
        [data-testid="stForm"] {{ background:rgba(11,18,24,.88); border:1px solid var(--aq-border); border-radius:15px; padding:.85rem 1rem; }}
        .aq-brand {{ display:flex; align-items:center; gap:.65rem; color:var(--aq-text); font-weight:750; font-size:1rem; line-height:1.25; }}
        .aq-mark {{ width:34px; height:34px; border-radius:11px; display:grid; place-items:center; background:linear-gradient(140deg,#35D6D0,#62B7F5); color:#061114; border:1px solid rgba(255,255,255,.16); font-size:.72rem; font-weight:850; }}
        .aq-hero {{ display:flex; justify-content:space-between; align-items:flex-end; gap:.8rem; padding:.25rem 0 .8rem; border-bottom:1px solid var(--aq-border); margin-bottom:.85rem; }}
        .aq-title {{ color:var(--aq-text); font-weight:760; font-size:clamp(1.45rem, 2.2vw, 2rem); letter-spacing:-.04em; line-height:1.12; margin:0; }}
        .aq-subtitle {{ color:var(--aq-muted); font-size:.84rem; margin:.35rem 0 0; }}
        .aq-live {{ color:var(--aq-muted); font-size:.73rem; border:1px solid var(--aq-border); border-radius:999px; padding:.45rem .7rem; white-space:nowrap; }}
        .aq-kpi {{ min-height:108px; height:100%; background:linear-gradient(145deg,#14242A,#0C1418); border:1px solid var(--aq-border); border-radius:14px; padding:.82rem .95rem; position:relative; overflow:hidden; box-shadow:0 10px 24px rgba(0,0,0,.22); }}
        .aq-kpi:before {{ content:""; position:absolute; inset:0 auto 0 0; width:3px; background:var(--kpi-accent,var(--aq-accent)); }}
        .aq-kpi-label {{ color:var(--aq-muted); font-size:.77rem; font-weight:650; }}
        .aq-kpi-value {{ color:var(--aq-text); font-size:1.65rem; font-weight:760; letter-spacing:-.04em; margin:.55rem 0 .25rem; }}
        .aq-kpi-meta {{ color:var(--aq-muted); font-size:.73rem; }}
        .aq-pill {{ display:inline-flex; margin-left:.35rem; border-radius:999px; padding:.18rem .48rem; color:#000000; font-size:.67rem; font-weight:800; vertical-align:.15rem; }}
        .aq-panel {{ background:rgba(11,18,24,.9); border:1px solid var(--aq-border); border-radius:14px; padding:.82rem .9rem; box-shadow:0 10px 24px rgba(0,0,0,.18); }}
        .aq-panel-title {{ color:var(--aq-text); font-size:.92rem; font-weight:700; margin:0 0 .12rem; }}
        .aq-panel-note {{ color:var(--aq-muted); font-size:.7rem; margin:0; }}
        .aq-card {{ background:linear-gradient(145deg,#14242A,#0C1418); border:1px solid var(--aq-border); border-radius:14px; padding:.9rem 1rem; box-shadow:0 10px 24px rgba(0,0,0,.22); }}
        .aq-kicker {{ color:var(--aq-accent); font-size:.67rem; font-weight:750; letter-spacing:.08em; text-transform:uppercase; }}
        .aq-forecast-hero {{ position:relative; overflow:hidden; display:flex; justify-content:space-between; align-items:center; gap:1rem; margin:0 0 1rem; padding:1rem clamp(1rem,2.5vw,1.6rem); border:1px solid rgba(53,214,208,.28); border-radius:17px; background:radial-gradient(circle at 88% 10%,rgba(53,214,208,.1),transparent 30%),linear-gradient(120deg,#14252B,#0C1418 68%,#101B20); box-shadow:0 14px 36px rgba(0,0,0,.3); }}
        .aq-forecast-hero-main,.aq-forecast-hero-meta {{ position:relative; z-index:1; }}
        .aq-forecast-number {{ color:#F4FBFC; font-size:clamp(2.7rem,5.2vw,4.4rem); line-height:.95; font-weight:800; letter-spacing:-.07em; margin:.35rem 0 .45rem; }}
        .aq-forecast-number span {{ color:var(--aq-muted); font-size:1rem; font-weight:650; letter-spacing:.02em; margin-left:.5rem; }}
        .aq-forecast-meta-label {{ color:var(--aq-muted); font-size:.68rem; text-transform:uppercase; letter-spacing:.14em; }}
        .aq-forecast-meta-value {{ color:var(--aq-text); font-size:1rem; font-weight:700; margin:.2rem 0 .65rem; overflow-wrap:anywhere; }}
        .aq-empty {{ background:var(--aq-surface); border:1px dashed var(--aq-border); border-radius:12px; color:var(--aq-muted); padding:1rem; }}
        hr {{ border-color:var(--aq-border); }}
        @media(max-width:760px) {{ .aq-hero {{ align-items:flex-start; flex-direction:column; }} .aq-kpi {{ min-height:96px; }} .aq-forecast-hero {{ align-items:flex-start; flex-direction:column; }} .aq-forecast-hero-meta {{ display:flex; flex-wrap:wrap; gap:.5rem 1rem; }} .aq-forecast-meta-value {{ margin:0; }} [data-testid="stRadio"] label {{ flex:1 1 42%; }} [data-testid="stFormSubmitButton"] button {{ width:100%; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, description: str) -> None:
    st.markdown(
        f'<div class="aq-hero"><div><h1 class="aq-title">{escape(title)}</h1>'
        f'<p class="aq-subtitle">{escape(description)}</p></div></div>',
        unsafe_allow_html=True,
    )


def chart_layout(title: str) -> dict:
    return {
        "title": {"text": title, "font": {"color": COLORS["text"], "size": 15}, "x": 0.02},
        "paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": COLORS["muted"], "family": "Inter, Segoe UI, sans-serif", "size": 11},
        "margin": {"l": 42, "r": 20, "t": 52, "b": 38},
        "legend": {"font": {"color": COLORS["muted"], "size": 10}, "orientation": "h", "y": 1.08},
        "xaxis": {"gridcolor": "#242424", "zerolinecolor": "#363636", "linecolor": COLORS["border"]},
        "yaxis": {"gridcolor": "#242424", "zerolinecolor": "#363636", "linecolor": COLORS["border"]},
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


def forecast_hero(aqi: float, target_date: str, category: str, model: str, title: str, note: str = "") -> None:
    """Render the prominent AQI forecast card used on dashboard and prediction views."""
    color = AQI_COLORS.get(category, COLORS["accent"])
    st.markdown(
        f'<section class="aq-forecast-hero"><div class="aq-forecast-hero-main">'
        f'<div class="aq-kicker">{escape(title)}</div>'
        f'<div class="aq-forecast-number">{float(aqi):.0f}<span>AQI</span></div>'
        f'<span class="aq-pill" style="background:{color}">{escape(category)}</span>'
        f'<div class="aq-subtitle">{escape(note)}</div></div>'
        f'<div class="aq-forecast-hero-meta"><div class="aq-forecast-meta-label">Target date</div>'
        f'<div class="aq-forecast-meta-value">{escape(str(target_date))}</div>'
        f'<div class="aq-forecast-meta-label">Model</div><div class="aq-forecast-meta-value">{escape(str(model))}</div></div></section>',
        unsafe_allow_html=True,
    )


def panel_heading(title: str, note: str = "") -> None:
    st.markdown(f'<div class="aq-panel-title">{escape(title)}</div><p class="aq-panel-note">{escape(note)}</p>', unsafe_allow_html=True)


def empty_state(message: str) -> None:
    st.markdown(f'<div class="aq-empty">{escape(message)}</div>', unsafe_allow_html=True)
