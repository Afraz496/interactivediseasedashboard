# ============================================================
# 🦠 Metro Vancouver COVID Outbreak Forecaster
# Presenter dashboard + QR-linked voting page
# ============================================================

import io
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import qrcode
import streamlit as st

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

APP_TITLE = "Metro Vancouver COVID Forecaster"
PUBLIC_URL = "https://afrazdiseasedashboard.streamlit.app"
VOTE_URL = f"{PUBLIC_URL}?mode=vote"
DB_PATH = Path("covid_vote_state.db")

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
:root {
    --bg: #071225;
    --panel: #0d1b34;
    --panel-2: #102042;
    --border: #1f3561;
    --text: #eaf1ff;
    --muted: #a8b7d9;
    --subtle: #7e90b8;
    --accent: #47b3ff;
    --accent-2: #6dd3ff;
    --good: #22c55e;
    --warn: #f59e0b;
    --bad: #ef4444;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg) !important;
    color: var(--text) !important;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header {
    visibility: hidden;
}

.block-container {
    max-width: 1400px;
    padding-top: 1.25rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4, h5, h6, p, label, div, span {
    color: var(--text) !important;
}

/* Header */
.app-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 20px;
    margin-bottom: 22px;
    padding: 22px 24px;
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 18px;
}

.header-left h1 {
    font-size: 2.15rem;
    line-height: 1.05;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0;
}

.header-left p {
    margin: 10px 0 0;
    font-size: 1rem;
    color: var(--muted) !important;
    line-height: 1.45;
}

.status-chip {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-size: 0.9rem;
    font-weight: 700;
    padding: 10px 14px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--panel-2);
}

.live-dot {
    display: inline-block;
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--bad);
    animation: blink 1.8s infinite;
}
@keyframes blink {
    0%,100% { opacity: 1; }
    50% { opacity: .35; }
}

/* Metrics */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
    margin-bottom: 1.4rem;
}
.metric-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 18px 18px 16px;
}
.metric-card .label {
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: var(--subtle) !important;
    margin-bottom: 10px;
}
.metric-card .value {
    font-size: 2rem;
    font-weight: 800;
    line-height: 1.05;
}
.metric-card .sub {
    font-size: 0.95rem;
    color: var(--muted) !important;
    margin-top: 8px;
    line-height: 1.35;
}

/* Section labels */
.section-label {
    font-size: 0.85rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--accent-2) !important;
    margin: 0 0 10px;
    display: flex;
    align-items: center;
    gap: 10px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}

/* Panels */
.panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
}

/* Compare strip */
.compare-strip {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
    margin-top: 0.8rem;
}
.compare-card {
    border-radius: 14px;
    padding: 16px 16px 12px;
    border: 1px solid var(--border);
}
.before-card {
    background: #22160b;
    border-color: #5b3a17;
}
.after-card {
    background: #0c1d2d;
    border-color: #1a4c73;
}
.compare-card .c-label {
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 10px;
    font-weight: 800;
}
.compare-card .c-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    font-size: 1rem;
    color: var(--muted) !important;
    padding: 5px 0;
}
.compare-card .c-row span {
    font-weight: 800;
}

/* Insight banner */
.insight-banner {
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: 14px;
    padding: 14px 16px;
    font-size: 1rem;
    color: var(--muted) !important;
    line-height: 1.65;
    margin-top: 1rem;
}

