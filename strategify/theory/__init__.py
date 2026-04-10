"""Geopolitical theories: academic foundations for simulation.

Implements classical and modern geopolitical theories as
theory-aware agent behaviors. Provides the academic
underpinnings for strategic decision-making.

Theories implemented:
- Realpolitik (power politics, balance of power)
- Democratic Peace Theory
- Power Transition Theory
- Offensive/Defensive Realism
- Liberal Institutionalism
- Constructivism (identity-based)
- Bandwagoning vs Balancing

Usage:

    from strategify.theory import TheoryRegistry, RealpolitikTheory

    registry = TheoryRegistry()
    registry.register(RealpolitikTheory())

    action = registry.decide(agent, model, "alpha")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class PowerMetric(Enum):
    """How to measure state power."""

    MILITARY = "military"
    ECONOMIC = "economic"
    COMPOSITE = "composite"
    GDP = "gdp"


@dataclass
class TheoryResult:
    """Result from theory-based analysis."""

    theory: str
    recommended_action: str
    confidence: float  # 0-1
    rationale: str
    power_assessment: dict = None

    def __post_init__(self):
        if self.power_assessment is None:
            self.power_assessment = {}


class GeopoliticalTheory(ABC):
    """Base class for geopolitical theories."""

    name: str
    description: str

    @abstractmethod
    def evaluate(
        self,
        agent,
        model: GeopolModel,
    ) -> TheoryResult:
        """Evaluate situation and recommend action."""
        pass

    @abstractmethod
    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Calculate power of state."""
        pass


class RealpolitikTheory(GeopoliticalTheory):
    """Realpolitik: power politics and balance of power.

    Key principles:
    - States seek power maximally
    - International system is anarchic
    - Balance of power determines stability
    - Power is the only reliable currency

    Based on: Hans Morgenthau, John Mearsheimer
    """

    name = "Realpolitik"
    description = "Power politics and balance of power"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate using Realpolitik principles."""
        my_power = self.calculate_power(agent, model)

        # Find most powerful rival
        max_rival_power = 0.0
        rival_id = None
        for other in model.schedule.agents:
            if getattr(other, "region_id", "") == getattr(agent, "region_id", ""):
                continue
            rival_power = self.calculate_power(other, model)
            if rival_power > max_rival_power:
                max_rival_power = rival_power
                rival_id = getattr(other, "region_id", "")

        # Balance of power calculation
        power_ratio = my_power / max_rival_power if max_rival_power > 0 else 1.0

        # Decision logic
        if power_ratio < 0.8 and getattr(agent, "posture", "Deescalate") == "Deescalate":
            return TheoryResult(
                theory=self.name,
                recommended_action="balance",
                confidence=0.8,
                rationale=f"Power ratio {power_ratio:.2f} - balance against {rival_id}",
            )

        if power_ratio > 1.2:
            # Power advantage - maximize influence
            return TheoryResult(
                theory=self.name,
                recommended_action="exploit",
                confidence=0.7,
                rationale=f"Power ratio {power_ratio:.2f} - favorable position",
            )

        return TheoryResult(
            theory=self.name,
            recommended_action="maintain",
            confidence=0.6,
            rationale="Balance maintained",
        )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Calculate state power using theory metrics."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Alliance weighted power
        ally_bonus = 0.0
        if model.relations:
            allies = model.relations.get_allies(agent.unique_id)
            for auid in allies:
                for a in model.schedule.agents:
                    if a.unique_id == auid:
                        ally_bonus += (
                            a.capabilities.get("military", 0.5) * 0.5 + a.capabilities.get("economic", 0.5) * 0.5
                        )

        if metric == PowerMetric.MILITARY:
            return military + ally_bonus * 0.3
        elif metric == PowerMetric.ECONOMIC:
            return economic + ally_bonus * 0.2
        else:  # COMPOSITE
            return (military + economic) / 2 + ally_bonus * 0.25


class DemocraticPeaceTheory(GeopoliticalTheory):
    """Democratic Peace Theory: democracies don't fight each other.

    Key principles:
    - Democracies are inherently more peaceful
    - Democratic norms约束 behavior
    - Public accountability reduces aggression
    - Trade promotes peace

    Based on: Michael Doyle, Bruce Russett
    """

    name = "Democratic Peace"
    description = "Democratic norms constrain aggression"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate using Democratic Peace principles."""
        personality = getattr(agent, "personality", "Neutral")

        # Check if any adversary is democratic
        has_democratic_rival = False
        for other in model.schedule.agents:
            if getattr(other, "region_id", "") == getattr(agent, "region_id", ""):
                continue
            other_personality = getattr(other, "personality", "Neutral")
            if other_personality in ("Pacifist", "Tit-for-Tat"):
                has_democratic_rival = True

        if personality == "Pacifist":
            return TheoryResult(
                theory=self.name,
                recommended_action="deescalate",
                confidence=0.9,
                rationale="Democratic norms - prefer peace",
            )

        if has_democratic_rival and getattr(agent, "posture", "Deescalate") == "Escalate":
            return TheoryResult(
                theory=self.name,
                recommended_action="deescalate",
                confidence=0.7,
                rationale="Democratic peace norm - avoid conflict with democracy",
            )

        return TheoryResult(
            theory=self.name,
            recommended_action="maintain",
            confidence=0.5,
            rationale="No democratic constraints detected",
        )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Democratic power includes institutional quality."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Institutional bonus (democracies more efficient)
        personality = getattr(agent, "personality", "Neutral")
        inst_bonus = 0.1 if personality == "Pacifist" else 0.0

        return (military + economic) / 2 + inst_bonus


