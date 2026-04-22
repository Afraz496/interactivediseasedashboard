
import io
import json
import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import qrcode
import streamlit as st
from branca.element import Element
from streamlit_autorefresh import st_autorefresh
from streamlit_folium import st_folium

APP_TITLE = "Metro Vancouver Outbreak Simulator"
DB_PATH = Path("disease_audience_state.db")
SEED = 42
DEFAULT_PUBLIC_URL = "https://afrazdiseasedashboard.streamlit.app/"

st.set_page_config(page_title=APP_TITLE, page_icon="🦠", layout="wide")

st.markdown("""
<style>
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #0b1020 0%, #10172a 45%, #0b1020 100%);
        color: #eef2ff;
    }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    h1, h2, h3, h4, h5, h6, p, label, div, span {
        color: #eef2ff;
    }
    .block-container {
        padding-top: 1.0rem;
        padding-bottom: 1.2rem;
        max-width: 1500px;
    }
    .hero {
        background: linear-gradient(135deg, rgba(20,184,166,0.18), rgba(59,130,246,0.18));
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 24px;
        padding: 22px 24px;
        margin-bottom: 14px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.22);
    }
    .metric-card, .section-card {
        background: rgba(15, 23, 42, 0.82);
        border: 1px solid rgba(148,163,184,0.14);
        border-radius: 20px;
        padding: 16px 18px;
        box-shadow: 0 8px 24px rgba(0,0,0,0.22);
    }
    .section-card {
        border-radius: 22px;
        padding: 16px 16px 8px 16px;
    }
    .metric-label {
        font-size: 0.88rem;
        color: #cbd5e1;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 1.9rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1.1;
    }
    .metric-sub {
        font-size: 0.9rem;
        color: #94a3b8;
        margin-top: 8px;
    }
    .small-note {
        color: #a5b4fc;
        font-size: 0.9rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
        border-right: 1px solid rgba(148,163,184,0.10);
    }
    [data-testid="stSidebar"] * {
        color: #eef2ff !important;
    }
    .stTextInput input, .stSelectbox [data-baseweb="select"] > div {
        background: rgba(15,23,42,0.94) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(148,163,184,0.25) !important;
        border-radius: 12px !important;
    }
    .stSelectbox [data-baseweb="select"] * {
        color: #f8fafc !important;
    }
    .stButton button, .stDownloadButton button, div[data-testid="stFormSubmitButton"] > button {
        border-radius: 12px !important;
        border: none !important;
        font-weight: 800 !important;
        color: white !important;
        background: linear-gradient(135deg, #0891b2, #2563eb) !important;
    }
    .stButton button:hover, .stDownloadButton button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
        filter: brightness(1.08) !important;
    }
    .stSlider label, .stSlider span, .stSlider div {
        color: #e2e8f0 !important;
    }
    div[role="radiogroup"] label {
        background: rgba(15,23,42,0.92) !important;
        border: 1px solid rgba(148,163,184,0.20) !important;
        border-radius: 12px !important;
        padding: 8px 14px !important;
        margin-right: 8px !important;
    }
    div[role="radiogroup"] * { color: #f8fafc !important; }
    .status-open { color: #86efac; font-weight: 800; }
    .status-locked { color: #fca5a5; font-weight: 800; }
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Shared state
# -----------------------------
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
            disease TEXT NOT NULL,
            horizon REAL NOT NULL,
            base_cases REAL NOT NULL,
            growth REAL NOT NULL,
            mobility REAL NOT NULL,
            prevention REAL NOT NULL,
            vacc_gap REAL NOT NULL,
            lineages REAL NOT NULL,
            seasonality REAL NOT NULL,
            indoor REAL NOT NULL,
            school_mix REAL NOT NULL,
            severity REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    defaults = {
        "accepting_votes": "1",
        "scenario_locked": "0",
        "last_snapshot": "",
        "public_url": DEFAULT_PUBLIC_URL,
    }
    for k, v in defaults.items():
        cur.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
    conn.commit()
    conn.close()


def get_setting(key, default=""):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = cur.fetchone()
    conn.close()
    return row["value"] if row else default


def set_setting(key, value):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    conn.commit()
    conn.close()


def add_vote(voter_name, disease, horizon, base_cases, growth, mobility, prevention,
             vacc_gap, lineages, seasonality, indoor, school_mix, severity):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO votes (
            voter_name, disease, horizon, base_cases, growth, mobility, prevention,
            vacc_gap, lineages, seasonality, indoor, school_mix, severity, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        voter_name, disease, float(horizon), float(base_cases), float(growth),
        float(mobility), float(prevention), float(vacc_gap), float(lineages),
        float(seasonality), float(indoor), float(school_mix), float(severity),
        datetime.utcnow().isoformat()
    ))
    conn.commit()
    conn.close()


def load_votes():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM votes ORDER BY id DESC", conn)
    conn.close()
    return df


def reset_votes():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM votes")
    conn.commit()
    conn.close()
    set_setting("scenario_locked", "0")
    set_setting("last_snapshot", "")
    set_setting("accepting_votes", "1")


# -----------------------------
# Data + model logic
# -----------------------------
@st.cache_data
def load_zones():
    return pd.DataFrame({
        "zone": [
            "Vancouver", "Burnaby", "Richmond", "Surrey",
            "Coquitlam", "North Vancouver", "New Westminster", "Delta"
        ],
        "lat": [49.2827, 49.2488, 49.1666, 49.1913, 49.2838, 49.3200, 49.2057, 49.0847],
        "lon": [-123.1207, -122.9805, -123.1336, -122.8490, -122.7932, -123.0720, -122.9110, -123.0580],
        "base_weight": [1.35, 1.05, 0.92, 1.12, 0.98, 0.82, 0.76, 0.70]
    })


@st.cache_data
def load_hospitals():
    return pd.DataFrame({
        "hospital": [
            "Vancouver General Hospital", "Burnaby Hospital", "Surrey Memorial Hospital",
            "Royal Columbian Hospital", "Lions Gate Hospital", "Richmond Hospital"
        ],
        "zone": ["Vancouver", "Burnaby", "Surrey", "New Westminster", "North Vancouver", "Richmond"],
        "lat": [49.2612, 49.2500, 49.1805, 49.2218, 49.3180, 49.1705],
        "lon": [-123.1237, -122.9693, -122.8448, -122.8895, -123.0683, -123.1367],
        "baseline_beds": [950, 320, 700, 470, 280, 220]
    })


def baseline_params():
    return {
        "disease": "COVID-19",
        "horizon": 14,
        "base_cases": 450,
        "growth": 1.05,
        "mobility": 1.0,
        "prevention": 0.8,
        "vacc_gap": 0.7,
        "lineages": 4,
        "seasonality": 1.2,
        "indoor": 1.0,
        "school_mix": 0.9,
        "severity": 0.45,
    }


def consensus_params(votes_df):
    defaults = baseline_params()
    if votes_df.empty:
        return defaults, 0

    disease = votes_df["disease"].mode().iat[0] if not votes_df["disease"].mode().empty else defaults["disease"]
    params = {
        "disease": disease,
        "horizon": int(round(votes_df["horizon"].mean())),
        "base_cases": int(round(votes_df["base_cases"].mean())),
        "growth": float(votes_df["growth"].mean()),
        "mobility": float(votes_df["mobility"].mean()),
        "prevention": float(votes_df["prevention"].mean()),
        "vacc_gap": float(votes_df["vacc_gap"].mean()),
        "lineages": int(round(votes_df["lineages"].mean())),
        "seasonality": float(votes_df["seasonality"].mean()),
        "indoor": float(votes_df["indoor"].mean()),
        "school_mix": float(votes_df["school_mix"].mean()),
        "severity": float(votes_df["severity"].mean()),
    }
    return params, len(votes_df)


def scenario_forecast(params, zones_df):
    horizon = int(params["horizon"])
    base_cases = params["base_cases"]
    disease = params["disease"]
    disease_factor = {"COVID-19": 1.0, "Respiratory Illness": 1.18, "Influenza-like Illness": 0.92}[disease]

    vaccination_gap = 1 + params["vacc_gap"] * 0.55
    lineage_factor = 1 + params["lineages"] * 0.06
    mobility_factor = 0.72 + params["mobility"] * 0.55
    seasonality_factor = 0.75 + params["seasonality"] * 0.6
    prevention_factor = 1.20 - params["prevention"] * 0.45
    school_factor = 0.88 + params["school_mix"] * 0.35
    indoor_factor = 0.84 + params["indoor"] * 0.42

    growth = (
        1.005
        + (params["growth"] - 1.0) * 0.08
        + params["vacc_gap"] * 0.012
        + params["lineages"] * 0.003
        + params["mobility"] * 0.008
        + params["seasonality"] * 0.006
        - params["prevention"] * 0.007
    )
    growth = max(0.985, min(1.09, growth))

    dates = [datetime.today().date() + timedelta(days=i) for i in range(horizon)]
    city_cases = []
    current = base_cases * disease_factor * vaccination_gap * lineage_factor * mobility_factor * seasonality_factor * prevention_factor * school_factor * indoor_factor / 2.8

    for day in range(horizon):
        wave = 1 + 0.08 * math.sin(day / 3.5) + 0.03 * math.cos(day / 5.0)
        current = current * growth * wave
        city_cases.append(max(10, current))

    city_df = pd.DataFrame({"date": dates, "forecast_cases": np.round(city_cases).astype(int)})

    rng = np.random.default_rng(SEED)
    zone_rows = []
    final_cases = city_df["forecast_cases"].iloc[-1]
    for _, row in zones_df.iterrows():
        zone_multiplier = row["base_weight"] * rng.uniform(0.93, 1.08)
        zcases = max(15, int(final_cases * zone_multiplier / zones_df["base_weight"].sum() * len(zones_df)))
        admissions = int(zcases * (0.03 + 0.04 * params["severity"]))
        ed_visits = int(zcases * (0.11 + 0.08 * params["severity"]))
        zone_rows.append({
            "zone": row["zone"],
            "lat": row["lat"],
            "lon": row["lon"],
            "cases": zcases,
            "admissions": admissions,
            "ed_visits": ed_visits
        })
    zone_df = pd.DataFrame(zone_rows).sort_values("cases", ascending=False).reset_index(drop=True)
    return city_df, zone_df


def hospital_pressure(hospitals_df, zone_df, params):
    zone_lookup = zone_df.set_index("zone").to_dict("index")
    rows = []
    for _, h in hospitals_df.iterrows():
        z = zone_lookup[h["zone"]]
        beds_needed = max(8, int(z["admissions"] * (1.2 + params["severity"] * 1.6)))
        strain = beds_needed / h["baseline_beds"]
        rows.append({
            **h.to_dict(),
            "beds_needed": beds_needed,
            "strain": strain
        })
    return pd.DataFrame(rows).sort_values("beds_needed", ascending=False).reset_index(drop=True)


def push_pull_forces(params):
    base = baseline_params()
    contributions = {
        "Mobility": (params["mobility"] - base["mobility"]) * 30,
        "Vaccination gap": (params["vacc_gap"] - base["vacc_gap"]) * 26,
        "Seasonality": (params["seasonality"] - base["seasonality"]) * 22,
        "Lineages": (params["lineages"] - base["lineages"]) * 7,
        "Indoor mixing": (params["indoor"] - base["indoor"]) * 16,
        "School mixing": (params["school_mix"] - base["school_mix"]) * 14,
        "Transmission momentum": (params["growth"] - base["growth"]) * 260,
        "Prevention strength": -(params["prevention"] - base["prevention"]) * 24,
        "Severity": (params["severity"] - base["severity"]) * 18,
    }
    df = pd.DataFrame({
        "driver": list(contributions.keys()),
        "impact": list(contributions.values())
    }).sort_values("impact")
    return df


# -----------------------------
# Visuals
# -----------------------------
def make_qr_image(url: str):
    qr = qrcode.QRCode(box_size=8, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def add_pulse_css(m):
    css = """
    <style>
      .pulse-wrap {
        position: relative;
        width: 42px;
        height: 42px;
      }
      .pulse-ring {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        position: absolute;
        left: 0;
        top: 0;
        background: rgba(239,68,68,0.18);
        border: 2px solid rgba(248,113,113,0.80);
        animation: pulse 1.8s infinite;
        box-shadow: 0 0 0 0 rgba(248,113,113,0.5);
      }
      .pulse-core {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        background: #ef4444;
        position: absolute;
        left: 12px;
        top: 12px;
        box-shadow: 0 0 12px rgba(239,68,68,0.95);
      }
      .bed-icon {
        position: absolute;
        left: 8px;
        top: 8px;
        font-size: 22px;
        z-index: 10;
        filter: drop-shadow(0 0 5px rgba(255,255,255,0.2));
      }
      @keyframes pulse {
        0% {transform: scale(0.7); opacity: 0.95;}
        70% {transform: scale(1.45); opacity: 0.18;}
        100% {transform: scale(1.55); opacity: 0;}
      }
    </style>
    """
    m.get_root().header.add_child(Element(css))


def build_map(zone_df, hosp_df, delta_scale=1.0):
    m = folium.Map(
        location=[49.24, -123.05],
        zoom_start=10,
        tiles=None,
        control_scale=True,
    )

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB Dark Matter",
        name="Dark",
        control=False
    ).add_to(m)

    add_pulse_css(m)

    max_cases = max(zone_df["cases"].max(), 1)
    cutoff = zone_df["cases"].quantile(0.7)

    for _, r in zone_df.iterrows():
        radius = 1800 + (r["cases"] / max_cases) * 5300 * delta_scale
        hot = r["cases"] >= cutoff
        color = "#f59e0b" if not hot else "#ef4444"
        fill = "#f97316" if not hot else "#fb7185"
        folium.Circle(
            location=[r["lat"], r["lon"]],
            radius=radius,
            color=color,
            weight=3,
            fill=True,
            fill_opacity=0.28,
            fill_color=fill,
            popup=folium.Popup(
                f"<b>{r['zone']}</b><br>Forecast cases: {int(r['cases'])}<br>"
                f"Expected admissions: {int(r['admissions'])}<br>ED visits: {int(r['ed_visits'])}",
                max_width=260
            ),
            tooltip=f"{r['zone']}: {int(r['cases'])} forecast cases"
        ).add_to(m)

    for _, r in hosp_df.iterrows():
        html = """
        <div class="pulse-wrap">
            <div class="pulse-ring"></div>
            <div class="bed-icon">🛏️</div>
            <div class="pulse-core"></div>
        </div>
        """
        folium.Marker(
            location=[r["lat"], r["lon"]],
            icon=folium.DivIcon(html=html),
            tooltip=f"{r['hospital']} | Beds needed: {int(r['beds_needed'])}"
        ).add_to(m)

        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=2,
            color="#ffffff",
            fill=True,
            fill_opacity=0.9,
            popup=folium.Popup(
                f"<b>{r['hospital']}</b><br>Additional beds needed: {int(r['beds_needed'])}<br>"
                f"Baseline beds: {int(r['baseline_beds'])}<br>Strain: {r['strain']:.1%}",
                max_width=260
            )
        ).add_to(m)

    legend_html = """
    <div style="
        position: fixed;
        bottom: 18px;
        left: 18px;
        z-index: 9999;
        background: rgba(15,23,42,0.92);
        color: #e2e8f0;
        padding: 12px 14px;
        border-radius: 14px;
        border: 1px solid rgba(148,163,184,0.20);
        font-size: 13px;">
        <div style="font-weight:700; margin-bottom:8px;">Map legend</div>
        <div><span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#fb7185;margin-right:8px;"></span>Hotter forecast zone</div>
        <div><span style="display:inline-block;width:11px;height:11px;border-radius:50%;background:#f97316;margin-right:8px;"></span>Moderate forecast zone</div>
        <div style="margin-top:6px;">🛏️ Pulsing marker = hospital bed pressure</div>
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))
    return m