/* Inputs */
div[data-testid="stRadio"] > label {
    font-size: 0.82rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    color: var(--subtle) !important;
    margin-bottom: 6px !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
div[data-testid="stRadio"] label {
    background: var(--panel-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 10px 12px !important;
    font-size: 1rem !important;
    color: var(--text) !important;
}
div[data-testid="stRadio"] label:hover {
    border-color: var(--accent) !important;
}
div[data-testid="stTextInput"] input {
    background: var(--panel-2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
}
div[data-testid="stButton"] > button {
    width: 100%;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    background: var(--panel-2) !important;
    color: var(--text) !important;
    font-weight: 800 !important;
    font-size: 1rem !important;
    padding: 0.8rem 1rem !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: var(--accent) !important;
    background: #15305f !important;
}

/* Small helper */
.small-muted {
    font-size: 0.92rem;
    color: var(--muted) !important;
    line-height: 1.45;
}

/* Responsive */
@media (max-width: 1100px) {
    .metric-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .compare-strip {
        grid-template-columns: 1fr;
    }
    .app-header {
        flex-direction: column;
    }
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_name TEXT,
            mask TEXT NOT NULL,
            distance TEXT NOT NULL,
            vaccine TEXT NOT NULL,
            closure TEXT NOT NULL,
            testing TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    defaults = {
        "session_open": "0",
        "applied": "0",
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    conn.commit()
    conn.close()

def get_setting(key: str, default: str = "") -> str:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value)),
    )
    conn.commit()
    conn.close()

def add_vote(voter_name: str, mask: str, distance: str, vaccine: str, closure: str, testing: str):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO votes (voter_name, mask, distance, vaccine, closure, testing, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        voter_name.strip(),
        mask,
        distance,
        vaccine,
        closure,
        testing,
        datetime.utcnow().isoformat(),
    ))
    conn.commit()
    conn.close()

def clear_votes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes")
    conn.commit()
    conn.close()

def load_votes() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM votes ORDER BY id DESC", conn)
    conn.close()
    return df

def vote_consensus(votes_df: pd.DataFrame) -> dict:
    defaults = {
        "mask": "None (0%)",
        "distance": "None",
        "vaccine": "0%",
        "closure": "Open",
        "testing": "Low",
    }
    if votes_df.empty:
        return defaults

    out = {}
    for col, fallback in defaults.items():
        mode = votes_df[col].mode()
        out[col] = mode.iat[0] if not mode.empty else fallback
    return out

# ──────────────────────────────────────────────
# ML FORECASTING ENGINE
# ──────────────────────────────────────────────

HISTORICAL_WEEKS = 26
FORECAST_WEEKS = 12

def generate_historical(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, HISTORICAL_WEEKS)
    wave1 = 2000 * np.exp(-((t - 0.25) ** 2) / 0.02)
    wave2 = 3500 * np.exp(-((t - 0.70) ** 2) / 0.03)
    base = 400 + wave1 + wave2
    noise = rng.normal(0, 120, HISTORICAL_WEEKS)
    return np.clip(base + noise, 50, None).astype(float)

def holt_winters(series: np.ndarray, n_ahead: int,
                 alpha: float = 0.35, beta: float = 0.15,
                 season_len: int = 4) -> np.ndarray:
    n = len(series)
    level = series[:season_len].mean()
    trend = (series[season_len:2 * season_len].mean() - level) / season_len
    seasons = series[:season_len] - level

    for t in range(n):
        s_idx = t % season_len
        prev_level = level
        level = alpha * (series[t] - seasons[s_idx]) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seasons[s_idx] = series[t] - prev_level

    forecast = np.zeros(n_ahead)
    for i in range(n_ahead):
        forecast[i] = level + (i + 1) * trend + seasons[(n + i) % season_len]
    return np.clip(forecast, 0, None)

def linear_trend(series: np.ndarray, n_ahead: int, window: int = 8) -> np.ndarray:
    tail = series[-window:]
    x = np.arange(window, dtype=float)
    xm, ym = x.mean(), tail.mean()
    slope = np.sum((x - xm) * (tail - ym)) / np.sum((x - xm) ** 2)
    intercept = ym - slope * xm
    fut = np.arange(window, window + n_ahead, dtype=float)
    return np.clip(intercept + slope * fut, 0, None)

def ensemble_forecast(series: np.ndarray, n_ahead: int,
                      hw_weight: float = 0.65) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    hw = holt_winters(series, n_ahead)
    lt = linear_trend(series, n_ahead)
    mean = hw_weight * hw + (1 - hw_weight) * lt
    sigma = mean * (0.06 + 0.012 * np.arange(n_ahead))
    return mean, mean - sigma, mean + sigma

MASK_EFFECT = {"None (0%)": 1.0, "Low (25%)": 0.87, "Medium (60%)": 0.70, "High (90%)": 0.52}
DISTANCE_EFFECT = {"None": 1.0, "Mild": 0.90, "Moderate": 0.76, "Strict": 0.60}
VACCINE_EFFECT = {"0%": 1.0, "30%": 0.82, "60%": 0.62, "90%": 0.38}
CLOSURE_EFFECT = {"Open": 1.0, "Partial": 0.83, "Full": 0.65}
TESTING_EFFECT = {"Low": 1.0, "Moderate": 0.93, "High": 0.88}

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
    ramp = np.linspace(1.0, mult, min(4, len(base_fc)))
    full = np.full(len(base_fc), mult)
    full[:len(ramp)] = ramp
    return base_fc * full, lo * full, hi * full

def metrics_from(fc: np.ndarray) -> dict:
    peak_val = int(fc.max())
    peak_week = int(fc.argmax()) + 1
    total = int(fc.sum())
    trend = "↓ Declining" if fc[-1] < fc[0] else "↑ Growing"
    trend_pct = abs(fc[-1] - fc[0]) / (fc[0] + 1e-6) * 100
    return {
        "peak_val": peak_val,
        "peak_week": peak_week,
        "total": total,
        "trend": trend,
        "trend_pct": round(trend_pct, 1),
        "week12": int(fc[-1]),
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
# CHART
# ──────────────────────────────────────────────

def build_chart(history, base_fc, cur_fc, cur_lo, cur_hi, date_labels_hist, date_labels_fc, applied, mult):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=date_labels_fc + date_labels_fc[::-1],
        y=list(cur_hi) + list(cur_lo[::-1]),
        fill='toself',
        fillcolor='rgba(71,179,255,0.10)',
        line=dict(width=0),
        showlegend=False,
        hoverinfo='skip',
        name='CI band',
    ))

    if applied:
        fig.add_trace(go.Scatter(
            x=date_labels_fc,
            y=base_fc,
            mode='lines',
            name='Baseline (no intervention)',
            line=dict(color='rgba(245,158,11,0.65)', width=2, dash='dot'),
            hovertemplate='<b>Baseline</b>: %{y:,.0f}<extra></extra>',
        ))

    fig.add_trace(go.Scatter(
        x=date_labels_hist,
        y=history,
        mode='lines+markers',
        name='Historical cases',
        line=dict(color='#7e90b8', width=2),
        marker=dict(size=5, color='#7e90b8'),
        hovertemplate='<b>%{x}</b><br>Cases: %{y:,.0f}<extra></extra>',
    ))

    fc_color = '#47b3ff' if not applied else ('#22c55e' if mult < 0.75 else '#f59e0b' if mult < 0.92 else '#ef4444')
    fig.add_trace(go.Scatter(
        x=date_labels_fc,
        y=cur_fc,
        mode='lines+markers',
        name='ML Forecast',
        line=dict(color=fc_color, width=3.5),
        marker=dict(size=6, color=fc_color),
        hovertemplate='<b>%{x}</b><br>Forecast: %{y:,.0f}<extra></extra>',
    ))

    now_x = date_labels_hist[-1]
    fig.add_shape(
        type="line",
        x0=now_x,
        x1=now_x,
        y0=0,
        y1=1,
        xref="x",
        yref="paper",
        line=dict(color='rgba(255,255,255,0.18)', width=1, dash='dash'),
    )
    fig.add_annotation(
        x=now_x,
        y=1,
        xref="x",
        yref="paper",
        text="NOW",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=10, color='rgba(255,255,255,0.55)')
    )

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0),
        height=360,
        font=dict(color='#d6e2ff', size=13),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='left',
            x=0,
            font=dict(size=12, color='#c6d4f4'),
            bgcolor='rgba(0,0,0,0)',
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickcolor='rgba(0,0,0,0)',
            linecolor='rgba(255,255,255,0.08)',
            tickfont=dict(size=12),
            tickangle=-30,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(255,255,255,0.05)',
            tickcolor='rgba(0,0,0,0)',
            linecolor='rgba(255,255,255,0.08)',
            tickfont=dict(size=12),
            tickformat=',d',
        ),
        hovermode='x unified',
    )

    return fig

