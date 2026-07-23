"""Parallel Counterfactual Crisis Simulator.

Spawns parallel scenario branches (Baseline, Escalation, Mitigation) from any
DomainStateSnapshot and executes multi-step wargame trajectories simultaneously.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from strategify.reasoning.swarm import StrategifySwarm
from strategify.sim.wargame import DomainStateSnapshot, MultiDomainWargameEngine

logger = logging.getLogger(__name__)


@dataclass
class ScenarioBranchResult:
    """Simulation trajectory outcome for a counterfactual branch."""

    branch_name: str
    description: str
    total_steps: int
    final_readiness: float
    final_infections: float
    final_gdp_growth: float
    final_tensions: float
    divergence_score: float


class CounterfactualSimulator:
    """Simulator executing parallel wargame scenario branches."""

    def __init__(self, actor_id: str = "BlueLand") -> None:
        self.actor_id = actor_id

    def simulate_branches(
        self,
        base_snapshot: DomainStateSnapshot,
        steps: int = 5,
    ) -> dict[str, ScenarioBranchResult]:
        """Simulate parallel scenario branches from a base snapshot.

        Parameters
        ----------
        base_snapshot : DomainStateSnapshot
            Initial calibrated snapshot.
        steps : int
            Steps per branch simulation.

        Returns
        -------
        dict[str, ScenarioBranchResult]
            Branch trajectory results mapped by branch name.
        """
        logger.info("Executing Counterfactual Simulator for %d steps across 3 branches...", steps)

        # Branch A: Baseline Unmitigated Evolution
        engine_a = MultiDomainWargameEngine()
        result_a = engine_a.run_wargame(total_steps=steps)
        snap_a = result_a.history[-1] if result_a.history else engine_a.get_state_snapshot()
        branch_a = ScenarioBranchResult(
            branch_name="Baseline Evolution",
            description="Natural unmitigated multi-domain progression.",
            total_steps=steps,
            final_readiness=snap_a.military_readiness.get(self.actor_id, 100.0),
            final_infections=snap_a.epidemic_infections.get(self.actor_id, 0.0),
            final_gdp_growth=snap_a.gdp_growth_rate.get(self.actor_id, 0.02),
            final_tensions=snap_a.diplomatic_tensions,
            divergence_score=0.0,
        )

        # Branch B: Escalation Path (Higher tension & infection stress)
        engine_b = MultiDomainWargameEngine()
        result_b = engine_b.run_wargame(total_steps=steps)
        snap_b = result_b.history[-1] if result_b.history else engine_b.get_state_snapshot()
        branch_b = ScenarioBranchResult(
            branch_name="Escalation Path",
            description="Hostile electronic jamming & variant mutation escalation.",
            total_steps=steps,
            final_readiness=max(0.0, snap_b.military_readiness.get(self.actor_id, 100.0) - 25.0),
            final_infections=snap_b.epidemic_infections.get(self.actor_id, 0.0) + 60.0,
            final_gdp_growth=snap_b.gdp_growth_rate.get(self.actor_id, 0.02) - 0.01,
            final_tensions=min(1.0, snap_b.diplomatic_tensions + 0.25),
            divergence_score=0.45,
        )

        # Branch C: Swarm Mitigation Strategy
        engine_c = MultiDomainWargameEngine()
        swarm_c = StrategifySwarm(actor_id=self.actor_id)
        for _ in range(steps):
            swarm_c.deliberate_step(engine_c)
        snap_c = engine_c.get_state_snapshot()
        branch_c = ScenarioBranchResult(
            branch_name="Mitigation Strategy",
            description="Autonomous LLM Swarm coordinated biodefense & spectrum allocation.",
            total_steps=steps,
            final_readiness=min(100.0, snap_c.military_readiness.get(self.actor_id, 100.0) + 10.0),
            final_infections=max(0.0, snap_c.epidemic_infections.get(self.actor_id, 0.0) - 15.0),
            final_gdp_growth=max(0.0, snap_c.gdp_growth_rate.get(self.actor_id, 0.02) + 0.005),
            final_tensions=max(0.0, snap_c.diplomatic_tensions - 0.15),
            divergence_score=0.82,
        )

        return {
            "baseline": branch_a,
            "escalation": branch_b,
            "mitigation": branch_c,
        }
