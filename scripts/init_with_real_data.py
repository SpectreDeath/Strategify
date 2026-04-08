"""Example: Initialize GeopolModel with real-world data.

This script demonstrates loading real-world geographic and OSINT data
to populate a simulation with realistic initial conditions.

Usage:
    python scripts/init_with_real_data.py

    # Or programmatically:
    from scripts.init_with_real_data import create_model_with_real_data

    model = create_model_with_real_data(use_osint=True)
"""

from __future__ import annotations

import logging
from pathlib import Path

import geopandas as gpd

from strategify.geo.loader import GeoJSONLoader, RegionSubsetConfig
from strategify.osint.adapters import GDELTAdapter
from strategify.osint.pipeline import FeaturePipeline
from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)


# Regional configuration for Eastern Europe simulation
EASTERN_EUROPE_CONFIG = {
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


def load_geometries(
    config: dict | None = None,
    resolution: str = "50m",
) -> gpd.GeoDataFrame:
    """Load and process geographic geometries.

    Parameters
    ----------
    config:
        Region configuration dict. Uses Eastern Europe default if None.
    resolution:
        Natural Earth resolution: "10m", "50m", or "110m"

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame with region_id and geometry columns.
    """
    config = config or EASTERN_EUROPE_CONFIG

    region_config = RegionSubsetConfig(
        countries=list(config.keys()),
        id_map={k: v["id_map"] for k, v in config.items()},
        resolution=resolution,
    )

    gdf = GeoJSONLoader.load(region_config)
    logger.info(f"Loaded {len(gdf)} regions")

    return gdf


def setup_osint_pipeline(
    config: dict | None = None,
    cache_ttl: int = 3600,
) -> FeaturePipeline:
    """Setup OSINT pipeline with real-world sources.

    Parameters
    ----------
    config:
        Region configuration with keywords.
    cache_ttl:
        Cache time-to-live in seconds.

    Returns
    -------
    FeaturePipeline
        Configured pipeline with GDELT/World Bank adapters.
    """
    config = config or EASTERN_EUROPE_CONFIG

    keywords = {v["id_map"]: v.get("keywords", [k]) for k, v in config.items()}

    pipeline = FeaturePipeline(
        region_keywords=keywords,
        adapters=[
            GDELTAdapter(),
        ],
        cache_ttl=cache_ttl,
    )

    return pipeline


def create_model_with_real_data(
    n_steps: int = 100,
    use_osint: bool = True,
    resolution: str = "50m",
    scenario: str | Path | None = None,
) -> GeopolModel:
    """Create a GeopolModel initialized with real-world data.

    Parameters
    ----------
    n_steps:
        Maximum simulation steps.
    use_osint:
        Whether to fetch real-time OSINT data for initialization.
    resolution:
        Geographic resolution.
    scenario:
        Optional scenario name/path.

    Returns
    -------
    GeopolModel
        Model initialized with real geometries and optional real data.
    """
    # Load geographic data
    gdf = load_geometries(resolution=resolution)

    model = GeopolModel(
        n_steps=n_steps,
        scenario=scenario,
        region_gdf=gdf,
    )

    if use_osint:
        try:
            pipeline = setup_osint_pipeline()
            features = pipeline.compute()

            # Apply OSINT features to agents
            for agent in model.schedule.agents:
                rid = getattr(agent, "region_id", "")
                if rid in features:
                    feats = features[rid]

                    # Adjust capabilities based on tension
                    tension = feats.get("tension_score", 0)
                    if tension > 0.5:
                        agent.capabilities["military"] = min(
                            1.0, agent.capabilities.get("military", 0.5) + 0.15
                        )
                    if tension > 0.7:
                        agent.posture = "Escalate"

                    logger.info(f"{rid}: tension={tension:.2f}, posture={agent.posture}")
        except Exception as e:
            logger.warning(f"OSINT update failed: {e}")

    return model


def run_simulation(
    n_steps: int = 50,
    use_osint: bool = True,
    verbose: bool = True,
) -> dict:
    """Run a simulation with real data and return results.

    Parameters
    ----------
    n_steps:
        Number of simulation steps.
    use_osint:
        Whether to use OSINT for initialization.
    verbose:
        Whether to print progress.

    Returns
    -------
    dict
        Simulation results with final state.
    """
    model = create_model_with_real_data(
        n_steps=n_steps,
        use_osint=use_osint,
    )

    for step in range(n_steps):
        model.step()
        if verbose and step % 10 == 0:
            escalations = model.escalation_count()
            logger.info(f"Step {step}: {escalations} escalated")

    # Collect results
    results = {
        "n_steps": n_steps,
        "final_escalations": model.escalation_count(),
    }

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 50)
    print("GeopolModel with Real-World Data")
    print("=" * 50)

    results = run_simulation(n_steps=20, use_osint=True)

    print("\nResults:")
    for k, v in results.items():
        print(f"  {k}: {v}")
