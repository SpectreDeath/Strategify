"""Scenario comparison: side-by-side trajectory analysis across simulation runs.

Compares escalation trajectories, diplomacy evolution, and economic
outcomes between different scenarios or parameter configurations.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def extract_trajectory(model: Any) -> dict[str, Any]:
    """Extract a simulation trajectory snapshot from the current model state.

    Parameters
    ----------
    model:
        A GeopolModel that has been stepped at least once.

    Returns
    -------
    dict
        Trajectory data: ``postures``, ``resources``, ``diplomacy_weights``,
        ``escalation_levels`` (if available).
    """
    postures = {}
    resources = {}
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        postures[rid] = 1.0 if agent.posture == "Escalate" else 0.0
        resources[rid] = model.region_resources.get(rid, 0.0)

    diplomacy_weights = []
    if hasattr(model, "relations"):
        for u, v, data in model.relations.graph.edges(data=True):
            diplomacy_weights.append(
                {
                    "source": u,
                    "target": v,
                    "weight": data.get("weight", 0.0),
                }
            )

    escalation_levels = {}
    if hasattr(model, "escalation_ladder") and model.escalation_ladder is not None:
        for uid, level in model.escalation_ladder.levels.items():
            agent = next((a for a in model.schedule.agents if a.unique_id == uid), None)
            if agent:
                escalation_levels[getattr(agent, "region_id", str(uid))] = int(level)

    return {
        "postures": postures,
        "resources": resources,
        "diplomacy_weights": diplomacy_weights,
        "escalation_levels": escalation_levels,
    }


def collect_trajectories(
    model: Any,
    n_steps: int = 20,
) -> list[dict[str, Any]]:
    """Run a simulation and collect trajectory at each step.

    Parameters
    ----------
    model:
        A GeopolModel instance.
    n_steps:
        Number of steps to run.

    Returns
    -------
    list[dict]
        List of trajectory snapshots, one per step.
    """
    trajectories = []
    for step in range(n_steps):
        model.step()
        snapshot = extract_trajectory(model)
        snapshot["step"] = step
        trajectories.append(snapshot)
    return trajectories


def compare_trajectories(
    trajectories_a: list[dict[str, Any]],
    trajectories_b: list[dict[str, Any]],
    names: tuple[str, str] = ("A", "B"),
) -> dict[str, Any]:
    """Compare two simulation trajectories.

    Parameters
    ----------
    trajectories_a, trajectories_b:
        Trajectory lists from ``collect_trajectories()``.
    names:
        Labels for the two scenarios.

    Returns
    -------
    dict
        Comparison results: ``escalation_divergence``, ``max_escalation_diff``,
        ``diplomacy_drift``, ``summary``.
    """
    min_len = min(len(trajectories_a), len(trajectories_b))

    if min_len == 0:
        return {"error": "Empty trajectories"}

    # Escalation divergence: mean absolute difference in escalation counts
    esc_diffs = []
    for i in range(min_len):
        a_esc = sum(trajectories_a[i]["postures"].values())
        b_esc = sum(trajectories_b[i]["postures"].values())
        esc_diffs.append(abs(a_esc - b_esc))

    # Diplomacy drift: change in mean edge weight over time
    def _mean_weight(trajectory):
        weights = [e["weight"] for e in trajectory.get("diplomacy_weights", [])]
        return np.mean(weights) if weights else 0.0

    dip_drift = []
    for i in range(min_len):
        a_w = _mean_weight(trajectories_a[i])
        b_w = _mean_weight(trajectories_b[i])
        dip_drift.append(abs(a_w - b_w))

    return {
        "names": names,
        "steps_compared": min_len,
        "escalation_divergence": np.mean(esc_diffs),
        "max_escalation_diff": max(esc_diffs) if esc_diffs else 0.0,
        "diplomacy_drift": np.mean(dip_drift),
        "escalation_diffs": esc_diffs,
        "diplomacy_drifts": dip_drift,
    }


def multi_scenario_comparison(
    scenario_trajectories: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Compare multiple scenario trajectories pairwise.

    Parameters
    ----------
    scenario_trajectories:
        ``{scenario_name: trajectory_list}``.

    Returns
    -------
    dict
        ``{("name_a", "name_b"): comparison_result}``
    """
    names = list(scenario_trajectories.keys())
    results = {}
    for i, name_a in enumerate(names):
        for name_b in names[i + 1 :]:
            key = (name_a, name_b)
            results[key] = compare_trajectories(
                scenario_trajectories[name_a],
                scenario_trajectories[name_b],
                names=(name_a, name_b),
            )
    return results


def trajectory_to_dataframe(
    trajectories: list[dict[str, Any]],
) -> pd.DataFrame:
    """Convert trajectory list to a DataFrame for analysis.

    Returns
    -------
    pd.DataFrame
        Rows = steps, columns = ``{region_id}_escalation``, ``{region_id}_resource``
    """
    records = []
    for t in trajectories:
        row = {"step": t["step"]}
        for rid, val in t["postures"].items():
            row[f"{rid}_escalation"] = val
        for rid, val in t["resources"].items():
            row[f"{rid}_resource"] = val
        records.append(row)
    return pd.DataFrame(records)
