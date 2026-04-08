"""Leverage power analysis for geopolitical agents.

Computes different types of leverage power each agent has in the dynamic:
- Military leverage (hard power projection)
- Economic leverage (trade dependencies)
- Diplomatic leverage (alliance networks)
- Information leverage (OSINT/tension)
- Geographic leverage (position, adjacency)
- Temporal leverage (escalation level, timing)

Usage::

    from strategify.analysis.leverage import LeverageAnalyzer

    analyzer = LeverageAnalyzer(model)
    leverage_scores = analyzer.compute_all_leverage(region_id)

    # Get breakdown by type
    military = leverage_scores["military"]
    economic = leverage_scores["economic"]
    diplomatic = leverage_scores["diplomatic"]

    # Compare two agents
    comparison = analyzer.compare_agents(agent_a_id, agent_b_id)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class LeverageType(Enum):
    """Types of leverage power in geopolitical dynamics."""

    MILITARY = "military"
    ECONOMIC = "economic"
    DIPLOMATIC = "diplomatic"
    INFORMATION = "information"
    GEOGRAPHIC = "geographic"
    TEMPORAL = "temporal"


@dataclass
class LeverageScore:
    """Quantitative leverage score for a single type."""

    leverage_type: LeverageType
    raw_score: float  # Absolute score
    normalized_score: float  # 0-1 relative to all agents
    components: dict[str, float]  # Breakdown of contributing factors
    description: str


@dataclass
class AgentLeverage:
    """Complete leverage profile for an agent."""

    region_id: str
    agent_id: int
    overall_score: float  # Weighted average
    by_type: dict[LeverageType, LeverageScore]
    timestamp: int | None = None

    def __getitem__(self, key: str) -> LeverageScore:
        """Allow dict-style access by string key (e.g., leverage["military"])."""
        key_lower = key.lower()
        for lt in LeverageType:
            if lt.value == key_lower or lt.name == key_lower.upper():
                return self.by_type[lt]
        raise KeyError(f"No leverage type found for key: {key}")

    def __contains__(self, key: str) -> bool:
        """Check if leverage type exists."""
        key_lower = key.lower()
        return any(lt.value == key_lower or lt.name == key_lower.upper() for lt in LeverageType)

    def get(self, key: str, default: float = 0.0) -> float:
        """Get raw score by string key, with default."""
        try:
            return self[key].raw_score
        except KeyError:
            return default


class LeverageAnalyzer:
    """Analyze leverage power types for all agents in the model.

    Computes military, economic, diplomatic, information, geographic,
    and temporal leverage for each agent and provides comparison tools.
    """

    # Default weights for overall leverage calculation
    DEFAULT_WEIGHTS = {
        LeverageType.MILITARY: 0.30,
        LeverageType.ECONOMIC: 0.25,
        LeverageType.DIPLOMATIC: 0.20,
        LeverageType.INFORMATION: 0.10,
        LeverageType.GEOGRAPHIC: 0.10,
        LeverageType.TEMPORAL: 0.05,
    }

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        self._cache: dict[int, AgentLeverage] = {}
        self._weights = self.DEFAULT_WEIGHTS.copy()

    def set_weights(self, weights: dict[LeverageType, float]) -> None:
        """Set custom weights for overall leverage calculation."""
        total = sum(weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError("Weights must sum to 1.0")
        self._weights = weights

    def compute_all_leverage(self, region_id: str) -> AgentLeverage:
        """Compute all leverage types for an agent.

        Parameters
        ----------
        region_id:
            The region ID to analyze.

        Returns
        -------
        AgentLeverage
            Complete leverage profile.
        """
        agent = self._get_agent(region_id)
        if agent is None:
            raise ValueError(f"No agent found for region {region_id}")

        by_type: dict[LeverageType, LeverageScore] = {}

        by_type[LeverageType.MILITARY] = self._compute_military_leverage(agent)
        by_type[LeverageType.ECONOMIC] = self._compute_economic_leverage(agent)
        by_type[LeverageType.DIPLOMATIC] = self._compute_diplomatic_leverage(agent)
        by_type[LeverageType.INFORMATION] = self._compute_information_leverage(agent)
        by_type[LeverageType.GEOGRAPHIC] = self._compute_geographic_leverage(agent)
        by_type[LeverageType.TEMPORAL] = self._compute_temporal_leverage(agent)

        overall = self._compute_overall_score(by_type)

        timestamp = getattr(self.model, "steps", None)

        return AgentLeverage(
            region_id=region_id,
            agent_id=agent.unique_id,
            overall_score=overall,
            by_type=by_type,
            timestamp=timestamp,
        )

    def _get_agent(self, region_id: str):
        """Get agent by region_id."""
        for agent in self.model.schedule.agents:
            if getattr(agent, "region_id", None) == region_id:
                return agent
        return None

    def _compute_military_leverage(self, agent) -> LeverageScore:
        """Compute military leverage based on capabilities and units."""
        caps = getattr(agent, "capabilities", {})
        military_cap = caps.get("military", 0.5)

        military_component = getattr(agent, "military", None)
        if military_component and hasattr(military_component, "get_total_power"):
            unit_power = military_component.get_total_power()
        else:
            unit_power = military_cap * 10

        raw_score = military_cap * 0.7 + min(unit_power / 20.0, 1.0) * 0.3

        return LeverageScore(
            leverage_type=LeverageType.MILITARY,
            raw_score=raw_score,
            normalized_score=0.0,
            components={
                "military_capability": military_cap,
                "unit_power": unit_power / 20.0,
            },
            description="Military power projection capability",
        )

    def _compute_economic_leverage(self, agent) -> LeverageScore:
        """Compute economic leverage based on resources and trade position."""
        caps = getattr(agent, "capabilities", {})
        economic_cap = caps.get("economic", 0.5)

        resources = getattr(self.model, "region_resources", {})
        region_res = resources.get(getattr(agent, "region_id", ""), 1.0)

        trade_balance = 0.0
        if hasattr(self.model, "trade_network") and self.model.trade_network:
            trade_info = self.model.trade_network.get_economic_features(agent.unique_id)
            trade_balance = trade_info.get("trade_balance", 0.0)

        raw_score = economic_cap * 0.6 + region_res * 0.2 + (trade_balance + 1) * 0.2

        return LeverageScore(
            leverage_type=LeverageType.ECONOMIC,
            raw_score=raw_score,
            normalized_score=0.0,
            components={
                "economic_capability": economic_cap,
                "gdp_factor": region_res,
                "trade_balance": trade_balance,
            },
            description="Economic influence through resources and trade",
        )

    def _compute_diplomatic_leverage(self, agent) -> LeverageScore:
        """Compute diplomatic leverage based on alliance network."""
        relations = getattr(self.model, "relations", None)

        if relations is None:
            raw_score = 0.3
            ally_count = 0
            rival_count = 0
        else:
            allies = relations.get_allies(agent.unique_id)
            rivals = relations.get_rivals(agent.unique_id)

            ally_count = len(allies)
            rival_count = len(rivals)

            raw_score = min(ally_count / 5.0, 1.0) * 0.5 + min(rival_count / 5.0, 1.0) * 0.5

        return LeverageScore(
            leverage_type=LeverageType.DIPLOMATIC,
            raw_score=raw_score,
            normalized_score=0.0,
            components={
                "ally_count": ally_count,
                "rival_count": rival_count,
            },
            description="Diplomatic influence through alliances and rivalries",
        )

    def _compute_information_leverage(self, agent) -> LeverageScore:
        """Compute information leverage based on OSINT/tension scores."""
        osint_features = getattr(self.model, "osint_features", {})
        region_osint = osint_features.get(getattr(agent, "region_id", ""), {})

        tension_score = region_osint.get("tension_score", 0.5)
        event_count = region_osint.get("event_count", 0)

        raw_score = tension_score * 0.7 + min(event_count / 100.0, 1.0) * 0.3

        return LeverageScore(
            leverage_type=LeverageType.INFORMATION,
            raw_score=raw_score,
            normalized_score=0.0,
            components={
                "tension_score": tension_score,
                "event_count": event_count,
            },
            description="Information advantage through OSINT and awareness",
        )

    def _compute_geographic_leverage(self, agent) -> LeverageScore:
        """Compute geographic leverage based on position and adjacency."""
        imap = getattr(self.model, "influence_map", None)

        region_id = getattr(agent, "region_id", "")

        if imap is None or not hasattr(imap, "influence_data"):
            raw_score = 0.3
            total_influence = 0
            adjacency_count = 0
        else:
            region_influence = imap.influence_data.get(region_id, {})
            total_influence = sum(region_influence.values())

            adjacency_count = len(region_influence)

            raw_score = (
                min(total_influence / 5.0, 1.0) * 0.5 + min(adjacency_count / 10.0, 1.0) * 0.5
            )

        return LeverageScore(
            leverage_type=LeverageType.GEOGRAPHIC,
            raw_score=raw_score,
            normalized_score=0.0,
            components={
                "total_influence": total_influence,
                "adjacency_count": adjacency_count,
            },
            description="Geographic position and influence network",
        )

    def _compute_temporal_leverage(self, agent) -> LeverageScore:
        """Compute temporal leverage based on escalation level and timing."""
        ladder = getattr(self.model, "escalation_ladder", None)

        if ladder is None:
            raw_score = 0.3
        else:
            level = ladder.get_level(agent.unique_id)
            raw_score = min(int(level) / 3.0, 1.0)

        return LeverageScore(
            leverage_type=LeverageType.TEMPORAL,
            raw_score=raw_score,
            normalized_score=0.0,
            components={
                "escalation_level": int(level) if ladder else 0,
            },
            description="Temporal advantage through escalation commitment",
        )

    def _compute_overall_score(self, by_type: dict[LeverageType, LeverageScore]) -> float:
        """Compute weighted overall leverage score."""
        overall = 0.0
        for lt, score in by_type.items():
            weight = self._weights.get(lt, 0.0)
            overall += score.raw_score * weight
        return overall

    def normalize_scores(self, leverage_profiles: list[AgentLeverage]) -> None:
        """Normalize scores across all agents to 0-1 range."""
        if not leverage_profiles:
            return

        for lt in LeverageType:
            scores = [lp.by_type[lt].raw_score for lp in leverage_profiles]
            min_s, max_s = min(scores), max(scores)
            range_s = max_s - min_s

            if range_s < 1e-6:
                continue

            for lp in leverage_profiles:
                lp.by_type[lt].normalized_score = (lp.by_type[lt].raw_score - min_s) / range_s

    def compare_agents(self, region_id_a: str, region_id_b: str) -> dict[str, Any]:
        """Compare leverage between two agents.

        Returns a dict with:
        - agent_a: leverage profile
        - agent_b: leverage profile
        - advantage: which agent has overall advantage
        - by_type: advantage per leverage type
        """
        profile_a = self.compute_all_leverage(region_id_a)
        profile_b = self.compute_all_leverage(region_id_b)

        all_profiles = [profile_a, profile_b]
        self.normalize_scores(all_profiles)

        by_type = {}
        for lt in LeverageType:
            score_a = profile_a.by_type[lt].normalized_score
            score_b = profile_b.by_type[lt].normalized_score
            by_type[lt.value] = {
                "agent_a": score_a,
                "agent_b": score_b,
                "advantage": "a" if score_a > score_b else "b",
                "margin": abs(score_a - score_b),
            }

        return {
            "agent_a": profile_a,
            "agent_b": profile_b,
            "advantage": "a" if profile_a.overall_score > profile_b.overall_score else "b",
            "by_type": by_type,
        }

    def get_leaderboard(self) -> list[dict[str, Any]]:
        """Get leverage leaderboard across all agents."""
        profiles = []

        for agent in self.model.schedule.agents:
            region_id = getattr(agent, "region_id", None)
            if region_id is None:
                continue

            try:
                profile = self.compute_all_leverage(region_id)
                profiles.append(profile)
            except Exception:
                continue

        self.normalize_scores(profiles)

        profiles.sort(key=lambda p: p.overall_score, reverse=True)

        return [
            {
                "region_id": p.region_id,
                "agent_id": p.agent_id,
                "overall_score": p.overall_score,
                "military": p.by_type[LeverageType.MILITARY].normalized_score,
                "economic": p.by_type[LeverageType.ECONOMIC].normalized_score,
                "diplomatic": p.by_type[LeverageType.DIPLOMATIC].normalized_score,
                "information": p.by_type[LeverageType.INFORMATION].normalized_score,
                "geographic": p.by_type[LeverageType.GEOGRAPHIC].normalized_score,
                "temporal": p.by_type[LeverageType.TEMPORAL].normalized_score,
            }
            for p in profiles
        ]

    def get_dominant_leverage_type(self, region_id: str) -> LeverageType:
        """Get the dominant leverage type for an agent."""
        profile = self.compute_all_leverage(region_id)

        max_type = None
        max_score = -1.0

        for lt, score in profile.by_type.items():
            if score.normalized_score > max_score:
                max_score = score.normalized_score
                max_type = lt

        return max_type or LeverageType.MILITARY


def compute_leverage(model: GeopolModel, region_id: str) -> AgentLeverage:
    """Convenience function to compute leverage for a region."""
    analyzer = LeverageAnalyzer(model)
    return analyzer.compute_all_leverage(region_id)


class LeverageHistory:
    """Tracks leverage over simulation time steps.

    Records leverage snapshots at each step and provides
    trend analysis and time-series extraction.
    """

    def __init__(self) -> None:
        self._snapshots: list[dict[str, AgentLeverage]] = []

    def record(self, step: int, profiles: dict[str, AgentLeverage]) -> None:
        """Record leverage profiles for all agents at a given step.

        Parameters
        ----------
        step:
            The simulation step number.
        profiles:
            Dict mapping region_id to AgentLeverage.
        """
        self._snapshots.append({"step": step, "profiles": profiles.copy()})

    def get_snapshot(self, step: int) -> dict[str, AgentLeverage] | None:
        """Get leverage profiles for a specific step."""
        for snap in self._snapshots:
            if snap["step"] == step:
                return snap["profiles"]
        return None

    def get_history(self, region_id: str) -> list[tuple[int, float]]:
        """Get time series of overall leverage for a region.

        Returns list of (step, overall_score) tuples.
        """
        history = []
        for snap in self._snapshots:
            profile = snap["profiles"].get(region_id)
            if profile:
                history.append((snap["step"], profile.overall_score))
        return history

    def get_type_history(
        self, region_id: str, leverage_type: LeverageType
    ) -> list[tuple[int, float]]:
        """Get time series for a specific leverage type."""
        history = []
        for snap in self._snapshots:
            profile = snap["profiles"].get(region_id)
            if profile and leverage_type in profile.by_type:
                history.append((snap["step"], profile.by_type[leverage_type].raw_score))
        return history

    def compute_trend(self, region_id: str) -> dict[LeverageType, str]:
        """Compute trend direction for each leverage type.

        Returns dict mapping leverage type to trend: "rising", "falling", "stable"
        """
        trends = {}
        for lt in LeverageType:
            history = self.get_type_history(region_id, lt)
            if len(history) < 2:
                trends[lt] = "stable"
                continue

            recent = [h[1] for h in history[-3:]]
            if all(recent[i] < recent[i + 1] for i in range(len(recent) - 1)):
                trends[lt] = "rising"
            elif all(recent[i] > recent[i + 1] for i in range(len(recent) - 1)):
                trends[lt] = "falling"
            else:
                trends[lt] = "stable"

        return trends

    def get_all_regions(self) -> list[str]:
        """Get list of all regions that have been tracked."""
        regions = set()
        for snap in self._snapshots:
            regions.update(snap["profiles"].keys())
        return sorted(regions)

    @property
    def steps(self) -> list[int]:
        """Get list of recorded steps."""
        return [snap["step"] for snap in self._snapshots]


def track_leverage(
    model: GeopolModel,
    history: LeverageHistory | None = None,
) -> LeverageHistory:
    """Track leverage for all agents in the model.

    Convenience function to record current leverage state.

    Parameters
    ----------
    model:
        The geopolitical model.
    history:
        Existing LeverageHistory to append to, or None to create new.

    Returns
    -------
    LeverageHistory
        The history object with current step recorded.
    """
    if history is None:
        history = LeverageHistory()

    analyzer = LeverageAnalyzer(model)
    lb = analyzer.get_leaderboard()

    profiles = {}
    for entry in lb:
        try:
            profile = analyzer.compute_all_leverage(entry["region_id"])
            profiles[entry["region_id"]] = profile
        except Exception:
            continue

    step = getattr(model, "steps", 0)
    history.record(step, profiles)

    return history


class LeverageAlertLevel:
    """Leverage alert severity levels."""

    NONE = "none"
    SHIFTING = "shifting"  # Leverage types changing
    UNSTABLE = "unstable"  # Rapid changes
    CRITICAL = "critical"  # Major leverage shift


def detect_leverage_anomalies(
    history: LeverageHistory,
    region_id: str,
    threshold: float = 0.2,
) -> list[dict[str, Any]]:
    """Detect anomalous leverage changes.

    Identifies sudden shifts in leverage power that may indicate
    strategic turning points.

    Parameters
    ----------
    history:
        Leverage history with temporal data.
    region_id:
        Region to analyze.
    threshold:
        Minimum change magnitude to flag as anomaly.

    Returns
    -------
    list[dict]
        Anomalies with step, leverage_type, change, direction.
    """
    anomalies = []

    for lt in LeverageType:
        history_data = history.get_type_history(region_id, lt)
        if len(history_data) < 3:
            continue

        for i in range(1, len(history_data)):
            step, prev = history_data[i - 1]
            step, curr = history_data[i]
            change = curr - prev

            if abs(change) >= threshold:
                anomalies.append(
                    {
                        "step": step,
                        "leverage_type": lt.value,
                        "change": change,
                        "direction": "rising" if change > 0 else "falling",
                        "magnitude": abs(change),
                        "level": (
                            LeverageAlertLevel.CRITICAL
                            if abs(change) >= 0.3
                            else LeverageAlertLevel.UNSTABLE
                        ),
                    }
                )

    anomalies.sort(key=lambda a: a["step"], reverse=True)
    return anomalies


def detect_leverage_shift(
    history: LeverageHistory,
    region_id: str,
    window: int = 5,
) -> dict[str, Any]:
    """Detect when dominant leverage type changes.

    Identifies strategic pivot points where a different type
    of leverage becomes dominant.

    Parameters
    ----------
    history:
        Leverage history.
    region_id:
        Region to analyze.
    window:
        Number of recent steps to compare.

    Returns
    -------
    dict
        Current dominant type, previous dominant type, shift detected.
    """
    type_histories = {}
    for lt in LeverageType:
        type_histories[lt] = history.get_type_history(region_id, lt)

    def get_dominant_type(
        histories: dict[LeverageType, list[tuple[int, float]]],
    ) -> LeverageType | None:
        if not histories:
            return None
        avg_scores = {}
        for lt, hist in histories.items():
            if hist:
                recent = [h[1] for h in hist[-window:]]
                avg_scores[lt] = sum(recent) / len(recent)
        if not avg_scores:
            return None
        return max(avg_scores.keys(), key=lambda k: avg_scores[k])

    current = get_dominant_type(type_histories)

    all_steps = sorted(set(s for h in type_histories.values() for s, _ in h))
    if len(all_steps) < window * 2:
        return {
            "current_dominant": current.value if current else None,
            "previous_dominant": None,
            "shift_detected": False,
            "step": None,
        }

    recent_window = all_steps[-window:]
    older_window = all_steps[-window * 2 : -window]

    recent_histories = {}
    older_histories = {}
    for lt, hist in type_histories.items():
        recent_histories[lt] = [(s, v) for s, v in hist if s in recent_window]
        older_histories[lt] = [(s, v) for s, v in hist if s in older_window]

    previous = get_dominant_type(older_histories)

    return {
        "current_dominant": current.value if current else None,
        "previous_dominant": previous.value if previous else None,
        "shift_detected": current != previous and current is not None,
        "step": recent_window[-1] if recent_window else None,
    }


def compute_leverage_volatility(
    history: LeverageHistory,
    region_id: str,
) -> dict[str, float]:
    """Compute volatility (standard deviation) for each leverage type.

    Higher volatility indicates less predictable leverage position.

    Returns
    -------
    dict
        Volatility score per leverage type.
    """
    volatilities = {}

    for lt in LeverageType:
        hist = history.get_type_history(region_id, lt)
        if len(hist) < 2:
            volatilities[lt.value] = 0.0
            continue

        values = [h[1] for h in hist]
        volatilities[lt.value] = float(np.std(values))

    return volatilities


def detect_leverage_regime_change(
    history: LeverageHistory,
    region_id: str,
    volatility_threshold: float = 0.15,
) -> dict[str, Any]:
    """Detect regime changes in leverage structure.

    A regime change occurs when the overall leverage composition
    shifts significantly, indicating strategic reorientation.

    Returns
    -------
    dict
        Regime change detected, step, previous regime, current regime.
    """
    if len(history.steps) < 5:
        return {
            "regime_change_detected": False,
            "step": None,
            "previous_regime": None,
            "current_regime": None,
        }

    first_half_steps = history.steps[: len(history.steps) // 2]
    second_half_steps = history.steps[len(history.steps) // 2 :]

    def get_regime_snapshot(steps: list[int]) -> dict[LeverageType, float]:
        regime = {}
        for lt in LeverageType:
            hist = history.get_type_history(region_id, lt)
            relevant = [v for s, v in hist if s in steps]
            if relevant:
                regime[lt] = sum(relevant) / len(relevant)
            else:
                regime[lt] = 0.0
        return regime

    previous_regime = get_regime_snapshot(first_half_steps)
    current_regime = get_regime_snapshot(second_half_steps)

    total_change = sum(
        abs(current_regime.get(lt, 0) - previous_regime.get(lt, 0)) for lt in LeverageType
    )

    return {
        "regime_change_detected": total_change >= volatility_threshold,
        "step": second_half_steps[-1] if second_half_steps else None,
        "previous_regime": previous_regime,
        "current_regime": current_regime,
        "total_change": total_change,
    }


def sensitivity_analysis(
    model: GeopolModel,
    region_id: str,
    n_iterations: int = 100,
) -> dict[str, Any]:
    """Perform sensitivity analysis on leverage weights.

    Tests how sensitive leverage scores are to different weight
    configurations using Monte Carlo sampling.

    Parameters
    ----------
    model:
        The geopolitical model.
    region_id:
        Region to analyze.
    n_iterations:
        Number of random weight configurations to test.

    Returns
    -------
    dict
        Sensitivity results with importance rankings.
    """
    import random

    base_analyzer = LeverageAnalyzer(model)
    base_profile = base_analyzer.compute_all_leverage(region_id)
    base_scores = {lt: base_profile.by_type[lt].raw_score for lt in LeverageType}

    weight_perturbations: dict[LeverageType, list[float]] = {lt: [] for lt in LeverageType}

    for _ in range(n_iterations):
        weights = {}
        remaining = 1.0
        for i, lt in enumerate(LeverageType):
            if i == len(LeverageType) - 1:
                weights[lt] = remaining
            else:
                max_w = remaining
                w = random.uniform(0, max_w)
                weights[lt] = w
                remaining -= w

        test_analyzer = LeverageAnalyzer(model)
        test_analyzer.set_weights(weights)
        test_profile = test_analyzer.compute_all_leverage(region_id)

        for lt in LeverageType:
            perturbation = test_profile.by_type[lt].raw_score - base_scores[lt]
            weight_perturbations[lt].append(perturbation)

    importance = {}
    for lt in LeverageType:
        perturbations = weight_perturbations[lt]
        if perturbations:
            importance[lt.value] = {
                "mean_impact": float(np.mean(perturbations)),
                "std_impact": float(np.std(perturbations)),
                "max_impact": float(np.max(perturbations)),
                "min_impact": float(np.min(perturbations)),
            }
        else:
            importance[lt.value] = {
                "mean_impact": 0.0,
                "std_impact": 0.0,
                "max_impact": 0.0,
                "min_impact": 0.0,
            }

    ranking = sorted(
        importance.items(),
        key=lambda x: abs(x[1]["mean_impact"]),
        reverse=True,
    )

    return {
        "base_scores": base_scores,
        "importance": importance,
        "ranking": ranking,
        "n_iterations": n_iterations,
    }


def compare_leverage_types(
    history: LeverageHistory,
    region_id: str,
) -> dict[str, Any]:
    """Compare leverage types over time to identify relative strengths.

    Provides comparison metrics between leverage types showing which
    types dominate and their relative trajectories.

    Returns
    -------
    dict
        Comparison results with relative strengths and trajectories.
    """
    type_histories = {lt: history.get_type_history(region_id, lt) for lt in LeverageType}

    avg_scores = {}
    for lt, hist in type_histories.items():
        if hist:
            avg_scores[lt.value] = sum(h[1] for h in hist) / len(hist)
        else:
            avg_scores[lt.value] = 0.0

    sorted_types = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

    correlations = {}
    types_list = list(LeverageType)
    for i, lt1 in enumerate(types_list):
        hist1 = type_histories.get(lt1, [])
        if len(hist1) < 2:
            continue
        for lt2 in types_list[i + 1 :]:
            hist2 = type_histories.get(lt2, [])
            if len(hist2) < 2:
                continue

            steps1 = set(s for s, _ in hist1)
            steps2 = set(s for s, _ in hist2)
            common_steps = steps1 & steps2

            if len(common_steps) >= 2:
                vals1 = [v for s, v in hist1 if s in common_steps]
                vals2 = [v for s, v in hist2 if s in common_steps]
                if len(vals1) >= 2:
                    corr = np.corrcoef(vals1, vals2)[0, 1]
                    if not np.isnan(corr):
                        correlations[f"{lt1.value}_vs_{lt2.value}"] = float(corr)

    return {
        "average_scores": avg_scores,
        "ranked_types": [t for t, _ in sorted_types],
        "dominant_type": sorted_types[0][0] if sorted_types else None,
        "correlations": correlations,
    }
