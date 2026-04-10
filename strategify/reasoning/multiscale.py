"""Multi-scale modeling: nested simulations at global, regional, and local scales.

Provides a framework for running simulations at different scales and
coupling them through cross-scale parameter passing.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class Scale:
    """Simulation scale levels."""

    GLOBAL = "global"
    REGIONAL = "regional"
    LOCAL = "local"


class MultiScaleModel:
    """Orchestrates simulations at multiple scales.

    Runs a global simulation (country-level) and can nest regional
    simulations (state/province-level) that inherit parameters from
    the global level and feed results back up.

    Parameters
    ----------
    global_model_factory:
        Callable returning a GeopolModel for the global scale.
    regional_model_factories:
        Dict mapping region_id -> model factory for regional simulations.
    """

    def __init__(
        self,
        global_model_factory: Callable[[], Any],
        regional_model_factories: dict[str, Callable[[], Any]] | None = None,
    ) -> None:
        self.global_model = global_model_factory()
        self.regional_models: dict[str, Any] = {}
        self.regional_factories = regional_model_factories or {}
        self._step_count: int = 0

        # Initialize regional models
        for region_id, factory in self.regional_factories.items():
            self.regional_models[region_id] = factory()

    def step(self, regional_steps: int = 3) -> None:
        """Advance all simulation scales by one global step.

        Parameters
        ----------
        regional_steps:
            Number of steps each regional model takes per global step.
        """
        self._step_count += 1

        # Step global model
        self.global_model.step()

        # Step regional models
        for region_id, regional_model in self.regional_models.items():
            # Pass global state down
            self._sync_global_to_regional(region_id, regional_model)

            for _ in range(regional_steps):
                regional_model.step()

            # Pass regional results up
            self._sync_regional_to_global(region_id, regional_model)

    def _sync_global_to_regional(self, region_id: str, regional_model: Any) -> None:
        """Pass global simulation state to a regional model.

        Transfers capabilities and alliance weights from the global
        agent corresponding to this region.
        """
        global_agent = None
        for agent in self.global_model.schedule.agents:
            if getattr(agent, "region_id", "") == region_id:
                global_agent = agent
                break

        if global_agent is None:
            return

        # Transfer capabilities to regional agents
        for reg_agent in regional_model.schedule.agents:
            if hasattr(reg_agent, "capabilities"):
                # Regional agents inherit a fraction of global capabilities
                reg_agent.capabilities["military"] = min(1.0, global_agent.capabilities.get("military", 0.5) * 0.8)
                reg_agent.capabilities["economic"] = min(1.0, global_agent.capabilities.get("economic", 0.5) * 0.8)

    def _sync_regional_to_global(self, region_id: str, regional_model: Any) -> None:
        """Pass regional simulation results back to the global model.

        Aggregates regional escalation state to influence the global
        agent's posture.
        """
        global_agent = None
        for agent in self.global_model.schedule.agents:
            if getattr(agent, "region_id", "") == region_id:
                global_agent = agent
                break

        if global_agent is None:
            return

        # Count regional escalation
        escalated = sum(1 for a in regional_model.schedule.agents if getattr(a, "posture", "Deescalate") == "Escalate")
        total = len(regional_model.schedule.agents)
        escalation_ratio = escalated / total if total > 0 else 0.0

        # Regional tension influences global posture
        if escalation_ratio > 0.6:
            global_agent.posture = "Escalate"
        elif escalation_ratio < 0.2:
            global_agent.posture = "Deescalate"

    def get_global_model(self) -> Any:
        """Return the global scale model."""
        return self.global_model

    def get_regional_model(self, region_id: str) -> Any | None:
        """Return a regional model by region ID."""
        return self.regional_models.get(region_id)

    def get_scale_summary(self) -> dict[str, Any]:
        """Return multi-scale simulation summary."""
        regional_summaries = {}
        for rid, model in self.regional_models.items():
            escalated = sum(1 for a in model.schedule.agents if getattr(a, "posture", "Deescalate") == "Escalate")
            regional_summaries[rid] = {
                "n_agents": len(model.schedule.agents),
                "escalated": escalated,
                "steps": model.schedule.steps if hasattr(model, "schedule") else 0,
            }

        return {
            "global_step": self._step_count,
            "global_agents": len(self.global_model.schedule.agents),
            "regional_models": regional_summaries,
        }
