# ============================================================
# Metro Vancouver COVID Forecaster
# ML time-series ensemble · Holt-Winters + Linear Trend
# ============================================================

import io
import numpy as np
import plotly.graph_objects as go
import qrcode
import streamlit as st
from datetime import datetime, timedelta

APP_TITLE  = "Metro Vancouver COVID Forecaster"
PUBLIC_URL = "https://afrazdiseasedashboardapp.streamlit.app"
VOTE_URL   = f"{PUBLIC_URL}?mode=vote"

st.set_page_config(page_title=APP_TITLE, page_icon="🦠", layout="wide",
                   initial_sidebar_state="collapsed")

# ──────────────────────────────────────────────────────────────
# STYLES
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif !important;
    background: #050810 !important;
    color: #c8d0e8;
}
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 100% !important; }

.top-bar {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 18px; margin-bottom: 22px;
    border-bottom: 1px solid #0d1228;
}
.top-bar h1 {
    font-size: 22px; font-weight: 700; color: #e4eaff;
    letter-spacing: -.5px; margin: 0;
}
.top-bar .sub { font-size: 11px; color: #2e3d60; margin-top: 4px; letter-spacing: .6px; text-transform: uppercase; }
.pill {
    display: inline-block; padding: 3px 12px; border-radius: 99px;
    font-size: 10px; font-weight: 600; letter-spacing: 1px;
    text-transform: uppercase; margin-left: 10px;
}
.pill-green { background: #0a2218; color: #22c55e; border: 1px solid #15532e; }
.pill-gray  { background: #0d1228; color: #3a4a70; border: 1px solid #1a2240; }

.kpi-row {
    display: grid; grid-template-columns: repeat(4,1fr);
    gap: 10px; margin-bottom: 22px;
}
.kpi {
    background: #07091a; border: 1px solid #0f1630;
    border-radius: 12px; padding: 16px 18px;
}
.kpi .k-label { font-size: 10px; letter-spacing: 1px; text-transform: uppercase; color: #2e3d60; margin-bottom: 8px; }
.kpi .k-val   { font-family: 'DM Mono', monospace; font-size: 28px; font-weight: 500; line-height: 1; letter-spacing: -1px; }
.kpi .k-sub   { font-size: 11px; color: #2a3455; margin-top: 6px; }

.chart-box {
    background: #07091a; border: 1px solid #0f1630;
    border-radius: 14px; padding: 20px 20px 8px; margin-bottom: 14px;
}
.ch-title {
    font-size: 11px; letter-spacing: 1px; text-transform: uppercase;
    color: #2e3d60; margin-bottom: 4px;
    display: flex; align-items: center; gap: 10px;
}
.ch-title::after { content:''; flex:1; height:1px; background:#0d1228; }

.ba-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 14px; }
.ba-card { border-radius: 10px; padding: 14px 16px; }
.ba-before { background: #0d0800; border: 1px solid #1e1000; }
.ba-after  { background: #030d18; border: 1px solid #0a2038; }
.ba-head   { font-size: 10px; letter-spacing: 1px; text-transform: uppercase; font-weight: 600; margin-bottom: 10px; }
.ba-line   { display: flex; justify-content: space-between; font-size: 12px; color: #2e3d60; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,.03); }
.ba-line:last-child { border-bottom: none; }
.ba-line .mono { font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 500; }
.delta-dn { color: #22c55e; font-size: 10px; margin-left: 5px; }
.delta-up { color: #ef4444; font-size: 10px; margin-left: 5px; }

.insight {
    background: #06080f; border-left: 2px solid #1a3060;
    border-radius: 0 8px 8px 0; padding: 12px 16px;
    font-size: 12px; color: #3a4e78; line-height: 1.8;
}
.insight b { color: #5870a0; }

.side-label {
    font-size: 10px; letter-spacing: 1.2px; text-transform: uppercase;
    color: #2e3d60; margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
}
.side-label::after { content:''; flex:1; height:1px; background:#0d1228; }

.qr-wrap {
    background: white; border-radius: 10px;
    padding: 10px; display: inline-block; margin-bottom: 6px;
}

.mult-bar-bg {
    height: 5px; background: #0d1228; border-radius: 3px;
    overflow: hidden; margin-top: 6px;
}
.mult-bar-fill { height: 100%; border-radius: 3px; }

hr { border-color: #0d1228 !important; margin: 14px 0 !important; }

div[data-testid="stSelectSlider"] { margin-bottom: 12px; }
div[data-testid="stSelectSlider"] > label {
    font-size: 10px !important; letter-spacing: .9px !important;
    text-transform: uppercase !important; color: #3a4a70 !important;
}

div[data-testid="stButton"] > button {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important;
    border-radius: 8px !important; transition: all .12s !important;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
VOTE_PARAMS = {
    "mask":     ["0%", "25%", "60%", "90%"],
    "distance": ["None", "Mild", "Moderate", "Strict"],
    "vaccine":  ["0%", "30%", "60%", "90%"],
    "closure":  ["Open", "Partial", "Full"],
    "testing":  ["Low", "Moderate", "High"],
}
DEFAULTS = dict(
    session_open=False, votes_cast=0, applied=False, before_metrics=None,
    vote_mask="0%", vote_distance="None",
    vote_vaccine="0%", vote_closure="Open", vote_testing="Low",
)
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ──────────────────────────────────────────────────────────────
# ML FORECAST ENGINE
# ──────────────────────────────────────────────────────────────
HIST_W = 26
FORE_W = 12

def make_history(seed=42):
    rng = np.random.default_rng(seed)
    t   = np.linspace(0, 1, HIST_W)
    w1  = 2800 * np.exp(-((t - 0.22)**2) / 0.018)
    w2  = 4200 * np.exp(-((t - 0.68)**2) / 0.025)
    base = 600 + w1 + w2
    return np.clip(base + rng.normal(0, 140, HIST_W), 80, None).astype(float)

def holt_winters(y, n, alpha=0.35, beta=0.15, period=4):
    L = float(y[:period].mean())
    T = float((y[period:2*period].mean() - L) / period)
    S = list(y[:period] - L)
    for i in range(len(y)):
        s  = i % period
        L0 = L
        L  = alpha * (y[i] - S[s]) + (1 - alpha) * (L + T)
        T  = beta  * (L - L0)      + (1 - beta)  * T
        S[s] = y[i] - L0
    return np.array([max(0.0, L + (i+1)*T + S[(len(y)+i) % period]) for i in range(n)])

def lin_trend(y, n, w=8):
    tail = y[-w:].astype(float)
    x    = np.arange(w, dtype=float)
    xm, ym = x.mean(), tail.mean()
    m = ((x-xm)*(tail-ym)).sum() / ((x-xm)**2).sum()
    b = ym - m*xm
    return np.clip(b + m*np.arange(w, w+n, dtype=float), 0, None)

def ensemble_forecast(y, n, hw_w=0.65):
    hw   = holt_winters(y, n)
    lt   = lin_trend(y, n)
    mean = hw_w*hw + (1-hw_w)*lt
    sig  = mean * (0.05 + 0.013*np.arange(n))
    return mean, mean-sig, mean+sig

EFFECTS = {
    "mask":     {"0%": 1.00, "25%": 0.87, "60%": 0.70, "90%": 0.52},
    "distance": {"None": 1.00, "Mild": 0.90, "Moderate": 0.76, "Strict": 0.60},
    "vaccine":  {"0%": 1.00, "30%": 0.82, "60%": 0.62, "90%": 0.38},
    "closure":  {"Open": 1.00, "Partial": 0.83, "Full": 0.65},
    "testing":  {"Low": 1.00, "Moderate": 0.93, "High": 0.88},
}

def calc_multiplier(mask, distance, vaccine, closure, testing):
    return (EFFECTS["mask"][mask] * EFFECTS["distance"][distance] *
            EFFECTS["vaccine"][vaccine] * EFFECTS["closure"][closure] *
            EFFECTS["testing"][testing])

def apply_mult(fc, lo, hi, m):
    ramp      = np.full(len(fc), m)
    ramp[:4]  = np.linspace(1.0, m, min(4, len(fc)))
    return fc*ramp, lo*ramp, hi*ramp

def get_metrics(fc):
    peak  = int(fc.max())
    pw    = int(fc.argmax()) + 1
    total = int(fc.sum())
    chg   = fc[-1] - fc[0]
    return {"peak": peak, "pw": pw, "total": total,
            "trend": "Declining ↓" if chg < 0 else "Growing ↑",
            "pct": round(abs(chg)/(fc[0]+1e-6)*100, 1),
            "wk12": int(fc[-1])}

# ──────────────────────────────────────────────────────────────
# DATA
# ──────────────────────────────────────────────────────────────
history = make_history()
base_fc, base_lo, base_hi = ensemble_forecast(history, FORE_W)

start  = datetime(2024, 1, 1)
h_lbl  = [(start + timedelta(weeks=i)).strftime("%b %d") for i in range(HIST_W)]
f_lbl  = [(start + timedelta(weeks=HIST_W+i)).strftime("%b %d") for i in range(FORE_W)]

mult_val = calc_multiplier(
    st.session_state.vote_mask, st.session_state.vote_distance,
    st.session_state.vote_vaccine, st.session_state.vote_closure,
    st.session_state.vote_testing,
)
if st.session_state.applied:
    cur_fc, cur_lo, cur_hi = apply_mult(base_fc.copy(), base_lo.copy(), base_hi.copy(), mult_val)
else:
    cur_fc, cur_lo, cur_hi = base_fc.copy(), base_lo.copy(), base_hi.copy()

base_m = get_metrics(base_fc)
cur_m  = get_metrics(cur_fc)
bef_m  = st.session_state.before_metrics or base_m

# ──────────────────────────────────────────────────────────────
# CHART
# ──────────────────────────────────────────────────────────────
def hex_rgb(h):
    h = h.lstrip('#')
    return ','.join(str(int(h[i:i+2],16)) for i in (0,2,4))

def build_chart():
    fc_color = ("#22c55e" if (st.session_state.applied and mult_val < 0.70) else
                "#f59e0b" if (st.session_state.applied and mult_val < 0.90) else
                "#3b82f6")

    # unified y range across history + forecast bands
    y_max = max(float(history.max()), float(cur_hi.max()), float(base_hi.max())) * 1.1
    y_min = 0.0

    fig = go.Figure()

    # CI band
    fig.add_trace(go.Scatter(
        x=f_lbl + f_lbl[::-1],
        y=list(cur_hi) + list(cur_lo[::-1]),
        fill='toself',
        fillcolor=f'rgba({hex_rgb(fc_color)},0.07)',
        line=dict(width=0), showlegend=False, hoverinfo='skip',
    ))

    # Baseline dashed (only when applied)
    if st.session_state.applied:
        fig.add_trace(go.Scatter(
            x=f_lbl, y=base_fc, mode='lines',
            name='No-intervention baseline',
            line=dict(color='rgba(200,140,50,0.45)', width=1.5, dash='dot'),
            hovertemplate='Baseline: %{y:,.0f}<extra></extra>',
        ))

    # Historical
    fig.add_trace(go.Scatter(
        x=h_lbl, y=history, mode='lines+markers',
        name='Historical cases',
        line=dict(color='#2e4a6a', width=2),
        marker=dict(size=3, color='#3a5a80'),
        hovertemplate='%{x}<br>Cases: %{y:,.0f}<extra></extra>',
    ))

    # Forecast
    fig.add_trace(go.Scatter(
        x=f_lbl, y=cur_fc, mode='lines+markers',
        name='ML Forecast',
        line=dict(color=fc_color, width=2.5),
        marker=dict(size=5, color=fc_color,
                    line=dict(width=1.5, color='#050810')),
        hovertemplate='%{x}<br>Forecast: %{y:,.0f}<extra></extra>',
    ))

    # NOW divider — shape only, no add_vline
    now_x = h_lbl[-1]
    fig.update_layout(
        shapes=[dict(
            type="line", xref="x", yref="paper",
            x0=now_x, x1=now_x, y0=0, y1=1,
            line=dict(color='rgba(255,255,255,0.08)', width=1.5, dash='dash'),
        )],
        annotations=[dict(
            xref="x", yref="paper",
            x=now_x, y=0.97, text="NOW →",
            showarrow=False,
            font=dict(size=9, color='rgba(200,210,255,0.2)', family='DM Mono'),
            xanchor="left",
        )],
    )

    # tick thinning — every 3rd label
    tick_vals = h_lbl[::3] + f_lbl[::2]

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=370,
        margin=dict(l=10, r=10, t=10, b=50),
        font=dict(family='Outfit', color='#2e3d60', size=11),
        legend=dict(
            orientation='h', y=1.09, x=0,
            font=dict(size=11, color='#3a5070'),
            bgcolor='rgba(0,0,0,0)', itemgap=24,
        ),
        xaxis=dict(
            tickmode='array', tickvals=tick_vals,
            tickfont=dict(size=10, color='#2e3d60'),
            tickangle=-35,
            showgrid=False, zeroline=False,
            linecolor='#0d1228', tickcolor='rgba(0,0,0,0)',
        ),
        yaxis=dict(
            range=[y_min, y_max],
            tickfont=dict(size=10, color='#2e3d60'),
            gridcolor='rgba(255,255,255,0.025)',
            zeroline=False, tickformat=',d',
            linecolor='rgba(0,0,0,0)', tickcolor='rgba(0,0,0,0)',
        ),
        hovermode='x unified',
        hoverlabel=dict(
            bgcolor='#0d1228', bordercolor='#1a2848',
            font=dict(family='DM Mono', size=11, color='#c8d0e8'),
        ),
    )
    return fig

# ──────────────────────────────────────────────────────────────
# QR
# ──────────────────────────────────────────────────────────────
@st.cache_data
def make_qr(url):
    img = qrcode.make(url)
    buf = io.BytesIO(); img.save(buf)
    return buf.getvalue()

qr = make_qr(VOTE_URL)

# ──────────────────────────────────────────────────────────────
# RENDER
# ──────────────────────────────────────────────────────────────

# ── Top bar ──
sess_pill  = ('<span class="pill pill-green">● VOTING OPEN</span>'
              if st.session_state.session_open else
              '<span class="pill pill-gray">○ CLOSED</span>')
votes_pill = f'<span class="pill pill-gray">{st.session_state.votes_cast} votes</span>'

st.markdown(f"""
<div class="top-bar">
  <div>
    <h1>Metro Vancouver COVID Forecaster {sess_pill} {votes_pill}</h1>
    <div class="sub">ML Ensemble · Holt-Winters + Linear Trend · 12-Week Outlook</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI row ──
pc = cur_m["peak"]; bc = base_m["peak"]
tc = cur_m["total"]; bt = base_m["total"]
pd_ = pc - bc;  td_ = tc - bt
p_col  = "#22c55e" if pd_ < 0 else ("#ef4444" if pd_ > 0 else "#3a4a70")
t_col  = "#22c55e" if td_ < 0 else ("#ef4444" if td_ > 0 else "#3a4a70")
tr_col = "#22c55e" if "Decl" in cur_m["trend"] else "#ef4444"
mx_pct = round((1 - mult_val)*100, 1)
mx_col = "#22c55e" if mult_val < 0.7 else ("#f59e0b" if mult_val < 0.9 else "#3b82f6")

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi">
    <div class="k-label">Peak weekly cases</div>
    <div class="k-val" style="color:{p_col}">{pc:,}</div>
    <div class="k-sub">Week {cur_m['pw']} &nbsp;·&nbsp; {'▼' if pd_<0 else '▲'} {abs(pd_):,} vs baseline</div>
  </div>
  <div class="kpi">
    <div class="k-label">12-week total</div>
    <div class="k-val" style="color:{t_col}">{tc:,}</div>
    <div class="k-sub">{'▼' if td_<0 else '▲'} {abs(td_):,} vs baseline</div>
  </div>
  <div class="kpi">
    <div class="k-label">Forecast trend</div>
    <div class="k-val" style="color:{tr_col};font-size:19px;padding-top:5px">{cur_m['trend']}</div>
    <div class="k-sub">{cur_m['pct']}% change over 12 weeks</div>
  </div>
  <div class="kpi">
    <div class="k-label">Intervention effect</div>
    <div class="k-val" style="color:{mx_col}">−{mx_pct}%</div>
    <div class="k-sub">Vote multiplier ×{mult_val:.2f}</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Two-column layout ──
col_chart, col_side = st.columns([3, 1], gap="large")

with col_chart:
    st.markdown('<div class="chart-box"><div class="ch-title">Weekly new cases · Metro Vancouver · ML ensemble forecast</div>', unsafe_allow_html=True)
    st.plotly_chart(build_chart(), use_container_width=True, config={"displayModeBar": False})
    st.markdown('</div>', unsafe_allow_html=True)

    # Before / After
    bm = bef_m; cm = cur_m
    def delta_html(a, b):
        d = a - b
        if d == 0: return ""
        return f'<span class="{"delta-dn" if d<0 else "delta-up"}">{"▼" if d<0 else "▲"}{abs(d):,}</span>'

    st.markdown(f"""
<div class="ba-row">
  <div class="ba-card ba-before">
    <div class="ba-head" style="color:#b06020">◈ Before votes — baseline</div>
    <div class="ba-line"><span>Peak weekly</span><span class="mono" style="color:#c07030">{bm['peak']:,}</span></div>
    <div class="ba-line"><span>12-week total</span><span class="mono" style="color:#c07030">{bm['total']:,}</span></div>
    <div class="ba-line"><span>Week 12 cases</span><span class="mono" style="color:#c07030">{bm['wk12']:,}</span></div>
    <div class="ba-line"><span>Multiplier</span><span class="mono" style="color:#c07030">×1.00</span></div>
  </div>
  <div class="ba-card ba-after">
    <div class="ba-head" style="color:#1a80c0">◈ After votes — current</div>
    <div class="ba-line"><span>Peak weekly</span><span class="mono" style="color:#3090d0">{cm['peak']:,}{delta_html(cm['peak'],bm['peak'])}</span></div>
    <div class="ba-line"><span>12-week total</span><span class="mono" style="color:#3090d0">{cm['total']:,}{delta_html(cm['total'],bm['total'])}</span></div>
    <div class="ba-line"><span>Week 12 cases</span><span class="mono" style="color:#3090d0">{cm['wk12']:,}{delta_html(cm['wk12'],bm['wk12'])}</span></div>
    <div class="ba-line"><span>Multiplier</span><span class="mono" style="color:#3090d0">×{mult_val:.2f}</span></div>
  </div>
</div>
<div class="insight">
<b>How the model works:</b> Weighted ensemble — <b>Holt-Winters exponential smoothing</b>
(65% weight, captures level + trend + 4-week seasonality) blended with a <b>linear trend
regressor</b> (35%, projects the last-8-week slope). Votes scale forecasted case counts via
a combined transmission multiplier, ramped in over <b>4 weeks</b> to simulate real policy lag.
Shaded band = ±1σ uncertainty, widening at longer horizons.
</div>
""", unsafe_allow_html=True)

with col_side:
    # QR
    st.markdown('<div class="side-label">Scan to vote</div>', unsafe_allow_html=True)
    st.markdown('<div class="qr-wrap">', unsafe_allow_html=True)
    st.image(qr, width=148)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;color:#2a3860;word-break:break-all;margin-bottom:14px">{VOTE_URL}</div>',
                unsafe_allow_html=True)

    # Session
    st.markdown('<div class="side-label">Session</div>', unsafe_allow_html=True)
    if st.session_state.session_open:
        if st.button("● Close voting session", use_container_width=True, type="primary"):
            st.session_state.session_open = False
            st.rerun()
        st.markdown('<div style="font-size:11px;color:#22c55e;text-align:center;margin-top:6px">Open · votes live</div>',
                    unsafe_allow_html=True)
    else:
        if st.button("▶  Open voting session", use_container_width=True):
            st.session_state.session_open   = True
            st.session_state.applied        = False
            st.session_state.before_metrics = base_m
            st.rerun()
        st.markdown('<div style="font-size:11px;color:#2e3d60;text-align:center;margin-top:6px">Closed · controls locked</div>',
                    unsafe_allow_html=True)

    st.markdown("---")

    # Intervention sliders
    st.markdown('<div class="side-label">Intervention parameters</div>', unsafe_allow_html=True)
    disabled = not st.session_state.session_open

    v_mask = st.select_slider("Mask wearing",      options=VOTE_PARAMS["mask"],
                               value=st.session_state.vote_mask,     disabled=disabled, key="sl_mask")
    v_dist = st.select_slider("Social distancing", options=VOTE_PARAMS["distance"],
                               value=st.session_state.vote_distance, disabled=disabled, key="sl_dist")
    v_vacc = st.select_slider("Vaccination rate",  options=VOTE_PARAMS["vaccine"],
                               value=st.session_state.vote_vaccine,  disabled=disabled, key="sl_vacc")
    v_clos = st.select_slider("School / work closure", options=VOTE_PARAMS["closure"],
                               value=st.session_state.vote_closure,  disabled=disabled, key="sl_clos")
    v_test = st.select_slider("Testing intensity", options=VOTE_PARAMS["testing"],
                               value=st.session_state.vote_testing,  disabled=disabled, key="sl_test")

    if not disabled:
        st.session_state.vote_mask     = v_mask
        st.session_state.vote_distance = v_dist
        st.session_state.vote_vaccine  = v_vacc
        st.session_state.vote_closure  = v_clos
        st.session_state.vote_testing  = v_test
        st.session_state.votes_cast    = max(st.session_state.votes_cast, 1)

    # Live multiplier bar
    live_m  = calc_multiplier(st.session_state.vote_mask, st.session_state.vote_distance,
                              st.session_state.vote_vaccine, st.session_state.vote_closure,
                              st.session_state.vote_testing)
    bar_pct = round((1 - live_m)*100, 1)
    bar_col = "#22c55e" if live_m < 0.70 else ("#f59e0b" if live_m < 0.90 else "#3b82f6")
    st.markdown(f"""
<div style="font-size:11px;color:#2e3d60;margin-top:2px">
  Combined reduction: <span style="color:{bar_col};font-family:'DM Mono',monospace;font-weight:500">−{bar_pct}%</span>
</div>
<div class="mult-bar-bg">
  <div class="mult-bar-fill" style="width:{bar_pct}%;background:{bar_col}"></div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("⚡ Apply", use_container_width=True, type="primary"):
            st.session_state.applied        = True
            st.session_state.before_metrics = base_m
            st.rerun()
    with c2:
        if st.button("↺ Reset", use_container_width=True):
            for k, v in DEFAULTS.items():
                st.session_state[k] = v
            st.rerun()