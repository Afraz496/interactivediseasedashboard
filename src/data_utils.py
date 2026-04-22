
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_zone_geojson() -> dict:
    with open(DATA_DIR / "metro_vancouver_zones.geojson", "r", encoding="utf-8") as f:
        return json.load(f)


def load_hospitals() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "hospitals.csv")
