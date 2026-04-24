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

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

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
    font-family: 'Space Grotesk', ui-sans-serif, system-ui, sans-serif;
    color: var(--text) !important;
}

.stApp, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
}
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer { visibility: hidden; }

/* Kill ALL default Streamlit top padding / whitespace */
.block-container {
    max-width: 1420px;
    padding-top: 0.3rem !important;
    padding-bottom: 2rem;
}
[data-testid="stAppViewBlockContainer"] {
    padding-top: 0 !important;
}
/* Remove gap between plotly charts and surrounding elements */
[data-testid="stPlotlyChart"] {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding: 0 !important;
}
div[data-testid="element-container"] {
    margin-bottom: 0 !important;
}

h1, h2, h3, h4, h5, h6, p, label, div, span {
    color: var(--text) !important;
}

/* HERO */
.hero {
    display: flex;
    justify-content: space-between;
    gap: 18px;
    align-items: flex-start;
    background: linear-gradient(135deg, rgba(15,40,90,0.97) 0%, rgba(8,22,54,0.97) 100%);
    border: 1px solid rgba(72,125,193,0.50);
    border-radius: 22px;
    padding: 22px 24px 20px;
    margin-bottom: 14px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.28), inset 0 1px 0 rgba(255,255,255,0.06);
}
.hero-title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    line-height: 1.03;
    margin: 0;
}
.hero-sub {
    margin-top: 8px;
    font-size: 0.95rem;
    line-height: 1.5;
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace;
}
.hero-pill {
    border: 1px solid rgba(100,153,220,0.40);
    background: rgba(8,24,51,0.88);
    padding: 10px 18px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.92rem;
    white-space: nowrap;
    letter-spacing: 0.03em;
}

/* METRIC GRID */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0,1fr));
    gap: 12px;
    margin-bottom: 12px;
}
.metric-card {
    background: linear-gradient(160deg, rgba(13,38,79,0.98), rgba(8,22,50,0.98));
    border: 1px solid rgba(72,125,193,0.38);
    border-radius: 16px;
    padding: 16px 18px 14px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.18);
}
.metric-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: var(--subtle) !important;
    font-weight: 700;
    margin-bottom: 8px;
    font-family: 'JetBrains Mono', monospace;
}
.metric-value {
    font-size: 2.05rem;
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.02em;
}
.metric-sub {
    margin-top: 7px;
    font-size: 0.88rem;
    color: var(--muted) !important;
    line-height: 1.4;
}

/* SECTION TITLES — much bigger and more prominent */
.section-title {
    font-size: 1.05rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--accent-2) !important;
    margin: 18px 0 12px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, rgba(109,225,255,0.50), rgba(109,225,255,0.03));
    border-radius: 2px;
}

/* PANEL */
.panel {
    background: linear-gradient(180deg, rgba(10,29,63,0.98), rgba(8,22,50,0.98));
    border: 1px solid rgba(72,125,193,0.38);
    border-radius: 16px;
    padding: 16px;
}
.small-note {
    color: var(--muted) !important;
    font-size: 0.93rem;
    line-height: 1.6;
}

/* TRAFFIC LIGHTS */
.traffic-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0,1fr));
    gap: 10px;
    align-items: start;
}
.traffic-card {
    background: rgba(8,22,50,0.86);
    border: 1px solid rgba(72,125,193,0.30);
    border-radius: 14px;
    padding: 14px 12px;
    text-align: center;
    min-height: 100px;
}
.traffic-dot {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    display: inline-block;
    margin-bottom: 7px;
}
.traffic-name {
    font-size: 0.88rem;
    font-weight: 700;
    letter-spacing: -0.01em;
}
.traffic-val {
    margin-top: 5px;
    font-size: 0.82rem;
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace;
}

