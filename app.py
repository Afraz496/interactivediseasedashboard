# ============================================================
# 🦠 Metro Vancouver COVID Outbreak Forecaster
# ML-powered time series forecasting with live student voting
# ============================================================

import io
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import qrcode
import streamlit as st
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

APP_TITLE  = "Metro Vancouver COVID Forecaster"
PUBLIC_URL = "https://afrazmathapp.streamlit.app"
VOTE_URL   = f"{PUBLIC_URL}?mode=vote"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# GLOBAL STYLES
# ──────────────────────────────────────────────

st.markdown("""
<style>
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
    background-color: #04060f !important;
    color: #dde3f0;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 4rem; max-width: 100%; }

/* ── Metric cards ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #090d1e;
    border: 1px solid #1a2240;
    border-radius: 12px;
    padding: 16px 18px;
}
.metric-card .label {
    font-size: 10px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    color: #4a5680;
    margin-bottom: 6px;
}
.metric-card .value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -1.5px;
    line-height: 1;
}
.metric-card .sub {
    font-size: 11px;
    color: #3a4560;
    margin-top: 5px;
}

/* ── Section labels ── */
.section-label {
    font-size: 10px;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: #3a4a70;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1a2240;
}

/* ── Header ── */
.app-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24px;
    padding-bottom: 20px;
    border-bottom: 1px solid #0e1530;
}
.header-left h1 {
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -1px;
    color: #e8eeff;
    margin: 0;
}
.header-left p {
    font-size: 12px;
    color: #3a4a70;
    margin: 4px 0 0;
    letter-spacing: .5px;
}
.live-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #ef4444;
    margin-right: 6px;
    animation: blink 1.8s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }

/* ── Before/After comparison strip ── */
.compare-strip {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 1rem;
}
.compare-card {
    border-radius: 10px;
    padding: 14px 16px;
}
.before-card { background:#100b00; border:1px solid #2a1800; }
.after-card  { background:#000f1a; border:1px solid #003050; }
.compare-card .c-label {
    font-size: 10px;
    letter-spacing: 1.2px;
    text-transform: uppercase;
    margin-bottom: 10px;
    font-weight: 600;
}
.compare-card .c-row {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: #4a5680;
    padding: 3px 0;
}
.compare-card .c-row span { font-family:'JetBrains Mono',monospace; font-weight:600; }

/* ── Insight banner ── */
.insight-banner {
    background: #070b1a;
    border-left: 3px solid #1e4080;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    font-size: 13px;
    color: #6878a0;
    line-height: 1.7;
    margin-top: 1rem;
}
.insight-banner b { color: #8898c0; }

/* ── Vote option pills ── */
div[data-testid="stRadio"] > label {
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #3a4a70;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
div[data-testid="stRadio"] label {
    background: #090d1e;
    border: 1px solid #1a2240;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    color: #7888b0;
    cursor: pointer;
    transition: all .1s;
    letter-spacing: normal;
    text-transform: none;
}
div[data-testid="stRadio"] label:hover { border-color: #2a4080; color: #aabbd0; }
div[data-testid="stRadio"] label[data-checked="true"] {
    background: #0a1a35;
    border-color: #1a6090;
    color: #60aadf;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: .5px;
    border-radius: 8px;
    padding: 10px 0;
    width: 100%;
    transition: all .12s;
}

/* ── Sliders ── */
div[data-testid="stSlider"] label {
    font-size: 11px;
    letter-spacing: .8px;
    text-transform: uppercase;
    color: #3a4a70;
}
div[data-testid="stSlider"] div[data-testid="stTickBarMin"],
div[data-testid="stSlider"] div[data-testid="stTickBarMax"] {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: #2a3450;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: #070b1a !important;
    border-right: 1px solid #0e1530;
}

/* ── Plotly chart background fix ── */
.js-plotly-plot .plotly { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────

defaults = {
    "session_open":   False,
    "votes_cast":     0,
    "voted":          False,
    "before_metrics": None,
    "vote_mask":      "None (0%)",
    "vote_distance":  "None",
    "vote_vaccine":   "0%",
    "vote_closure":   "Open",
    "vote_testing":   "Low",
    "applied":        False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────
# ML FORECASTING ENGINE
# ──────────────────────────────────────────────

# Realistic BC COVID historical anchor data (weekly new cases, relative scale)
# Anchored to approximate Metro Vancouver waves (2020-2022 shape, normalised)
HISTORICAL_WEEKS = 26  # 6 months of history shown
FORECAST_WEEKS   = 12  # 3 months forecast

def generate_historical(seed: int = 42) -> np.ndarray:
    """Synthetic but realistic historical weekly case counts for Metro Vancouver."""
    rng = np.random.default_rng(seed)
    t   = np.linspace(0, 1, HISTORICAL_WEEKS)
    # Two overlapping waves + noise
    wave1 = 2000 * np.exp(-((t - 0.25) ** 2) / 0.02)
    wave2 = 3500 * np.exp(-((t - 0.70) ** 2) / 0.03)
    base  = 400 + wave1 + wave2
    noise = rng.normal(0, 120, HISTORICAL_WEEKS)
    return np.clip(base + noise, 50, None).astype(float)

# ── Exponential Smoothing (Holt-Winters additive) ──────────────────────────

def holt_winters(series: np.ndarray, n_ahead: int,
                 alpha: float = 0.35, beta: float = 0.15,
                 season_len: int = 4) -> np.ndarray:
    """Simple additive Holt-Winters with weekly seasonality."""
    n = len(series)
    level   = series[:season_len].mean()
    trend   = (series[season_len:2*season_len].mean() - level) / season_len
    seasons = series[:season_len] - level

    for t in range(n):
        s_idx = t % season_len
        prev_level = level
        level  = alpha * (series[t] - seasons[s_idx]) + (1 - alpha) * (level + trend)
        trend  = beta  * (level - prev_level)           + (1 - beta)  * trend
        seasons[s_idx] = series[t] - prev_level

    forecast = np.zeros(n_ahead)
    for i in range(n_ahead):
        forecast[i] = level + (i + 1) * trend + seasons[(n + i) % season_len]
    return np.clip(forecast, 0, None)

# ── Linear regression on recent trend ─────────────────────────────────────

def linear_trend(series: np.ndarray, n_ahead: int, window: int = 8) -> np.ndarray:
    tail = series[-window:]
    x    = np.arange(window, dtype=float)
    xm, ym = x.mean(), tail.mean()
    slope  = np.sum((x - xm) * (tail - ym)) / np.sum((x - xm) ** 2)
    intercept = ym - slope * xm
    fut = np.arange(window, window + n_ahead, dtype=float)
    return np.clip(intercept + slope * fut, 0, None)

# ── Weighted ensemble ──────────────────────────────────────────────────────

def ensemble_forecast(series: np.ndarray, n_ahead: int,
                      hw_weight: float = 0.65) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hw   = holt_winters(series, n_ahead)
    lt   = linear_trend(series, n_ahead)
    mean = hw_weight * hw + (1 - hw_weight) * lt
    # Uncertainty grows with horizon (±1 std band)
    sigma = mean * (0.06 + 0.012 * np.arange(n_ahead))
    return mean, mean - sigma, mean + sigma

# ── Parameter → multiplier mapping ────────────────────────────────────────

MASK_EFFECT      = {"None (0%)": 1.0, "Low (25%)": 0.87, "Medium (60%)": 0.70, "High (90%)": 0.52}
DISTANCE_EFFECT  = {"None": 1.0, "Mild": 0.90, "Moderate": 0.76, "Strict": 0.60}
VACCINE_EFFECT   = {"0%": 1.0, "30%": 0.82, "60%": 0.62, "90%": 0.38}
CLOSURE_EFFECT   = {"Open": 1.0, "Partial": 0.83, "Full": 0.65}
TESTING_EFFECT   = {"Low": 1.0, "Moderate": 0.93, "High": 0.88}   # testing affects *detected* count

def compute_multiplier(mask, distance, vaccine, closure, testing) -> float:
    return (
        MASK_EFFECT[mask]
        * DISTANCE_EFFECT[distance]
        * VACCINE_EFFECT[vaccine]
        * CLOSURE_EFFECT[closure]
        * TESTING_EFFECT[testing]
    )

def apply_interventions(base_fc: np.ndarray, lo: np.ndarray, hi: np.ndarray,
                        mult: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Gradually ramp intervention effect in over 4 weeks (policy lag)."""
    ramp = np.linspace(1.0, mult, min(4, len(base_fc)))
    full = np.full(len(base_fc), mult)
    full[:len(ramp)] = ramp
    return base_fc * full, lo * full, hi * full

def metrics_from(fc: np.ndarray) -> dict:
    peak_val  = int(fc.max())
    peak_week = int(fc.argmax()) + 1
    total     = int(fc.sum())
    trend     = "↓ Declining" if fc[-1] < fc[0] else "↑ Growing"
    trend_pct = abs(fc[-1] - fc[0]) / (fc[0] + 1e-6) * 100
    return {
        "peak_val":   peak_val,
        "peak_week":  peak_week,
        "total":      total,
        "trend":      trend,
        "trend_pct":  round(trend_pct, 1),
        "week12":     int(fc[-1]),
    }

# ──────────────────────────────────────────────
# QR CODE
# ──────────────────────────────────────────────

@st.cache_data
def make_qr(url: str) -> bytes:
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()

qr_bytes = make_qr(VOTE_URL)

# ──────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────

history   = generate_historical()
base_fc, base_lo, base_hi = ensemble_forecast(history, FORECAST_WEEKS)
start_date = datetime(2024, 1, 1)
hist_dates = [start_date + timedelta(weeks=i) for i in range(HISTORICAL_WEEKS)]
fc_dates   = [hist_dates[-1] + timedelta(weeks=i+1) for i in range(FORECAST_WEEKS)]
date_labels_hist = [d.strftime("%b %d") for d in hist_dates]
date_labels_fc   = [d.strftime("%b %d") for d in fc_dates]

# ──────────────────────────────────────────────
# COMPUTE CURRENT FORECAST (with votes applied)
# ──────────────────────────────────────────────

mult = compute_multiplier(
    st.session_state.vote_mask,
    st.session_state.vote_distance,
    st.session_state.vote_vaccine,
    st.session_state.vote_closure,
    st.session_state.vote_testing,
)

if st.session_state.applied:
    cur_fc, cur_lo, cur_hi = apply_interventions(base_fc.copy(), base_lo.copy(), base_hi.copy(), mult)
else:
    cur_fc, cur_lo, cur_hi = base_fc.copy(), base_lo.copy(), base_hi.copy()

cur_m  = metrics_from(cur_fc)
base_m = metrics_from(base_fc)
before_m = st.session_state.before_metrics or base_m

# ──────────────────────────────────────────────
# PLOTLY CHART
# ──────────────────────────────────────────────

def build_chart(history, base_fc, base_lo, base_hi,
                cur_fc, cur_lo, cur_hi,
                hist_dates, fc_dates, applied, before_m):

    fig = go.Figure()

    all_dates_str = date_labels_hist + date_labels_fc

    # Confidence band (current)
    fig.add_trace(go.Scatter(
        x=date_labels_fc + date_labels_fc[::-1],
        y=list(cur_hi) + list(cur_lo[::-1]),
        fill='toself',
        fillcolor='rgba(30,100,200,0.08)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip',
        name='CI band',
    ))

    # Baseline dashed (only if interventions applied)
    if applied:
        fig.add_trace(go.Scatter(
            x=date_labels_fc,
            y=base_fc,
            mode='lines',
            name='Baseline (no intervention)',
            line=dict(color='rgba(240,150,50,0.55)', width=1.5, dash='dot'),
            hovertemplate='<b>Baseline</b>: %{y:,.0f}<extra></extra>',
        ))

    # Historical
    fig.add_trace(go.Scatter(
        x=date_labels_hist,
        y=history,
        mode='lines+markers',
        name='Historical cases',
        line=dict(color='#4a6080', width=1.5),
        marker=dict(size=3, color='#4a6080'),
        hovertemplate='<b>%{x}</b><br>Cases: %{y:,.0f}<extra></extra>',
    ))

    # Forecast
    fc_color = '#1a8fd1' if not applied else ('#22c55e' if mult < 0.75 else '#f59e0b' if mult < 0.92 else '#ef4444')
    fig.add_trace(go.Scatter(
        x=date_labels_fc,
        y=cur_fc,
        mode='lines+markers',
        name='ML Forecast',
        line=dict(color=fc_color, width=2.5),
        marker=dict(size=4, color=fc_color),
        hovertemplate='<b>%{x}</b><br>Forecast: %{y:,.0f}<extra></extra>',
    ))

    # Vertical "today" line — use shapes instead of add_vline (categorical x-axis)
    now_x = date_labels_hist[-1]
    fig.update_layout(
        shapes=[dict(
            type="line",
            xref="x", yref="paper",
            x0=now_x, x1=now_x,
            y0=0, y1=1,
            line=dict(color='rgba(255,255,255,0.1)', width=1, dash='dash'),
        )],
        annotations=[dict(
            xref="x", yref="paper",
            x=now_x, y=1.01,
            text="NOW",
            showarrow=False,
            font=dict(size=9, color='rgba(255,255,255,0.3)'),
            xanchor="left",
        )],
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        height=340,
        font=dict(family='Syne, sans-serif', color='#4a5680', size=11),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='left', x=0,
            font=dict(size=10, color='#4a5680'),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.03)',
            tickcolor='rgba(0,0,0,0)', linecolor='rgba(255,255,255,0.05)',
            tickfont=dict(size=10),
            tickangle=-30,
        ),
        yaxis=dict(
            showgrid=True, gridcolor='rgba(255,255,255,0.03)',
            tickcolor='rgba(0,0,0,0)', linecolor='rgba(255,255,255,0.05)',
            tickfont=dict(size=10),
            tickformat=',d',
        ),
        hovermode='x unified',
    )

    return fig

