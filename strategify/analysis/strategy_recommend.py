"""Strategic recommendations: AI-generated strategic advice.

Provides automated strategic recommendations based on:
- Game-theoretic optimal strategies
- Risk-weighted decision making
- Historical pattern analysis
- Multi-objective optimization
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


@dataclass
class StrategicRecommendation:
    """A strategic recommendation."""

    action: str
    rationale: str
    expected_impact: float  # -1 to 1
    risk_level: str  # "low", "medium", "high"
    confidence: float  # 0 to 1
    region: str


@dataclass
class StrategyReport:
    """Complete strategic analysis report."""

    region: str
    recommendations: list[StrategicRecommendation] = field(default_factory=list)
    risk_assessment: str = ""
    opportunities: list[str] = field(default_factory=list)
    threats: list[str] = field(default_factory=list)


def analyze_strategic_position(
    model: GeopolModel,
    region_id: str,
) -> dict:
    """Analyze strategic position of a region.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to analyze.

    Returns
    -------
    dict
        Position metrics.
    """
    agent = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == region_id),
        None,
    )
    if agent is None:
        return {"error": "Region not found"}

    # Capabilities
    military = agent.capabilities.get("military", 0.5)
    economic = agent.capabilities.get("economic", 0.5)

    # Relations
    if model.relations:
        allies = model.relations.get_allies(agent.unique_id)
        rivals = model.relations.get_rivals(agent.unique_id)
        ally_count = len(allies)
        rival_count = len(rivals)
    else:
        ally_count = rival_count = 0

    # Posture
    posture = getattr(agent, "posture", "Deescalate")

    # Composite score
    power_score = (military + economic) / 2
    position_score = power_score + (ally_count * 0.1) - (rival_count * 0.15)

    return {
        "military": military,
        "economic": economic,
        "ally_count": ally_count,
        "rival_count": rival_count,
        "posture": posture,
        "power_score": power_score,
        "position_score": position_score,
    }


def compute_optimal_action(
    model: GeopolModel,
    region_id: str,
    objective: str = "stability",
) -> StrategicRecommendation:
    """Compute optimal strategic action.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to analyze.
    objective:
        Objective: "stability", "power", "influence".

    Returns
    -------
    StrategicRecommendation
        Recommended action.
    """
    position = analyze_strategic_position(model, region_id)
    if "error" in position:
        return StrategicRecommendation(
            action="unknown",
            rationale="region_not_found",
            expected_impact=0.0,
            risk_level="high",
            confidence=0.0,
            region=region_id,
        )

    # Decision logic based on objective
    if objective == "stability":
        # Minimize escalation risk
        if position["rival_count"] > position["ally_count"]:
            action = "deescalate"
            rationale = "reduce_rival_threat"
            expected_impact = 0.6
            risk_level = "low"
        elif position["posture"] == "Escalate" and position["rival_count"] > 0:
            action = "deescalate"
            rationale = "de_escalate_to_prevent_spiral"
            expected_impact = 0.5
            risk_level = "medium"
        else:
            action = "maintain"
            rationale = "stable_position"
            expected_impact = 0.3
            risk_level = "low"

    elif objective == "power":
        # Maximize military/economic
        if position["military"] < 0.5:
            action = "militarize"
            rationale = "increase_military_capability"
            expected_impact = 0.4
            risk_level = "high"
        elif position["ally_count"] < 2:
            action = "alliance_build"
            rationale = "seek_allies"
            expected_impact = 0.5
            risk_level = "medium"
        else:
            action = "maintain"
            rationale = "maintain_power"
            expected_impact = 0.2
            risk_level = "low"

    elif position.get("objective") == "influence":
        if position["economic"] < 0.5:
            action = "economic_expand"
            rationale = "increase_economic_influence"
            expected_impact = 0.4
            risk_level = "medium"
        else:
            action = "diplomatic"
            rationale = "leverage_economic_power"
            expected_impact = 0.5
            risk_level = "low"

    # Confidence based on position certainty
    confidence = min(1.0, position["power_score"] + 0.3)

    return StrategicRecommendation(
        action=action,
        rationale=rationale,
        expected_impact=expected_impact,
        risk_level=risk_level,
        confidence=confidence,
        region=region_id,
    )


def generate_strategy_report(
    model: GeopolModel,
    region_id: str,
) -> StrategyReport:
    """Generate comprehensive strategic report.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to analyze.

    Returns
    -------
    StrategyReport
        Strategic recommendations.
    """
    position = analyze_strategic_position(model, region_id)
    if "error" in position:
        return StrategyReport(region=region_id)

    # Generate recommendations for different objectives
    recommendations = [
        compute_optimal_action(model, region_id, "stability"),
        compute_optimal_action(model, region_id, "power"),
        compute_optimal_action(model, region_id, "influence"),
    ]

    # Identify opportunities
    opportunities = []
    if position["ally_count"] < 2:
        opportunities.append("expand_alliance_network")
    if position["economic"] > 0.6:
        opportunities.append("leverage_economic_relationships")
    if position["military"] > 0.6:
        opportunities.append("military_deterrence")

    # Identify threats
    threats = []
    if position["rival_count"] > position["ally_count"]:
        threats.append("numerical_disadvantage")
    if position["military"] < 0.3:
        threats.append("military_weakness")
    if position["economic"] < 0.3:
        threats.append("economic_vulnerability")
    if position["posture"] == "Escalate":
        threats.append("escalation_spiral_risk")

    # Risk assessment
    risk_score = position.get("position_score", 0.5)
    if risk_score < 0.3:
        risk_assessment = "critical"
    elif risk_score < 0.5:
        risk_assessment = "vulnerable"
    elif risk_score < 0.7:
        risk_assessment = "stable"
    else:
        risk_assessment = "dominant"

    return StrategyReport(
        region=region_id,
        recommendations=recommendations,
        risk_assessment=risk_assessment,
        opportunities=opportunities,
        threats=threats,
    )


def recommend_preemptive_actions(
    model: GeopolModel,
    target_risk: float = 0.5,
) -> list[dict]:
    """Recommend preemptive actions for high-risk regions.

    Parameters
    ----------
    model:
        The GeopolModel.
    target_risk:
        Risk threshold for recommendations.

    Returns
    -------
    list
        Recommended actions per region.
    """
    from strategify.analysis.strategic_risk import assess_all_risks

    risks = assess_all_risks(model)
    actions = []

    for rid, data in risks.items():
        if data["threat_score"] > target_risk:
            analyze_strategic_position(model, rid)  # noqa: F841
            rec = compute_optimal_action(model, rid)

            actions.append(
                {
                    "region": rid,
                    "threat_score": data["threat_score"],
                    "recommended_action": rec.action,
                    "rationale": rec.rationale,
                    "expected_impact": rec.expected_impact,
                }
            )

    return sorted(actions, key=lambda x: x["threat_score"], reverse=True)


def compute_win_probability(
    model: GeopolModel,
    aggressor_id: str,
    defender_id: str,
    include_uncertainty: bool = False,
) -> float | dict:
    """Compute win probability in bilateral conflict.

    Parameters
    ----------
    model:
        The GeopolModel.
    aggressor_id:
        Attacking region.
    defender_id:
        Defending region.
    include_uncertainty:
        If True, return dict with probability and uncertainty bounds.

    Returns
    -------
    float or dict
        Aggressor win probability in [0, 1], or dict with bounds if include_uncertainty=True.
    """

    attacker = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == aggressor_id),
        None,
    )
    defender = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == defender_id),
        None,
    )

    if attacker is None or defender is None:
        return (
            {"probability": 0.5, "ci_lower": 0.2, "ci_upper": 0.8, "uncertainty": 0.3} if include_uncertainty else 0.5
        )

    att_military = attacker.capabilities.get("military", 0.5)
    def_military = defender.capabilities.get("military", 0.5)
    att_economic = attacker.capabilities.get("economic", 0.5)
    def_economic = defender.capabilities.get("economic", 0.5)

    att_power = att_military + att_economic
    def_power = def_military + def_economic

    att_allies = model.relations.get_allies(attacker.unique_id) if model.relations else []
    def_allies = model.relations.get_allies(defender.unique_id) if model.relations else []

    ally_strength_att = 0.0
    for aid in att_allies:
        ally = next((a for a in model.schedule.agents if a.unique_id == aid), None)
        if ally:
            ally_strength_att += (ally.capabilities.get("military", 0.5) + ally.capabilities.get("economic", 0.5)) / 2

    ally_strength_def = 0.0
    for aid in def_allies:
        ally = next((a for a in model.schedule.agents if a.unique_id == aid), None)
        if ally:
            ally_strength_def += (ally.capabilities.get("military", 0.5) + ally.capabilities.get("economic", 0.5)) / 2

    total_att_power = att_power + ally_strength_att * 0.5
    total_def_power = def_power + ally_strength_def * 0.5

    if total_att_power + total_def_power > 0:
        power_ratio = total_att_power / (total_att_power + total_def_power)
    else:
        power_ratio = 0.5

    ally_advantage = (len(att_allies) - len(def_allies)) * 0.05
    ally_power_adv = (ally_strength_att - ally_strength_def) * 0.1

    score = power_ratio + ally_advantage + ally_power_adv
    probability = np.clip(score, 0.05, 0.95)

    if include_uncertainty:
        power_spread = abs(att_military - def_military) + abs(att_economic - def_economic)
        uncertainty = 0.15 + 0.1 * (1 - min(1.0, power_spread))
        ci_lower = max(0.05, probability - uncertainty)
        ci_upper = min(0.95, probability + uncertainty)
        return {
            "probability": probability,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "uncertainty": uncertainty,
            "ally_count_att": len(att_allies),
            "ally_count_def": len(def_allies),
            "total_power_att": total_att_power,
            "total_power_def": total_def_power,
        }

    return probability
