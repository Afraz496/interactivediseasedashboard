
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ZONE_WEIGHTS = {
    "Vancouver": 1.18,
    "Burnaby": 1.05,
    "Richmond": 0.95,
    "North Vancouver": 0.92,
    "West Vancouver": 0.72,
    "New Westminster": 1.00,
    "Coquitlam": 0.97,
    "Port Moody": 0.88,
    "Surrey": 1.22,
    "Delta": 0.90,
    "Langley": 0.98,
    "Maple Ridge": 1.02,
    "White Rock": 0.76,
}

DISEASE_MULTIPLIER = {
    "COVID-19": 1.00,
    "Influenza-like Illness": 0.88,
    "General Respiratory Illness": 0.94,
}

ADMISSION_RATE = {
    "COVID-19": 0.085,
    "Influenza-like Illness": 0.055,
    "General Respiratory Illness": 0.050,
}

ED_RATE = {
    "COVID-19": 0.16,
    "Influenza-like Illness": 0.18,
    "General Respiratory Illness": 0.20,
}

@dataclass(frozen=True)
class ScenarioInputs:
    disease: str
    baseline_cases: int
    growth_factor: float
    mobility_factor: float
    prevention_factor: float
    weather_factor: float
    vaccination_gap: float
    lineage_pressure: float
    horizon_days: int


def _risk_bucket(x: float) -> str:
    if x >= 1.25:
        return "Very high"
    if x >= 1.05:
        return "High"
    if x >= 0.9:
        return "Moderate"
    return "Lower"


def simulate_forecast(s: ScenarioInputs) -> pd.DataFrame:
    rows = []
    disease_mult = DISEASE_MULTIPLIER[s.disease]
    pressure = (
        s.growth_factor
        * s.mobility_factor
        * (1 - s.prevention_factor)
        * s.weather_factor
        * (1 + s.vaccination_gap)
        * (1 + 0.12 * s.lineage_pressure)
        * disease_mult
    )
    horizon_scale = s.horizon_days / 7.0

    for zone, zone_w in ZONE_WEIGHTS.items():
        zone_factor = pressure * zone_w
        forecast_cases = max(1, int(round(s.baseline_cases * horizon_scale * zone_factor / len(ZONE_WEIGHTS))))
        admissions = max(0, int(round(forecast_cases * ADMISSION_RATE[s.disease] * (1 + 0.08 * s.lineage_pressure))))
        ed_visits = max(0, int(round(forecast_cases * ED_RATE[s.disease] * (1 + s.vaccination_gap * 0.5))))
        rows.append({
            'zone': zone,
            'forecast_cases': forecast_cases,
            'hospital_admissions': admissions,
            'ed_visits': ed_visits,
            'zone_pressure': round(zone_factor, 3),
            'risk_level': _risk_bucket(zone_factor),
        })

    df = pd.DataFrame(rows).sort_values('forecast_cases', ascending=False).reset_index(drop=True)
    return df


def allocate_bed_pressure(forecast_df: pd.DataFrame, hospitals_df: pd.DataFrame) -> pd.DataFrame:
    zone_adm = forecast_df.set_index('zone')['hospital_admissions'].to_dict()
    out = hospitals_df.copy()
    zone_counts = out.groupby('zone')['hospital'].transform('count').clip(lower=1)
    out['projected_admissions'] = out['zone'].map(zone_adm).fillna(0) / zone_counts
    out['projected_admissions'] = out['projected_admissions'].round(1)
    out['bed_need_index'] = (out['projected_admissions'] / (out['base_beds'] * 0.18)).replace([np.inf, -np.inf], 0).fillna(0)
    out['bed_need_index'] = out['bed_need_index'].clip(lower=0)
    out['surge_beds_needed'] = np.maximum(np.ceil(out['projected_admissions'] - out['base_beds'] * 0.12), 0)
    return out.sort_values('bed_need_index', ascending=False).reset_index(drop=True)