class PowerTransitionTheory(GeopoliticalTheory):
    """Power Transition Theory: rising powers challenge status quo.

    Key principles:
    - Status quo powers are satisfied
    - Rising powers are revisionist
    - Wars occur when rising power overtakes status quo
    - Power parity is most dangerous

    Based on: A.F.K. Organski
    """

    name = "Power Transition"
    description = "Rising powers challenge status quo"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate using Power Transition logic."""
        my_power = self.calculate_power(agent, model)

        # Find average system power (status quo)
        total_power = my_power
        n_states = 1
        for other in model.schedule.agents:
            if getattr(other, "region_id", "") == getattr(agent, "region_id", ""):
                continue
            total_power += self.calculate_power(other, model)
            n_states += 1

        avg_power = total_power / n_states

        # Power transition zones
        if my_power > avg_power * 1.3:
            return TheoryResult(
                theory=self.name,
                recommended_action="consolidate",
                confidence=0.8,
                rationale="Status quo power - maintain dominance",
            )
        elif my_power > avg_power * 0.8:
            return TheoryResult(
                theory=self.name,
                recommended_action="expand",
                confidence=0.7,
                rationale="Approaching parity - challenge status quo",
            )
        else:
            return TheoryResult(
                theory=self.name,
                recommended_action="bide",
                confidence=0.6,
                rationale="Below parity - build strength",
            )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Power calculation for transition analysis."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Growth potential (economic drives growth)
        economic = economic * 1.2  # Boost economic weight

        return (military + economic) / 2


class OffensiveRealism(GeopoliticalTheory):
    """Offensive Realism: states are naturally aggressive.

    Key principles:
    - States seek maximum power
    - International system rewards aggression
    - Hegemony is the only security
    - Best defense is offense

    Based on: John Mearsheimer
    """

    name = "Offensive Realism"
    description = "Aggressive power maximization"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate with aggressive realism."""
        personality = getattr(agent, "personality", "Neutral")

        if personality == "Aggressor":
            # Check for targets of opportunity
            for other in model.schedule.agents:
                if getattr(other, "region_id", "") == getattr(agent, "region_id", ""):
                    continue
                other_power = (other.capabilities.get("military", 0.5) + other.capabilities.get("economic", 0.5)) / 2
                my_power = (agent.capabilities.get("military", 0.5) + agent.capabilities.get("economic", 0.5)) / 2

                if my_power > other_power * 1.3:
                    return TheoryResult(
                        theory=self.name,
                        recommended_action="exploit",
                        confidence=0.9,
                        rationale="Superior power - exploit advantage",
                    )

        return TheoryResult(
            theory=self.name,
            recommended_action="maintain",
            confidence=0.5,
            rationale="No targets of opportunity",
        )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Offensive power emphasizes military."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Military weighted heavily
        return military * 0.6 + economic * 0.4


