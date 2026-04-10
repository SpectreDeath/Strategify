"""Counterfactual analysis: systematic what-if scenario exploration.

Allows modifying simulation state at specific steps and comparing
outcomes against the baseline trajectory.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def run_baseline(
    model_factory: Callable,
    n_steps: int = 20,
) -> dict[str, Any]:
    """Run a baseline simulation and collect trajectory.

    Parameters
    ----------
    model_factory:
        Callable returning a fresh GeopolModel.
    n_steps:
        Number of steps.

    Returns
    -------
    dict
        ``trajectories``, ``final_postures``, ``escalation_count``.
    """
    from strategify.analysis.comparison import collect_trajectories

    model = model_factory()
    trajectories = collect_trajectories(model, n_steps)
    final = trajectories[-1] if trajectories else {}

    return {
        "trajectories": trajectories,
        "final_postures": final.get("postures", {}),
        "escalation_count": sum(final.get("postures", {}).values()),
    }


def apply_intervention(
    model: Any,
    step: int,
    interventions: list[dict[str, Any]],
) -> None:
    """Apply interventions to the model at a specific step.

    Parameters
    ----------
    model:
        GeopolModel instance.
    step:
        Current step number.
    interventions:
        List of intervention dicts. Each has ``type`` and parameters:

        - ``"set_posture"``: ``{"type": "set_posture", "region": "alpha", "posture": "Deescalate"}``
        - ``"set_relation"``: ``{"type": "set_relation",
          "source": "alpha", "target": "bravo", "weight": 0.5}``
        - ``"set_resource"``: ``{"type": "set_resource", "region": "alpha", "value": 2.0}``
        - ``"set_escalation"``: ``{"type": "set_escalation", "region": "alpha", "level": 0}``
    """
    agents_by_rid = {getattr(a, "region_id", ""): a for a in model.schedule.agents}

    for intervention in interventions:
        itype = intervention.get("type", "")

        if itype == "set_posture":
            rid = intervention["region"]
            agent = agents_by_rid.get(rid)
            if agent:
                agent.posture = intervention["posture"]
                logger.debug("Step %d: set %s posture to %s", step, rid, intervention["posture"])

        elif itype == "set_relation":
            src_rid = intervention["source"]
            tgt_rid = intervention["target"]
            src = agents_by_rid.get(src_rid)
            tgt = agents_by_rid.get(tgt_rid)
            if src and tgt and hasattr(model, "relations"):
                model.relations.set_relation(src.unique_id, tgt.unique_id, intervention["weight"])
                logger.debug(
                    "Step %d: set relation %s-%s to %s",
                    step,
                    src_rid,
                    tgt_rid,
                    intervention["weight"],
                )

        elif itype == "set_resource":
            rid = intervention["region"]
            model.region_resources[rid] = intervention["value"]
            logger.debug("Step %d: set %s resource to %s", step, rid, intervention["value"])

        elif itype == "set_escalation":
            rid = intervention["region"]
            agent = agents_by_rid.get(rid)
            if agent and hasattr(model, "escalation_ladder") and model.escalation_ladder is not None:
                from strategify.agents.escalation import EscalationLevel

                level = EscalationLevel(intervention["level"])
                model.escalation_ladder.set_level(agent.unique_id, level)
                logger.debug("Step %d: set %s escalation to %s", step, rid, level.name)


def run_counterfactual(
    model_factory: Callable,
    intervention_step: int,
    interventions: list[dict[str, Any]],
    n_steps: int = 20,
) -> dict[str, Any]:
    """Run a counterfactual simulation with interventions.

    Parameters
    ----------
    model_factory:
        Callable returning a fresh GeopolModel.
    intervention_step:
        Step at which to apply interventions.
    interventions:
        List of intervention dicts (see ``apply_intervention()``).
    n_steps:
        Total steps to run.

    Returns
    -------
    dict
        ``trajectories``, ``final_postures``, ``escalation_count``,
        ``intervention_step``, ``interventions``.
    """

    model = model_factory()
    trajectories = []

    for step in range(n_steps):
        if step == intervention_step:
            apply_intervention(model, step, interventions)
        model.step()

        snapshot = {
            "step": step,
            "postures": {},
            "resources": dict(model.region_resources),
        }
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            snapshot["postures"][rid] = 1.0 if agent.posture == "Escalate" else 0.0
        trajectories.append(snapshot)

    final = trajectories[-1] if trajectories else {}

    return {
        "trajectories": trajectories,
        "final_postures": final.get("postures", {}),
        "escalation_count": sum(final.get("postures", {}).values()),
        "intervention_step": intervention_step,
        "interventions": interventions,
    }


def compare_counterfactual(
    baseline: dict[str, Any],
    counterfactual: dict[str, Any],
) -> dict[str, Any]:
    """Compare baseline and counterfactual outcomes.

    Parameters
    ----------
    baseline:
        Result from ``run_baseline()``.
    counterfactual:
        Result from ``run_counterfactual()``.

    Returns
    -------
    dict
        ``escalation_diff``, ``posture_changes``, ``impact_summary``.
    """
    base_esc = baseline.get("escalation_count", 0)
    cf_esc = counterfactual.get("escalation_count", 0)
    escalation_diff = cf_esc - base_esc

    base_postures = baseline.get("final_postures", {})
    cf_postures = counterfactual.get("final_postures", {})

    posture_changes = {}
    for rid in set(base_postures) | set(cf_postures):
        b = base_postures.get(rid, 0)
        c = cf_postures.get(rid, 0)
        if b != c:
            posture_changes[rid] = {"baseline": b, "counterfactual": c}

    impact = "neutral"
    if escalation_diff < 0:
        impact = "deescalation"
    elif escalation_diff > 0:
        impact = "escalation"

    return {
        "escalation_diff": escalation_diff,
        "baseline_escalations": base_esc,
        "counterfactual_escalations": cf_esc,
        "posture_changes": posture_changes,
        "impact_summary": impact,
    }


def systematic_counterfactuals(
    model_factory: Callable,
    intervention_step: int,
    intervention_configs: list[list[dict[str, Any]]],
    n_steps: int = 20,
) -> list[dict[str, Any]]:
    """Run multiple counterfactual scenarios and compare each to baseline.

    Parameters
    ----------
    model_factory:
        Callable returning a fresh GeopolModel.
    intervention_step:
        Step at which to apply interventions.
    intervention_configs:
        List of intervention lists (one per counterfactual scenario).
    n_steps:
        Total steps to run.

    Returns
    -------
    list[dict]
        Each dict has ``counterfactual``, ``comparison``, ``index``.
    """
    baseline = run_baseline(model_factory, n_steps)
    results = []

    for i, interventions in enumerate(intervention_configs):
        cf = run_counterfactual(model_factory, intervention_step, interventions, n_steps)
        comparison = compare_counterfactual(baseline, cf)
        results.append(
            {
                "index": i,
                "interventions": interventions,
                "counterfactual": cf,
                "comparison": comparison,
            }
        )

    return results
