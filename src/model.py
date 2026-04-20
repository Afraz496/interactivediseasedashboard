from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ScenarioInputs:
    disease: str
    baseline_cases: int
    growth_factor: float
    mobility_factor: float
    prevention_factor: float
    weather_factor: float
    horizon_days: int


def _zone_templates() -> pd.DataFrame:
    """Synthetic zone setup for classroom demos.

    You can later replace this with real health regions / FSAs / CHSAs.
    """
    rows = [
        ("North", 1.12, 0.92, 0.10, 0.05),
        ("South", 0.95, 1.04, 0.18, 0.09),
        ("East", 1.08, 1.15, 0.14, 0.08),
        ("West", 0.90, 0.87, 0.11, 0.06),
        ("Central", 1.25, 1.25, 0.24, 0.12),
        ("Harbour", 0.98, 1.10, 0.16, 0.07),
        ("Hills", 0.85, 0.80, 0.08, 0.04),
        ("Valley", 1.05, 0.98, 0.15, 0.08),
        ("Airport", 1.18, 1.30, 0.19, 0.10),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "zone",
            "susceptibility",
            "mobility_weight",
            "hospital_burden_weight",
            "ed_burden_weight",
        ],
    )


DISEASE_CONFIG: Dict[str, Dict[str, float]] = {
    "COVID-19": {"base_multiplier": 1.0, "hospitalization_rate": 0.08, "seasonality_sensitivity": 0.80},
    "Influenza-like Illness": {"base_multiplier": 0.92, "hospitalization_rate": 0.05, "seasonality_sensitivity": 1.10},
    "General Respiratory Illness": {"base_multiplier": 0.86, "hospitalization_rate": 0.035, "seasonality_sensitivity": 0.95},
}


def simulate_forecast(inputs: ScenarioInputs) -> pd.DataFrame:
    cfg = DISEASE_CONFIG[inputs.disease]
    zones = _zone_templates().copy()

    # Intuitive demo model: past cases scaled by scenario choices and zone properties.
    prevention_multiplier = max(0.25, 1.15 - inputs.prevention_factor)
    horizon_multiplier = 1 + (inputs.horizon_days / 14.0) * 0.18

    expected_cases = (
        inputs.baseline_cases
        * cfg["base_multiplier"]
        * zones["susceptibility"]
        * (0.75 + 0.50 * inputs.growth_factor)
        * (0.70 + 0.60 * inputs.mobility_factor * zones["mobility_weight"])
        * prevention_multiplier
        * (0.70 + cfg["seasonality_sensitivity"] * inputs.weather_factor)
        * horizon_multiplier
        / 9.0
    )

    zones["forecast_cases"] = np.maximum(0, np.round(expected_cases)).astype(int)
    zones["hospital_admissions"] = np.maximum(
        0,
        np.round(zones["forecast_cases"] * cfg["hospitalization_rate"] * (1 + zones["hospital_burden_weight"])),
    ).astype(int)
    zones["ed_visits"] = np.maximum(
        0,
        np.round(zones["forecast_cases"] * 0.18 * (1 + zones["ed_burden_weight"])),
    ).astype(int)

    case_q = zones["forecast_cases"].quantile([0.33, 0.66]).tolist()

    def label_risk(x: int) -> str:
        if x <= case_q[0]:
            return "Low"
        if x <= case_q[1]:
            return "Medium"
        return "High"

    zones["risk_level"] = zones["forecast_cases"].apply(label_risk)
    zones["summary"] = zones.apply(
        lambda r: (
            f"{r['zone']}: forecast {r['forecast_cases']} cases, "
            f"{r['hospital_admissions']} hospital admissions, "
            f"{r['ed_visits']} ED visits"
        ),
        axis=1,
    )
    return zones.sort_values("forecast_cases", ascending=False).reset_index(drop=True)
