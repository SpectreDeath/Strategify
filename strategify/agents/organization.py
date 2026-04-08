"""Organization agent: non-state and intergovernmental actors.

Supports International Governmental Organizations (IGOs) like UN/NATO
and Non-Governmental Organizations (NGOs) with different decision logic
from state actors.
"""

from __future__ import annotations

import logging
from typing import Any

from shapely.geometry import base as shp_base

from strategify.agents.base import BaseActorAgent

logger = logging.getLogger(__name__)


class OrganizationAgent(BaseActorAgent):
    """An organizational actor (IGO or NGO) with specialized decision logic.

    Organizations don't participate in the standard escalation game.
    Instead, they observe the overall state and take mediating or
    advocacy actions.

    Parameters
    ----------
    unique_id:
        Unique agent identifier.
    model:
        Parent GeopolModel.
    geometry:
        Shapely geometry (may be a point or small polygon).
    crs:
        Coordinate reference system.
    org_type:
        ``"IGO"`` for intergovernmental organizations (UN, NATO),
        ``"NGO"`` for non-governmental organizations.
    mandate:
        Describes the organization's primary objective:
        ``"peacekeeping"``, ``"humanitarian"``, ``"economic"``,
        or ``"security"``.
    member_ids:
        List of state actor unique_ids that are members.
    """

    def __init__(
        self,
        unique_id: int,
        model: Any,
        geometry: shp_base.BaseGeometry,
        crs: str,
        org_type: str = "IGO",
        mandate: str = "peacekeeping",
        member_ids: list[int] | None = None,
    ) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.posture: str = "Deescalate"
        self.org_type = org_type
        self.mandate = mandate
        self.member_ids: list[int] = member_ids or []
        self.region_id = f"org_{org_type.lower()}_{unique_id}"
        self.capabilities = {"military": 0.0, "economic": 0.3}
        self.personality = "Neutral"
        self.role = "observer"
        self._resolution_count = 0
        self._aid_count = 0

    def decide(self) -> dict:
        """Decide action based on mandate and member state conditions.

        IGOs with peacekeeping mandate:
        - If members are escalating: propose mediation (Deescalate)
        - If all members peaceful: maintain status quo

        NGOs:
        - Respond to high escalation with humanitarian advocacy
        """
        if not self.member_ids:
            return {"action": "Deescalate", "type": "observe"}

        # Assess member states
        member_agents = [a for a in self.model.schedule.agents if a.unique_id in self.member_ids]

        if not member_agents:
            return {"action": "Deescalate", "type": "observe"}

        escalation_count = sum(
            1 for a in member_agents if getattr(a, "posture", "Deescalate") == "Escalate"
        )
        escalation_ratio = escalation_count / len(member_agents)

        if self.org_type == "IGO":
            if self.mandate == "peacekeeping":
                if escalation_ratio > 0.5:
                    self._resolution_count += 1
                    return {"action": "Deescalate", "type": "resolution"}
                elif escalation_ratio > 0.25:
                    return {"action": "Deescalate", "type": "advisory"}
            elif self.mandate == "security":
                if escalation_ratio > 0.5:
                    return {"action": "Escalate", "type": "collective_defense"}
            elif self.mandate == "economic":
                return {"action": "Deescalate", "type": "economic_coordination"}

        elif self.org_type == "NGO":
            if self.mandate == "humanitarian":
                if escalation_ratio > 0.3:
                    self._aid_count += 1
                    return {"action": "Deescalate", "type": "humanitarian_aid"}
            elif self.mandate == "economic":
                return {"action": "Deescalate", "type": "development_aid"}

        return {"action": "Deescalate", "type": "observe"}

    def _apply(self, action: dict) -> None:
        """Apply organization-specific action effects."""
        super()._apply(action)
        self.posture = action["action"]

        # Organizations influence member relations
        action_type = action.get("type", "observe")
        if action_type == "resolution":
            # Reduce tension between members
            for uid in self.member_ids:
                for uid2 in self.member_ids:
                    if uid != uid2:
                        current = self.model.relations.get_relation(uid, uid2)
                        new_weight = min(1.0, current + 0.1)
                        self.model.relations.set_relation(uid, uid2, new_weight)
        elif action_type == "collective_defense":
            # Strengthen alliance bonds
            for uid in self.member_ids:
                for uid2 in self.member_ids:
                    if uid != uid2:
                        current = self.model.relations.get_relation(uid, uid2)
                        new_weight = min(1.0, current + 0.05)
                        self.model.relations.set_relation(uid, uid2, new_weight)

    def get_stats(self) -> dict:
        """Return organization activity statistics."""
        return {
            "org_type": self.org_type,
            "mandate": self.mandate,
            "members": len(self.member_ids),
            "resolutions": self._resolution_count,
            "aid_operations": self._aid_count,
        }
