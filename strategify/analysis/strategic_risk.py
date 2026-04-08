"""Strategic risk assessment: probability-based threat scoring and risk levels.

Provides risk scoring for each region based on multiple factors:
- Escalation probability
- Military capability
- Economic vulnerability
- Alliance strength
- Historical volatility

Also includes adaptive weight learning based on historical accuracy.
"""

from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class RiskLevel(IntEnum):
    """Risk levels from 0 (minimal) to 4 (critical)."""

    MINIMAL = 0
    LOW = 1
    MODERATE = 2
    HIGH = 3
    CRITICAL = 4


class AdaptiveWeightLearner:
    """Learns optimal factor weights based on prediction accuracy.

    Uses exponential moving average to adjust weights when predictions
    are validated or contradicted by actual outcomes.

    Singleton instance accessible via module-level functions.
    """

    _instance: AdaptiveWeightLearner | None = None
    _initialized: bool = False

    def __new__(cls, n_factors: int = 5, learning_rate: float = 0.1) -> AdaptiveWeightLearner:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, n_factors: int = 5, learning_rate: float = 0.1):
        if not AdaptiveWeightLearner._initialized:
            self.n_factors = n_factors
            self.learning_rate = learning_rate
            self.weights = np.array([0.3, 0.25, 0.15, 0.15, 0.15])
            self.factor_names = ["posture", "military", "economic", "alliance", "volatility"]
            self.correct_predictions = np.zeros(n_factors)
            self.total_predictions = np.zeros(n_factors)
            AdaptiveWeightLearner._initialized = True

    @classmethod
    def get_instance(cls) -> AdaptiveWeightLearner:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton for testing."""
        cls._instance = None
        cls._initialized = False

    def update(
        self,
        factor_values: list[float],
        actual_outcome: float,
        predicted_outcome: float,
    ) -> None:
        error = actual_outcome - predicted_outcome
        for i, _ in enumerate(factor_values):
            self.total_predictions[i] += 1
            if abs(error) < 0.2:
                self.correct_predictions[i] += 1

        accuracy = np.divide(
            self.correct_predictions,
            self.total_predictions,
            where=self.total_predictions > 0,
            out=np.zeros_like(self.correct_predictions),
        )

        target_weights = (
            accuracy / accuracy.sum()
            if accuracy.sum() > 0
            else np.ones(self.n_factors) / self.n_factors
        )

        self.weights = (1 - self.learning_rate) * self.weights + self.learning_rate * target_weights
        self.weights = np.clip(self.weights, 0.05, 0.5)
        self.weights = self.weights / self.weights.sum()

    def get_weights(self) -> dict[str, float]:
        return dict(zip(self.factor_names, self.weights, strict=True))


def get_adaptive_learner() -> AdaptiveWeightLearner:
    """Get the global adaptive weight learner instance."""
    return AdaptiveWeightLearner.get_instance()


def compute_threat_score_adaptive(
    model: GeopolModel,
    region_id: str,
    lookback_steps: int = 10,
) -> float:
    """Compute threat score using adaptive learned weights.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to assess.
    lookback_steps:
        Number of steps for historical volatility.

    Returns
    -------
    float
        Threat score in [0, 1] - higher is more threatening.
    """
    learner = get_adaptive_learner()
    weights = learner.get_weights()
    weight_list = [weights.get(name, 0.2) for name in learner.factor_names]
    return compute_threat_score(model, region_id, lookback_steps, weight_list)


def compute_threat_score(
    model: GeopolModel,
    region_id: str,
    lookback_steps: int = 10,
    weights: list[float] | None = None,
) -> float:
    """Compute composite threat score for a region.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to assess.
    lookback_steps:
        Number of steps for historical volatility.
    weights:
        Optional custom weights for factors. Defaults to [0.3, 0.25, 0.15, 0.15, 0.15].

    Returns
    -------
    float
        Threat score in [0, 1] - higher is more threatening.
    """
    agent = next(
        (a for a in model.schedule.agents if getattr(a, "region_id", "") == region_id),
        None,
    )
    if agent is None:
        return 0.0

    if weights is None:
        weights = [0.3, 0.25, 0.15, 0.15, 0.15]

    posture_score = 1.0 if getattr(agent, "posture", "Deescalate") == "Escalate" else 0.0
    military = agent.capabilities.get("military", 0.5)
    economic = agent.capabilities.get("economic", 0.5)
    vuln_score = 1.0 - economic

    alliance_pressure = 0.0
    if model.relations:
        for other in model.schedule.agents:
            if getattr(other, "region_id", "") == region_id:
                continue
            rel = model.relations.get_relation(agent.unique_id, other.unique_id)
            if rel < 0:
                alliance_pressure += abs(rel)
    alliance_pressure = min(1.0, alliance_pressure / 2.0)

    volatility = compute_volatility(model, region_id, lookback_steps)

    factors = [posture_score, military, vuln_score, alliance_pressure, volatility]
    threat = sum(w * f for w, f in zip(weights, factors, strict=True))

    return min(1.0, threat)


def compute_volatility(
    model: GeopolModel,
    region_id: str,
    lookback_steps: int = 10,
) -> float:
    """Compute historical volatility of escalation posture.

    Parameters
    ----------
    model:
        The GeopolModel.
    region_id:
        Region to assess.
    lookback_steps:
        Number of steps to examine.

    Returns
    -------
    float
        Volatility score in [0, 1].
    """
    try:
        df = model.datacollector.get_agent_vars_dataframe()
        agent_df = df[df["region_id"] == region_id].tail(lookback_steps)
        if len(agent_df) < 2:
            return 0.0
        changes = (agent_df["posture"] != agent_df["posture"].shift(1)).sum()
        return min(1.0, changes / len(agent_df))
    except Exception:
        return 0.0


def get_risk_level(threat_score: float) -> RiskLevel:
    """Convert threat score to risk level.

    Parameters
    ----------
    threat_score:
        Threat score in [0, 1].

    Returns
    -------
    RiskLevel
        Enum from MINIMAL to CRITICAL.
    """
    if threat_score < 0.2:
        return RiskLevel.MINIMAL
    elif threat_score < 0.4:
        return RiskLevel.LOW
    elif threat_score < 0.6:
        return RiskLevel.MODERATE
    elif threat_score < 0.8:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


def assess_all_risks(model: GeopolModel) -> dict[str, dict]:
    """Assess risks for all regions.

    Parameters
    ----------
    model:
        The GeopolModel.

    Returns
    -------
    dict
        ``{region_id: {threat_score, risk_level, factors}}``.
    """
    results = {}
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        if rid == "unknown":
            continue

        threat = compute_threat_score(model, rid)
        risk_level = get_risk_level(threat)

        # Individual factors for transparency
        posture = getattr(agent, "posture", "Deescalate")
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)
        volatility = compute_volatility(model, rid)

        results[rid] = {
            "threat_score": threat,
            "risk_level": risk_level.name,
            "posture": posture,
            "military": military,
            "economic": economic,
            "volatility": volatility,
        }

    return results


def identify_critical_regions(risks: dict[str, dict]) -> list[str]:
    """Identify regions with HIGH or CRITICAL risk.

    Parameters
    ----------
    risks:
        Output from ``assess_all_risks``.

    Returns
    -------
    list
        Region IDs sorted by threat score descending.
    """
    critical = [rid for rid, data in risks.items() if data["risk_level"] in ("HIGH", "CRITICAL")]
    return sorted(
        critical,
        key=lambda r: risks[r].get("threat_score", 0),
        reverse=True,
    )


def compute_regional_risk_matrix(
    model: GeopolModel,
    lookback_steps: int = 20,
) -> np.ndarray:
    """Compute pairwise risk influence matrix.

    Shows how risk in one region propagates to others.

    Parameters
    ----------
    model:
        The GeopolModel.
    lookback_steps:
        Steps to consider for propagation.

    Returns
    -------
    np.ndarray
        Matrix where entry [i,j] shows risk influence of j on i.
    """
    region_ids = sorted(
        [getattr(a, "region_id", "") for a in model.schedule.agents if hasattr(a, "region_id")]
    )
    n = len(region_ids)
    matrix = np.zeros((n, n))

    for i, target_id in enumerate(region_ids):
        for j, source_id in enumerate(region_ids):
            if i == j:
                continue

            # Risk propagation based on adjacency and relations
            source_threat = compute_threat_score(model, source_id, lookback_steps)

            # Propagation factor based on proximity
            propagation = 0.5  # default
            if model.relations:
                rel = model.relations.get_relation(
                    next(a.unique_id for a in model.schedule.agents if a.region_id == target_id),
                    next(a.unique_id for a in model.schedule.agents if a.region_id == source_id),
                )
                if rel is not None:
                    propagation = min(1.0, abs(rel))

            matrix[i, j] = source_threat * propagation

    return matrix
