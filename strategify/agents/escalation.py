"""Escalation ladder: discrete escalation levels with transition costs.

Provides an EscalationLevel enum and EscalationLadder class that tracks
each actor's position on the escalation ladder and enforces transition
costs when moving between levels.
"""

from __future__ import annotations

import logging
from enum import IntEnum
from typing import TYPE_CHECKING

from strategify.config.settings import (
    ESCALATION_TRANSITION_COSTS,
)
from strategify.geo.adjacency import is_edge_neighbor

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)


class EscalationLevel(IntEnum):
    """Discrete escalation levels from cooperation to military action."""

    Cooperative = 0
    Diplomatic = 1
    Economic = 2
    Military = 3


# Map level names to enum
_LEVEL_MAP: dict[str, EscalationLevel] = {
    "Cooperative": EscalationLevel.Cooperative,
    "Diplomatic": EscalationLevel.Diplomatic,
    "Economic": EscalationLevel.Economic,
    "Military": EscalationLevel.Military,
}


class EscalationLadder:
    """Tracks and manages escalation levels for all actors.

    Parameters
    ----------
    model:
        The parent GeopolModel.
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        # levels[unique_id] = current EscalationLevel
        self.levels: dict[int, EscalationLevel] = {}
        # history[unique_id] = list of (step, level)
        self.history: dict[int, list[tuple[int, EscalationLevel]]] = {}
        # Accumulated costs per agent
        self.transition_costs: dict[int, float] = {}
        self._step: int = 0

    def initialize(self, default_level: EscalationLevel = EscalationLevel.Cooperative) -> None:
        """Set all actors to the default escalation level."""
        for agent in self.model.schedule.agents:
            uid = agent.unique_id
            self.levels[uid] = default_level
            self.history[uid] = [(0, default_level)]
            self.transition_costs[uid] = 0.0

    def get_level(self, unique_id: int) -> EscalationLevel:
        """Return current escalation level for an actor."""
        return self.levels.get(unique_id, EscalationLevel.Cooperative)

    def get_level_name(self, unique_id: int) -> str:
        """Return current escalation level name for an actor."""
        level = self.get_level(unique_id)
        return level.name

    def get_numeric_level(self, unique_id: int) -> int:
        """Return numeric escalation level (0-3) for an actor."""
        return int(self.get_level(unique_id))

    def can_transition(self, unique_id: int, target: EscalationLevel) -> bool:
        """Check if transition to target level is allowed.

        Only single-step transitions are allowed (no skipping levels).
        """
        current = self.get_level(unique_id)
        return abs(int(target) - int(current)) <= 1

    def transition_cost(self, current: EscalationLevel, target: EscalationLevel) -> float:
        """Return cost of transitioning from current to target level."""
        key = (current.name, target.name)
        return ESCALATION_TRANSITION_COSTS.get(key, 0.0)

    def set_level(self, unique_id: int, target: EscalationLevel) -> float:
        """Set escalation level for an actor, returning transition cost.

        Parameters
        ----------
        unique_id:
            Actor's unique ID.
        target:
            Desired escalation level.

        Returns
        -------
        float
            Cost of the transition (positive = cost, negative = benefit).
            Returns 0.0 if transition is not allowed.
        """
        current = self.levels.get(unique_id, EscalationLevel.Cooperative)

        if not self.can_transition(unique_id, target):
            logger.debug(
                "Blocked escalation transition for %d: %s -> %s (skips level)",
                unique_id,
                current.name,
                target.name,
            )
            return 0.0

        cost = self.transition_cost(current, target)
        self.levels[unique_id] = target
        self.transition_costs[unique_id] = self.transition_costs.get(unique_id, 0.0) + cost
        self.history.setdefault(unique_id, []).append((self._step, target))
        return cost

    def set_level_by_name(self, unique_id: int, name: str) -> float:
        """Set escalation level by name, returning transition cost."""
        target = _LEVEL_MAP.get(name)
        if target is None:
            logger.warning("Unknown escalation level '%s'", name)
            return 0.0
        return self.set_level(unique_id, target)

    def step(self) -> None:
        """Advance one simulation step."""
        self._step += 1

    def get_max_level(self) -> EscalationLevel:
        """Return the highest escalation level across all actors."""
        if not self.levels:
            return EscalationLevel.Cooperative
        return max(self.levels.values())

    def get_escalation_pressure(self, unique_id: int) -> float:
        """Return normalized escalation pressure [0, 1] based on neighbors.

        Pressure increases when neighbors are at higher escalation levels.
        """
        current = self.get_level(unique_id)
        agent = next(
            (a for a in self.model.schedule.agents if a.unique_id == unique_id),
            None,
        )
        if agent is None:
            return 0.0

        try:
            neighbors = self.model.space.get_neighbors(agent)
            # Filter out corner-contacts: only shared borders count
            neighbors = [n for n in neighbors if is_edge_neighbor(agent.geometry, n.geometry)]
        except Exception:
            return 0.0

        if not neighbors:
            return 0.0

        neighbor_levels = [self.get_numeric_level(n.unique_id) for n in neighbors]
        avg_neighbor = sum(neighbor_levels) / len(neighbor_levels)
        # Pressure = how much higher neighbors are, normalized to [0, 1]
        pressure = max(0.0, (avg_neighbor - int(current)) / len(EscalationLevel))
        return pressure

    def summary(self) -> dict[str, dict]:
        """Return summary of all actors' escalation states."""
        result = {}
        for uid, level in self.levels.items():
            agent = next(
                (a for a in self.model.schedule.agents if a.unique_id == uid),
                None,
            )
            rid = getattr(agent, "region_id", str(uid)) if agent else str(uid)
            result[rid] = {
                "level": level.name,
                "numeric": int(level),
                "total_cost": self.transition_costs.get(uid, 0.0),
            }
        return result
