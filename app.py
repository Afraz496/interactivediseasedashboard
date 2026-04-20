from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data_utils import load_zone_geojson
from src.model import ScenarioInputs, simulate_forecast
from src.qr_utils import build_qr_code_bytes

st.set_page_config(page_title="Disease Forecast Demo", page_icon="🦠", layout="wide")

st.title("🦠 Disease Forecast Demo for Students")
st.caption(
    "Change a few parameters and see how a simple forecasting model changes predicted cases, "
    "hospital burden, and which zones are most at risk."
)

with st.sidebar:
    st.header("Scenario controls")
    disease = st.selectbox(
        "Disease",
        ["COVID-19", "Influenza-like Illness", "General Respiratory Illness"],
        index=0,
    )
    baseline_cases = st.slider("Past weekly cases", min_value=20, max_value=900, value=240, step=10)
    growth_factor = st.slider("Transmission growth", min_value=0.5, max_value=1.7, value=1.0, step=0.05)
    mobility_factor = st.slider("Population mixing / mobility", min_value=0.5, max_value=1.7, value=1.0, step=0.05)
    prevention_factor = st.slider("Prevention strength", min_value=0.0, max_value=0.8, value=0.25, step=0.05)
    weather_factor = st.slider("Seasonal pressure", min_value=0.6, max_value=1.5, value=1.0, step=0.05)
    horizon_days = st.select_slider("Forecast horizon (days)", options=[3, 5, 7, 10, 14], value=7)

scenario = ScenarioInputs(
    disease=disease,
    baseline_cases=baseline_cases,
    growth_factor=growth_factor,
    mobility_factor=mobility_factor,
    prevention_factor=prevention_factor,
    weather_factor=weather_factor,
    horizon_days=horizon_days,
)

forecast_df = simulate_forecast(scenario)
geojson = load_zone_geojson()
map_df = forecast_df.copy()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Forecast total cases", int(forecast_df["forecast_cases"].sum()))
kpi2.metric("Expected hospital admissions", int(forecast_df["hospital_admissions"].sum()))
kpi3.metric("Expected ED visits", int(forecast_df["ed_visits"].sum()))

left, right = st.columns([1.3, 1.0])

with left:
    st.subheader("Zone-level forecast map")
    fig = px.choropleth(
        map_df,
        geojson=geojson,
        locations="zone",
        featureidkey="properties.zone",
        color="forecast_cases",
        hover_name="zone",
        hover_data={
            "forecast_cases": True,
            "hospital_admissions": True,
            "ed_visits": True,
            "risk_level": True,
        },
        color_continuous_scale="OrRd",
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
        coloraxis_colorbar_title="Cases",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Top zones")
    top = forecast_df[["zone", "forecast_cases", "hospital_admissions", "ed_visits", "risk_level"]].copy()
    st.dataframe(top, use_container_width=True, hide_index=True)

bar_fig = px.bar(
    forecast_df.sort_values("forecast_cases", ascending=True),
    x="forecast_cases",
    y="zone",
    color="risk_level",
    orientation="h",
    title="Which zones could see more cases?",
)
bar_fig.update_layout(height=420, legend_title_text="Risk")
st.plotly_chart(bar_fig, use_container_width=True)

with st.expander("How this demo works"):
    st.markdown(
        """
This app uses a **simple classroom forecasting model**, not a production medical model.

It combines:
- recent case counts,
- disease type,
- transmission growth,
- mobility,
- prevention,
- seasonality,
- and zone-specific vulnerability.

That makes it great for teaching how changing inputs can change forecasts and hospital burden.
        """
    )

st.subheader("Create a QR code for phones")
st.write(
    "After you deploy the app, paste the public URL below and this app will generate a QR code that students can scan."
)
public_url = st.text_input("Public app URL", placeholder="https://your-app-name.streamlit.app")
if public_url:
    qr_bytes = build_qr_code_bytes(public_url)
    st.image(qr_bytes, caption="Scan this QR code to open the web app on a phone.", width=240)
    st.download_button(
        label="Download QR code PNG",
        data=qr_bytes,
        file_name="forecast_demo_qr.png",
        mime="image/png",
    )

st.subheader("Presenter tips")
st.markdown(
    """
- Start with a calm baseline, then raise mobility and growth.
- Ask students which zones they think will spike first.
- Show how stronger prevention changes hospital burden.
- Explain that better models use real data, but the ideas are the same.
    """
)
