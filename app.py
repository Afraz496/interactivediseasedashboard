# =============================
# 🦠 FINAL Outbreak Simulator (Clean UX Version)
# =============================

import io
import math
from datetime import datetime, timedelta

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import qrcode
import streamlit as st
from streamlit_folium import st_folium

# =============================
# CONFIG
# =============================

APP_TITLE = "Metro Vancouver Outbreak Simulator"
PUBLIC_URL = "https://afrazmathapp.streamlit.app"
VOTE_URL = f"{PUBLIC_URL}?mode=vote"

st.set_page_config(page_title=APP_TITLE, page_icon="🦠", layout="wide")

# =============================
# DARK THEME
# =============================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg,#0b1020,#0f172a);
    color: white;
}
h1,h2,h3,h4,p,label {
    color:white;
}
</style>
""", unsafe_allow_html=True)

# =============================
# DATA
# =============================

zones = pd.DataFrame({
    "zone": ["Vancouver","Burnaby","Richmond","Surrey"],
    "lat": [49.28,49.25,49.16,49.19],
    "lon": [-123.12,-122.98,-123.13,-122.84],
    "weight": [1.3,1.0,0.9,1.1]
})

# =============================
# MODEL
# =============================

def forecast(base, growth):
    vals = []
    cur = base
    for i in range(14):
        cur = cur * growth
        vals.append(cur)
    return vals

# =============================
# MAPS
# =============================

def build_metro_map(base_cases):
    m = folium.Map(location=[49.25,-123.1], zoom_start=10,
                   tiles="cartodb dark_matter")

    for _,r in zones.iterrows():
        folium.Circle(
            location=[r["lat"], r["lon"]],
            radius=base_cases * r["weight"] * 5,
            color="#ef4444",
            fill=True,
            fill_opacity=0.4
        ).add_to(m)

    return m


def build_bc_map(base_cases):
    center = [53.7267, -127.6476]
    m = folium.Map(location=center, zoom_start=5,
                   tiles="cartodb dark_matter")

    scale = min(base_cases / 1000, 2.5)

    folium.Circle(
        location=center,
        radius=200000 * (scale ** 1.5),
        color="#ef4444",
        fill=True,
        fill_opacity=0.25
    ).add_to(m)

    return m

# =============================
# QR
# =============================

def make_qr(url):
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue()

qr = make_qr(VOTE_URL)

# =============================
# HERO
# =============================

st.markdown("""
<div style="
    background: linear-gradient(135deg,#0ea5e9,#1e3a8a);
    padding:20px;
    border-radius:20px;
    margin-bottom:20px;
">
<h1 style="color:white;">🦠 Metro Vancouver Outbreak Simulator</h1>
<p style="color:#cbd5e1;">
Students change parameters → watch the outbreak react live
</p>
</div>
""", unsafe_allow_html=True)

# =============================
# CONTROLS
# =============================

left, right = st.columns([2.5,1])

with right:
    st.subheader("📱 Scan to vote")
    st.image(qr)
    st.caption(VOTE_URL)

    st.markdown("---")

    st.subheader("🎛 Controls")

    base_cases = st.slider("Base cases", 50, 2000, 450)
    growth = st.slider("Growth rate", 0.9, 1.2, 1.05, 0.01)

    st.markdown("---")

    if growth > 1.1:
        st.error("🔥 Rapid outbreak")
    elif growth > 1.05:
        st.warning("⚠️ Moderate growth")
    else:
        st.success("✅ Stable")

# =============================
# MAIN VISUALS
# =============================

with left:

    st.subheader("🔥 Metro outbreak map")
    metro_map = build_metro_map(base_cases)
    st_folium(metro_map, height=550)

    st.markdown("### 📈 Forecast")

    vals = forecast(base_cases, growth)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=vals,
        mode="lines+markers",
        line=dict(width=4)
    ))
    fig.update_layout(template="plotly_dark")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 🌎 BC-wide spread")

    bc_map = build_bc_map(base_cases)
    st_folium(bc_map, height=450)