def forecast_chart(city_df, disease_name):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=city_df["date"],
        y=city_df["forecast_cases"],
        mode="lines+markers",
        name="Forecast",
        line=dict(width=4, color="#38bdf8"),
        marker=dict(size=8, color="#f472b6"),
        fill="tozeroy",
        fillcolor="rgba(56,189,248,0.16)"
    ))
    fig.update_layout(
        title=f"{disease_name} forecast over time",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.55)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=380,
        legend=dict(orientation="h", y=1.1, x=0.0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(title="Cases", gridcolor="rgba(148,163,184,0.18)")
    return fig


def zone_bar_chart(zone_df):
    d = zone_df.sort_values("cases", ascending=True)
    fig = go.Figure(go.Bar(
        x=d["cases"],
        y=d["zone"],
        orientation="h",
        marker=dict(color="#22c55e")
    ))
    fig.update_layout(
        title="Where the outbreak is strongest",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.55)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=380,
    )
    fig.update_xaxes(title="Forecast cases", gridcolor="rgba(148,163,184,0.18)")
    return fig


def push_pull_chart(force_df):
    colors = ["#38bdf8" if x < 0 else "#fb7185" for x in force_df["impact"]]
    fig = go.Figure(go.Bar(
        x=force_df["impact"],
        y=force_df["driver"],
        orientation="h",
        marker=dict(color=colors),
        text=[f"{x:+.1f}" for x in force_df["impact"]],
        textposition="outside",
    ))
    fig.update_layout(
        title="Push vs pull on spread",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.55)",
        margin=dict(l=20, r=20, t=50, b=20),
        height=420,
        showlegend=False
    )
    fig.add_vline(x=0, line_width=2, line_dash="dash", line_color="rgba(255,255,255,0.35)")
    fig.update_xaxes(title="Negative pulls down spread • Positive pushes up spread", gridcolor="rgba(148,163,184,0.18)")
    return fig


