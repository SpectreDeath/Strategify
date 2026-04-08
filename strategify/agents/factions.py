"""Internal factions and domestic politics for geopolitical actors.

This module defines the InternalFaction class that tracks domestic
pressures and affects the agent's overall posture and stability.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class FactionType:
    """Standard faction types with different priorities."""

    HAWKS = "Hawks"
    DOVES = "Doves"
    INDUSTRIALISTS = "Industrialists"
    NATIONALISTS = "Nationalists"


class InternalFaction:
    """Represents a domestic pressure group within a state actor.

    Attributes
    ----------
    name : str
        The name of the faction.
    power : float
        Current political influence [0.0, 1.0].
    preferred_actions : Set[str]
        Set of action strings (postures) this faction supports.
    """

    def __init__(
        self,
        name: str,
        power: float = 0.3,
        preferred_actions: list[str] = None,
    ) -> None:
        self.name = name
        self.power = power
        self.preferred_actions = set(preferred_actions or [])

    def supports(self, action: str) -> bool:
        """Check if the faction supports a given model action."""
        return action in self.preferred_actions

    def __repr__(self) -> str:
        return f"<Faction {self.name} (P:{self.power:.2f})>"


def get_default_factions() -> list[InternalFaction]:
    """Helper to generate a default set of competing groups."""
    return [
        InternalFaction(
            FactionType.HAWKS,
            power=0.3,
            preferred_actions=["Escalate", "Act", "Protect"],
        ),
        InternalFaction(
            FactionType.DOVES,
            power=0.3,
            preferred_actions=["Deescalate", "Restrain", "Open"],
        ),
        InternalFaction(
            FactionType.INDUSTRIALISTS,
            power=0.4,
            preferred_actions=["Open", "Deescalate", "Comply"],
        ),
    ]
