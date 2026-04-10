"""Domestic politics and ideological models for geopolitical simulation.

Models internal power dynamics within states:
- Factional politics (military, economic, diplomatic)
- Ideological spectrum (left-right, nationalist-globalist)
- Public opinion and leadership cycles
- Internal coalition building
- Elite networks

Usage:

    from strategify.dynamics import FactionalPolitics, IdeologyModel, PublicOpinion

    # Factional dynamics
    fp = FactionalPolitics(agent)
    dominant = fp.get_dominant_faction()

    # Ideology
    ideology = IdeologyModel(personality="Aggressor")
    position = ideology.get_position()

    # Public opinion
    po = PublicOpinion(model, "alpha")
    approval = po.get_approval_rating()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class FactionType(Enum):
    """Types of domestic factions."""

    MILITARY = "military"
    ECONOMIC = "economic"
    DIPLOMATIC = "diplomatic"
    SECURITY = "security"
    INTELLIGENCE = "intelligence"
    PROPAGANDA = "propaganda"


class IdeologyAxis(Enum):
    """Political ideology axes."""

    LEFT_RIGHT = "left_right"  # Economic
    NATIONALIST = "nationalist"  # Sovereignty vs globalism
    HAWK_DOVE = "hawk_dove"  # Security


@dataclass
class Faction:
    """Internal state faction."""

    faction_type: FactionType
    power: float  # 0-1 influence
    preferred_posture: str  # "Escalate" or "Deescalate"
    key_people: list[str] = field(default_factory=list)
    policy_preferences: dict = field(default_factory=dict)


class FactionalPolitics:
    """Model internal factional dynamics.

    States are not unitary actors - internal factions
    compete for influence over foreign policy.
    """

    def __init__(self, agent) -> None:
        self.agent = agent
        self._factions: list[Faction] = []
        self._initialize_factions()

    def _initialize_factions(self) -> None:
        """Initialize factions based on agent personality."""
        personality = getattr(self.agent, "personality", "Neutral")

        # Base factions
        if personality == "Aggressor":
            self._factions = [
                Faction(FactionType.MILITARY, 0.4, "Escalate"),
                Faction(FactionType.SECURITY, 0.3, "Escalate"),
                Faction(FactionType.ECONOMIC, 0.2, "Deescalate"),
                Faction(FactionType.DIPLOMATIC, 0.1, "Deescalate"),
            ]
        elif personality == "Pacifist":
            self._factions = [
                Faction(FactionType.ECONOMIC, 0.4, "Deescalate"),
                Faction(FactionType.DIPLOMATIC, 0.3, "Deescalate"),
                Faction(FactionType.MILITARY, 0.2, "Escalate"),
                Faction(FactionType.SECURITY, 0.1, "Escalate"),
            ]
        elif personality == "Grudger":
            self._factions = [
                Faction(FactionType.MILITARY, 0.35, "Escalate"),
                Faction(FactionType.SECURITY, 0.35, "Escalate"),
                Faction(FactionType.DIPLOMATIC, 0.15, "Deescalate"),
                Faction(FactionType.ECONOMIC, 0.15, "Deescalate"),
            ]
        else:  # Neutral, Tit-for-Tat
            self._factions = [
                Faction(FactionType.MILITARY, 0.25, "Escalate"),
                Faction(FactionType.ECONOMIC, 0.25, "Deescalate"),
                Faction(FactionType.DIPLOMATIC, 0.25, "Deescalate"),
                Faction(FactionType.SECURITY, 0.25, "Escalate"),
            ]

    def get_factions(self) -> list[Faction]:
        """Get all factions."""
        return self._factions

    def get_dominant_faction(self) -> FactionType:
        """Get the most powerful faction."""
        return max(self._factions, key=lambda f: f.power).faction_type

    def get_dominant_posture(self) -> str:
        """Get dominant faction's preferred posture."""
        return max(self._factions, key=lambda f: f.power).preferred_posture

    def apply_external_shock(
        self,
        event_type: str,
        magnitude: float = 0.1,
    ) -> None:
        """Apply external event to faction balances.

        Events can shift internal power:
        - military defeat: military faction loses, diplomatic gains
        - economic crisis: economic faction loses, security gains
        - diplomacy success: diplomatic faction gains
        """
        for faction in self._factions:
            if event_type == "military_defeat":
                if faction.faction_type == FactionType.MILITARY:
                    faction.power = max(0.1, faction.power - magnitude)
                elif faction.faction_type == FactionType.DIPLOMATIC:
                    faction.power = min(0.9, faction.power + magnitude)
            elif event_type == "economic_crisis":
                if faction.faction_type == FactionType.ECONOMIC:
                    faction.power = max(0.1, faction.power - magnitude)
                elif faction.faction_type == FactionType.SECURITY:
                    faction.power = min(0.9, faction.power + magnitude)
            else:
                if faction.faction_type == FactionType.DIPLOMATIC:
                    faction.power = min(0.9, faction.power + magnitude)

        # Renormalize
        total = sum(f.power for f in self._factions)
        for faction in self._factions:
            faction.power /= total

    def get_faction_balance(self) -> str:
        """Get overall internal balance."""
        military_power = sum(
            f.power for f in self._factions if f.faction_type in (FactionType.MILITARY, FactionType.SECURITY)
        )
        diplomatic_power = sum(
            f.power for f in self._factions if f.faction_type in (FactionType.DIPLOMATIC, FactionType.ECONOMIC)
        )

        if military_power > diplomatic_power + 0.2:
            return "hawk_dominant"
        elif diplomatic_power > military_power + 0.2:
            return "dove_dominant"
        else:
            return "balanced"