# ──────────────────────────────────────────────
# LAYOUT
# ──────────────────────────────────────────────

# ── Header ─────────────────────────────────────
status_tag = "VOTING OPEN" if st.session_state.session_open else "SESSION CLOSED"
status_col = "#22c55e" if st.session_state.session_open else "#3a4a70"

st.markdown(f"""
<div class="app-header">
  <div class="header-left">
    <h1><span class="live-dot"></span>Metro Vancouver COVID Forecaster</h1>
    <p>ML TIME-SERIES ENSEMBLE &nbsp;·&nbsp; HOLT-WINTERS + LINEAR TREND &nbsp;·&nbsp;
       <span style="color:{status_col};font-weight:700;letter-spacing:1px">{status_tag}</span>
       &nbsp;·&nbsp; {st.session_state.votes_cast} VOTES CAST</p>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Metric strip ────────────────────────────────
peak_change   = cur_m["peak_val"]  - base_m["peak_val"]
total_change  = cur_m["total"]     - base_m["total"]
peak_arrow    = "↓" if peak_change  < 0 else ("↑" if peak_change  > 0 else "—")
total_arrow   = "↓" if total_change < 0 else ("↑" if total_change > 0 else "—")
peak_col      = "#22c55e" if peak_change  < 0 else ("#ef4444" if peak_change  > 0 else "#4a6080")
total_col     = "#22c55e" if total_change < 0 else ("#ef4444" if total_change > 0 else "#4a6080")

trend_color   = "#22c55e" if "↓" in cur_m["trend"] else "#ef4444"
mult_pct      = round((1 - mult) * 100, 1)

st.markdown(f"""
<div class="metric-grid">
  <div class="metric-card">
    <div class="label">Peak weekly cases</div>
    <div class="value" style="color:{peak_col}">{cur_m['peak_val']:,}</div>
    <div class="sub">Wk {cur_m['peak_week']} &nbsp;{peak_arrow} {abs(peak_change):,} vs baseline</div>
  </div>
  <div class="metric-card">
    <div class="label">12-week total</div>
    <div class="value" style="color:{total_col}">{cur_m['total']:,}</div>
    <div class="sub">{total_arrow} {abs(total_change):,} vs baseline</div>
  </div>
  <div class="metric-card">
    <div class="label">Forecast trend</div>
    <div class="value" style="color:{trend_color};font-size:18px">{cur_m['trend']}</div>
    <div class="sub">{cur_m['trend_pct']}% over 12 weeks</div>
  </div>
  <div class="metric-card">
    <div class="label">Intervention effect</div>
    <div class="value" style="color:#38bdf8">−{mult_pct}%</div>
    <div class="sub">Combined vote multiplier: ×{mult:.2f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout ───────────────────────────
col_main, col_side = st.columns([2.6, 1], gap="large")

with col_main:
    st.markdown('<div class="section-label">ML Forecast · Weekly new cases · Metro Vancouver</div>', unsafe_allow_html=True)
    fig = build_chart(
        history, base_fc, base_lo, base_hi,
        cur_fc, cur_lo, cur_hi,
        hist_dates, fc_dates,
        st.session_state.applied,
        before_m,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ── Before / After comparison ──────────────────
    st.markdown('<div class="section-label">Before / After intervention</div>', unsafe_allow_html=True)

    bm = before_m
    cm = cur_m
    bpeak_d = f"{'↓' if cm['peak_val']  < bm['peak_val']  else '↑'} {abs(cm['peak_val']  - bm['peak_val']):,}"
    btotal_d = f"{'↓' if cm['total']     < bm['total']     else '↑'} {abs(cm['total']     - bm['total']):,}"
    bwk12_d  = f"{'↓' if cm['week12']   < bm['week12']    else '↑'} {abs(cm['week12']    - bm['week12']):,}"
    b_mult_d = f"×{1.0:.2f}"
    a_mult_d = f"×{mult:.2f}"

    st.markdown(f"""
<div class="compare-strip">
  <div class="compare-card before-card">
    <div class="c-label" style="color:#c2621a">◈ Before votes (baseline)</div>
    <div class="c-row">Peak weekly cases   <span style="color:#d07030">{bm['peak_val']:,}</span></div>
    <div class="c-row">12-week total       <span style="color:#d07030">{bm['total']:,}</span></div>
    <div class="c-row">Wk 12 cases         <span style="color:#d07030">{bm['week12']:,}</span></div>
    <div class="c-row">Multiplier          <span style="color:#d07030">{b_mult_d}</span></div>
  </div>
  <div class="compare-card after-card">
    <div class="c-label" style="color:#1a90d1">◈ After votes (current)</div>
    <div class="c-row">Peak weekly cases   <span style="color:#30a8e0">{cm['peak_val']:,} &nbsp;<small>{bpeak_d}</small></span></div>
    <div class="c-row">12-week total       <span style="color:#30a8e0">{cm['total']:,} &nbsp;<small>{btotal_d}</small></span></div>
    <div class="c-row">Wk 12 cases         <span style="color:#30a8e0">{cm['week12']:,} &nbsp;<small>{bwk12_d}</small></span></div>
    <div class="c-row">Multiplier          <span style="color:#30a8e0">{a_mult_d}</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── ML model explainer ─────────────────────────
    st.markdown(f"""
<div class="insight-banner">
<b>How the ML model works:</b> The forecast is a <b>weighted ensemble</b> of two algorithms: 
<b>Holt-Winters exponential smoothing</b> (65% weight) captures level, trend, and 4-week 
seasonal cycles in recent case data. A <b>linear trend regressor</b> (35%) projects the 
slope of the last 8 weeks forward. Intervention votes apply a <b>multiplier</b> to the 
forecast with a 4-week policy lag — matching real-world delay between mandate and effect. 
Shaded bands show ±1σ model uncertainty, which widens at longer horizons.
</div>
""", unsafe_allow_html=True)

with col_side:
    # ── QR + session control ────────────────────────
    st.markdown('<div class="section-label">Scan to vote</div>', unsafe_allow_html=True)
    st.image(qr_bytes, width=160)
    st.caption(VOTE_URL)

    st.markdown("---")
    st.markdown('<div class="section-label">Session</div>', unsafe_allow_html=True)

    if st.session_state.session_open:
        if st.button("🔴  Close voting session", use_container_width=True, type="primary"):
            st.session_state.session_open = False
            st.rerun()
        st.markdown(
            f'<div style="font-size:11px;color:#22c55e;text-align:center;margin-top:6px;">'
            f'✓ Open · {st.session_state.votes_cast} votes received</div>',
            unsafe_allow_html=True,
        )
    else:
        if st.button("▶  Open voting session", use_container_width=True):
            st.session_state.session_open  = True
            st.session_state.applied       = False
            st.session_state.before_metrics = base_m
            st.rerun()
        st.markdown(
            '<div style="font-size:11px;color:#3a4a70;text-align:center;margin-top:6px;">Session closed</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown('<div class="section-label">Intervention votes</div>', unsafe_allow_html=True)

    disabled = not st.session_state.session_open

    vote_mask = st.radio(
        "Mask wearing",
        ["None (0%)", "Low (25%)", "Medium (60%)", "High (90%)"],
        index=["None (0%)", "Low (25%)", "Medium (60%)", "High (90%)"].index(st.session_state.vote_mask),
        disabled=disabled, key="r_mask",
    )
    vote_distance = st.radio(
        "Social distancing",
        ["None", "Mild", "Moderate", "Strict"],
        index=["None", "Mild", "Moderate", "Strict"].index(st.session_state.vote_distance),
        disabled=disabled, key="r_distance",
    )
    vote_vaccine = st.radio(
        "Vaccination rate",
        ["0%", "30%", "60%", "90%"],
        index=["0%", "30%", "60%", "90%"].index(st.session_state.vote_vaccine),
        disabled=disabled, key="r_vaccine",
    )
    vote_closure = st.radio(
        "School / work closure",
        ["Open", "Partial", "Full"],
        index=["Open", "Partial", "Full"].index(st.session_state.vote_closure),
        disabled=disabled, key="r_closure",
    )
    vote_testing = st.radio(
        "Testing intensity",
        ["Low", "Moderate", "High"],
        index=["Low", "Moderate", "High"].index(st.session_state.vote_testing),
        disabled=disabled, key="r_testing",
    )

    if not disabled:
        st.session_state.vote_mask     = vote_mask
        st.session_state.vote_distance = vote_distance
        st.session_state.vote_vaccine  = vote_vaccine
        st.session_state.vote_closure  = vote_closure
        st.session_state.vote_testing  = vote_testing
        st.session_state.votes_cast    = max(st.session_state.votes_cast, 1)

    st.markdown("---")

    if st.button("⚡  Apply votes to forecast", use_container_width=True, type="primary"):
        st.session_state.applied = True
        st.session_state.before_metrics = base_m
        st.rerun()

    if st.button("↺  Reset to baseline", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()