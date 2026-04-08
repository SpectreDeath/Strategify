"""Scenario runner: CLI for running named scenarios with parameter sweeps.

Provides utilities for batch runs, parameter sweeps, and headless
experiment execution.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def run_scenario(
    scenario: str | Path,
    n_steps: int | None = None,
    output_dir: str | Path = "output",
    save_checkpoints: bool = False,
    checkpoint_interval: int = 0,
) -> dict[str, Any]:
    """Run a scenario and collect results.

    Parameters
    ----------
    scenario:
        Scenario name or path to JSON scenario file.
    n_steps:
        Override step count (uses scenario default if None).
    output_dir:
        Directory for output files.
    save_checkpoints:
        Whether to save state at each checkpoint_interval.
    checkpoint_interval:
        Steps between checkpoints (0 = only final state).

    Returns
    -------
    dict
        Run results with keys: ``scenario``, ``n_steps``, ``output_dir``,
        ``csv_path``, ``checkpoint_paths``.
    """
    from strategify.sim.model import GeopolModel
    from strategify.sim.persistence import save_state

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    model = GeopolModel(scenario=scenario)
    steps = n_steps or model.n_steps or 20

    checkpoint_paths = []

    for step in range(steps):
        model.step()

        if save_checkpoints and checkpoint_interval > 0 and (step + 1) % checkpoint_interval == 0:
            cp_path = output_dir / f"checkpoint_step_{step + 1:04d}.json"
            save_state(model, cp_path, metadata={"step": step + 1})
            checkpoint_paths.append(str(cp_path))

    # Save final state
    final_path = output_dir / "final_state.json"
    save_state(model, final_path, metadata={"steps_completed": steps})
    checkpoint_paths.append(str(final_path))

    # Save CSV
    try:
        df = model.datacollector.get_agent_vars_dataframe()
        df = df.sort_index().reset_index()
        csv_path = output_dir / "simulation_output.csv"
        df.to_csv(str(csv_path), index=False)
    except Exception:
        csv_path = None

    return {
        "scenario": getattr(model, "scenario_name", str(scenario)),
        "n_steps": steps,
        "output_dir": str(output_dir),
        "csv_path": str(csv_path) if csv_path else None,
        "checkpoint_paths": checkpoint_paths,
    }


def run_parameter_sweep(
    scenario: str | Path,
    param_grid: dict[str, list[Any]],
    n_steps: int = 20,
    output_dir: str | Path = "sweep_output",
    metric_fn: Callable | None = None,
) -> list[dict[str, Any]]:
    """Run a parameter sweep over a scenario.

    Parameters
    ----------
    scenario:
        Base scenario name or path.
    param_grid:
        Dict of parameter name -> list of values.
        Example: ``{"alpha_military": [0.3, 0.5, 0.7, 0.9]}``
    n_steps:
        Steps per run.
    output_dir:
        Directory for output files.
    metric_fn:
        Optional callable(model) -> float to compute a metric per run.

    Returns
    -------
    list[dict]
        One result dict per parameter combination with ``params``, ``metric``,
        ``agent_postures``.
    """
    from strategify.sim.model import GeopolModel

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate all parameter combinations
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    combinations = _cartesian_product(param_values)

    results = []
    for i, combo in enumerate(combinations):
        params = dict(zip(param_names, combo, strict=False))
        logger.info("Sweep run %d/%d: %s", i + 1, len(combinations), params)

        model = GeopolModel(scenario=scenario)

        # Apply parameter overrides to actor configs
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "")
            for param_name, value in params.items():
                if param_name.startswith(f"{rid}_"):
                    cap_key = param_name[len(rid) + 1 :]
                    if cap_key in agent.capabilities:
                        agent.capabilities[cap_key] = value

        for _ in range(n_steps):
            model.step()

        metric_value = metric_fn(model) if metric_fn else None
        postures = {a.region_id: a.posture for a in model.schedule.agents}

        results.append(
            {
                "run_id": i,
                "params": params,
                "metric": metric_value,
                "agent_postures": postures,
            }
        )

    # Save sweep results
    results_path = output_dir / "sweep_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    return results


def _cartesian_product(lists: list[list]) -> list[tuple]:
    """Compute Cartesian product of lists."""
    if not lists:
        return [()]
    result = [()]
    for lst in lists:
        result = [x + (y,) for x in result for y in lst]
    return result


def run_comparison(
    scenarios: list[str | Path],
    n_steps: int = 20,
    output_dir: str | Path = "comparison_output",
) -> dict[str, Any]:
    """Run multiple scenarios and compare results.

    Parameters
    ----------
    scenarios:
        List of scenario names or paths.
    n_steps:
        Steps per scenario.
    output_dir:
        Directory for output files.

    Returns
    -------
    dict
        ``{scenario_name: {n_steps, final_postures, escalation_summary}}``
    """
    from strategify.sim.model import GeopolModel

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    comparison = {}
    for scenario in scenarios:
        model = GeopolModel(scenario=scenario)
        for _ in range(n_steps):
            model.step()

        name = getattr(model, "scenario_name", str(scenario))
        postures = {a.region_id: a.posture for a in model.schedule.agents}
        escalated = sum(1 for a in model.schedule.agents if a.posture == "Escalate")

        comparison[name] = {
            "n_steps": n_steps,
            "final_postures": postures,
            "escalation_count": escalated,
            "deescalation_count": len(model.schedule.agents) - escalated,
        }

    # Save comparison
    comparison_path = output_dir / "comparison_results.json"
    with open(comparison_path, "w") as f:
        json.dump(comparison, f, indent=2, default=str)

    return comparison
