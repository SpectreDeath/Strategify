"""Alliance forecasting: predict alliance stability and fracture points.

Analyzes alliance networks to predict:
- Alliance stability scores
- Potential fracture points
- Recommended rebalancing actions
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


@dataclass
class AllianceStability:
    """Alliance stability assessment."""

    region_id: str
    stability_score: float  # 0-1, higher is more stable
    fracture_probability: float  # 0-1
    risk_factors: list[str]
    recommendations: list[str]
    uncertainty: float = 0.0  # Bayesian uncertainty
    posterior_alpha: float = 0.0  # Beta distribution shape parameter
    posterior_beta: float = 0.0  # Beta distribution shape parameter


class BayesianAllianceTracker:
    """Bayesian tracker for alliance fracture probability with uncertainty estimation.

    Uses Beta distribution to model fracture probability with conjugate prior,
    allowing updates as new evidence arrives.
    """

    def __init__(self, prior_alpha: float = 1.0, prior_beta: float = 1.0):
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.posterior_alpha = prior_alpha
        self.posterior_beta = prior_beta

    def update(self, fracture_observed: bool, n_trials: int = 1) -> None:
        self.posterior_alpha += int(fracture_observed) * n_trials
        self.posterior_beta += (1 - int(fracture_observed)) * n_trials

    def get_probability(self) -> float:
        """Get the expected value (mean) of the probability distribution."""
        alpha = self.posterior_alpha
        beta = self.posterior_beta
        if alpha + beta == 0:
            return 0.5
        return alpha / (alpha + beta)

    def get_mode(self) -> float:
        """Get the mode (most likely value) of the distribution."""
        alpha = self.posterior_alpha
        beta = self.posterior_beta
        if alpha <= 1 and beta <= 1:
            return 0.5
        if alpha <= 1:
            return 0.0
        if beta <= 1:
            return 1.0
        return (alpha - 1) / (alpha + beta - 2)

    def get_uncertainty(self) -> float:
        """Get normalized uncertainty (0-1, lower is more confident)."""
        alpha = self.posterior_alpha
        beta = self.posterior_beta
        total = alpha + beta
        if total < 2:
            return 1.0
        variance = (alpha * beta) / (total**2 * (total + 1))
        std = np.sqrt(variance)
        return min(1.0, std * 4)

    def get_confidence_interval(self, confidence: float = 0.95) -> tuple[float, float]:
        """Get confidence interval for the probability."""
        try:
            import scipy.stats

            return scipy.stats.beta.interval(confidence, self.posterior_alpha, self.posterior_beta)
        except ImportError:
            alpha = self.posterior_alpha
            beta = self.posterior_beta
            mean = alpha / (alpha + beta) if alpha + beta > 0 else 0.5
            std = (
                np.sqrt((alpha * beta) / ((alpha + beta) ** 2 * (alpha + beta + 1)))
                if alpha + beta > 1
                else 0.3
            )
            z_value = 1.96
            return (max(0.0, mean - z_value * std), min(1.0, mean + z_value * std))

    def get_pdf_value(self, x: float) -> float:
        """Get probability density at point x."""
        try:
            import scipy.stats

            return scipy.stats.beta.pdf(x, self.posterior_alpha, self.posterior_beta)
        except ImportError:
            alpha = self.posterior_alpha
            beta = self.posterior_beta
            if x <= 0 or x >= 1:
                return 0.0
            if alpha <= 1 and beta <= 1:
                return 1.0
            try:
                import scipy.special

                log_beta = np.log(scipy.special.beta(alpha, beta))
            except (ImportError, ValueError):
                log_beta = 0.0
            log_prob = (alpha - 1) * np.log(x) + (beta - 1) * np.log(1 - x)
            return np.exp(log_prob - log_beta) if log_beta != 0 else np.exp(log_prob)

    def reset(self) -> None:
        self.posterior_alpha = self.prior_alpha
        self.posterior_beta = self.prior_beta


def compute_alliance_strength(
    model: GeopolModel,
    region_id: str,
) -> float:
    """Compute alliance strength score for a region.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to assess.

    Returns
    -------
    float
        Alliance strength in [0, 1].
    """
    agent = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == region_id),
        None,
    )
    if agent is None or not model.relations:
        return 0.5

    allies = model.relations.get_allies(agent.unique_id)
    rivals = model.relations.get_rivals(agent.unique_id)

    if not allies and not rivals:
        return 0.5

    # Weight positive relations vs negative
    ally_strength = sum(
        model.relations.get_relation(agent.unique_id, auid) for auid in allies
    ) / max(1, len(allies))

    rival_strength = abs(
        sum(model.relations.get_relation(agent.unique_id, ruid) for ruid in rivals)
    ) / max(1, len(rivals))

    # Net alliance strength
    strength = (ally_strength - rival_strength + 1) / 2
    return np.clip(strength, 0, 1)


def predict_fracture_probability(
    model: GeopolModel,
    region_id: str,
    n_future_steps: int = 10,
) -> float:
    """Predict probability of alliance fracture.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to assess.
    n_future_steps:
        Steps to forecast.

    Returns
    -------
    float
        Fracture probability in [0, 1].
    """
    agent = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == region_id),
        None,
    )
    if agent is None or not model.relations:
        return 0.0

    # Factors that increase fracture risk
    risk_factors = 0.0

    # 1. Posture volatility
    try:
        df = model.datacollector.get_agent_vars_dataframe()
        agent_df = df[df["region_id"] == region_id].tail(5)
        if len(agent_df) > 1:
            changes = (agent_df["posture"] != agent_df["posture"].shift(1)).sum()
            risk_factors += changes / len(agent_df) * 0.3
    except Exception:
        pass

    # 2. Economic stress
    economic = agent.capabilities.get("economic", 0.5)
    if economic < 0.3:
        risk_factors += 0.2

    # 3. External pressure (rivals increasing strength)
    current_military = agent.capabilities.get("military", 0.5)
    for other in model.schedule.agents:
        if getattr(other, "region_id", "") == region_id:
            continue
        rel = (
            model.relations.get_relation(agent.unique_id, other.unique_id) if model.relations else 0
        )
        if rel < -0.3:  # Rival
            other_military = other.capabilities.get("military", 0.5)
            if other_military > current_military:
                risk_factors += 0.15

    # 4. Alliance neglect
    allies = model.relations.get_allies(agent.unique_id) if model.relations else []
    rivals = model.relations.get_rivals(agent.unique_id) if model.relations else []
    if len(allies) > 0 and len(rivals) > len(allies):
        risk_factors += 0.1 * (len(rivals) - len(allies))

    # Time decay - fractures less likely in short term
    time_factor = 1.0 - np.exp(-0.1 * n_future_steps)

    return np.clip(risk_factors * time_factor, 0, 1)


def predict_fracture_bayesian(
    model: GeopolModel,
    region_id: str,
    n_future_steps: int = 10,
    prior_strength: float = 0.5,
) -> dict[str, float]:
    """Predict fracture probability with Bayesian uncertainty estimation.

    Uses Beta distribution conjugate prior for fracture probability,
    updating based on observed risk factors.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to assess.
    n_future_steps:
        Steps to forecast.
    prior_strength:
        Prior belief strength (higher = more confident in prior).

    Returns
    -------
    dict
        Keys: 'probability', 'uncertainty', 'ci_lower', 'ci_upper', 'confidence'.
    """
    agent = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == region_id),
        None,
    )
    if agent is None or not model.relations:
        return {
            "probability": 0.0,
            "uncertainty": 1.0,
            "ci_lower": 0.0,
            "ci_upper": 1.0,
            "confidence": 0.0,
        }

    base_prob = predict_fracture_probability(model, region_id, n_future_steps)

    prior_alpha = prior_strength * base_prob + 1
    prior_beta = prior_strength * (1 - base_prob) + 1

    tracker = BayesianAllianceTracker(prior_alpha, prior_beta)

    evidence_weight = 0.0

    try:
        df = model.datacollector.get_agent_vars_dataframe()
        agent_df = df[df["region_id"] == region_id].tail(10)
        if len(agent_df) > 1:
            changes = (agent_df["posture"] != agent_df["posture"].shift(1)).sum()
            volatility = changes / len(agent_df)
            if volatility > 0.3:
                evidence_weight += 0.2
    except Exception:
        pass

    economic = agent.capabilities.get("economic", 0.5)
    if economic < 0.3:
        evidence_weight += 0.15

    allies = model.relations.get_allies(agent.unique_id) if model.relations else []
    rivals = model.relations.get_rivals(agent.unique_id) if model.relations else []
    if len(rivals) > len(allies):
        evidence_weight += 0.1 * min(1.0, (len(rivals) - len(allies)))

    if evidence_weight > 0:
        n_observations = int(evidence_weight * 10)
        for _ in range(n_observations):
            if evidence_weight > 0.3:
                tracker.update(True, 1)
            else:
                tracker.update(False, 1)

    probability = tracker.get_probability()
    uncertainty = tracker.get_uncertainty()
    ci_lower, ci_upper = tracker.get_confidence_interval(0.95)
    confidence = 1 - min(1.0, uncertainty)

    return {
        "probability": float(np.clip(probability, 0, 1)),
        "uncertainty": float(np.clip(uncertainty, 0, 1)),
        "ci_lower": float(np.clip(ci_lower, 0, 1)),
        "ci_upper": float(np.clip(ci_upper, 0, 1)),
        "confidence": float(confidence),
    }


def forecast_alliance_stability(
    model: GeopolModel,
    n_future_steps: int = 20,
) -> dict[str, AllianceStability]:
    """Forecast alliance stability for all regions.

    Parameters
    ----------
    model:
        The GeopolModel.
    n_future_steps:
        Steps to forecast.

    Returns
    -------
    dict
        ``{region_id: AllianceStability}``.
    """
    results = {}

    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        if rid == "unknown" or not model.relations:
            continue

        stability_score = compute_alliance_strength(model, rid)
        fracture_prob = predict_fracture_probability(model, rid, n_future_steps)

        # Identify risk factors
        risk_factors = []
        economic = agent.capabilities.get("economic", 0.5)
        if economic < 0.3:
            risk_factors.append("economic_stress")

        posture = getattr(agent, "posture", "Deescalate")
        if posture == "Escalate":
            risk_factors.append("escalation_posture")

        allies = model.relations.get_allies(agent.unique_id)
        rivals = model.relations.get_rivals(agent.unique_id)
        if len(rivals) > len(allies):
            risk_factors.append("numerical_disadvantage")

        # Recommendations
        recommendations = []
        if fracture_prob > 0.5:
            recommendations.append("diversify_alliance_partners")
        if stability_score < 0.3:
            recommendations.append("strengthen_existing_ties")
        if economic < 0.4:
            recommendations.append("address_economic_vulnerabilities")

        results[rid] = AllianceStability(
            region_id=rid,
            stability_score=stability_score,
            fracture_probability=fracture_prob,
            risk_factors=risk_factors,
            recommendations=recommendations,
        )

    return results


def identify_vulnerable_alliances(
    stability_results: dict[str, AllianceStability],
    threshold: float = 0.4,
) -> list[tuple[str, float]]:
    """Identify alliances at risk of fracture.

    Parameters
    ----------
    stability_results:
        Output from ``forecast_alliance_stability``.
    threshold:
        Stability below this is vulnerable.

    Returns
    -------
    list
        ``[(region_id, fracture_prob)]`` sorted by risk.
    """
    vulnerable = [
        (rid, s.fracture_probability)
        for rid, s in stability_results.items()
        if s.stability_score < threshold or s.fracture_probability > 0.3
    ]
    return sorted(vulnerable, key=lambda x: x[1], reverse=True)


def compute_network_resilience(
    model: GeopolModel,
) -> float:
    """Compute overall alliance network resilience.

    Parameters
    ----------
    model:
        The GeopolModel.

    Returns
    -------
    float
        Network resilience in [0, 1].
    """
    if not model.relations:
        return 0.5

    regions = [getattr(a, "region_id", "") for a in model.schedule.agents]
    if not regions:
        return 0.5

    # Average stability
    stabilities = [compute_alliance_strength(model, rid) for rid in regions]

    return np.mean(stabilities)


def suggest_rebalancing(
    model: GeopolModel,
    target_region: str,
) -> list[str]:
    """Suggest alliance rebalancing actions.

    Parameters
    ----------
    model:
        The GeopolModel.
    target_region:
        Region to analyze.

    Returns
    -------
    list
        Strategic recommendations.
    """
    suggestions = []

    agent = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == target_region),
        None,
    )
    if agent is None or not model.relations:
        return ["insufficient_data"]

    # Check current alliances
    allies = model.relations.get_allies(agent.unique_id)
    rivals = model.relations.get_rivals(agent.unique_id)

    # Add new allies
    if len(allies) < 2:
        suggestions.append("seek_additional_allies")

    # Strengthen existing
    for auid in allies:
        rel = model.relations.get_relation(agent.unique_id, auid)
        if rel < 0.7:
            suggestions.append("deepen_existing_partnerships")

    # Counter rival influence
    for ruid in rivals:
        rel = model.relations.get_relation(agent.unique_id, ruid)
        if rel < -0.5:
            suggestions.append("counter_rival_influence")

    # Economic stability
    economic = agent.capabilities.get("economic", 0.5)
    if economic < 0.5:
        suggestions.append("strengthen_economic_foundation")

    return suggestions if suggestions else ["maintain_current_strategy"]