def voter_table(votes_df):
    if votes_df.empty:
        return votes_df
    d = votes_df[[
        "voter_name", "disease", "base_cases", "mobility", "prevention",
        "vacc_gap", "lineages", "seasonality", "severity"
    ]].copy().head(12)
    d.columns = [
        "Name", "Disease", "Base cases", "Mobility", "Prevention",
        "Vacc gap", "Lineages", "Seasonality", "Severity"
    ]
    return d


# -----------------------------
# Pages
# -----------------------------
def render_vote_page():
    st_autorefresh(interval=4000, limit=None, key="vote_refresh")
    accepting_votes = get_setting("accepting_votes", "1") == "1"

    st.markdown("""
    <div class="hero">
        <div style="font-size:2.1rem;font-weight:900;">📱 Audience Scenario Voting</div>
        <div class="small-note" style="margin-top:8px;">
            Help shape the outbreak. Your votes update the live disease dashboard on the main screen.
        </div>
    </div>
    """, unsafe_allow_html=True)

    status_class = "status-open" if accepting_votes else "status-locked"
    status_text = "OPEN — votes are being accepted" if accepting_votes else "LOCKED — presenter has frozen submissions"
    st.markdown(f'<div class="{status_class}" style="font-size:1rem;margin-bottom:10px;">Status: {status_text}</div>', unsafe_allow_html=True)

    if not accepting_votes:
        st.warning("Voting is closed. Watch the main screen for the final scenario reveal.")
        return

    with st.form("disease_vote_form", clear_on_submit=True):
        voter_name = st.text_input("Your name or nickname", max_chars=30, placeholder="Optional")
        disease = st.radio("Which disease should we simulate?", ["COVID-19", "Respiratory Illness", "Influenza-like Illness"])
        horizon = st.slider("Forecast horizon (days)", 7, 30, 14)
        base_cases = st.slider("Recent daily cases", 50, 2000, 450, step=25)
        growth = st.slider("Transmission momentum", 0.85, 1.25, 1.05, 0.01)
        mobility = st.slider("Mobility / gatherings", 0.0, 2.0, 1.0, 0.05)
        prevention = st.slider("Masking / prevention strength", 0.0, 2.0, 0.8, 0.05)
        vacc_gap = st.slider("Vaccination gap / susceptibility", 0.0, 2.0, 0.7, 0.05)
        lineages = st.slider("Number of active lineages", 1, 12, 4)
        seasonality = st.slider("Seasonality pressure", 0.0, 2.0, 1.2, 0.05)
        indoor = st.slider("Indoor mixing", 0.0, 2.0, 1.0, 0.05)
        school_mix = st.slider("School / social mixing", 0.0, 2.0, 0.9, 0.05)
        severity = st.slider("Severity / hospital burden", 0.0, 1.0, 0.45, 0.05)
        submitted = st.form_submit_button("Submit my scenario vote", use_container_width=True)

    if submitted:
        add_vote(
            voter_name=voter_name.strip(),
            disease=disease,
            horizon=horizon,
            base_cases=base_cases,
            growth=growth,
            mobility=mobility,
            prevention=prevention,
            vacc_gap=vacc_gap,
            lineages=lineages,
            seasonality=seasonality,
            indoor=indoor,
            school_mix=school_mix,
            severity=severity,
        )
        st.success("Vote submitted. Watch the main dashboard update in real time.")


