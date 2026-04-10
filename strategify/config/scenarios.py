"""Pre-built scenario configurations for geopolitical simulations.

Scenarios can be defined as JSON files in ``geo/scenarios/`` and loaded
via ``load_scenario()``. The hardcoded defaults below are used when no
scenario file is specified.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "geo" / "scenarios"


# ---------------------------------------------------------------------------
# Preset Classes
# ---------------------------------------------------------------------------
@dataclass
class ScenarioPreset:
    """Pre-configured simulation scenario."""

    name: str
    description: str
    regions: list[str]
    initial_relations: dict[tuple[str, str], float]
    keywords: dict[str, list[str]]
    duration: int = 50
    geojson: str | None = None


# ---------------------------------------------------------------------------
# Hardcoded defaults (original Eastern Europe crisis)
# ---------------------------------------------------------------------------
DEFAULT_ACTOR_CONFIGS: dict[str, dict[str, Any]] = {
    "alpha": {
        "caps": {"military": 0.8, "economic": 0.4},
        "role": "row",
        "personality": "Aggressor",
    },
    "delta": {
        "caps": {"military": 0.5, "economic": 0.7},
        "role": "col",
        "personality": "Pacifist",
    },
    "bravo": {
        "caps": {"military": 0.3, "economic": 0.2},
        "role": "row",
        "personality": "Tit-for-Tat",
    },
    "charlie": {
        "caps": {"military": 0.4, "economic": 0.4},
        "role": "col",
        "personality": "Neutral",
    },
}

DEFAULT_REGION_RESOURCES: dict[str, float] = {
    "alpha": 1.0,
    "bravo": 2.0,
    "charlie": 1.0,
    "delta": 1.0,
}

DEFAULT_ALLIANCES: list[tuple[str, str, float]] = [
    ("alpha", "bravo", 1.0),
    ("alpha", "delta", -0.5),
    ("delta", "bravo", -0.5),
]


# ---------------------------------------------------------------------------
# Scenario loading
# ---------------------------------------------------------------------------
def list_scenarios() -> list[str]:
    """Return names of available JSON scenario files."""
    if not _SCENARIOS_DIR.exists():
        return []
    return sorted(p.stem for p in _SCENARIOS_DIR.glob("*.json"))


def load_scenario(name: str | Path) -> dict[str, Any]:
    """Load a scenario from a JSON file.

    Parameters
    ----------
    name:
        Scenario name (e.g. ``"default"``) or full path to a JSON file.

    Returns
    -------
    dict
        Scenario data with keys: ``name``, ``actors``, ``region_resources``,
        ``alliances``, ``geojson``, ``random_seed``, ``n_steps``.
    """
    path = Path(name)
    if not path.exists():
        path = _SCENARIOS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Scenario not found: {name}. Available: {list_scenarios()}")

    with open(path) as f:
        data = json.load(f)

    # Validate required keys
    required = {"actors", "region_resources", "alliances"}
    missing = required - set(data.keys())
    if missing:
        raise ValueError(f"Scenario {path} missing keys: {missing}")

    return data


def scenario_to_configs(
    data: dict[str, Any],
) -> tuple[
    dict[str, dict[str, Any]],
    dict[str, float],
    list[tuple[str, str, float]],
]:
    """Convert loaded scenario data to the format used by GeopolModel.

    Returns
    -------
    tuple
        ``(actor_configs, region_resources, alliances)`` in the same format
        as the hardcoded defaults above.
    """
    actor_configs: dict[str, dict[str, Any]] = {}
    for rid, actor in data["actors"].items():
        actor_configs[rid] = {
            "caps": dict(actor.get("capabilities", {"military": 0.5, "economic": 0.5})),
            "role": actor.get("role", "row"),
            "personality": actor.get("personality", "Neutral"),
        }

    region_resources: dict[str, float] = dict(data["region_resources"])

    alliances: list[tuple[str, str, float]] = [(a["source"], a["target"], a["weight"]) for a in data["alliances"]]

    return actor_configs, region_resources, alliances


# ---------------------------------------------------------------------------
# Pre-configured Scenario Presets
# ---------------------------------------------------------------------------

UKRAINE_PRESET = ScenarioPreset(
    name="Ukraine Crisis",
    description=("Simulation of the 2022 Russia-Ukraine conflict with neighboring NATO and EU states"),
    regions=["UKR", "RUS", "BLR", "POL", "MDA", "ROU", "HUN", "SVK", "LVA", "LTU", "EST"],
    initial_relations={
        ("RUS", "UKR"): -0.9,
        ("RUS", "BLR"): 0.8,
        ("UKR", "POL"): 0.7,
        ("POL", "RUS"): -0.6,
        ("UKR", "MDA"): 0.5,
        ("ROU", "UKR"): 0.5,
        ("RUS", "LVA"): -0.4,
        ("RUS", "LTU"): -0.4,
        ("RUS", "EST"): -0.4,
    },
    keywords={
        "UKR": ["Ukraine", "Russia", "war", "military", "invasion", "Kyiv"],
        "RUS": ["Russia", "Putin", "sanctions", "Kremlin", "Moscow"],
        "BLR": ["Belarus", "Lukashenko", "military"],
        "POL": ["Poland", "NATO", "border", "refugees"],
        "MDA": ["Moldova", "Transnistria", "Romania"],
    },
    duration=50,
    geojson="real_world.geojson",
)

MIDDLE_EAST_PRESET = ScenarioPreset(
    name="Middle East Crisis",
    description="Israeli-Palestinian conflict with regional Arab states and Iran",
    regions=["ISR", "PSE", "JOR", "LBN", "SYR", "SAU", "EGY", "IRN", "ARE", "QAT"],
    initial_relations={
        ("ISR", "PSE"): -0.9,
        ("ISR", "IRN"): -0.8,
        ("ISR", "SAU"): 0.3,
        ("ISR", "EGY"): 0.2,
        ("JOR", "PSE"): 0.8,
        ("IRN", "PSE"): 0.6,
        ("IRN", "LBN"): 0.7,
        ("SAU", "IRN"): -0.5,
        ("EGY", "PSE"): 0.7,
    },
    keywords={
        "ISR": ["Israel", "Gaza", "Jerusalem", " Netanyahu"],
        "PSE": ["Palestine", "Gaza", "West Bank", "Hamas"],
        "IRN": ["Iran", "nuclear", "Tehran", "revolutionary"],
        "SAU": ["Saudi Arabia", "oil", "Gulf"],
        "EGY": ["Egypt", "Suez", "Cairo"],
    },
    duration=40,
    geojson="middle_east.geojson",
)

SOUTH_CHINA_SEA_PRESET = ScenarioPreset(
    name="South China Sea",
    description="Maritime disputes in the Indo-Pacific with US, China, and ASEAN",
    regions=["CHN", "VNM", "PHL", "MYS", "BRN", "IDN", "TWN", "USA", "AUS", "JPN", "IND"],
    initial_relations={
        ("CHN", "VNM"): -0.6,
        ("CHN", "PHL"): -0.5,
        ("CHN", "MYS"): -0.3,
        ("CHN", "TWN"): -0.9,
        ("USA", "CHN"): -0.7,
        ("USA", "JPN"): 0.8,
        ("USA", "AUS"): 0.8,
        ("VNM", "USA"): 0.4,
        ("PHL", "USA"): 0.7,
        ("IND", "CHN"): -0.5,
    },
    keywords={
        "CHN": ["China", "South China Sea", "Taiwan", "Nine-dash line"],
        "VNM": ["Vietnam", "South China Sea", "Spratly"],
        "PHL": ["Philippines", "West Philippine Sea", "Barro Colorado"],
        "USA": ["United States", "Indo-Pacific", "Freedom of navigation"],
        "TWN": ["Taiwan", "straits", " Taipei"],
    },
    duration=60,
    geojson="indo_pacific.geojson",
)

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def get_preset(name: str) -> ScenarioPreset:
    """Get a preset by name.

    Parameters
    ----------
    name:
        Preset name: "ukraine", "middle_east", or "south_china_sea"

    Returns
    -------
    ScenarioPreset
        The requested preset.

    Raises
    ------
    ValueError
        If preset name is not recognized.
    """
    presets = {
        "ukraine": UKRAINE_PRESET,
        "middle_east": MIDDLE_EAST_PRESET,
        "south_china_sea": SOUTH_CHINA_SEA_PRESET,
    }

    if name.lower() not in presets:
        raise ValueError(f"Unknown preset: {name}. Available: {list(presets.keys())}")

    return presets[name.lower()]


def list_presets() -> list[str]:
    """List available preset names."""
    return ["ukraine", "middle_east", "south_china_sea"]