# ──────────────────────────────────────────────
# PAGES
# ──────────────────────────────────────────────

def render_vote_page():
    session_open = get_setting("session_open", "0") == "1"

    st.markdown("""
    <div class="app-header">
      <div class="header-left">
        <h1>📱 Vote on interventions</h1>
        <p>Choose how the class wants to respond to the outbreak. Your vote affects the presenter dashboard.</p>
      </div>
      <div class="status-chip">Audience page</div>
    </div>
    """, unsafe_allow_html=True)

    if not session_open:
        st.warning("Voting is currently closed. Wait for the presenter to open the session.")
        return

    with st.form("vote_form", clear_on_submit=True):
        voter_name = st.text_input("Your name or nickname", placeholder="Optional")

        mask = st.radio("Mask wearing", ["None (0%)", "Low (25%)", "Medium (60%)", "High (90%)"])
        distance = st.radio("Social distancing", ["None", "Mild", "Moderate", "Strict"])
        vaccine = st.radio("Vaccination rate", ["0%", "30%", "60%", "90%"])
        closure = st.radio("School / work closure", ["Open", "Partial", "Full"])
        testing = st.radio("Testing intensity", ["Low", "Moderate", "High"])

        submitted = st.form_submit_button("Submit vote")

    if submitted:
        add_vote(voter_name, mask, distance, vaccine, closure, testing)
        st.success("Vote submitted. Look at the main screen to see the forecast update.")


