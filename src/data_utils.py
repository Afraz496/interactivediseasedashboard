from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_zone_geojson() -> Dict:
    path = Path(__file__).resolve().parents[1] / "data" / "zones.geojson"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def zone_order() -> List[str]:
    return [
        "North",
        "South",
        "East",
        "West",
        "Central",
        "Harbour",
        "Hills",
        "Valley",
        "Airport",
    ]
