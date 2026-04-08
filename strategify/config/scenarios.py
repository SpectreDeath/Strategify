"""Pre-built scenario configurations for geopolitical simulations.

Scenarios can be defined as JSON files in ``geo/scenarios/`` and loaded
via ``load_scenario()``. The hardcoded defaults below are used when no
scenario file is specified.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCENARIOS_DIR = Path(__file__).resolve().parent.parent / "geo" / "scenarios"

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

    alliances: list[tuple[str, str, float]] = [
        (a["source"], a["target"], a["weight"]) for a in data["alliances"]
    ]

    return actor_configs, region_resources, alliances