class IdeologyModel:
    """Model ideological positions.

    Tracks state ideology on multiple axes:
    - Left-Right (economic policy)
    - Nationalist-Globalist (sovereignty)
    - Hawk-Dove (security posture)
    """

    # Default positions for each personality
    PERSONALITY_POSITIONS = {
        "Aggressor": {
            IdeologyAxis.LEFT_RIGHT: 0.8,
            IdeologyAxis.NATIONALIST: 0.9,
            IdeologyAxis.HAWK_DOVE: 0.9,
        },
        "Pacifist": {
            IdeologyAxis.LEFT_RIGHT: 0.3,
            IdeologyAxis.NATIONALIST: 0.2,
            IdeologyAxis.HAWK_DOVE: 0.1,
        },
        "Grudger": {
            IdeologyAxis.LEFT_RIGHT: 0.6,
            IdeologyAxis.NATIONALIST: 0.8,
            IdeologyAxis.HAWK_DOVE: 0.8,
        },
        "Tit-for-Tat": {
            IdeologyAxis.LEFT_RIGHT: 0.5,
            IdeologyAxis.NATIONALIST: 0.5,
            IdeologyAxis.HAWK_DOVE: 0.5,
        },
        "Neutral": {
            IdeologyAxis.LEFT_RIGHT: 0.5,
            IdeologyAxis.NATIONALIST: 0.5,
            IdeologyAxis.HAWK_DOVE: 0.5,
        },
    }

    def __init__(
        self,
        personality: str = "Neutral",
        positions: dict[IdeologyAxis, float] | None = None,
    ) -> None:
        self.positions = positions or self.PERSONALITY_POSITIONS.get(personality, {axis: 0.5 for axis in IdeologyAxis})

    def get_position(self, axis: IdeologyAxis | None = None) -> float | dict:
        """Get position on axis/axes."""
        if axis:
            return self.positions.get(axis, 0.5)
        return self.positions.copy()

    def get_ideology_label(self) -> str:
        """Get human-readable ideology label."""
        nationalist = self.positions[IdeologyAxis.NATIONALIST]
        hawk_dove = self.positions[IdeologyAxis.HAWK_DOVE]

        # Combine into label
        if nationalist > 0.7:
            nationalist_label = "Nationalist"
        elif nationalist < 0.3:
            nationalist_label = "Globalist"
        else:
            nationalist_label = "Centrist"

        if hawk_dove > 0.6:
            security_label = "Hawk"
        elif hawk_dove < 0.4:
            security_label = "Dove"
        else:
            security_label = "Pragmatist"

        return f"{nationalist_label} {security_label}"

    def shift_position(
        self,
        axis: IdeologyAxis,
        delta: float,
    ) -> None:
        """Shift position on an axis."""
        current = self.positions.get(axis, 0.5)
        self.positions[axis] = np.clip(current + delta, 0.0, 1.0)

    def get_compatibility(self, other: IdeologyModel) -> float:
        """Calculate ideological compatibility with another state."""
        total_diff = 0.0
        for axis in IdeologyAxis:
            diff = abs(self.positions.get(axis, 0.5) - other.positions.get(axis, 0.5))
            total_diff += diff
        return 1.0 - (total_diff / 3)


