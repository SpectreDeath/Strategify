"""Type definitions for the logic layer.

Provides Python wrappers for Prolog concepts:
- Behavioral traits
- Agent profiles
- Decision results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Trait(Enum):
    """Behavioral traits that define agent decision-making DNA.

    These map to Prolog predicates in traits.pl:
    - RECIPROCITY: "I do what you did to me"
    - FORGIVENESS: "If you cheated once but cooperated twice, I trust you again"
    - AGGRESSION: "If I have more resources than you, I always compete"
    - TIT_FOR_TAT: Classic Axelrod strategy
    - GRUDGER: "Once you defect, I never cooperate again"
    - PACIFIST: Always cooperates
    """

    RECIPROCITY = "reciprocity"
    FORGIVENESS = "forgiveness"
    AGGRESSION = "aggression"
    TIT_FOR_TAT = "tit_for_tat"
    GRUDGER = "grudger"
    PACIFIST = "pacifist"

    def __str__(self) -> str:
        return self.value


class Personality(Enum):
    """Higher-order behavioral profiles (from Section 9 of traits.pl).

    These represent how an agent "thinks" - their decision-making style:
    - CAUTIOUS: Only escalates if risk is low
    - OPPORTUNISTIC: Escalates on any potential gain
    - ANALYST: Calculates expected value before committing
    - IDEALIST: Prioritizes mutual cooperation
    """

    CAUTIOUS = "cautious"
    OPPORTUNISTIC = "opportunistic"
    ANALYST = "analyst"
    IDEALIST = "idealist"

    def __str__(self) -> str:
        return self.value


class RiskLevel(Enum):
    """Risk assessment levels for decision context."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class PotentialGain(Enum):
    """Potential gain assessment for decision context."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class Action(Enum):
    """Actions in the escalation game."""

    ESCALATE = "escalate"
    DEESCALATE = "deescalate"


@dataclass
class AgentProfile:
    """Profile defining an agent's behavioral characteristics.

    This class bridges Python agents to the Prolog knowledge base.
    It represents the "DNA" of agent behavior.

    Parameters
    ----------
    traits:
        List of behavioral traits (in priority order). First trait wins ties.
    resources:
        Numeric resource level. Used by AGGRESSION trait (>5.0 = attack).
    tom_level:
        Theory of Mind level (0-2). Higher = deeper nested beliefs.
        Level 0: Knows the goal.
        Level 1: Models what others know.
        Level 2: Can be deceived.
    memory:
        Internal state for stateful strategies (Grudger, etc).
    name:
        Optional agent identifier for debugging.

    Example
    -------
    >>> profile = AgentProfile(
    ...     traits=[Trait.TIT_FOR_TAT, Trait.FORGIVENESS],
    ...     resources=5.0,
    ...     tom_level=1,
    ... )
    """

    traits: list[Trait] = field(default_factory=lambda: [Trait.TIT_FOR_TAT])
    resources: float = 5.0
    tom_level: int = 0
    memory: dict[str, Any] = field(default_factory=dict)
    name: str | None = None

    def __post_init__(self) -> None:
        # Validate TOM level
        if not 0 <= self.tom_level <= 2:
            raise ValueError(f"TOM level must be 0-2, got {self.tom_level}")

    def has_trait(self, trait: Trait) -> bool:
        """Check if profile has a specific trait."""
        return trait in self.traits

    def add_trait(self, trait: Trait) -> None:
        """Add a trait to the profile."""
        if trait not in self.traits:
            self.traits.append(trait)

    def remove_trait(self, trait: Trait) -> None:
        """Remove a trait from the profile."""
        self.traits = [t for t in self.traits if t != trait]

    def get_primary_trait(self) -> Trait | None:
        """Get the primary (first) trait."""
        return self.traits[0] if self.traits else None

    @classmethod
    def from_personality(cls, personality: str) -> AgentProfile:
        """Create profile from Strategify personality string.

        Maps old personality names to new trait system:
        - "Aggressor" -> AGGRESSION
        - "Pacifist" -> PACIFIST
        - "Tit-for-Tat" -> TIT_FOR_TAT
        - "Neutral" -> TIT_FOR_TAT (majority vote)
        - "Grudger" -> GRUDGER
        """
        mapping = {
            "Aggressor": [Trait.AGGRESSION],
            "Pacifist": [Trait.PACIFIST],
            "Tit-for-Tat": [Trait.TIT_FOR_TAT],
            "Tit-for-Tat": [Trait.TIT_FOR_TAT],
            "Neutral": [Trait.TIT_FOR_TAT],
            "Grudger": [Trait.GRUDGER],
        }
        traits = mapping.get(personality, [Trait.TIT_FOR_TAT])
        return cls(traits=traits)

    def to_prolog_term(self) -> str:
        """Convert to Prolog term format."""
        traits_list = "[" + ",".join(t.value for t in self.traits) + "]"
        return f"profile(traits,{self.resources},{self.tom_level})"


@dataclass
class DecisionResult:
    """Result of a behavioral decision.

    Parameters
    ----------
    action:
        The chosen action ("escalate" or "deescalate").
    trace:
        Reasoning trace for debugging/observability.
    confidence:
        Confidence in decision (0.0-1.0). Lower when using fallback.
    source:
        Where the decision came from ("prolog" or "python_fallback").
    """

    action: str
    trace: str = ""
    confidence: float = 1.0
    source: str = "prolog"

    def __post_init__(self) -> None:
        # Infer source from trace
        if "python" in self.trace.lower():
            self.source = "python_fallback"

    @property
    def is_escalate(self) -> bool:
        """True if action is escalate."""
        return self.action == "escalate"

    @property
    def is_deescalate(self) -> bool:
        """True if action is deescalate."""
        return self.action == "deescalate"

    def __str__(self) -> str:
        return f"Decision({self.action}, conf={self.confidence:.1f})"


@dataclass
class Belief:
    """Represents a nested belief for Theory of Mind.

    Parameters
    ----------
    level:
        Depth of belief nesting (0-2).
    agent:
        Agent this belief belongs to.
    content:
        The factual content of the belief.
    """

    level: int
    agent: str
    content: Any

    def __post_init__(self) -> None:
        if not 0 <= self.level <= 2:
            raise ValueError(f"Belief level must be 0-2, got {self.level}")

    def __str__(self) -> str:
        return f"Belief(L{self.level},{self.agent}:{self.content})"


@dataclass
class Payoff:
    """Payoff calculation result."""

    my_payoff: int
    opponent_payoff: int

    @property
    def total(self) -> int:
        """Sum of both payoffs."""
        return self.my_payoff + self.opponent_payoff

    @property
    def differential(self) -> int:
        """My payoff minus opponent payoff."""
        return self.my_payoff - self.opponent_payoff

    def __str__(self) -> str:
        return f"Payoff({self.my_payoff}, {self.opponent_payoff})"


# backwards compatibility alias
Decision = DecisionResult
