"""Historical calibration: fit simulation parameters to real-world crisis data.

Provides functions to load historical crisis datasets and compute
parameter values that reproduce observed escalation patterns.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Built-in historical crisis data
HISTORICAL_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "historical"


def create_sample_historical_data() -> dict[str, Any]:
    """Create sample historical crisis data for calibration.

    Returns a synthetic dataset mimicking the Cuban Missile Crisis
    escalation pattern for demonstration purposes.
    """
    return {
        "name": "cuban_missile_crisis",
        "period": "1962-10-14/1962-10-28",
        "actors": {
            "us": {"name": "United States", "military": 0.9, "economic": 0.9},
            "ussr": {"name": "Soviet Union", "military": 0.85, "economic": 0.7},
            "cuba": {"name": "Cuba", "military": 0.3, "economic": 0.2},
        },
        "escalation_timeline": [
            {"step": 0, "us": 0, "ussr": 0, "cuba": 0, "label": "Discovery"},
            {"step": 1, "us": 1, "ussr": 0, "cuba": 0, "label": "Reconnaissance"},
            {"step": 2, "us": 1, "ussr": 1, "cuba": 0, "label": "Diplomatic pressure"},
            {"step": 3, "us": 2, "ussr": 1, "cuba": 0, "label": "Quarantine"},
            {"step": 4, "us": 2, "ussr": 2, "cuba": 1, "label": "Military buildup"},
            {"step": 5, "us": 3, "ussr": 2, "cuba": 1, "label": "DEFCON 2"},
            {"step": 6, "us": 2, "ussr": 2, "cuba": 1, "label": "Back-channel talks"},
            {"step": 7, "us": 1, "ussr": 1, "cuba": 0, "label": "Resolution"},
        ],
        "alliances": [
            {"source": "ussr", "target": "cuba", "weight": 0.8},
            {"source": "us", "target": "ussr", "weight": -0.7},
        ],
    }


def load_historical_crisis(name: str) -> dict[str, Any]:
    """Load a historical crisis dataset.

    Parameters
    ----------
    name:
        Crisis name (e.g. ``"cuban_missile_crisis"``) or path to JSON file.

    Returns
    -------
    dict
        Historical crisis data.
    """
    # Try built-in file first
    path = HISTORICAL_DATA_DIR / f"{name}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)

    # Try as direct path
    direct = Path(name)
    if direct.exists():
        with open(direct) as f:
            return json.load(f)

    # Return sample data for known crises
    if name == "cuban_missile_crisis":
        return create_sample_historical_data()

    raise FileNotFoundError(f"Historical crisis data not found: {name}")


def timeline_to_dataframe(timeline: list[dict]) -> pd.DataFrame:
    """Convert escalation timeline to a wide DataFrame."""
    return pd.DataFrame(timeline).set_index("step")


def compute_calibration_error(
    simulation_ts: pd.DataFrame,
    historical_ts: pd.DataFrame,
    mapping: dict[str, str] | None = None,
) -> float:
    """Compute mean squared error between simulation and historical trajectories.

    Parameters
    ----------
    simulation_ts:
        Simulation time series (steps x regions).
    historical_ts:
        Historical time series (steps x actors).
    mapping:
        Optional mapping from simulation region IDs to historical actor IDs.
        If None, uses column order matching.

    Returns
    -------
    float
        Mean squared error (lower = better calibration).
    """
    if mapping:
        sim_cols = [c for c in simulation_ts.columns if c in mapping]
        hist_cols = [mapping[c] for c in sim_cols]
        sim_data = simulation_ts[sim_cols].values
        hist_data = (
            historical_ts[hist_cols].values
            if all(c in historical_ts.columns for c in hist_cols)
            else None
        )
    else:
        min_cols = min(simulation_ts.shape[1], historical_ts.shape[1])
        sim_data = simulation_ts.iloc[:, :min_cols].values
        hist_data = historical_ts.iloc[:, :min_cols].values

    if hist_data is None:
        return float("inf")

    min_len = min(len(sim_data), len(hist_data))
    sim_data = sim_data[:min_len]
    hist_data = hist_data[:min_len]

    return float(np.mean((sim_data - hist_data) ** 2))


def calibrate_parameters(
    model_factory: Callable,
    historical_data: dict[str, Any],
    param_ranges: dict[str, tuple[float, float]],
    n_samples: int = 20,
    n_steps: int = 8,
) -> dict[str, Any]:
    """Calibrate model parameters to match historical escalation patterns.

    Uses random search to find parameter values that minimize the MSE
    between simulation output and historical data.

    Parameters
    ----------
    model_factory:
        Callable(**kwargs) -> GeopolModel.
    historical_data:
        Historical crisis dataset from ``load_historical_crisis()``.
    param_ranges:
        Parameter search space: ``{param_name: (low, high)}``.
    n_samples:
        Number of random samples to try.
    n_steps:
        Simulation steps per sample.

    Returns
    -------
    dict
        ``best_params``, ``best_error``, ``all_results``, ``historical_name``.
    """
    from strategify.analysis.timeseries import prepare_agent_timeseries

    hist_timeline = historical_data.get("escalation_timeline", [])
    if not hist_timeline:
        return {"error": "No historical timeline data"}

    hist_df = timeline_to_dataframe(hist_timeline)
    actor_mapping = {a: a for a in historical_data.get("actors", {})}

    param_names = list(param_ranges.keys())
    best_error = float("inf")
    best_params = {}
    all_results = []

    rng = np.random.default_rng(42)

    for i in range(n_samples):
        # Sample random parameters
        params = {}
        for name in param_names:
            low, high = param_ranges[name]
            params[name] = float(rng.uniform(low, high))

        try:
            model = model_factory(**params)

            # Run simulation
            for _ in range(n_steps):
                model.step()

            # Extract time series
            agent_df = model.datacollector.get_agent_vars_dataframe()
            sim_ts = prepare_agent_timeseries(agent_df)

            # Compute error
            error = compute_calibration_error(sim_ts, hist_df, actor_mapping)

            all_results.append({"params": params, "error": error})

            if error < best_error:
                best_error = error
                best_params = params

        except Exception as exc:
            logger.warning("Calibration sample %d failed: %s", i, exc)
            all_results.append({"params": params, "error": float("inf")})

    return {
        "best_params": best_params,
        "best_error": best_error,
        "all_results": sorted(all_results, key=lambda x: x["error"]),
        "historical_name": historical_data.get("name", "unknown"),
    }
