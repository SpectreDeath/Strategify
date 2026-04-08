"""Global configuration, constants, and paths for strategify."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
GEO_DIR = PACKAGE_ROOT / "geo"
REAL_WORLD_GEOJSON = GEO_DIR / "real_world.geojson"
SCENARIOS_DIR = GEO_DIR / "scenarios"

# ---------------------------------------------------------------------------
# Simulation defaults
# ---------------------------------------------------------------------------
DEFAULT_N_STEPS: int = 20
RANDOM_SEED: int = 42

# ---------------------------------------------------------------------------
# Mesa server
# ---------------------------------------------------------------------------
MESA_SERVER_PORT: int = 8521

# ---------------------------------------------------------------------------
# Region colors
# ---------------------------------------------------------------------------
# Canonical colors for well-known region IDs
REGION_COLORS: dict[str, str] = {
    "alpha": "blue",
    "bravo": "red",
    "charlie": "green",
    "delta": "orange",
}

# Palette for auto-assignment to unknown region IDs
_COLOR_PALETTE: list[str] = [
    "blue",
    "red",
    "green",
    "orange",
    "purple",
    "brown",
    "pink",
    "gray",
    "olive",
    "cyan",
    "magenta",
    "teal",
    "navy",
    "maroon",
    "lime",
]

# Hex color map for Folium/pyvis (maps from canonical named colors)
REGION_HEX_COLORS: dict[str, str] = {
    "blue": "#2196F3",
    "red": "#F44336",
    "green": "#4CAF50",
    "orange": "#FF9800",
    "purple": "#9C27B0",
    "brown": "#795548",
    "pink": "#E91E63",
    "gray": "#9E9E9E",
    "olive": "#808000",
    "cyan": "#00BCD4",
    "magenta": "#E91E63",
    "teal": "#009688",
    "navy": "#3F51B5",
    "maroon": "#800000",
    "lime": "#CDDC39",
}


def get_region_color(region_id: str) -> str:
    """Return a color for any region ID, auto-assigning from palette if needed."""
    if region_id in REGION_COLORS:
        return REGION_COLORS[region_id]
    # Deterministic assignment: hash the ID to pick from palette
    idx = hash(region_id) % len(_COLOR_PALETTE)
    color = _COLOR_PALETTE[idx]
    REGION_COLORS[region_id] = color
    return color


def get_region_hex_color(region_id: str) -> str:
    """Return hex color for any region ID."""
    color_name = get_region_color(region_id)
    return REGION_HEX_COLORS.get(color_name, "#888888")


# ---------------------------------------------------------------------------
# Decision-making weights
# ---------------------------------------------------------------------------
INFLUENCE_WEIGHT: float = 1.5
CONTAGION_WEIGHT: float = 0.5
PERSONALITY_BIAS_BASE: float = 1.0
RESOURCE_BASELINE: float = 1.0
DISTANCE_DECAY_OFFSET: int = 1

# ---------------------------------------------------------------------------
# Escalation levels
# ---------------------------------------------------------------------------
ESCALATION_LEVELS: list[str] = [
    "Cooperative",
    "Diplomatic",
    "Economic",
    "Military",
]
ESCALATION_THRESHOLDS: dict[str, float] = {
    "Cooperative": 0.0,
    "Diplomatic": 0.25,
    "Economic": 0.5,
    "Military": 0.75,
}
ESCALATION_TRANSITION_COSTS: dict[tuple[str, str], float] = {
    ("Cooperative", "Diplomatic"): 0.1,
    ("Diplomatic", "Economic"): 0.3,
    ("Economic", "Military"): 0.6,
    ("Diplomatic", "Cooperative"): -0.05,
    ("Economic", "Diplomatic"): -0.1,
    ("Military", "Economic"): -0.2,
}
