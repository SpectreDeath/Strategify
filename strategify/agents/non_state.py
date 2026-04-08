"""Non-state actors: NGOs, insurgent groups, and transnational entities.

These agents do not own territory but operate within regions owned by
StateActorAgents, affecting their stability and resources.
"""

from __future__ import annotations

import logging
from typing import Any

from shapely.geometry import base as shp_base

from strategify.agents.base import BaseActorAgent

logger = logging.getLogger(__name__)


class NonStateActor(BaseActorAgent):
    """An agent that operates inside regions to subvert or support state actors.

    Attributes
    ----------
    actor_type : str
        Type of group (e.g. 'Insurgent', 'NGO', 'PMC').
    target_region : str
        The region_id where this agent is currently operating.
    influence : float
        Current local influence [0.0, 1.0].
    """

    def __init__(
        self,
        unique_id: int,
        model: Any,
        geometry: shp_base.BaseGeometry,
        crs: str,
        actor_type: str = "Insurgent",
    ) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.actor_type = actor_type
        self.target_region: str = "unknown"
        self.region_id: str = f"nsa_{actor_type}_{unique_id}"
        self.influence: float = 0.1
        self.posture: str = "Infiltrate"
        self.capabilities: dict = {"military": 0.1, "economic": 0.0}

    def decide(self) -> dict:
        """Sample an asymmetric action."""
        # Simple heuristic: if influence is high, Sabotage. Else, Infiltrate.
        if self.influence > 0.6:
            action = "Sabotage"
        elif self.influence > 0.3:
            action = "Subvert"
        else:
            action = "Infiltrate"

        return {"action": action}

    def _apply(self, action: dict) -> None:
        """Apply asymmetric effects."""
        act = action["action"]
        self.posture = act

        # Effect on the target region — O(1) via model registry
        target_agent = self.model.get_agent_by_region(self.target_region)

        if target_agent and hasattr(target_agent, "stability"):
            if act == "Sabotage":
                # Direct hit to stability
                target_agent.stability = max(0.0, target_agent.stability - 0.1)
                self.influence = max(0.0, self.influence - 0.2)  # Exposed
            elif act == "Subvert":
                target_agent.stability = max(0.0, target_agent.stability - 0.02)
                self.influence = min(1.0, self.influence + 0.05)
            elif act == "Infiltrate":
                self.influence = min(1.0, self.influence + 0.02)

    def step(self) -> None:
        """Standard Mesa step."""
        self.observe()
        action = self.decide()
        self._apply(action)