class DefensiveRealism(GeopoliticalTheory):
    """Defensive Realism: states seek security, not power.

    Key principles:
    - States seek adequate power (security)
    - Balancing is default strategy
    - Overexpansion is self-defeating
    - Territorial defense is primary

    Based on: Kenneth Waltz
    """

    name = "Defensive Realism"
    description = "Security-first defensiveness"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate with defensive realism."""
        # Check alliance structure - should balance threats
        allies = model.relations.get_allies(agent.unique_id) if model.relations else []

        if len(allies) < 2:
            return TheoryResult(
                theory=self.name,
                recommended_action="balance",
                confidence=0.8,
                rationale="Insufficient alliances - balance threats",
            )

        return TheoryResult(
            theory=self.name,
            recommended_action="maintain",
            confidence=0.7,
            rationale="Adequate security - maintain position",
        )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Defensive power - security minimums."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Adequacy threshold
        adequate = 0.4

        if military < adequate:
            return military + 0.2  # Boost toward adequacy

        return military * 0.5 + economic * 0.5


class LiberalInstitutionalism(GeopoliticalTheory):
    """Liberal Institutionalism: institutions promote cooperation.

    Key principles:
    - Institutions enable cooperation
    - Absolute gains matter more than relative
    - Information reduces uncertainty
    - Reputations matter

    Based on: Robert Keohane
    """

    name = "Liberal Institutionalism"
    description = "Institutional cooperation"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate with institutional logic."""
        # Check trade relationships
        if model.trade_network:
            trade_balance = model.trade_network.get_trade_balance(agent.unique_id)

            if trade_balance > 0:
                return TheoryResult(
                    theory=self.name,
                    recommended_action="cooperate",
                    confidence=0.7,
                    rationale="Institutional cooperation beneficial",
                )

        # Check diplomatic ties
        allies = model.relations.get_allies(agent.unique_id) if model.relations else []
        if len(allies) > 1:
            return TheoryResult(
                theory=self.name,
                recommended_action="institutionalize",
                confidence=0.6,
                rationale="Deepen institutional ties",
            )

        return TheoryResult(
            theory=self.name,
            recommended_action="engage",
            confidence=0.5,
            rationale="Seek institutional engagement",
        )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Institutional power includes network effects."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Institutional network bonus
        allies = model.relations.get_allies(agent.unique_id) if model.relations else []
        trade_partners = 0
        if model.trade_network:
            trade_partners = len(model.trade_network.get_partners(agent.unique_id))

        network_bonus = (len(allies) + trade_partners) * 0.05

        return (military + economic) / 2 + network_bonus


class Constructivism(GeopoliticalTheory):
    """Constructivism: identity and norms shape interests.

    Key principles:
    - Identity defines interests
    - Norms construct reality
    - Social context matters
    - Ideas are causal

    Based on: Alexander Wendt
    """

    name = "Constructivism"
    description = "Identity and norms-based analysis"

    def evaluate(self, agent, model: GeopolModel) -> TheoryResult:
        """Evaluate with identity logic."""
        personality = getattr(agent, "personality", "Neutral")

        # Identity-based decision rules
        if personality == "Pacifist":
            return TheoryResult(
                theory=self.name,
                recommended_action="deescalate",
                confidence=0.9,
                rationale="Pacifist identity - peace identity",
            )
        elif personality == "Aggressor":
            return TheoryResult(
                theory=self.name,
                recommended_action="escalate",
                confidence=0.9,
                rationale="Aggressor identity - conflict identity",
            )
        elif personality == "Grudger":
            return TheoryResult(
                theory=self.name,
                recommended_action="retaliate",
                confidence=0.8,
                rationale="Grudger identity - revenge norms",
            )
        elif personality == "Tit-for-Tat":
            # Check opponent's last action
            return TheoryResult(
                theory=self.name,
                recommended_action="reciprocate",
                confidence=0.7,
                rationale="Tit-for-Tat identity - reciprocity",
            )

        return TheoryResult(
            theory=self.name,
            recommended_action="maintain",
            confidence=0.5,
            rationale="Neutral identity",
        )

    def calculate_power(
        self,
        agent,
        model: GeopolModel,
        metric: PowerMetric = PowerMetric.COMPOSITE,
    ) -> float:
        """Identity-influenced power."""
        military = agent.capabilities.get("military", 0.5)
        economic = agent.capabilities.get("economic", 0.5)

        # Identity coherence bonus
        personality = getattr(agent, "personality", "Neutral")
        coherence = 0.1 if personality != "Neutral" else 0.0

        return (military + economic) / 2 + coherence


class TheoryRegistry:
    """Registry for geopolitical theories."""

    def __init__(self) -> None:
        self._theories: dict[str, GeopoliticalTheory] = {}

        # Register built-in theories
        self.register(RealpolitikTheory())
        self.register(DemocraticPeaceTheory())
        self.register(PowerTransitionTheory())
        self.register(OffensiveRealism())
        self.register(DefensiveRealism())
        self.register(LiberalInstitutionalism())
        self.register(Constructivism())

    def register(self, theory: GeopoliticalTheory) -> None:
        """Register a theory."""
        self._theories[theory.name] = theory

    def get(self, name: str) -> GeopoliticalTheory | None:
        """Get theory by name."""
        return self._theories.get(name)

    def list_theories(self) -> list[str]:
        """List registered theories."""
        return list(self._theories.keys())

    def decide(self, agent, model: GeopolModel, theory_name: str) -> TheoryResult:
        """Get theory-based decision."""
        theory = self._theories.get(theory_name)
        if theory is None:
            return TheoryResult(
                theory="none",
                recommended_action="maintain",
                confidence=0.0,
                rationale="Theory not found",
            )
        return theory.evaluate(agent, model)

    def analyze_with_all(self, agent, model: GeopolModel) -> list[TheoryResult]:
        """Analyze with all theories."""
        results = []
        for theory in self._theories.values():
            results.append(theory.evaluate(agent, model))
        return results


# Default registry
DEFAULT_REGISTRY = TheoryRegistry()
