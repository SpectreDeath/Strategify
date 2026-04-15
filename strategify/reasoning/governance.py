"""International Governance: UN Security Council and Global Resolutions.

This module manages the global layer of the simulation, allowing actors to
coordinate collective action and constrain aggressive behavior through
multilateral resolutions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ResolutionType(Enum):
    """Types of UN resolutions."""

    CEASEFIRE = "ceasefire"
    SANCTIONS = "sanctions"
    CONDEMNATION = "condemnation"
    PEACEKEEPING = "peacekeeping"
    NONE = "none"


@dataclass
class Resolution:
    """A multilateral resolution drafted by the Security Council."""

    resolution_type: ResolutionType
    target_regions: list[str]
    proposer_id: int
    step_passed: int = -1
    is_active: bool = False
    votes_for: list[int] = field(default_factory=list)
    votes_against: list[int] = field(default_factory=list)
    vetoed_by: int | None = None


class GovernanceEngine:
    """Manages global tension and international voting sessions.

    Parameters
    ----------
    model : GeopolModel
        The parent simulation model.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self.global_tension: float = 0.0
        self.active_resolutions: list[Resolution] = []
        self.session_cooldown: int = 0  # Prevents spamming sessions

    def update(self) -> None:
        """Update global metrics and check for session triggers."""
        self._calculate_global_tension()

        if self.session_cooldown > 0:
            self.session_cooldown -= 1
            return

        # Trigger session if tension is high and no ceasefire is active
        if self.global_tension > 0.6:
            self._trigger_security_council()

    def _calculate_global_tension(self) -> None:
        """Aggregate tension across all regions."""
        total_escalation = 0.0
        n_actors = 0
        from strategify.agents.state_actor import StateActorAgent

        for agent in self.model.schedule.agents:
            if isinstance(agent, StateActorAgent):
                # Scale: Infiltrate (0.1) -> Escalate/Invade (0.8-1.0)
                score = 0.0
                if agent.posture == "Escalate": score = 0.8
                elif agent.posture == "Infiltrate": score = 0.2
                elif agent.posture == "Invade": score = 1.0
                
                total_escalation += score
                n_actors += 1

        if n_actors > 0:
            self.global_tension = total_escalation / n_actors
        else:
            self.global_tension = 0.0

    def _trigger_security_council(self) -> None:
        """Organize a voting session among P5 members."""
        logger.info("Governance: GLOBAL TENSION RELEVANT (%.2f). Triggering Security Council.", self.global_tension)
        self.session_cooldown = 10  # Only meet every 10 steps max

        # Find actors in actual conflict (Escalators or Invaders)
        conflict_regions = []
        from strategify.agents.state_actor import StateActorAgent
        for agent in self.model.schedule.agents:
            if isinstance(agent, StateActorAgent) and agent.posture in ["Escalate", "Invade"]:
                conflict_regions.append(agent.region_id)

        if not conflict_regions:
            return

        # Propose Ceasefire for the most stressed region
        target_rid = conflict_regions[0]
        resolution = Resolution(
            resolution_type=ResolutionType.CEASEFIRE,
            target_regions=[target_rid],
            proposer_id=-1, # Secretary General
        )

        self.hold_vote(resolution)

    def hold_vote(self, resolution: Resolution) -> bool:
        """Conduct a vote among all StateActorAgents."""
        logger.info("Governance: Voting on %s for regions %s", 
                    resolution.resolution_type.value, resolution.target_regions)

        from strategify.agents.state_actor import StateActorAgent
        agents = [a for a in self.model.schedule.agents if isinstance(a, StateActorAgent)]

        for agent in agents:
            vote = agent.vote(resolution)
            
            if vote == "Aye":
                resolution.votes_for.append(agent.unique_id)
            elif vote == "No":
                resolution.votes_against.append(agent.unique_id)
                # Check for Veto
                if getattr(agent, "un_seat_type", "") == "Permanent":
                    resolution.vetoed_by = agent.unique_id
                    logger.warning("Governance: Resolution VETOED by %s!", agent.region_id)
                    return False

        # Majority rule (assuming simple majority for this simulation)
        if len(resolution.votes_for) > len(resolution.votes_against):
            resolution.is_active = True
            resolution.step_passed = self.model.schedule.steps
            self.active_resolutions.append(resolution)
            logger.info("Governance: Resolution PASSED (%d vs %d).", 
                        len(resolution.votes_for), len(resolution.votes_against))
            return True

        logger.info("Governance: Resolution FAILED (%d vs %d).", 
                    len(resolution.votes_for), len(resolution.votes_against))
        return False

    def get_resolutions_for_region(self, region_id: str) -> list[Resolution]:
        """Return all active resolutions affecting a specific region."""
        return [r for r in self.active_resolutions if region_id in r.target_regions and r.is_active]