/* BEFORE / AFTER — bigger, clearer */
.compare-strip {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 10px;
}
.compare-card {
    border-radius: 18px;
    padding: 22px 22px 18px;
}
.before-card {
    background: linear-gradient(145deg, #2a1808, #1e1004);
    border: 1px solid #72401a;
}
.after-card {
    background: linear-gradient(145deg, #0a2945, #061a30);
    border: 1px solid #2a6996;
}
.compare-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace;
    margin-bottom: 10px;
}
.compare-headline {
    font-size: 2.0rem;
    font-weight: 900;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin-bottom: 16px;
}
.compare-row {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    padding: 9px 0;
    font-size: 1.02rem;
    color: var(--muted) !important;
    border-bottom: 1px solid rgba(255,255,255,0.05);
}
.compare-row:last-child { border-bottom: none; }
.compare-row span {
    font-weight: 800;
    font-size: 1.05rem;
    color: var(--text) !important;
    font-family: 'JetBrains Mono', monospace;
}

/* BANNER */
.banner-note {
    background: linear-gradient(180deg, rgba(13,38,79,0.94), rgba(10,29,63,0.94));
    border: 1px solid rgba(72,125,193,0.38);
    border-left: 4px solid var(--accent);
    border-radius: 16px;
    padding: 15px 18px;
    margin-top: 16px;
    font-size: 0.95rem;
    line-height: 1.65;
    color: var(--muted) !important;
}

/* SIDEBAR */
.vote-stat {
    font-size: 0.88rem;
    color: var(--muted) !important;
    margin-top: 8px;
    font-family: 'JetBrains Mono', monospace;
}
.summary-box {
    background: rgba(8,22,50,0.85);
    border: 1px solid rgba(72,125,193,0.32);
    border-radius: 14px;
    padding: 14px 16px;
}
.summary-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 7px 0;
    font-size: 0.95rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.summary-row:last-child { border-bottom: none; }
.summary-row .k { color: var(--muted) !important; }
.summary-row .v { font-weight: 800; font-family: 'JetBrains Mono', monospace; }

/* STATUS PILLS */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 16px;
    border-radius: 999px;
    font-weight: 800;
    font-size: 0.95rem;
    margin-top: 10px;
    margin-bottom: 4px;
    border: 1px solid rgba(255,255,255,0.18);
    letter-spacing: 0.01em;
}
.status-green  { background: rgba(34,197,94,0.18);  color: #b9ffd1 !important; border-color: rgba(34,197,94,0.40); }
.status-yellow { background: rgba(245,158,11,0.18); color: #ffe1a8 !important; border-color: rgba(245,158,11,0.40); }
.status-red    { background: rgba(239,68,68,0.18);  color: #ffc2c2 !important; border-color: rgba(239,68,68,0.40); }

/* OVERRIDE BOX */
.override-box {
    background: rgba(8,22,50,0.85);
    border: 1px solid rgba(72,125,193,0.32);
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 10px;
}

/* BUTTONS */
[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button,
div[data-testid="stFormSubmitButton"] > button {
    width: 100%;
    border-radius: 12px !important;
    border: 1px solid rgba(72,125,193,0.45) !important;
    background: linear-gradient(160deg, rgba(20,62,122,0.96), rgba(14,40,84,0.96)) !important;
    color: #f5f9ff !important;
    font-weight: 800 !important;
    font-size: 0.96rem !important;
    padding: 0.75rem 1rem !important;
    letter-spacing: 0.02em;
    transition: border-color 0.15s, filter 0.15s;
}
[data-testid="stButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover,
div[data-testid="stFormSubmitButton"] > button:hover {
    border-color: rgba(109,225,255,0.70) !important;
    filter: brightness(1.08);
}

/* INPUTS */
.stTextInput input {
    background: rgba(13,38,79,0.92) !important;
    color: #f5f9ff !important;
    border: 1px solid rgba(72,125,193,0.42) !important;
    border-radius: 12px !important;
}
[data-testid="stRadio"] label { color: var(--text) !important; }
[data-testid="stRadio"] > label {
    font-size: 0.85rem !important;
    font-weight: 700 !important;
    color: var(--muted) !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stRadio"] [role="radiogroup"] { gap: 7px; }
[data-testid="stRadio"] [role="radiogroup"] label {
    background: rgba(13,38,79,0.92) !important;
    border: 1px solid rgba(72,125,193,0.38) !important;
    border-radius: 12px !important;
    padding: 9px 12px !important;
    font-size: 0.93rem !important;
}
[data-testid="stRadio"] [role="radiogroup"] label:hover {
    border-color: rgba(109,225,255,0.65) !important;
}
.stCaption { color: var(--muted) !important; }

@media (max-width: 1100px) {
    .metric-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .compare-strip { grid-template-columns: 1fr; }
    .traffic-grid { grid-template-columns: 1fr; }
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
        "frozen": "0",
        "frozen_payload": "",
        "public_url": DEFAULT_PUBLIC_URL,
        "presenter_override": "1.00",
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


def add_vote(voter_name, mask, distance, vaccine, closure, testing):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO votes (voter_name, mask, distance, vaccine, closure, testing, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
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
MASK_EFFECT     = {"None (0%)": 1.00, "Low (25%)": 0.85, "Medium (60%)": 0.68, "High (90%)": 0.50}
DISTANCE_EFFECT = {"None": 1.00, "Mild": 0.85, "Moderate": 0.70, "Strict": 0.55}
VACCINE_EFFECT  = {"0%": 1.00, "30%": 0.82, "60%": 0.63, "90%": 0.42}
CLOSURE_EFFECT  = {"Open": 1.00, "Partial": 0.75, "Full": 0.55}
TESTING_EFFECT  = {"Low": 1.00, "Moderate": 0.88, "High": 0.76}

HIST_WEEKS = 26
FC_WEEKS   = 12
SEED       = 42


@st.cache_data(show_spinner=False)
def generate_historical(seed: int = SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t        = np.linspace(0, 1, HIST_WEEKS)
    wave1    = 1500 * np.exp(-((t - 0.28) ** 2) / 0.018)
    wave2    = 2600 * np.exp(-((t - 0.78) ** 2) / 0.024)
    baseline = 520 + 180 * np.sin(2 * np.pi * t * 1.2)
    noise    = rng.normal(0, 90, HIST_WEEKS)
    return np.clip(baseline + wave1 + wave2 + noise, 120, None).astype(float)


def holt_winters(series, n_ahead, alpha=0.33, beta=0.16, season_len=4):
    level   = series[:season_len].mean()
    trend   = (series[season_len:2*season_len].mean() - level) / season_len
    seasons = list(series[:season_len] - level)
    n       = len(series)
    for t in range(n):
        s_idx      = t % season_len
        prev_level = level
        level      = alpha * (series[t] - seasons[s_idx]) + (1 - alpha) * (level + trend)
        trend      = beta * (level - prev_level) + (1 - beta) * trend
        seasons[s_idx] = series[t] - prev_level
    fc = np.zeros(n_ahead)
    for i in range(n_ahead):
        fc[i] = level + (i + 1) * trend + seasons[(n + i) % season_len]
    return np.clip(fc, 0, None)


def linear_trend(series, n_ahead, window=8):
    y         = series[-window:]
    x         = np.arange(window, dtype=float)
    slope     = np.polyfit(x, y, 1)[0]
    intercept = y.mean() - slope * x.mean()
    fut_x     = np.arange(window, window + n_ahead, dtype=float)
    return np.clip(intercept + slope * fut_x, 0, None)


def ensemble_forecast(series, n_ahead):
    hw    = holt_winters(series, n_ahead)
    lt    = linear_trend(series, n_ahead)
    mean  = 0.67 * hw + 0.33 * lt
    sigma = np.maximum(45, mean * (0.08 + 0.01 * np.arange(n_ahead)))
    return mean, np.clip(mean - sigma, 0, None), mean + sigma


def default_consensus():
    return {"mask": "None (0%)", "distance": "None", "vaccine": "0%", "closure": "Open", "testing": "Low"}


def vote_consensus(votes_df: pd.DataFrame) -> dict:
    if votes_df.empty:
        return default_consensus()
    out = {}
    for col, default in default_consensus().items():
        mode    = votes_df[col].mode()
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


def apply_interventions(base_fc, base_lo, base_hi, mult):
    # Apply multiplier immediately from week 1 — no ramp — so votes visibly
    # move the very next week prediction and hospital map colours.
    full = np.full(len(base_fc), mult)
    return base_fc * full, base_lo * full, base_hi * full


def apply_presenter_override(fc, lo, hi, override_mult):
    return fc * override_mult, lo * override_mult, hi * override_mult


def metrics_from(fc: np.ndarray) -> dict:
    peak_val  = int(fc.max())
    peak_week = int(fc.argmax()) + 1
    total     = int(fc.sum())
    week1     = int(fc[0])
    trend     = "↓ Declining" if fc[-1] < fc[0] else "↑ Growing"
    trend_pct = abs(fc[-1] - fc[0]) / max(fc[0], 1) * 100
    return dict(peak_val=peak_val, peak_week=peak_week, total=total,
                week1=week1, week_last=int(fc[-1]), trend=trend, trend_pct=round(trend_pct, 1))


def driver_table(consensus: dict) -> pd.DataFrame:
    rows = [
        ("Masking",     (1 - MASK_EFFECT[consensus["mask"]]) * 100),
        ("Distancing",  (1 - DISTANCE_EFFECT[consensus["distance"]]) * 100),
        ("Vaccination", (1 - VACCINE_EFFECT[consensus["vaccine"]]) * 100),
        ("Closures",    (1 - CLOSURE_EFFECT[consensus["closure"]]) * 100),
        ("Testing",     (1 - TESTING_EFFECT[consensus["testing"]]) * 100),
    ]
    return pd.DataFrame(rows, columns=["driver", "reduction_pct"]).sort_values("reduction_pct")


def severity_status(cur_m: dict):
    if cur_m["peak_val"] >= 2200 or cur_m["week1"] >= 1800 or cur_m["total"] >= 18000:
        return {"icon": "🚨", "label": "Too many cases", "css": "status-red"}
    if "↓" in cur_m["trend"]:
        return {"icon": "✅", "label": "Declining", "css": "status-green"}
    return {"icon": "⚠️", "label": "Cases rising", "css": "status-yellow"}


# ---------------------------------------------------------
# Metro hospitals
# ---------------------------------------------------------
METRO_HOSPITALS = pd.DataFrame({
    "hospital": [
        "Vancouver General", "BC Children's", "St. Paul's", "Burnaby Hospital",
        "Royal Columbian", "Surrey Memorial", "Richmond Hospital",
        "Lions Gate", "Eagle Ridge", "Peace Arch",
    ],
    "lat":    [49.2612, 49.2648, 49.2806, 49.2500, 49.2216, 49.1794, 49.1705, 49.3156, 49.2768, 49.0286],
    "lon":    [-123.1237, -123.1237, -123.1242, -122.9693, -122.8901, -122.8426, -123.1367, -123.0698, -122.7929, -122.8023],
    "weight": [1.18, 0.88, 0.95, 0.86, 1.02, 1.15, 0.78, 0.72, 0.68, 0.62],
})


def distribute_cases(total_cases: float, base_df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """
    Risk colours use ABSOLUTE per-hospital thresholds so they genuinely
    change as the multiplier / votes shift total_cases up or down.

    Thresholds (cases per hospital):
      Green  : < 60   cases  — manageable
      Yellow : 60–120 cases  — elevated
      Red    : > 120  cases  — high pressure
    """
    rng     = np.random.default_rng(seed)
    weights = base_df["weight"].to_numpy(dtype=float)
    weights = weights / weights.sum()
    # Small deterministic jitter so hospitals don't all land on exact same share
    jitter  = rng.uniform(0.94, 1.07, len(base_df))
    raw     = total_cases * weights * jitter
    raw     = raw / raw.sum() * total_cases

    out          = base_df.copy()
    out["cases"] = np.maximum(10, raw).round().astype(int)

    # Absolute thresholds — these are what actually make colours change
    def _risk(n):
        if n < 60:
            return "Green"
        elif n < 120:
            return "Yellow"
        else:
            return "Red"

    out["risk"] = out["cases"].apply(_risk)
    return out


def spread_light_color(label: str) -> str:
    return {"Green": "#22c55e", "Yellow": "#f59e0b", "Red": "#ef4444"}.get(label, "#22c55e")


# ---------------------------------------------------------
# Plot builders
# ---------------------------------------------------------
def build_forecast_chart(history, base_fc, cur_fc, cur_lo, cur_hi, hist_dates, fc_dates, live_mode=True):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=list(fc_dates) + list(fc_dates[::-1]),
        y=list(cur_hi) + list(cur_lo[::-1]),
        fill="toself", fillcolor="rgba(67,180,255,0.10)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fc_dates, y=base_fc, mode="lines",
        name="Baseline (no intervention)",
        line=dict(color="rgba(245,158,11,0.85)", width=2, dash="dot"),
        hovertemplate="<b>%{x|%b %d}</b><br>Baseline: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=hist_dates, y=history, mode="lines+markers",
        name="Historical cases",
        line=dict(color="#8aa7d8", width=2.2),
        marker=dict(size=4, color="#8aa7d8"),
        hovertemplate="<b>%{x|%b %d}</b><br>Observed: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=fc_dates, y=cur_fc, mode="lines+markers",
        name="Live prediction",
        line=dict(color="#ff5c4d", width=3.0),
        marker=dict(size=5, color="#ff5c4d"),
        hovertemplate="<b>%{x|%b %d}</b><br>Predicted: %{y:,.0f}<extra></extra>",
    ))

    now_x = hist_dates[-1]
    fig.add_vline(x=now_x, line=dict(color="rgba(255,255,255,0.15)", width=1, dash="dash"))
    fig.add_annotation(
        x=now_x,
        y=max(max(history), max(cur_hi)) * 1.02,
        text="NOW", showarrow=False,
        font=dict(size=10, color="rgba(255,255,255,0.45)"),
        xanchor="left",
    )
    subtitle = (
        "Live class votes are shaping the red prediction line."
        if live_mode else "Scenario frozen from the last live class consensus."
    )
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=1.12,
        text=subtitle, showarrow=False,
        font=dict(size=11, color="#b4c6e8"), align="left",
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=4, r=4, t=36, b=4),
        height=340,
        font=dict(color="#eef4ff", size=12),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0,
            font=dict(size=11), bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10), tickformat="%b %d",
                   linecolor="rgba(255,255,255,0.07)", zeroline=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.05)",
                   tickfont=dict(size=10), linecolor="rgba(255,255,255,0.07)",
                   tickformat=",d", zeroline=False),
        hovermode="x unified",
    )
    return fig


def build_driver_chart(drivers_df: pd.DataFrame):
    df       = drivers_df.copy().sort_values("reduction_pct", ascending=True)
    max_val  = float(df["reduction_pct"].max()) if len(df) else 0.0
    axis_max = max(5.0, max_val * 1.3)

    bar_colors = [
        "#22c55e" if x < 5 else "#f59e0b" if x < 20 else "#43b4ff"
        for x in df["reduction_pct"]
    ]

    fig = go.Figure(go.Bar(
        x=df["reduction_pct"], y=df["driver"],
        orientation="h",
        marker=dict(color=bar_colors),
        text=[f"-{x:.0f}%" for x in df["reduction_pct"]],
        textposition="outside",
        textfont=dict(size=13, color="#eef4ff"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=4, r=20, t=6, b=4),
        height=210,
        font=dict(color="#eef4ff", size=12),
        xaxis=dict(
            title=dict(text="Case reduction vs no intervention", font=dict(size=11)),
            gridcolor="rgba(255,255,255,0.05)",
            ticksuffix="%", range=[0, axis_max], zeroline=False,
        ),
        yaxis=dict(showgrid=False, tickfont=dict(size=12)),
    )
    return fig


def build_hospital_map(df: pd.DataFrame, title: str, subtitle: str):
    colors     = df["risk"].map({"Green": "#22c55e", "Yellow": "#f59e0b", "Red": "#ef4444"}).tolist()
    max_cases  = max(df["cases"].max(), 1)
    sizes      = 16 + (df["cases"] / max_cases) * 28
    halo_sizes = sizes + 16

    fig = go.Figure()
    fig.add_trace(go.Scattermapbox(
        lat=df["lat"], lon=df["lon"], mode="markers",
        marker=dict(size=halo_sizes, color=colors, opacity=0.16),
        hoverinfo="skip", showlegend=False,
    ))
    fig.add_trace(go.Scattermapbox(
        lat=df["lat"], lon=df["lon"], mode="markers+text",
        text=df["hospital"], textposition="top center",
        marker=dict(size=sizes, color=colors, opacity=0.88),
        hovertemplate="<b>%{text}</b><br>Cases: %{customdata:,}<br>Risk: %{meta}<extra></extra>",
        customdata=df["cases"], meta=df["risk"], showlegend=False,
    ))

    fig.update_layout(
        mapbox=dict(style="carto-darkmatter", center=dict(lat=49.23, lon=-122.98), zoom=8.7),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=44, b=0),
        height=370,
        font=dict(color="#eef4ff"),
        title=dict(
            text=f"<b>{title}</b><br><span style='font-size:11px;color:#b4c6e8'>{subtitle}</span>",
            x=0.02, y=0.97, font=dict(size=14),
        ),
    )
    return fig


# ---------------------------------------------------------
# Vote page
# ---------------------------------------------------------
def render_vote_page():
    st_autorefresh(interval=2500, limit=None, key="vote_refresh")
    session_open = get_setting("session_open", "0") == "1"

    st.markdown("""
        <div class="hero">
            <div>
                <div class="hero-title">📱 Vote on outbreak controls</div>
                <div class="hero-sub">Pick the class response. The presenter dashboard and hospital maps update live every few seconds.</div>
            </div>
            <div class="hero-pill">Audience voting page</div>
        </div>
    """, unsafe_allow_html=True)

    if not session_open:
        st.warning("Voting is currently closed. Ask the presenter to open the session.")
        return

    with st.form("vote_form", clear_on_submit=True):
        voter_name = st.text_input("Your name or nickname", placeholder="Optional")
        col1, col2 = st.columns(2)
        with col1:
            mask     = st.radio("Mask wearing", ["None (0%)", "Low (25%)", "Medium (60%)", "High (90%)"])
            distance = st.radio("Social distancing", ["None", "Mild", "Moderate", "Strict"])
            vaccine  = st.radio("Vaccination rate", ["0%", "30%", "60%", "90%"])
        with col2:
            closure = st.radio("School / workplace closure", ["Open", "Partial", "Full"])
            testing = st.radio("Testing intensity", ["Low", "Moderate", "High"])
            st.markdown(
                '<div class="panel"><div class="small-note"><b>Tip:</b> Stronger controls lower the next-week prediction and can flip hospitals red → yellow → green.</div></div>',
                unsafe_allow_html=True,
            )
        submitted = st.form_submit_button("Submit my vote", use_container_width=True)

    if submitted:
        add_vote(voter_name, mask, distance, vaccine, closure, testing)
        st.success("Vote submitted. The presenter dashboard should update in a few seconds.")
        st.rerun()


# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
def render_dashboard():
    st_autorefresh(interval=2500, limit=None, key="dashboard_refresh")

    votes_df           = load_votes()
    live_consensus     = vote_consensus(votes_df)
    session_open       = get_setting("session_open", "0") == "1"
    frozen             = get_setting("frozen", "0") == "1"
    frozen_payload     = get_setting("frozen_payload", "")
    presenter_override = float(get_setting("presenter_override", "1.00"))

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

    qr_bytes = make_qr(vote_url())

    history                   = generate_historical()
    base_fc, base_lo, base_hi = ensemble_forecast(history, FC_WEEKS)

    intervention_multiplier   = compute_multiplier(display_consensus)
    cur_fc, cur_lo, cur_hi    = apply_interventions(base_fc.copy(), base_lo.copy(), base_hi.copy(), intervention_multiplier)
    cur_fc, cur_lo, cur_hi    = apply_presenter_override(cur_fc, cur_lo, cur_hi, presenter_override)

    base_m     = metrics_from(base_fc)
    cur_m      = metrics_from(cur_fc)
    drivers_df = driver_table(display_consensus)
    status     = severity_status(cur_m)

    hist_dates = [datetime(2024, 1, 7) + timedelta(weeks=i) for i in range(HIST_WEEKS)]
    fc_dates   = [hist_dates[-1] + timedelta(weeks=i + 1) for i in range(FC_WEEKS)]

    last_week_total = int(history[-1])
    next_week_total = cur_m["week1"]

    # FIX: hospital colours now respond to the actual predicted case count
    hosp_last = distribute_cases(last_week_total, METRO_HOSPITALS, seed=SEED)
    hosp_next = distribute_cases(next_week_total, METRO_HOSPITALS, seed=SEED + 7)

    peak_delta       = cur_m["peak_val"] - base_m["peak_val"]
    total_delta      = cur_m["total"] - base_m["total"]
    trend_color      = "#22c55e" if "↓" in cur_m["trend"] else "#ef4444"
    intervention_pct = round((1 - intervention_multiplier) * 100, 1)
    override_pct     = round((presenter_override - 1.0) * 100, 1)

    # HERO
    st.markdown(f"""
        <div class="hero">
            <div>
                <div class="hero-title"><span style="color:#ef4444;">•</span> Metro Vancouver COVID Forecaster</div>
                <div class="hero-sub">ML ensemble · Holt-Winters + linear trend · <b>{'LIVE VOTING OPEN' if session_open else ('FROZEN SCENARIO' if frozen else 'SESSION CLOSED')}</b> · {len(votes_df)} votes cast</div>
                <div class="status-pill {status['css']}">{status['icon']} {status['label']}</div>
            </div>
            <div class="hero-pill">Presenter dashboard</div>
        </div>
    """, unsafe_allow_html=True)

    # METRIC GRID
    st.markdown(f"""
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
                <div class="metric-label">Forecast status</div>
                <div class="metric-value" style="font-size:1.45rem;color:{trend_color}">{status['icon']} {status['label']}</div>
                <div class="metric-sub">{cur_m['trend_pct']}% over forecast horizon</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Intervention + override</div>
                <div class="metric-value">{override_pct:+.0f}%</div>
                <div class="metric-sub">Votes: {intervention_pct:+.1f}% · Override: ×{presenter_override:.2f}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([2.65, 1.0], gap="large")

    with left:
        st.markdown('<div class="section-title">📈 ML Forecast — Weekly New Cases</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_forecast_chart(history, base_fc, cur_fc, cur_lo, cur_hi, hist_dates, fc_dates, live_mode=live_mode),
            use_container_width=True, config={"displayModeBar": False},
        )

        map_a, map_b = st.columns(2)
        with map_a:
            st.plotly_chart(
                build_hospital_map(hosp_last,
                    title="🏥 Last Week — Observed",
                    subtitle=f"Observed case load ({last_week_total:,} total) feeding the model."),
                use_container_width=True, config={"displayModeBar": False},
            )
        with map_b:
            st.plotly_chart(
                build_hospital_map(hosp_next,
                    title="🔴 Next Week — Predicted",
                    subtitle=f"Votes + override shift prediction to {next_week_total:,} cases."),
                use_container_width=True, config={"displayModeBar": False},
            )

        st.markdown('<div class="section-title">🏥 Hospital Risk Lights &amp; Policy Drivers</div>', unsafe_allow_html=True)
        m1, m2 = st.columns([1.7, 1.0], gap="medium")
        with m1:
            traffic_html = '<div class="traffic-grid">'
            for _, row in hosp_next.sort_values("cases", ascending=False).head(8).iterrows():
                c = spread_light_color(row["risk"])
                traffic_html += f'''
                <div class="traffic-card" style="border-color:{c}44;">
                    <div class="traffic-dot" style="background:{c};box-shadow:0 0 12px {c}88;"></div>
                    <div class="traffic-name">{row["hospital"]}</div>
                    <div class="traffic-val">{int(row["cases"]):,} cases · <b style="color:{c}">{row["risk"]}</b></div>
                </div>'''
            traffic_html += '</div>'
            st.markdown(traffic_html, unsafe_allow_html=True)
            st.markdown(
                '<div class="panel" style="margin-top:12px;"><div class="small-note"><b>How to read:</b> Left map = observed last week. Right map = predicted next week. Bigger, redder circles = heavier spread. <b>Colours update live with every vote and override change.</b></div></div>',
                unsafe_allow_html=True,
            )
        with m2:
            st.plotly_chart(build_driver_chart(drivers_df), use_container_width=True, config={"displayModeBar": False})

        # BEFORE / AFTER — much bigger and more scannable
        st.markdown('<div class="section-title">⚖️ Before vs After Interventions</div>', unsafe_allow_html=True)
        combined_mult = intervention_multiplier * presenter_override
        before_status = severity_status(base_m)
        after_status  = severity_status(cur_m)

        st.markdown(f"""
            <div class="compare-strip">
                <div class="compare-card before-card">
                    <div class="compare-label">Before — no intervention (baseline)</div>
                    <div class="compare-headline" style="color:#f97316;">{base_m['peak_val']:,} peak cases</div>
                    <div class="compare-row">12-week total <span>{base_m['total']:,}</span></div>
                    <div class="compare-row">Week 1 prediction <span>{base_m['week1']:,}</span></div>
                    <div class="compare-row">Combined multiplier <span>×1.00</span></div>
                    <div class="compare-row">Status <span>{before_status['icon']} {before_status['label']}</span></div>
                </div>
                <div class="compare-card after-card">
                    <div class="compare-label">After — votes + presenter override</div>
                    <div class="compare-headline" style="color:#43b4ff;">{cur_m['peak_val']:,} peak cases</div>
                    <div class="compare-row">12-week total <span>{cur_m['total']:,}</span></div>
                    <div class="compare-row">Week 1 prediction <span>{cur_m['week1']:,}</span></div>
                    <div class="compare-row">Combined multiplier <span>×{combined_mult:.2f}</span></div>
                    <div class="compare-row">Status <span>{after_status['icon']} {after_status['label']}</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown(
            '<div class="banner-note"><b>How the ML model works:</b> the app first learns the outbreak shape from historical weekly cases using a weighted ensemble of Holt-Winters exponential smoothing and a linear trend model. Class votes act as policy parameters that reduce the baseline forecast through a combined multiplier ramping in over the first four weeks. The presenter can apply an additional scenario override to make the outbreak more or less severe for teaching.</div>',
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="section-title">📱 Scan to Vote</div>', unsafe_allow_html=True)
        st.image(qr_bytes, width=210)
        st.caption(vote_url())
        st.download_button("⬇ Download QR", qr_bytes, file_name="covid_vote_qr.png", mime="image/png")

        st.markdown('<div class="section-title">🔒 Session</div>', unsafe_allow_html=True)
        if session_open:
            if st.button("Close voting session", use_container_width=True):
                set_setting("session_open", "0")
                st.rerun()
            st.markdown(f'<div class="vote-stat">🟢 Open · {len(votes_df)} votes · refreshes every 2.5s</div>', unsafe_allow_html=True)
        else:
            if st.button("Open voting session", use_container_width=True):
                set_setting("session_open", "1")
                set_setting("frozen", "0")
                set_setting("frozen_payload", "")
                st.rerun()
            st.markdown('<div class="vote-stat">🔴 Closed · open to accept student votes</div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">🗳️ Current Consensus</div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="summary-box">
                <div class="summary-row"><div class="k">Mask</div><div class="v">{display_consensus['mask']}</div></div>
                <div class="summary-row"><div class="k">Distance</div><div class="v">{display_consensus['distance']}</div></div>
                <div class="summary-row"><div class="k">Vaccination</div><div class="v">{display_consensus['vaccine']}</div></div>
                <div class="summary-row"><div class="k">Closure</div><div class="v">{display_consensus['closure']}</div></div>
                <div class="summary-row"><div class="k">Testing</div><div class="v">{display_consensus['testing']}</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">🎛️ Presenter Override</div>', unsafe_allow_html=True)
        override_value = st.slider(
            "Scenario severity multiplier",
            min_value=0.50, max_value=2.50,
            value=float(get_setting("presenter_override", "1.00")),
            step=0.05,
            help="1.00 = no override. Above 1.00 = worse outbreak. Below 1.00 = softened.",
        )
        if abs(override_value - presenter_override) > 1e-9:
            set_setting("presenter_override", f"{override_value:.2f}")
            st.rerun()

        st.markdown(f"""
            <div class="override-box">
                <div class="summary-row"><div class="k">Override multiplier</div><div class="v">×{override_value:.2f}</div></div>
                <div class="summary-row"><div class="k">Effect vs neutral</div><div class="v">{(override_value - 1.0)*100:+.0f}%</div></div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">⚡ Actions</div>', unsafe_allow_html=True)
        if session_open:
            if st.button("❄️ Freeze current scenario", use_container_width=True):
                set_setting("frozen_payload", json.dumps(live_consensus))
                set_setting("frozen", "1")
                set_setting("session_open", "0")
                st.rerun()
        else:
            if frozen and st.button("▶️ Resume live voting", use_container_width=True):
                set_setting("frozen", "0")
                set_setting("frozen_payload", "")
                set_setting("session_open", "1")
                st.rerun()

        if st.button("↩️ Reset override to neutral", use_container_width=True):
            set_setting("presenter_override", "1.00")
            st.rerun()

        if st.button("🔄 Reset everything to baseline", use_container_width=True):
            clear_votes()
            set_setting("session_open", "0")
            set_setting("frozen", "0")
            set_setting("frozen_payload", "")
            set_setting("presenter_override", "1.00")
            st.rerun()


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
init_db()
mode = st.query_params.get("mode", "dashboard")

if mode == "vote":
    render_vote_page()
else:
    render_dashboard()