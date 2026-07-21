"""Operations research for military force optimization and conflict prediction.

This module provides optimization and prediction capabilities for military
force allocation and conflict analysis.

Classes:
- ForceAllocationOptimizer: Optimize unit distribution across theaters
- ConflictPredictor: Predict conflict likelihood based on force posture
- WarGamingEngine: Monte Carlo conflict simulations
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class AllocationScenario:
    """A force allocation scenario for optimization.

    Attributes
    ----------
    scenario_id : str
        Unique identifier.
    theates : dict[str, float]
        Map of region_id to force allocation.
    total_cost : float
        Total cost of this allocation.
    defense_score : float
        Defensive capability score.
    offense_score : float
        Offensive capability score.
    response_time : float
        Average response time to threats.
    """

    scenario_id: str
    theates: dict[str, float]
    total_cost: float
    defense_score: float
    offense_score: float
    response_time: float


class ForceAllocationOptimizer:
    """Optimize force distribution across theaters.

    Supports multi-objective optimization for defense vs. offense tradeoffs.
    """

    def __init__(self, num_theaters: int = 5) -> None:
        self.num_theaters = num_theaters
        self.budget: float = 100.0
        self.cost_per_unit: float = 10.0
        self.defense_weight: float = 0.5
        self.offense_weight: float = 0.5

    def optimize(
        self,
        threat_levels: dict[str, float],
        target_regions: list[str],
        max_iterations: int = 100,
    ) -> list[AllocationScenario]:
        """Generate optimized allocation scenarios.

        Parameters
        ----------
        threat_levels : dict[str, float]
            Threat level per region [0.0, 1.0].
        target_regions : list[str]
            Regions to allocate forces to.
        max_iterations : int
            Maximum optimization iterations.

        Returns
        -------
        list[AllocationScenario]
            Pareto-optimal allocation scenarios.
        """
        scenarios: list[AllocationScenario] = []

        base_allocation = self.budget / len(target_regions)

        for _i in range(max_iterations):
            allocation = {}
            remaining_budget = self.budget

            sorted_regions = sorted(
                target_regions,
                key=lambda r: threat_levels.get(r, 0.0),
                reverse=True,
            )

            for region in sorted_regions[:-1]:
                threat_weight = threat_levels.get(region, 0.5)
                allocated = base_allocation * (1.0 + threat_weight)
                allocated = min(allocated, remaining_budget * 0.4)
                allocation[region] = allocated
                remaining_budget -= allocated

            if target_regions:
                allocation[target_regions[-1]] = remaining_budget

            scenario = self._evaluate_allocation(allocation, threat_levels)
            scenarios.append(scenario)

        return self._filter_pareto_optimal(scenarios)

    def _evaluate_allocation(
        self,
        allocation: dict[str, float],
        threat_levels: dict[str, float],
    ) -> AllocationScenario:
        """Evaluate an allocation scenario."""
        total_cost = sum(allocation.values())

        defense_score = 0.0
        offense_score = 0.0
        response_time = 0.0

        for region, force in allocation.items():
            threat = threat_levels.get(region, 0.5)
            defense_score += force * (1.0 - threat)
            offense_score += force * threat

            if threat > 0.3:
                response_time += force / max(threat, 0.1)

        num_regions = len(allocation) or 1
        response_time /= num_regions
        response_time = min(response_time, 24.0)

        return AllocationScenario(
            scenario_id=f"alloc_{random.randint(1000, 9999)}",
            theates=allocation,
            total_cost=total_cost,
            defense_score=defense_score,
            offense_score=offense_score,
            response_time=response_time,
        )

    def _filter_pareto_optimal(
        self,
        scenarios: list[AllocationScenario],
    ) -> list[AllocationScenario]:
        """Filter to Pareto-optimal scenarios."""
        if not scenarios:
            return []

        pareto: list[AllocationScenario] = []

        for scenario in scenarios:
            is_dominated = False

            for other in scenarios:
                if other is scenario:
                    continue

                if (
                    other.defense_score >= scenario.defense_score
                    and other.offense_score >= scenario.offense_score
                    and other.total_cost <= scenario.total_cost
                    and (
                        other.defense_score > scenario.defense_score
                        or other.offense_score > scenario.offense_score
                        or other.total_cost < scenario.total_cost
                    )
                ):
                    is_dominated = True
                    break

            if not is_dominated:
                pareto.append(scenario)

        return pareto[:10]

    def set_weights(self, defense: float, offense: float) -> None:
        """Set defense/offense optimization weights."""
        total = defense + offense
        self.defense_weight = defense / total
        self.offense_weight = offense / total


class ConflictPredictor:
    """Predict conflict likelihood based on force posture and indicators."""

    def __init__(self) -> None:
        self.base_escalation_threshold: float = 0.6
        self.military_pressure_weight: float = 0.4
        self.economic_pressure_weight: float = 0.2
        self.diplomatic_pressure_weight: float = 0.2
        self.historical_aggression_weight: float = 0.2

    def predict(
        self,
        attacker_power: float,
        defender_power: float,
        attacker_posture: str,
        defender_posture: str,
        relation_score: float,
        historical_escalations: int = 0,
        economic_pressure: float = 0.0,
        diplomatic_isolation: float = 0.0,
    ) -> dict[str, Any]:
        """Predict conflict likelihood and outcomes.

        Parameters
        ----------
        attacker_power : float
            Attacker's military power score.
        defender_power : float
            Defender's military power score.
        attacker_posture : str
            Attacker's current posture.
        defender_posture : str
            Defender's current posture.
        relation_score : float
            Relationship score [-1.0, 1.0].
        historical_escalations : int
            Number of historical escalations.
        economic_pressure : float
            Economic pressure on attacker [0.0, 1.0].
        diplomatic_isolation : float
            Diplomatic isolation of attacker [0.0, 1.0].

        Returns
        -------
        dict
            Prediction with likelihood, attrition, and escalation pathway.
        """
        power_ratio = attacker_power / max(defender_power, 0.1)

        posture_aggression = self._calculate_posture_aggression(attacker_posture, defender_posture)

        pressure_score = (
            self.military_pressure_weight * power_ratio
            + self.economic_pressure_weight * economic_pressure
            + self.diplomatic_pressure_weight * diplomatic_isolation
        )

        historical_factor = min(1.0, historical_escalations / 5.0)

        relation_factor = max(0.0, (1.0 - relation_score) / 2.0)

        likelihood = posture_aggression * 0.3 + pressure_score * 0.3 + historical_factor * 0.2 + relation_factor * 0.2

        likelihood = min(1.0, max(0.0, likelihood))

        attrition = self._calculate_attrition(attacker_power, defender_power)

        escalation_pathway = self._generate_escalation_pathway(likelihood, posture_aggression, relation_score)

        return {
            "likelihood": likelihood,
            "power_ratio": power_ratio,
            "attrition": attrition,
            "escalation_pathway": escalation_pathway,
            "recommended_response": self._recommend_response(likelihood),
        }

    def _calculate_posture_aggression(self, attacker: str, defender: str) -> float:
        """Calculate aggression score from postures."""
        aggression_scores = {
            "Escalate": 0.8,
            "Invade": 1.0,
            "Deploy": 0.6,
            "Patrol": 0.2,
            "Deescalate": 0.0,
            "Withdraw": 0.1,
        }

        attacker_agg = aggression_scores.get(attacker, 0.3)
        defender_agg = aggression_scores.get(defender, 0.3)

        return (attacker_agg + (1.0 - defender_agg)) / 2.0

    def _calculate_attrition(self, attacker_power: float, defender_power: float) -> dict[str, float]:
        """Calculate estimated attrition rates."""
        total_power = attacker_power + defender_power
        if total_power == 0:
            return {"attacker": 0.0, "defender": 0.0}

        attacker_share = attacker_power / total_power
        defender_share = defender_power / total_power

        intensity = min(1.0, total_power / 20.0)

        attacker_attrition = (defender_share * 0.5 + 0.1) * intensity
        defender_attrition = (attacker_share * 0.5 + 0.1) * intensity

        return {
            "attacker": min(0.8, attacker_attrition),
            "defender": min(0.8, defender_attrition),
        }

    def _generate_escalation_pathway(
        self,
        likelihood: float,
        aggression: float,
        relation: float,
    ) -> list[str]:
        """Generate likely escalation pathway."""
        pathway = []

        if likelihood > 0.7:
            pathway.append("Cyber operations")
            pathway.append("Economic sanctions")
            if aggression > 0.6:
                pathway.append("Military mobilization")
                pathway.append("Limited strike")
                pathway.append("Full-scale invasion")
        elif likelihood > 0.4:
            pathway.append("Diplomatic pressure")
            pathway.append("Economic coercion")
            pathway.append("Military posturing")

        return pathway

    def _recommend_response(self, likelihood: float) -> str:
        """Recommend a response strategy."""
        if likelihood < 0.2:
            return "Maintain current posture"
        elif likelihood < 0.4:
            return "Increase diplomatic engagement"
        elif likelihood < 0.6:
            return "Enhance defensive capabilities"
        elif likelihood < 0.8:
            return "Mobilize reserves"
        else:
            return "Pre-emptive strike consideration"


class WarGamingEngine:
    """Run Monte Carlo conflict simulations and analyze campaign outcomes."""

    def __init__(self, num_simulations: int = 100) -> None:
        self.num_simulations = num_simulations
        self.random_seed: int | None = None

    def simulate_campaign(
        self,
        attacker_power: float,
        defender_power: float,
        terrain_factor: float = 0.5,
        weather_factor: float = 0.5,
    ) -> dict[str, Any]:
        """Run Monte Carlo campaign simulation.

        Parameters
        ----------
        attacker_power : float
            Attacker's military power.
        defender_power : float
            Defender's military power.
        terrain_factor : float
            Terrain advantage [0.0, 1.0].
        weather_factor : float
            Weather impact [0.0, 1.0].

        Returns
        -------
        dict
            Simulation results with outcomes and statistics.
        """
        if self.random_seed:
            random.seed(self.random_seed)

        outcomes: list[str] = []
        attacker_losses: list[float] = []
        defender_losses: list[float] = []
        durations: list[int] = []

        for _ in range(self.num_simulations):
            outcome, att_loss, def_loss, duration = self._single_simulation(
                attacker_power, defender_power, terrain_factor, weather_factor
            )
            outcomes.append(outcome)
            attacker_losses.append(att_loss)
            defender_losses.append(def_loss)
            durations.append(duration)

        attacker_win_rate = outcomes.count("attacker_win") / self.num_simulations
        defender_win_rate = outcomes.count("defender_win") / self.num_simulations
        stalemate_rate = outcomes.count("stalemate") / self.num_simulations

        return {
            "attacker_win_rate": attacker_win_rate,
            "defender_win_rate": defender_win_rate,
            "stalemate_rate": stalemate_rate,
            "expected_attacker_loss": np.mean(attacker_losses),
            "expected_defender_loss": np.mean(defender_losses),
            "expected_duration": int(np.mean(durations)),
            "duration_variance": np.var(durations),
        }

    def _single_simulation(
        self,
        attacker_power: float,
        defender_power: float,
        terrain: float,
        weather: float,
    ) -> tuple[str, float, float, int]:
        """Run a single simulation."""
        effective_attacker = attacker_power * (1.0 - terrain * 0.3) * (1.0 - weather * 0.2)
        effective_defender = defender_power * (1.0 + terrain * 0.2)

        combat_factor = random.uniform(0.8, 1.2)

        attacker_score = effective_attacker * combat_factor * random.uniform(0.7, 1.3)
        defender_score = effective_defender * combat_factor * random.uniform(0.7, 1.3)

        margin = abs(attacker_score - defender_score)

        if margin < 2.0:
            outcome = "stalemate"
        elif attacker_score > defender_score:
            outcome = "attacker_win"
        else:
            outcome = "defender_win"

        attacker_loss = max(0.0, 1.0 - attacker_score / max(attacker_power, 0.1))
        defender_loss = max(0.0, 1.0 - defender_score / max(defender_power, 0.1))

        duration = int(margin * 5) + random.randint(1, 10)
        duration = min(duration, 100)

        return outcome, attacker_loss, defender_loss, duration

    def generate_recommendations(
        self,
        simulation_results: dict[str, Any],
        current_power: float,
        target_power: float,
    ) -> list[str]:
        """Generate strategic recommendations based on simulation.

        Parameters
        ----------
        simulation_results : dict
            Results from simulate_campaign.
        current_power : float
            Current military power.
        target_power : float
            Target's military power.

        Returns
        -------
        list[str]
            Strategic recommendations.
        """
        recommendations = []

        if simulation_results["attacker_win_rate"] > 0.7:
            recommendations.append("Favorable conditions for offensive operations")
            recommendations.append("Consider pre-emptive action")
        elif simulation_results["attacker_win_rate"] < 0.3:
            recommendations.append("Defensive posture recommended")
            recommendations.append("Seek allied support")

        if simulation_results["expected_attacker_loss"] > 0.5:
            recommendations.append("High attrition expected - consider attrition mitigation")

        if simulation_results["expected_duration"] > 30:
            recommendations.append("Prolonged conflict likely - prepare sustained operations")

        power_ratio = current_power / max(target_power, 0.1)
        if power_ratio < 0.5:
            recommendations.append("Significant power asymmetry - seek coalition")

        return recommendations
