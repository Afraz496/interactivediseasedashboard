import io
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import qrcode
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None


APP_TITLE = "Metro Vancouver COVID Forecaster"
DB_PATH = Path("covid_vote_state.db")
DEFAULT_PUBLIC_URL = "https://afrazdiseasedashboard.streamlit.app"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🦠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# Styling
# ---------------------------------------------------------
st.markdown(
    """
<style>
:root {
    --bg: #04142e;
    --panel: #0a1d3f;
    --panel-2: #0d264f;
    --panel-3: #081833;
    --border: #1f4b85;
    --text: #eef4ff;
    --muted: #b4c6e8;
    --subtle: #76a1d8;
    --accent: #43b4ff;
    --accent-2: #6de1ff;
    --green: #22c55e;
    --yellow: #f59e0b;
    --red: #ef4444;
}

html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    color: var(--text) !important;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
}
#MainMenu, footer {visibility: hidden;}
.block-container {
    max-width: 1420px;
    padding-top: 1.1rem;
    padding-bottom: 2.5rem;
}
h1, h2, h3, h4, h5, h6, p, label, div, span {
    color: var(--text) !important;
}

.hero {
    display:flex;
    justify-content:space-between;
    gap: 18px;
    align-items:flex-start;
    background: linear-gradient(180deg, rgba(12,34,73,0.96), rgba(10,29,63,0.96));
    border:1px solid rgba(72,125,193,0.45);
    border-radius:22px;
    padding:24px 24px 22px;
    margin-bottom:18px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.20);
}
.hero-title {
    font-size: 2.35rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    line-height: 1.03;
    margin: 0;
}
.hero-sub {
    margin-top: 10px;
    font-size: 1.05rem;
    line-height: 1.5;
    color: var(--muted) !important;
}
.hero-pill {
    border:1px solid rgba(100,153,220,0.35);
    background: rgba(8,24,51,0.88);
    padding: 11px 16px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 1rem;
    white-space: nowrap;
}

.metric-grid {
    display:grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap:14px;
    margin-bottom:14px;
}
.metric-card {
    background: linear-gradient(180deg, rgba(10,29,63,0.98), rgba(8,24,51,0.98));
    border:1px solid rgba(72,125,193,0.42);
    border-radius:18px;
    padding:18px 18px 16px;
}
.metric-label {
    font-size: 0.83rem;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: var(--subtle) !important;
    font-weight: 800;
    margin-bottom: 10px;
}
.metric-value {
    font-size: 2.1rem;
    font-weight: 900;
    line-height: 1.05;
}
.metric-sub {
    margin-top: 8px;
    font-size: 0.97rem;
    color: var(--muted) !important;
    line-height: 1.4;
}

.section-title {
    font-size: 0.93rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: var(--accent-2) !important;
    font-weight: 900;
    margin: 8px 0 12px;
    display: flex;
    gap: 10px;
    align-items: center;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(72,125,193,0.38);
}

.panel {
    background: linear-gradient(180deg, rgba(10,29,63,0.98), rgba(8,24,51,0.98));
    border:1px solid rgba(72,125,193,0.42);
    border-radius:18px;
    padding:16px;
}
.small-note {
    color: var(--muted) !important;
    font-size: 0.95rem;
    line-height: 1.5;
}

.traffic-grid {
    display:grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap:10px;
}
.traffic-card {
    background: rgba(8,24,51,0.86);
    border: 1px solid rgba(72,125,193,0.33);
    border-radius: 16px;
    padding: 14px 12px;
    text-align:center;
}
.traffic-dot {
    width: 16px;
    height: 16px;
    border-radius: 50%;
    display:inline-block;
    margin-bottom: 8px;
    box-shadow: 0 0 10px rgba(255,255,255,0.14);
}
.traffic-name {
    font-size: 0.9rem;
    font-weight: 800;
}
.traffic-val {
    margin-top: 6px;
    font-size: 0.88rem;
    color: var(--muted) !important;
}

.compare-strip {
    display:grid;
    grid-template-columns: 1fr 1fr;
    gap:14px;
    margin-top: 10px;
}
.compare-card {
    border-radius:16px;
    padding:16px;
}
.before-card {
    background: #2a1808;
    border:1px solid #72401a;
}
.after-card {
    background: #0a2945;
    border:1px solid #2a6996;
}
.compare-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.82rem;
    font-weight: 900;
    margin-bottom: 12px;
}
.compare-row {
    display:flex;
    justify-content:space-between;
    gap:10px;
    padding:5px 0;
    font-size: 0.98rem;
    color: var(--muted) !important;
}
.compare-row span {
    font-weight: 900;
    color: var(--text) !important;
}

.banner-note {
    background: linear-gradient(180deg, rgba(13,38,79,0.96), rgba(10,29,63,0.96));
    border: 1px solid rgba(72,125,193,0.42);
    border-left: 4px solid var(--accent);
    border-radius: 16px;
    padding: 15px 16px;
    margin-top: 16px;
    font-size: 1rem;
    line-height: 1.6;
    color: var(--muted) !important;
}
.vote-stat {
    font-size: 0.95rem;
    color: var(--muted) !important;
    margin-top: 8px;
}
.summary-box {
    background: rgba(8,24,51,0.85);
    border:1px solid rgba(72,125,193,0.35);
    border-radius:16px;
    padding:14px;
}
.summary-row {
    display:flex;
    justify-content:space-between;
    gap:12px;
    padding: 5px 0;
    font-size: 0.98rem;
}
.summary-row .k {color: var(--muted) !important;}
.summary-row .v {font-weight: 900;}

[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    width:100%;
    border-radius:14px !important;
    border:1px solid rgba(72,125,193,0.42) !important;
    background: linear-gradient(180deg, rgba(18,55,110,0.96), rgba(15,44,88,0.96)) !important;
    color: #f5f9ff !important;
    font-weight: 900 !important;
    font-size: 1rem !important;
    padding: 0.78rem 1rem !important;
}
[data-testid="stButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    border-color: rgba(109,225,255,0.65) !important;
    filter: brightness(1.05);
}
.stTextInput input {
    background: rgba(13,38,79,0.92) !important;
    color: #f5f9ff !important;
    border: 1px solid rgba(72,125,193,0.42) !important;
    border-radius: 14px !important;
}
[data-testid="stRadio"] label {
    color: var(--text) !important;
}
[data-testid="stRadio"] > label {
    font-size: 0.92rem !important;
    font-weight: 800 !important;
    color: var(--muted) !important;
}
[data-testid="stRadio"] [role="radiogroup"] {
    gap: 8px;
}
[data-testid="stRadio"] [role="radiogroup"] label {
    background: rgba(13,38,79,0.92) !important;
    border: 1px solid rgba(72,125,193,0.42) !important;
    border-radius: 14px !important;
    padding: 10px 12px !important;
}
[data-testid="stRadio"] [role="radiogroup"] label:hover {
    border-color: rgba(109,225,255,0.65) !important;
}
.stCaption {
    color: var(--muted) !important;
}

@media (max-width: 1100px) {
    .metric-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .compare-strip { grid-template-columns: 1fr; }
    .traffic-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .hero { flex-direction: column; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Database helpers
# ---------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
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
        """
    )
    defaults = {
        "session_open": "0",
        "frozen": "0",
        "frozen_payload": "",
        "public_url": DEFAULT_PUBLIC_URL,
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
    cur.execute(
        """
        INSERT INTO votes (voter_name, mask, distance, vaccine, closure, testing, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (voter_name.strip(), mask, distance, vaccine, closure, testing, datetime.utcnow().isoformat()),
    )
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


# ---------------------------------------------------------
# URL / QR
# ---------------------------------------------------------
def normalize_public_url(url: str) -> str:
    url = (url or DEFAULT_PUBLIC_URL).strip()
    if not url:
        url = DEFAULT_PUBLIC_URL
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url.rstrip("/")


def get_public_url() -> str:
    try:
        secret_url = st.secrets.get("PUBLIC_URL", "")
    except Exception:
        secret_url = ""
    saved_url = get_setting("public_url", DEFAULT_PUBLIC_URL)
    url = normalize_public_url(secret_url or saved_url or DEFAULT_PUBLIC_URL)
    if url != saved_url:
        set_setting("public_url", url)
    return url


def vote_url() -> str:
    return f"{get_public_url()}?mode=vote"


@st.cache_data(show_spinner=False)
def make_qr(url: str) -> bytes:
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------
# Forecast model
# ---------------------------------------------------------
MASK_EFFECT = {"None (0%)": 1.00, "Low (25%)": 0.92, "Medium (60%)": 0.82, "High (90%)": 0.70}
DISTANCE_EFFECT = {"None": 1.00, "Mild": 0.93, "Moderate": 0.84, "Strict": 0.74}
VACCINE_EFFECT = {"0%": 1.00, "30%": 0.90, "60%": 0.78, "90%": 0.62}
CLOSURE_EFFECT = {"Open": 1.00, "Partial": 0.88, "Full": 0.76}
TESTING_EFFECT = {"Low": 1.00, "Moderate": 0.96, "High": 0.91}

HIST_WEEKS = 26
FC_WEEKS = 12
SEED = 42


@st.cache_data(show_spinner=False)
def generate_historical(seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, HIST_WEEKS)
    wave1 = 1500 * np.exp(-((t - 0.28) ** 2) / 0.018)
    wave2 = 2600 * np.exp(-((t - 0.78) ** 2) / 0.024)
    baseline = 520 + 180 * np.sin(2 * np.pi * t * 1.2)
    noise = rng.normal(0, 90, HIST_WEEKS)
    history = np.clip(baseline + wave1 + wave2 + noise, 120, None)
    return history.astype(float)


def holt_winters(series: np.ndarray, n_ahead: int, alpha: float = 0.33, beta: float = 0.16, season_len: int = 4):
    level = series[:season_len].mean()
    trend = (series[season_len:2 * season_len].mean() - level) / season_len
    seasons = list(series[:season_len] - level)
    n = len(series)
    for t in range(n):
        s_idx = t % season_len
        prev_level = level
        level = alpha * (series[t] - seasons[s_idx]) + (1 - alpha) * (level + trend)
        trend = beta * (level - prev_level) + (1 - beta) * trend
        seasons[s_idx] = series[t] - prev_level
    fc = np.zeros(n_ahead)
    for i in range(n_ahead):
        fc[i] = level + (i + 1) * trend + seasons[(n + i) % season_len]
    return np.clip(fc, 0, None)


def linear_trend(series: np.ndarray, n_ahead: int, window: int = 8):
    y = series[-window:]
    x = np.arange(window, dtype=float)
    slope = np.polyfit(x, y, 1)[0]
    intercept = y.mean() - slope * x.mean()
    fut_x = np.arange(window, window + n_ahead, dtype=float)
    fc = intercept + slope * fut_x
    return np.clip(fc, 0, None)


def ensemble_forecast(series: np.ndarray, n_ahead: int):
    hw = holt_winters(series, n_ahead)
    lt = linear_trend(series, n_ahead)
    mean = 0.67 * hw + 0.33 * lt
    sigma = np.maximum(45, mean * (0.08 + 0.01 * np.arange(n_ahead)))
    return mean, np.clip(mean - sigma, 0, None), mean + sigma


def default_consensus():
    return {
        "mask": "None (0%)",
        "distance": "None",
        "vaccine": "0%",
        "closure": "Open",
        "testing": "Low",
    }


def vote_consensus(votes_df: pd.DataFrame) -> dict:
    if votes_df.empty:
        return default_consensus()
    out = {}
    for col, default in default_consensus().items():
        mode = votes_df[col].mode()
        out[col] = mode.iat[0] if not mode.empty else default
    return out


def compute_multiplier(consensus: dict) -> float:
    return (
        MASK_EFFECT[consensus["mask"]]
        * DISTANCE_EFFECT[consensus["distance"]]
        * VACCINE_EFFECT[consensus["vaccine"]]
        * CLOSURE_EFFECT[consensus["closure"]]
        * TESTING_EFFECT[consensus["testing"]]
    )


def apply_interventions(base_fc, base_lo, base_hi, mult: float):
    ramp_len = min(4, len(base_fc))
    ramp = np.linspace(1.0, mult, ramp_len)
    full = np.full(len(base_fc), mult)
    full[:ramp_len] = ramp
    cur_fc = base_fc * full
    cur_lo = base_lo * full
    cur_hi = base_hi * full
    return cur_fc, cur_lo, cur_hi


def metrics_from(fc: np.ndarray) -> dict:
    peak_val = int(fc.max())
    peak_week = int(fc.argmax()) + 1
    total = int(fc.sum())
    week1 = int(fc[0])
    week_last = int(fc[-1])
    trend = "↓ Declining" if fc[-1] < fc[0] else "↑ Growing"
    trend_pct = abs(fc[-1] - fc[0]) / max(fc[0], 1) * 100
    return {
        "peak_val": peak_val,
        "peak_week": peak_week,
        "total": total,
        "week1": week1,
        "week_last": week_last,
        "trend": trend,
        "trend_pct": round(trend_pct, 1),
    }


def driver_table(consensus: dict) -> pd.DataFrame:
    rows = [
        ("Masking", (1 - MASK_EFFECT[consensus["mask"]]) * 100),
        ("Distancing", (1 - DISTANCE_EFFECT[consensus["distance"]]) * 100),
        ("Vaccination", (1 - VACCINE_EFFECT[consensus["vaccine"]]) * 100),
        ("Closures", (1 - CLOSURE_EFFECT[consensus["closure"]]) * 100),
        ("Testing", (1 - TESTING_EFFECT[consensus["testing"]]) * 100),
    ]
    return pd.DataFrame(rows, columns=["driver", "reduction_pct"]).sort_values("reduction_pct")


# ---------------------------------------------------------
# Metro hospitals only
# ---------------------------------------------------------
METRO_HOSPITALS = pd.DataFrame(
    {
        "hospital": [
            "Vancouver General",
            "BC Children's",
            "St. Paul's",
            "Burnaby Hospital",
            "Royal Columbian",
            "Surrey Memorial",
            "Richmond Hospital",
            "Lions Gate",
            "Eagle Ridge",
            "Peace Arch",
        ],
        "lat": [49.2612, 49.2648, 49.2806, 49.2500, 49.2216, 49.1794, 49.1705, 49.3156, 49.2768, 49.0286],
        "lon": [-123.1237, -123.1237, -123.1242, -122.9693, -122.8901, -122.8426, -123.1367, -123.0698, -122.7929, -122.8023],
        "weight": [1.18, 0.88, 0.95, 0.86, 1.02, 1.15, 0.78, 0.72, 0.68, 0.62],
    }
)


def distribute_cases(total_cases: float, base_df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    weights = base_df["weight"].to_numpy(dtype=float)
    weights = weights / weights.sum()
    jitter = rng.uniform(0.94, 1.07, len(base_df))
    raw = total_cases * weights * jitter
    raw = raw / raw.sum() * total_cases
    out = base_df.copy()
    out["cases"] = np.maximum(10, raw).round().astype(int)
    max_cases = max(out["cases"].max(), 1)
    out["risk"] = pd.cut(
        out["cases"] / max_cases,
        bins=[-np.inf, 0.35, 0.68, np.inf],
        labels=["Green", "Yellow", "Red"],
    ).astype(str)
    return out


def spread_light_color(label: str) -> str:
    return {"Green": "#22c55e", "Yellow": "#f59e0b", "Red": "#ef4444"}.get(label, "#22c55e")


# ---------------------------------------------------------
# Plot builders
# ---------------------------------------------------------
def build_forecast_chart(history, base_fc, cur_fc, cur_lo, cur_hi, hist_dates, fc_dates, live_mode=True):
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=list(fc_dates) + list(fc_dates[::-1]),
            y=list(cur_hi) + list(cur_lo[::-1]),
            fill="toself",
            fillcolor="rgba(67,180,255,0.12)",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
            name="Prediction band",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=fc_dates,
            y=base_fc,
            mode="lines",
            name="Baseline (no intervention)",
            line=dict(color="rgba(245,158,11,0.9)", width=2.2, dash="dot"),
            hovertemplate="<b>%{x|%b %d}</b><br>Baseline: %{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=hist_dates,
            y=history,
            mode="lines+markers",
            name="Historical cases",
            line=dict(color="#8aa7d8", width=2.3),
            marker=dict(size=5, color="#8aa7d8"),
            hovertemplate="<b>%{x|%b %d}</b><br>Observed: %{y:,.0f}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=fc_dates,
            y=cur_fc,
            mode="lines+markers",
            name="Live prediction",
            line=dict(color="#ff5c4d", width=3.0),
            marker=dict(size=5, color="#ff5c4d"),
            hovertemplate="<b>%{x|%b %d}</b><br>Predicted: %{y:,.0f}<extra></extra>",
        )
    )

    now_x = hist_dates[-1]
    fig.add_vline(
        x=now_x,
        line=dict(color="rgba(255,255,255,0.18)", width=1.2, dash="dash"),
    )
    fig.add_annotation(
        x=now_x,
        y=max(max(history), max(cur_hi)) * 1.02,
        text="NOW",
        showarrow=False,
        font=dict(size=11, color="rgba(255,255,255,0.55)"),
        xanchor="left",
    )

    subtitle = (
        "Live class votes are already shaping the red prediction line."
        if live_mode
        else "Scenario frozen from the last live class consensus."
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=0,
        y=1.12,
        text=subtitle,
        showarrow=False,
        font=dict(size=12, color="#b4c6e8"),
        align="left",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=40, b=8),
        height=360,
        font=dict(color="#eef4ff", size=13),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            font=dict(size=12),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=11),
            tickformat="%b %d",
            linecolor="rgba(255,255,255,0.08)",
            zeroline=False,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(255,255,255,0.06)",
            tickfont=dict(size=11),
            linecolor="rgba(255,255,255,0.08)",
            tickformat=",d",
            zeroline=False,
        ),
        hovermode="x unified",
    )
    return fig


def build_driver_chart(drivers_df: pd.DataFrame):
    fig = go.Figure(
        go.Bar(
            x=drivers_df["reduction_pct"],
            y=drivers_df["driver"],
            orientation="h",
            marker=dict(color="#43b4ff"),
            text=[f"-{x:.0f}%" for x in drivers_df["reduction_pct"]],
            textposition="outside",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=10, b=8),
        height=280,
        font=dict(color="#eef4ff", size=13),
        xaxis=dict(title="Reduction versus no intervention", gridcolor="rgba(255,255,255,0.06)", ticksuffix="%"),
        yaxis=dict(showgrid=False),
    )
    return fig


def build_hospital_map(df: pd.DataFrame, title: str, subtitle: str):
    colors = df["risk"].map({"Green": "#22c55e", "Yellow": "#f59e0b", "Red": "#ef4444"}).tolist()
    max_cases = max(df["cases"].max(), 1)
    sizes = 16 + (df["cases"] / max_cases) * 28
    halo_sizes = sizes + 16

    fig = go.Figure()

    fig.add_trace(
        go.Scattermapbox(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers",
            marker=dict(
                size=halo_sizes,
                color=colors,
                opacity=0.18,
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig.add_trace(
        go.Scattermapbox(
            lat=df["lat"],
            lon=df["lon"],
            mode="markers+text",
            text=df["hospital"],
            textposition="top center",
            marker=dict(
                size=sizes,
                color=colors,
                opacity=0.85,
                line=dict(width=1.8, color="#ffffff"),
            ),
            hovertemplate="<b>%{text}</b><br>Cases: %{customdata:,}<br>Risk: %{meta}<extra></extra>",
            customdata=df["cases"],
            meta=df["risk"],
            showlegend=False,
        )
    )

    fig.update_layout(
        mapbox=dict(
            style="carto-darkmatter",
            center=dict(lat=49.23, lon=-122.98),
            zoom=8.7,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=48, b=0),
        height=380,
        font=dict(color="#eef4ff"),
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:12px;color:#b4c6e8'>{subtitle}</span>",
            x=0.02,
            y=0.97,
            font=dict(size=16),
        ),
    )
    return fig


# ---------------------------------------------------------
# Page renderers
# ---------------------------------------------------------
def render_vote_page():
    st_autorefresh(interval=2500, limit=None, key="vote_refresh")
    session_open = get_setting("session_open", "0") == "1"

    st.markdown(
        f"""
        <div class="hero">
            <div>
                <div class="hero-title">📱 Vote on outbreak controls</div>
                <div class="hero-sub">Pick the class response. The presenter dashboard and hospital maps update live every few seconds.</div>
            </div>
            <div class="hero-pill">Audience voting page</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not session_open:
        st.warning("Voting is currently closed. Ask the presenter to open the session.")
        return

    with st.form("vote_form", clear_on_submit=True):
        voter_name = st.text_input("Your name or nickname", placeholder="Optional")
        col1, col2 = st.columns(2)
        with col1:
            mask = st.radio("Mask wearing", ["None (0%)", "Low (25%)", "Medium (60%)", "High (90%)"])
            distance = st.radio("Social distancing", ["None", "Mild", "Moderate", "Strict"])
            vaccine = st.radio("Vaccination rate", ["0%", "30%", "60%", "90%"])
        with col2:
            closure = st.radio("School / workplace closure", ["Open", "Partial", "Full"])
            testing = st.radio("Testing intensity", ["Low", "Moderate", "High"])
            st.markdown(
                '<div class="panel"><div class="small-note"><b>Tip:</b> Stronger controls lower the next-week prediction and can flip hospitals from red to yellow or green.</div></div>',
                unsafe_allow_html=True,
            )

        submitted = st.form_submit_button("Submit my vote", use_container_width=True)

    if submitted:
        add_vote(voter_name, mask, distance, vaccine, closure, testing)
        st.success("Vote submitted. The presenter dashboard should update in a few seconds.")
        st.rerun()


def render_dashboard():
    st_autorefresh(interval=2500, limit=None, key="dashboard_refresh")

    votes_df = load_votes()
    live_consensus = vote_consensus(votes_df)
    session_open = get_setting("session_open", "0") == "1"
    frozen = get_setting("frozen", "0") == "1"
    frozen_payload = get_setting("frozen_payload", "")

    if session_open:
        display_consensus = live_consensus.copy()
        live_mode = True
    elif frozen and frozen_payload:
        try:
            display_consensus = json.loads(frozen_payload)
        except Exception:
            display_consensus = default_consensus()
        live_mode = False
    else:
        display_consensus = default_consensus()
        live_mode = False

    public_url = get_public_url()
    qr_bytes = make_qr(vote_url())

    history = generate_historical()
    base_fc, base_lo, base_hi = ensemble_forecast(history, FC_WEEKS)
    multiplier = compute_multiplier(display_consensus)
    cur_fc, cur_lo, cur_hi = apply_interventions(base_fc.copy(), base_lo.copy(), base_hi.copy(), multiplier)

    base_m = metrics_from(base_fc)
    cur_m = metrics_from(cur_fc)
    drivers_df = driver_table(display_consensus)

    hist_dates = [datetime(2024, 1, 7) + timedelta(weeks=i) for i in range(HIST_WEEKS)]
    fc_dates = [hist_dates[-1] + timedelta(weeks=i + 1) for i in range(FC_WEEKS)]

    last_week_total = int(history[-1])
    next_week_total = cur_m["week1"]

    hosp_last = distribute_cases(last_week_total, METRO_HOSPITALS, seed=SEED)
    hosp_next = distribute_cases(next_week_total, METRO_HOSPITALS, seed=SEED + 7)

    peak_delta = cur_m["peak_val"] - base_m["peak_val"]
    total_delta = cur_m["total"] - base_m["total"]
    trend_color = "#22c55e" if "↓" in cur_m["trend"] else "#ef4444"
    mult_pct = round((1 - multiplier) * 100, 1)

    st.markdown(
        f"""
        <div class="hero">
            <div>
                <div class="hero-title"><span style="color:#ef4444;">•</span> Metro Vancouver COVID Forecaster</div>
                <div class="hero-sub">ML time-series ensemble · Holt-Winters + linear trend · <b>{'LIVE VOTING OPEN' if session_open else ('FROZEN SCENARIO' if frozen else 'SESSION CLOSED')}</b> · {len(votes_df)} votes cast</div>
            </div>
            <div class="hero-pill">Presenter dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Peak weekly cases</div>
                <div class="metric-value">{cur_m['peak_val']:,}</div>
                <div class="metric-sub">Week {cur_m['peak_week']} · {'↓' if peak_delta < 0 else '↑' if peak_delta > 0 else '—'} {abs(peak_delta):,} vs baseline</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">12-week total</div>
                <div class="metric-value">{cur_m['total']:,}</div>
                <div class="metric-sub">{'↓' if total_delta < 0 else '↑' if total_delta > 0 else '—'} {abs(total_delta):,} vs baseline</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Forecast trend</div>
                <div class="metric-value" style="font-size:1.7rem;color:{trend_color}">{cur_m['trend']}</div>
                <div class="metric-sub">{cur_m['trend_pct']}% over forecast horizon</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Intervention effect</div>
                <div class="metric-value">-{mult_pct}%</div>
                <div class="metric-sub">Combined class multiplier: ×{multiplier:.2f}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([2.65, 1.0], gap="large")

    with left:
        st.markdown('<div class="section-title">ML forecast · weekly new cases · Metro Vancouver</div>', unsafe_allow_html=True)
        forecast_fig = build_forecast_chart(history, base_fc, cur_fc, cur_lo, cur_hi, hist_dates, fc_dates, live_mode=live_mode)
        st.plotly_chart(forecast_fig, use_container_width=True, config={"displayModeBar": False})

        map_a, map_b = st.columns(2)
        with map_a:
            st.plotly_chart(
                build_hospital_map(
                    hosp_last,
                    title="Observed hospital map · last week",
                    subtitle=f"These are the latest observed hospital-linked case loads feeding the model ({last_week_total:,} total).",
                ),
                use_container_width=True,
                config={"displayModeBar": False},
            )
        with map_b:
            st.plotly_chart(
                build_hospital_map(
                    hosp_next,
                    title="Predicted hospital map · next week",
                    subtitle=f"Live class votes shift the next-week prediction to {next_week_total:,} cases.",
                ),
                use_container_width=True,
                config={"displayModeBar": False},
            )

        st.markdown('<div class="section-title">Metro hospital lights and model drivers</div>', unsafe_allow_html=True)
        m1, m2 = st.columns([1.45, 1.0], gap="large")
        with m1:
            traffic_html = '<div class="traffic-grid">'
            for _, row in hosp_next.sort_values("cases", ascending=False).head(8).iterrows():
                traffic_html += f'''
                <div class="traffic-card">
                    <div class="traffic-dot" style="background:{spread_light_color(row['risk'])};"></div>
                    <div class="traffic-name">{row['hospital']}</div>
                    <div class="traffic-val">{int(row['cases']):,} cases · {row['risk']}</div>
                </div>
                '''
            traffic_html += '</div>'
            st.markdown(traffic_html, unsafe_allow_html=True)

            st.markdown(
                '<div class="panel" style="margin-top:12px;"><div class="small-note"><b>How to read this:</b> the left hospital map shows the most recent observed case pressure. The right hospital map shows the next-week prediction. Bigger circles and red lights mean heavier forecasted spread around those hospitals.</div></div>',
                unsafe_allow_html=True,
            )
        with m2:
            st.plotly_chart(build_driver_chart(drivers_df), use_container_width=True, config={"displayModeBar": False})

        st.markdown('<div class="section-title">Before / after intervention</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="compare-strip">
                <div class="compare-card before-card">
                    <div class="compare-label">Before votes (baseline)</div>
                    <div class="compare-row">Peak weekly cases <span>{base_m['peak_val']:,}</span></div>
                    <div class="compare-row">12-week total <span>{base_m['total']:,}</span></div>
                    <div class="compare-row">Week 1 prediction <span>{base_m['week1']:,}</span></div>
                    <div class="compare-row">Multiplier <span>×1.00</span></div>
                </div>
                <div class="compare-card after-card">
                    <div class="compare-label">After votes (current)</div>
                    <div class="compare-row">Peak weekly cases <span>{cur_m['peak_val']:,}</span></div>
                    <div class="compare-row">12-week total <span>{cur_m['total']:,}</span></div>
                    <div class="compare-row">Week 1 prediction <span>{cur_m['week1']:,}</span></div>
                    <div class="compare-row">Multiplier <span>×{multiplier:.2f}</span></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="banner-note"><b>How the ML model works:</b> the app first learns the outbreak shape from historical weekly cases using a weighted ensemble of Holt-Winters exponential smoothing and a linear trend model. Then the current class votes act like policy parameters, reducing the baseline forecast through a combined multiplier that ramps in over the first four weeks.</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="section-title">Scan to vote</div>', unsafe_allow_html=True)
        st.image(qr_bytes, width=210)
        st.caption(vote_url())
        st.download_button("Download QR", qr_bytes, file_name="covid_vote_qr.png", mime="image/png")

        st.markdown('<div class="section-title">Session</div>', unsafe_allow_html=True)
        if session_open:
            if st.button("Close voting session", use_container_width=True):
                set_setting("session_open", "0")
                st.rerun()
            st.markdown(
                f'<div class="vote-stat">Open · {len(votes_df)} votes received · dashboard auto-refreshes every 2.5s</div>',
                unsafe_allow_html=True,
            )
        else:
            if st.button("Open voting session", use_container_width=True):
                set_setting("session_open", "1")
                set_setting("frozen", "0")
                set_setting("frozen_payload", "")
                st.rerun()
            st.markdown(
                '<div class="vote-stat">Closed · open the session to accept student votes</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="section-title">Current class consensus</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="summary-box">
                <div class="summary-row"><div class="k">Mask</div><div class="v">{display_consensus['mask']}</div></div>
                <div class="summary-row"><div class="k">Distance</div><div class="v">{display_consensus['distance']}</div></div>
                <div class="summary-row"><div class="k">Vaccination</div><div class="v">{display_consensus['vaccine']}</div></div>
                <div class="summary-row"><div class="k">Closure</div><div class="v">{display_consensus['closure']}</div></div>
                <div class="summary-row"><div class="k">Testing</div><div class="v">{display_consensus['testing']}</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="section-title">Actions</div>', unsafe_allow_html=True)
        if session_open:
            if st.button("Freeze current live scenario", use_container_width=True):
                set_setting("frozen_payload", json.dumps(live_consensus))
                set_setting("frozen", "1")
                set_setting("session_open", "0")
                st.rerun()
        else:
            if frozen and st.button("Resume live voting", use_container_width=True):
                set_setting("frozen", "0")
                set_setting("frozen_payload", "")
                set_setting("session_open", "1")
                st.rerun()

        if st.button("Reset to baseline", use_container_width=True):
            clear_votes()
            set_setting("session_open", "0")
            set_setting("frozen", "0")
            set_setting("frozen_payload", "")
            st.rerun()

        st.markdown('<div class="small-note" style="margin-top:10px;">The QR code points to: ' + vote_url() + '</div>', unsafe_allow_html=True)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
init_db()
mode = st.query_params.get("mode", "dashboard")

if mode == "vote":
    render_vote_page()
else:
    render_dashboard()