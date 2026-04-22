# =============================
# 🔥 Metro Vancouver + BC Dashboard (FINAL)
# =============================

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

# ✅ FIXED URL
DEFAULT_PUBLIC_URL = "https://afrazmathapp.streamlit.app"

SEED = 42

st.set_page_config(page_title=APP_TITLE, page_icon="🦠", layout="wide")

# =============================
# DATABASE
# =============================

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
            disease TEXT,
            horizon REAL,
            base_cases REAL,
            growth REAL,
            mobility REAL,
            prevention REAL,
            vacc_gap REAL,
            lineages REAL,
            seasonality REAL,
            indoor REAL,
            school_mix REAL,
            severity REAL,
            created_at TEXT
        )
    """)

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
        "INSERT INTO settings (key,value) VALUES (?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, str(value))
    )
    conn.commit()
    conn.close()

# =============================
# 🔥 FORCE URL FIX EVERY RUN
# =============================

init_db()
set_setting("public_url", DEFAULT_PUBLIC_URL)

# =============================
# DATA
# =============================

@st.cache_data
def load_zones():
    return pd.DataFrame({
        "zone": ["Vancouver","Burnaby","Richmond","Surrey"],
        "lat": [49.28,49.25,49.16,49.19],
        "lon": [-123.12,-122.98,-123.13,-122.84],
        "weight": [1.3,1.0,0.9,1.1]
    })

# =============================
# MODEL
# =============================

def forecast(params):
    base = params["base_cases"]
    growth = params["growth"]

    vals = []
    cur = base

    for i in range(14):
        cur = cur * growth
        vals.append(cur)

    return vals

# =============================
# MAPS
# =============================

def build_metro_map(zone_df, cases):
    m = folium.Map(location=[49.25,-123.1], zoom_start=10,
                   tiles="cartodb dark_matter")

    for _,r in zone_df.iterrows():
        folium.Circle(
            location=[r["lat"], r["lon"]],
            radius=cases * r["weight"] * 5,
            color="#ef4444",
            fill=True,
            fill_opacity=0.4
        ).add_to(m)

    return m


def build_bc_map(base_cases):
    bc_center = [53.7267, -127.6476]

    m = folium.Map(
        location=bc_center,
        zoom_start=5,
        tiles="cartodb dark_matter"
    )

    scale = min(base_cases / 1000, 2.5)

    folium.Circle(
        location=bc_center,
        radius=200000 * (scale ** 1.5),
        color="#ef4444",
        fill=True,
        fill_opacity=0.25,
    ).add_to(m)

    cities = [
        ("Vancouver",49.28,-123.12),
        ("Victoria",48.43,-123.36),
        ("Kelowna",49.88,-119.49),
        ("Prince George",53.91,-122.75),
    ]

    for name,lat,lon in cities:
        folium.CircleMarker(
            location=[lat,lon],
            radius=6,
            color="#38bdf8",
            fill=True
        ).add_to(m)

    return m

# =============================
# QR CODE
# =============================

def make_qr(url):
    qr = qrcode.make(url)
    buf = io.BytesIO()
    qr.save(buf)
    return buf.getvalue()

# =============================
# MAIN
# =============================

zones = load_zones()

params = {
    "base_cases": 450,
    "growth": 1.05
}

forecast_vals = forecast(params)

public_url = get_setting("public_url")
vote_url = public_url + "?mode=vote"

qr = make_qr(vote_url)

# =============================
# UI
# =============================

st.title("🦠 Outbreak Simulator")

col1, col2 = st.columns([2,1])

with col1:
    tab1, tab2, tab3 = st.tabs(["Forecast","Metro Map","BC Impact"])

    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=forecast_vals, mode="lines+markers"))
        fig.update_layout(template="plotly_dark")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        m = build_metro_map(zones, params["base_cases"])
        st_folium(m, height=500)

    with tab3:
        bc_map = build_bc_map(params["base_cases"])
        st_folium(bc_map, height=500)

with col2:
    st.subheader("Scan to vote")

    st.image(qr)

    st.caption(vote_url)

    st.download_button("Download QR", qr)