def render_dashboard():
    history = generate_historical()
    base_fc, base_lo, base_hi = ensemble_forecast(history, FORECAST_WEEKS)

    start_date = datetime(2024, 1, 1)
    hist_dates = [start_date + timedelta(weeks=i) for i in range(HISTORICAL_WEEKS)]
    fc_dates = [hist_dates[-1] + timedelta(weeks=i + 1) for i in range(FORECAST_WEEKS)]
    date_labels_hist = [d.strftime("%b %d") for d in hist_dates]
    date_labels_fc = [d.strftime("%b %d") for d in fc_dates]

    votes_df = load_votes()
    consensus = vote_consensus(votes_df)

    session_open = get_setting("session_open", "0") == "1"
    applied = get_setting("applied", "0") == "1"

    mult = compute_multiplier(
        consensus["mask"],
        consensus["distance"],
        consensus["vaccine"],
        consensus["closure"],
        consensus["testing"],
    )

    if applied:
        cur_fc, cur_lo, cur_hi = apply_interventions(base_fc.copy(), base_lo.copy(), base_hi.copy(), mult)
    else:
        cur_fc, cur_lo, cur_hi = base_fc.copy(), base_lo.copy(), base_hi.copy()

    cur_m = metrics_from(cur_fc)
    base_m = metrics_from(base_fc)

    peak_change = cur_m["peak_val"] - base_m["peak_val"]
    total_change = cur_m["total"] - base_m["total"]
    peak_arrow = "↓" if peak_change < 0 else ("↑" if peak_change > 0 else "—")
    total_arrow = "↓" if total_change < 0 else ("↑" if total_change > 0 else "—")
    peak_col = "#22c55e" if peak_change < 0 else ("#ef4444" if peak_change > 0 else "#c7d2fe")
    total_col = "#22c55e" if total_change < 0 else ("#ef4444" if total_change > 0 else "#c7d2fe")
    trend_color = "#22c55e" if "↓" in cur_m["trend"] else "#ef4444"
    mult_pct = round((1 - mult) * 100, 1)

    status_tag = "VOTING OPEN" if session_open else "SESSION CLOSED"
    status_color = "#22c55e" if session_open else "#94a3b8"

    st.markdown(f"""
    <div class="app-header">
      <div class="header-left">
        <h1><span class="live-dot"></span>Metro Vancouver COVID Forecaster</h1>
        <p>
          ML time-series ensemble · Holt-Winters + linear trend ·
          <span style="color:{status_color};font-weight:800;">{status_tag}</span> ·
          {len(votes_df)} votes cast
        </p>
      </div>
      <div class="status-chip">Presenter dashboard</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-grid">
      <div class="metric-card">
        <div class="label">Peak weekly cases</div>
        <div class="value" style="color:{peak_col}">{cur_m['peak_val']:,}</div>
        <div class="sub">Week {cur_m['peak_week']} · {peak_arrow} {abs(peak_change):,} vs baseline</div>
      </div>
      <div class="metric-card">
        <div class="label">12-week total</div>
        <div class="value" style="color:{total_col}">{cur_m['total']:,}</div>
        <div class="sub">{total_arrow} {abs(total_change):,} vs baseline</div>
      </div>
      <div class="metric-card">
        <div class="label">Forecast trend</div>
        <div class="value" style="font-size:1.5rem;color:{trend_color}">{cur_m['trend']}</div>
        <div class="sub">{cur_m['trend_pct']}% over forecast horizon</div>
      </div>
      <div class="metric-card">
        <div class="label">Intervention effect</div>
        <div class="value" style="color:#47b3ff">−{mult_pct}%</div>
        <div class="sub">Combined vote multiplier: ×{mult:.2f}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col_main, col_side = st.columns([2.6, 1], gap="large")

    with col_main:
        st.markdown('<div class="section-label">ML forecast · weekly new cases · Metro Vancouver</div>', unsafe_allow_html=True)
        fig = build_chart(
            history, base_fc, cur_fc, cur_lo, cur_hi,
            date_labels_hist, date_labels_fc, applied, mult
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="section-label">Before / after intervention</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="compare-strip">
          <div class="compare-card before-card">
            <div class="c-label" style="color:#f59e0b">Before votes (baseline)</div>
            <div class="c-row">Peak weekly cases <span>{base_m['peak_val']:,}</span></div>
            <div class="c-row">12-week total <span>{base_m['total']:,}</span></div>
            <div class="c-row">Week 12 cases <span>{base_m['week12']:,}</span></div>
            <div class="c-row">Multiplier <span>×1.00</span></div>
          </div>
          <div class="compare-card after-card">
            <div class="c-label" style="color:#47b3ff">After votes (current)</div>
            <div class="c-row">Peak weekly cases <span>{cur_m['peak_val']:,}</span></div>
            <div class="c-row">12-week total <span>{cur_m['total']:,}</span></div>
            <div class="c-row">Week 12 cases <span>{cur_m['week12']:,}</span></div>
            <div class="c-row">Multiplier <span>×{mult:.2f}</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="insight-banner">
        <b>How the ML model works:</b> The forecast is a <b>weighted ensemble</b> of
        <b>Holt-Winters exponential smoothing</b> (65%) and a <b>linear trend regressor</b> (35%).
        Intervention votes apply a <b>multiplier</b> that ramps in over 4 weeks, reflecting real-world delay
        between policy change and outbreak impact.
        </div>
        """, unsafe_allow_html=True)

    with col_side:
        st.markdown('<div class="section-label">Scan to vote</div>', unsafe_allow_html=True)
        st.image(qr_bytes, width=185)
        st.caption(VOTE_URL)

        st.markdown('<div class="section-label" style="margin-top:18px;">Session</div>', unsafe_allow_html=True)

        if session_open:
            if st.button("Close voting session", use_container_width=True):
                set_setting("session_open", "0")
                st.rerun()
            st.markdown(
                f'<div class="small-muted" style="margin-top:8px;color:#22c55e !important;">Open · {len(votes_df)} votes received</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("Open voting session", use_container_width=True):
                set_setting("session_open", "1")
                set_setting("applied", "0")
                st.rerun()
            st.markdown(
                '<div class="small-muted" style="margin-top:8px;">Session closed</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-label" style="margin-top:18px;">Current class consensus</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="panel">
          <div class="small-muted"><b>Mask:</b> {consensus['mask']}</div>
          <div class="small-muted"><b>Distance:</b> {consensus['distance']}</div>
          <div class="small-muted"><b>Vaccination:</b> {consensus['vaccine']}</div>
          <div class="small-muted"><b>Closure:</b> {consensus['closure']}</div>
          <div class="small-muted"><b>Testing:</b> {consensus['testing']}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-label" style="margin-top:18px;">Actions</div>', unsafe_allow_html=True)

        if st.button("Apply votes to forecast", use_container_width=True):
            set_setting("applied", "1")
            st.rerun()

        if st.button("Reset to baseline", use_container_width=True):
            clear_votes()
            set_setting("session_open", "0")
            set_setting("applied", "0")
            st.rerun()

# ──────────────────────────────────────────────
# MAIN ROUTER
# ──────────────────────────────────────────────

init_db()

mode = st.query_params.get("mode", "dashboard")

if mode == "vote":
    render_vote_page()
else:
    render_dashboard()