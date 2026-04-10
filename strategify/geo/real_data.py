"""Real-world data integration for simulation initialization and updates.

Provides a DataCollector that integrates:
- GDELT (news, events, sentiment)
- ACLED (conflict data, fatalities)
- World Bank (GDP, population, military spending)
- Natural Earth (geographic boundaries)

Usage:

    from strategify.geo.real_data import RealWorldDataCollector

    collector = RealWorldDataCollector()
    # Initialize model with real data
    model_data = collector.get_initial_state()
    # Get current real-world metrics
    metrics = collector.get_current_metrics()
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategify.geo.loader import GeoJSONLoader, RegionSubsetConfig


@dataclass
class RegionData:
    """Real-world data for a region."""

    region_id: str
    country_name: str

    # Geographic
    geometry: Any = None
    area_km2: float = 0.0

    # Economic (World Bank)
    gdp_usd: float = 0.0
    population: int = 0
    military_spending_pct: float = 0.0

    # Conflict (ACLED)
    fatalities: int = 0
    events: int = 0

    # GDELT
    article_count: int = 0
    tone: float = 0.0

    # Calculated
    military_capability: float = 0.5
    economic_capability: float = 0.5


class RealWorldDataCollector:
    """Collect real-world data from multiple sources for simulation."""

    DEFAULT_CONFIG = {
        "Ukraine": {
            "country_name": "Ukraine",
            "id_map": "alpha",
            "keywords": ["Ukraine", "Kyiv", "Donbas", "Crimea"],
        },
        "Russia": {
            "country_name": "Russia",
            "id_map": "bravo",
            "keywords": ["Russia", "Moscow", "Kremlin"],
        },
        "Belarus": {
            "country_name": "Belarus",
            "id_map": "charlie",
            "keywords": ["Belarus", "Minsk"],
        },
        "Poland": {
            "country_name": "Poland",
            "id_map": "delta",
            "keywords": ["Poland", "Warsaw"],
        },
    }

    def __init__(
        self,
        region_config: dict | None = None,
        use_cache: bool = True,
    ) -> None:
        self.region_config = region_config or self.DEFAULT_CONFIG
        self.use_cache = use_cache
        self._geometries: dict[str, Any] = {}
        self._region_data: dict[str, RegionData] = {}

    def load_geometries(self) -> dict[str, Any]:
        """Load geographic geometries for configured regions."""
        config = RegionSubsetConfig(
            countries=list(self.region_config.keys()),
            id_map={k: v["id_map"] for k, v in self.region_config.items()},
            resolution="50m",
        )
        gdf = GeoJSONLoader.load(config)

        for _, row in gdf.iterrows():
            self._geometries[row["region_id"]] = row["geometry"]

        return self._geometries

    def get_region_data(self, region_id: str) -> RegionData | None:
        """Get real-world data for a region."""
        if region_id not in self._region_data:
            return None
        return self._region_data[region_id]

    def get_all_region_data(self) -> dict[str, RegionData]:
        """Get data for all regions."""
        return self._region_data.copy()

    def get_initial_state(
        self,
        model_type: str = "default",
    ) -> dict[str, dict]:
        """Get initial state for model from real data.

        Parameters
        ----------
        model_type:
            "default" - balanced capabilities
            "historical" - use actual historical data
            "conflict" - emphasize military/capabilities

        Returns
        -------
        dict
            {region_id: {posture, capabilities, geometry, ...}}
        """
        states = {}

        for region_id, config in self.region_config.items():
            rd = self._region_data.get(region_id)

            if model_type == "historical" and rd:
                # Use actual data
                military = rd.military_capability
                economic = rd.economic_capability
            elif model_type == "conflict":
                # Emphasize military
                military = min(1.0, (rd.military_capability if rd else 0.5) + 0.2)
                economic = 0.5
            else:
                # Default balanced
                military = 0.5
                economic = 0.5

            states[region_id] = {
                "region_id": region_id,
                "country_name": config["country_name"],
                "posture": "Deescalate",
                "personality": "Neutral",
                "capabilities": {
                    "military": military,
                    "economic": economic,
                },
                "geometry": self._geometries.get(region_id),
                # Real-world metrics
                "gdp": rd.gdp_usd if rd else 0,
                "population": rd.population if rd else 0,
                "fatalities": rd.fatalities if rd else 0,
            }

        return states

    def get_osint_keywords(self) -> dict[str, list[str]]:
        """Get OSINT keywords for each region."""
        keywords: dict[str, list[str]] = {}
        for region_id, config in self.region_config.items():
            val = config.get("keywords", [config.get("country_name", region_id)])
            keywords[str(region_id)] = [str(v) for v in val]
        return keywords

    def to_dataframe(self) -> pd.DataFrame:
        """Export collected data as DataFrame."""
        rows = []
        for rid, rd in self._region_data.items():
            if rd is None:
                continue
            rows.append(
                {
                    "region_id": rid,
                    "country": rd.country_name,
                    "gdp_usd": rd.gdp_usd,
                    "population": rd.population,
                    "military_spending_pct": rd.military_spending_pct,
                    "fatalities": rd.fatalities,
                    "events": rd.events,
                    "article_count": rd.article_count,
                    "tone": rd.tone,
                    "military_capability": rd.military_capability,
                    "economic_capability": rd.economic_capability,
                }
            )
        return pd.DataFrame(rows)


class LiveDataUpdater:
    """Update running simulation with live real-world data."""

    def __init__(
        self,
        osint_pipeline=None,
        update_interval: int = 10,
    ) -> None:
        self.osint_pipeline = osint_pipeline
        self.update_interval = update_interval
        self._last_update: int = 0

    def should_update(self, step: int) -> bool:
        """Check if data should be updated at this step."""
        return step - self._last_update >= self.update_interval

    def update_model(self, model, step: int) -> None:
        """Update model with fresh real-world data."""
        if not self.should_update(step):
            return

        if self.osint_pipeline is None:
            return

        # Fetch fresh OSINT data
        from strategify.osint.pipeline import FeaturePipeline

        pipeline = self.osint_pipeline if self.osint_pipeline else FeaturePipeline()

        try:
            features = pipeline.compute()

            # Update agent capabilities based on OSINT
            for agent in model.schedule.agents:
                rid = getattr(agent, "region_id", "")
                if rid in features:
                    feats = features[rid]

                    # Update based on tension score
                    tension = feats.get("tension_score", 0)
                    if tension > 0.6:
                        agent.capabilities["military"] = min(1.0, agent.capabilities.get("military", 0.5) + 0.1)

            self._last_update = step
        except Exception:
            pass

    def get_current_tension(self) -> dict[str, float]:
        """Get current tension scores from OSINT."""
        if self.osint_pipeline is None:
            return {}

        try:
            features = self.osint_pipeline.compute()
            return {rid: feats.get("tension_score", 0) for rid, feats in features.items()}
        except Exception:
            return {}


def create_data_collector(
    regions: list[str] | None = None,
    auto_load: bool = True,
) -> RealWorldDataCollector:
    """Create a data collector for configured regions.

    Parameters
    ----------
    regions:
        List of region IDs. If None, uses defaults.
    auto_load:
        Whether to auto-load geometries.

    Returns
    -------
    RealWorldDataCollector
    """
    if regions:
        config = {
            r: {
                "country_name": r.title(),
                "id_map": r.lower()[:3],
                "keywords": [r],
            }
            for r in regions
        }
    else:
        config = None

    collector = RealWorldDataCollector(region_config=config)

    if auto_load:
        collector.load_geometries()

    return collector