def render_dashboard():
    st_autorefresh(interval=3000, limit=None, key="dashboard_refresh")
    votes_df = load_votes()
    params, vote_count = consensus_params(votes_df)

    snapshot_raw = get_setting("last_snapshot", "")
    scenario_locked = get_setting("scenario_locked", "0") == "1"
    if scenario_locked and snapshot_raw:
        params = json.loads(snapshot_raw)

    zones_df = load_zones()
    hospitals_df = load_hospitals()
    city_df, zone_df = scenario_forecast(params, zones_df)
    hosp_df = hospital_pressure(hospitals_df, zone_df, params)
    force_df = push_pull_forces(params)

    base_city_df, _ = scenario_forecast(baseline_params(), zones_df)
    baseline_final = int(base_city_df["forecast_cases"].iloc[-1])
    current_final = int(city_df["forecast_cases"].iloc[-1])
    delta_cases = current_final - baseline_final
    delta_scale = 1.0 + min(abs(delta_cases) / max(baseline_final, 1), 1.2)

    surge_score = (
        100
        * (0.16 * min(2, params["growth"])
           + 0.18 * min(2, params["mobility"])
           + 0.17 * min(2, params["vacc_gap"])
           + 0.16 * min(2, params["seasonality"])
           + 0.10 * min(2, params["indoor"])
           + 0.06 * min(2, params["school_mix"])
           + 0.17 * params["severity"])
        / 2.0
    )
    surge_score = int(max(18, min(98, surge_score)))

    with st.sidebar:
        st.header("Presenter controls")
        public_url = st.text_input("Public app URL", value=get_setting("public_url", DEFAULT_PUBLIC_URL))
        if public_url != get_setting("public_url", DEFAULT_PUBLIC_URL):
            set_setting("public_url", public_url)

        accepting_votes = get_setting("accepting_votes", "1") == "1"
        st.markdown(f"Voting status: **{'OPEN' if accepting_votes else 'LOCKED'}**")
        st.markdown(f"Scenario mode: **{'FROZEN SNAPSHOT' if scenario_locked else 'LIVE CONSENSUS'}**")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("Open voting", use_container_width=True):
                set_setting("accepting_votes", "1")
                set_setting("scenario_locked", "0")
                st.rerun()
        with c2:
            if st.button("Freeze voting", use_container_width=True):
                set_setting("accepting_votes", "0")
                st.rerun()

        if st.button("Freeze current scenario", use_container_width=True):
            set_setting("last_snapshot", json.dumps(params))
            set_setting("scenario_locked", "1")
            set_setting("accepting_votes", "0")
            st.rerun()

        if st.button("Return to live consensus", use_container_width=True):
            set_setting("scenario_locked", "0")
            st.rerun()

        if st.button("Reset class session", use_container_width=True):
            reset_votes()
            st.rerun()

        st.caption("Students scan the QR and vote. The map and charts react live.")

    public_url = get_setting("public_url", DEFAULT_PUBLIC_URL).strip().rstrip("/")
    vote_url = public_url + ("&" if "?" in public_url else "?") + urlencode({"mode": "vote"})
    qr_bytes = make_qr_image(vote_url)

    st.markdown("""
    <div class="hero">
        <div style="font-size:2.3rem;font-weight:900;line-height:1.05;">🦠 Metro Vancouver Outbreak Simulator — Live Class Vote</div>
        <div style="font-size:1.05rem;color:#cbd5e1;margin-top:8px;">
            Students push the parameters up or down. The forecast, hospital pressure, and map react in real time.
        </div>
    </div>
    """, unsafe_allow_html=True)

    top1, top2, top3, top4 = st.columns([1.05, 1.05, 1.05, 1.1])
    with top1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Live end-of-horizon forecast</div>
            <div class="metric-value">{current_final:,}</div>
            <div class="metric-sub">{params['disease']} cases across Metro Vancouver</div>
        </div>
        """, unsafe_allow_html=True)
    with top2:
        arrow = "▲" if delta_cases >= 0 else "▼"
        color = "#fb7185" if delta_cases >= 0 else "#38bdf8"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Push / pull from baseline</div>
            <div class="metric-value" style="color:{color};">{arrow} {abs(delta_cases):,}</div>
            <div class="metric-sub">Change versus the neutral baseline scenario</div>
        </div>
        """, unsafe_allow_html=True)
    with top3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Top hospital pressure</div>
            <div class="metric-value">{hosp_df.iloc[0]["hospital"].replace(" Hospital","")}</div>
            <div class="metric-sub">{int(hosp_df.iloc[0]["beds_needed"]):,} extra beds needed</div>
        </div>
        """, unsafe_allow_html=True)
    with top4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Class votes / surge score</div>
            <div class="metric-value">{vote_count} / {surge_score}</div>
            <div class="metric-sub">Audience votes and scenario intensity</div>
        </div>
        """, unsafe_allow_html=True)

    left, right = st.columns([2.25, 1.0], gap="large")
    with left:
        tab1, tab2, tab3 = st.tabs(["Forecast", "Map", "Push vs Pull"])
        with tab1:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(forecast_chart(city_df, params["disease"]), use_container_width=True)
            with c2:
                st.plotly_chart(zone_bar_chart(zone_df), use_container_width=True)
        with tab2:
            st.markdown('<div class="section-card">', unsafe_allow_html=True)
            st.markdown("#### Live outbreak map")
            st.markdown('<div class="small-note">As students change values drastically, zone circles expand or contract and hospital pressure responds.</div>', unsafe_allow_html=True)
            m = build_map(zone_df, hosp_df, delta_scale=delta_scale)
            st_folium(m, width=None, height=640, returned_objects=[])
            st.markdown('</div>', unsafe_allow_html=True)
        with tab3:
            st.plotly_chart(push_pull_chart(force_df), use_container_width=True)
            st.markdown('<div class="small-note">Pink bars push spread upward. Blue bars pull it back down. Big class swings show up here immediately.</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown("#### Scan to vote")
        st.image(qr_bytes, use_container_width=True)
        st.caption(vote_url)
        st.download_button("Download QR PNG", qr_bytes, file_name="outbreak_vote_qr.png", mime="image/png")
        st.markdown("---")
        st.markdown("#### Live class consensus")
        summary_df = pd.DataFrame({
            "Feature": [
                "Disease", "Horizon", "Base cases", "Mobility", "Prevention",
                "Vacc gap", "Lineages", "Seasonality", "Indoor", "School mix", "Severity"
            ],
            "Consensus": [
                params["disease"], int(params["horizon"]), int(params["base_cases"]),
                round(params["mobility"], 2), round(params["prevention"], 2),
                round(params["vacc_gap"], 2), int(params["lineages"]),
                round(params["seasonality"], 2), round(params["indoor"], 2),
                round(params["school_mix"], 2), round(params["severity"], 2)
            ]
        })
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        st.markdown("---")
        st.markdown("#### Recent votes")
        vt = voter_table(votes_df)
        if vt.empty:
            st.info("No votes yet.")
        else:
            st.dataframe(vt, use_container_width=True, hide_index=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="small-note" style="margin-top:10px;">Demo note: this live voting version was built from your uploaded outbreak dashboard app and adds a presenter/audience workflow on top of it.</div>',
        unsafe_allow_html=True
    )


# -----------------------------
# Main
# -----------------------------
init_db()
mode = st.query_params.get("mode", "dashboard")

if mode == "vote":
    render_vote_page()
else:
    render_dashboard()
