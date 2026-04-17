"""War game simulation: adversary response and counter-strategy modeling.

Simulates how adversaries might respond to strategic actions,
allowing planners to anticipate and prepare for multiple scenarios.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class AdversaryType(Enum):
    """Types of adversary forecasting models."""

    RATIONAL = "rational"
    AGGRESSIVE = "aggressive"
    DEFENSIVE = "defensive"
    OPPORTUNISTIC = "opportunistic"
    FATALISTIC = "fatalistic"


@dataclass
class AdversaryScenario:
    """A simulated adversary response scenario."""

    scenario_id: str
    description: str
    probability: float
    outcome_score: float
    region_states: dict = field(default_factory=dict)


@dataclass
class WarGameResult:
    """Results from war game simulation."""

    scenario_id: str
    expected_outcome: float
    worst_case: float
    best_case: float
    recommended_response: str
    scenarios: list[AdversaryScenario]


def predict_adversary_response(
    model,
    actor_id: str,
    my_action: str,
    adversary_type: AdversaryType = AdversaryType.RATIONAL,
    deterministic: bool = False,
    escalate_prob: float = 0.7,
) -> str:
    """Predict adversary response to a given action.

    Parameters
    ----------
    model:
        The GeopolModel.
    actor_id:
        The adversary region ID.
    my_action:
        My planned action ("Escalate" or "Deescalate").
    adversary_type:
        Type of adversary forecasting model.
    deterministic:
        If True, use predictable fallback instead of random.
    escalate_prob:
        Probability of escalation for FATALISTIC adversaries (default 0.7).

    Returns
    -------
    str
        Predicted adversary response.
    """
    if model is None:
        if adversary_type == AdversaryType.AGGRESSIVE:
            return "Escalate"
        elif adversary_type == AdversaryType.DEFENSIVE:
            return "Deescalate"
        elif adversary_type == AdversaryType.FATALISTIC:
            return "Escalate" if escalate_prob >= 0.5 else "Deescalate"
        elif adversary_type == AdversaryType.OPPORTUNISTIC:
            return "Deescalate"
        else:
            return "Deescalate"

    adversary = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == actor_id),
        None,
    )
    if adversary is None:
        return "Unknown"

    current_posture = getattr(adversary, "posture", "Deescalate")
    military = adversary.capabilities.get("military", 0.5)
    personality = getattr(adversary, "personality", "Neutral")

    if adversary_type == AdversaryType.AGGRESSIVE:
        return "Escalate"
    elif adversary_type == AdversaryType.DEFENSIVE:
        return "Deescalate"
    elif adversary_type == AdversaryType.FATALISTIC:
        if deterministic:
            return "Escalate" if escalate_prob >= 0.5 else "Deescalate"
        return "Escalate" if np.random.random() < escalate_prob else "Deescalate"
    elif adversary_type == AdversaryType.OPPORTUNISTIC:
        if my_action == "Escalate":
            return "Escalate" if military > 0.6 else "Deescalate"
        else:
            return "Deescalate" if military < 0.4 else "Escalate"
    elif adversary_type == AdversaryType.RATIONAL:
        if my_action == "Escalate":
            return "Escalate" if military > 0.5 or current_posture == "Escalate" else "Deescalate"
        else:
            return "Deescalate" if personality == "Pacifist" else current_posture


def run_war_game(
    model_factory: Callable,
    initial_state: dict,
    my_actions: list[str],
    n_simulations: int = 100,
) -> WarGameResult:
    """Simulate multiple adversary response scenarios.

    Parameters
    ----------
    model_factory:
        Callable returning a GeopolModel.
    initial_state:
        Dict of region_id -> initial posture.
    my_actions:
        My planned actions per step.
    n_simulations:
        Number of Monte Carlo simulations.

    Returns
    -------
    WarGameResult
        Aggregated results from all scenarios.
    """
    outcomes = []
    all_scenarios: list[AdversaryScenario] = []

    for _ in range(n_simulations):
        model = model_factory()

        # Apply initial state
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "")
            if rid in initial_state:
                agent.posture = initial_state[rid]

        # Apply my actions and observe responses
        scenario_states = {}
        for action in my_actions:
            # Find adversaries and predict responses
            for agent in model.schedule.agents:
                rid = getattr(agent, "region_id", "")
                if rid not in initial_state:
                    continue

                # Determine adversary type based on personality
                adversary_type = {
                    "Aggressor": AdversaryType.AGGRESSIVE,
                    "Pacifist": AdversaryType.DEFENSIVE,
                    "Grudger": AdversaryType.FATALISTIC,
                    "Tit-for-Tat": AdversaryType.RATIONAL,
                    "Neutral": AdversaryType.OPPORTUNISTIC,
                }.get(getattr(agent, "personality", "Neutral"), AdversaryType.RATIONAL)

                response = predict_adversary_response(model, rid, action, adversary_type)
                agent.posture = response
                scenario_states[rid] = response

            model.step()

        # Compute outcome score
        escalate_count = sum(1 for a in model.schedule.agents if getattr(a, "posture", "") == "Escalate")
        outcome = -escalate_count  # Negative is bad (more escalation)
        outcomes.append(outcome)

        all_scenarios.append(
            AdversaryScenario(
                scenario_id=f"sim_{_}",
                description=f"Action sequence: {my_actions}",
                probability=1.0 / n_simulations,
                outcome_score=outcome,
                region_states=scenario_states,
            )
        )

    # Aggregate results
    outcomes = np.array(outcomes)

    # Determine recommended response
    mean_outcome = np.mean(outcomes)
    if mean_outcome < -2:
        recommended = "Consider de-escalation - high adversary aggression likely"
    elif mean_outcome < 0:
        recommended = "Proceed with caution - moderate risk"
    else:
        recommended = "Favorable conditions - proceed"

    return WarGameResult(
        scenario_id="war_game",
        expected_outcome=float(mean_outcome),
        worst_case=float(np.min(outcomes)),
        best_case=float(np.max(outcomes)),
        recommended_response=recommended,
        scenarios=all_scenarios,
    )


def simulate_counter_strategy(
    model: GeopolModel,
    target_region: str,
    strategy: str,
    n_steps: int = 10,
) -> dict:
    """Simulate counter-strategy effectiveness.

    Parameters
    ----------
    model:
        The GeopolModel.
    target_region:
        Region to analyze.
    strategy:
        Strategy name: "sanction", "alliance", "military", "diplomatic".
    n_steps:
        Simulation steps.

    Returns
    -------
    dict
        Effectiveness metrics.
    """
    target = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == target_region),
        None,
    )
    if target is None:
        return {"error": "Region not found"}

    initial_military = target.capabilities.get("military", 0.5)
    initial_economic = target.capabilities.get("economic", 0.5)

    # Strategy effects
    effects = {
        "sanction": {"military_impact": -0.1, "economic_impact": -0.3},
        "alliance": {"military_impact": 0.2, "economic_impact": 0.1},
        "military": {"military_impact": -0.2, "economic_impact": -0.1},
        "diplomatic": {"military_impact": 0.0, "economic_impact": 0.2},
    }

    impact = effects.get(strategy, {"military_impact": 0, "economic_impact": 0})

    # Run simulation
    for _ in range(n_steps):
        model.step()

    final_military = target.capabilities.get("military", 0.5)
    final_economic = target.capabilities.get("economic", 0.5)

    return {
        "strategy": strategy,
        "target": target_region,
        "initial_military": initial_military,
        "final_military": final_military,
        "military_change": final_military - initial_military,
        "initial_economic": initial_economic,
        "final_economic": final_economic,
        "economic_change": final_economic - initial_economic,
        "effectiveness_score": (-(impact.get("military_impact", 0) + impact.get("economic_impact", 0))),
    }


def analyze_red_lines(
    model: GeopolModel,
    region_ids: list[str],
) -> dict[str, list[str]]:
    """Identify red lines (actions that trigger escalation).

    Parameters
    ----------
    model:
        The GeopolModel.
    region_ids:
        Regions to analyze.

    Returns
    -------
    dict
        ``{region_id: [triggering_actions]}``.
    """
    red_lines = {}

    for rid in region_ids:
        agent = next(
            (a for a in model.schedule.agents if getattr(a, "region_id", "") == rid),
            None,
        )
        if agent is None:
            continue

        triggers = []

        # Military build-up triggers
        if agent.capabilities.get("military", 0) > 0.7:
            triggers.append("excessive_military_buildup")

        # Economic aggression triggers
        if agent.capabilities.get("economic", 0) > 0.8:
            triggers.append("economic_pressure")

        # Alliance expansion triggers
        if model.relations:
            allies = model.relations.get_allies(agent.unique_id)
            if len(allies) > 2:
                triggers.append("alliance_expansion")

        # Proximity triggers
        for other in model.schedule.agents:
            if getattr(other, "region_id", "") == rid:
                continue
            rel = model.relations.get_relation(agent.unique_id, other.unique_id)
            if rel > 0.5:  # Strong alliance with rival's rival
                triggers.append("strategic_partnership")

        red_lines[rid] = triggers

    return red_lines