class PublicOpinion:
    """Model public opinion dynamics.

    Public opinion affects leadership stability and
    can constrain policy options.
    """

    def __init__(
        self,
        model: GeopolModel,
        region_id: str,
    ) -> None:
        self.model = model
        self.region_id = region_id
        self._approval_history: list[float] = [0.5]  # Start at 50%
        self._initialize_opinion()

    def _initialize_opinion(self) -> None:
        """Initialize based on agent state."""
        agent = next(
            (a for a in self.model.schedule.agents if getattr(a, "region_id", "") == self.region_id),
            None,
        )
        if agent is None:
            return

        # Initial approval based on posture and capabilities
        posture = getattr(agent, "posture", "Deescalate")
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)
        base = 0.3 + military * 0.3 if posture == "Escalate" else 0.4 + economic * 0.3

        self._approval_history[-1] = np.clip(base, 0.1, 0.9)

    def get_approval_rating(self) -> float:
        """Get current approval rating."""
        return self._approval_history[-1]

    def get_trend(self) -> str:
        """Get approval trend."""
        if len(self._approval_history) < 2:
            return "stable"

        recent = self._approval_history[-3:]
        if all(recent[i] < recent[i + 1] for i in range(len(recent) - 1)):
            return "rising"
        elif all(recent[i] > recent[i + 1] for i in range(len(recent) - 1)):
            return "falling"
        return "stable"

    def update_approval(self) -> None:
        """Update approval based on current events."""
        agent = next(
            (a for a in self.model.schedule.agents if getattr(a, "region_id", "") == self.region_id),
            None,
        )
        if agent is None:
            return

        current = self._approval_history[-1]

        # Posture effect
        posture = getattr(agent, "posture", "Deescalate")
        if posture == "Escalate":
            current -= 0.02  # Escalation is unpopular
        else:
            current += 0.01  # Peace is popular

        # Random波动
        current += np.random.normal(0, 0.02)

        self._approval_history.append(np.clip(current, 0.1, 0.9))

    def get_policy_constraint(self) -> str:
        """Get public opinion constraint on policy."""
        approval = self.get_approval_rating()

        if approval < 0.3:
            return "revolution_risk"
        elif approval < 0.4:
            return "leadership_challenge"
        elif approval < 0.5:
            return "constrained"
        elif approval < 0.7:
            return "stable"
        else:
            return "popular mandate"

    def needs_election(self, election_prob: float = 0.1) -> bool:
        """Check if faced with election."""
        return np.random.random() < election_prob


@dataclass
class InternalCoalition:
    """Internal coalition government."""

    leader_faction: FactionType
    supporting_factions: list[FactionType]
    agenda: dict
    stability: float  # 0-1


class CoalitionBuilder:
    """Build internal coalitions from factions."""

    @staticmethod
    def build_coalition(factions: list[Faction]) -> InternalCoalition:
        """Build coalition from factions."""
        sorted_factions = sorted(factions, key=lambda f: f.power, reverse=True)

        leader = sorted_factions[0].faction_type

        # Seek supporting factions
        support = []
        total_power = sorted_factions[0].power
        for f in sorted_factions[1:]:
            if total_power + f.power >= 0.5:
                support.append(f.faction_type)
                total_power += f.power

        stability = 1.0 - abs(0.5 - total_power)

        return InternalCoalition(
            leader_faction=leader,
            supporting_factions=support,
            agenda={},
            stability=stability,
        )


class LeadershipCycle:
    """Model leadership transitions."""

    def __init__(self, term_length: int = 4) -> None:
        self.term_length = term_length
        self.term_progress: dict[str, int] = {}

    def get_term_remaining(self, region_id: str) -> int:
        """Get remaining terms in office."""
        return max(0, self.term_length - self.term_progress.get(region_id, 0))

    def should_hold_election(self, region_id: str) -> bool:
        """Check if election due."""
        progress = self.term_progress.get(region_id, 0)
        return progress >= self.term_length

    def advance_term(self, region_id: str) -> None:
        """Advance term counter."""
        self.term_progress[region_id] = self.term_progress.get(region_id, 0) + 1

    def force_election(self, region_id: str) -> None:
        """Force early election."""
        self.term_progress[region_id] = self.term_length


# Registry for domestic dynamics
DOMESTIC_DYNAMICS = {
    "factional": FactionalPolitics,
    "ideology": IdeologyModel,
    "public_opinion": PublicOpinion,
}
