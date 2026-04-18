"""Hierarchical Hybrid AI: RL for strategy + scripted for tactics.

Based on MCWL research combining reinforcement learning managers with
scripted tactical agents for improved performance in combat simulations.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class DecisionLevel(Enum):
    """Decision hierarchy levels."""

    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    TACTICAL = "tactical"


class TacticalAction(Enum):
    """Predefined tactical actions for scripted agents."""

    HOLD = "hold"
    ADVANCE = "advance"
    RETREAT = "flank"
    DEFEND = "defend"
    ATTACK = "attack"
    RECON = "recon"


SCRIPTED_TACTICS: dict[TacticalAction, dict[str, Any]] = {
    TacticalAction.HOLD: {
        "posture": "Deescalate",
        "mission": "Defend",
        "aggression": 0.0,
        "movement": "static",
    },
    TacticalAction.ADVANCE: {
        "posture": "Escalate",
        "mission": "Attack",
        "aggression": 1.0,
        "movement": "forward",
    },
    TacticalAction.RETREAT: {
        "posture": "Deescalate",
        "mission": "Withdraw",
        "aggression": -0.5,
        "movement": "backward",
    },
    TacticalAction.DEFEND: {
        "posture": "Deescalate",
        "mission": "Defend",
        "aggression": 0.2,
        "movement": "static",
    },
    TacticalAction.ATTACK: {
        "posture": "Escalate",
        "mission": "Attack",
        "aggression": 0.9,
        "movement": "forward",
    },
    TacticalAction.RECON: {
        "posture": "Observe",
        "mission": "Patrol",
        "aggression": 0.1,
        "movement": "patrol",
    },
}


@dataclass
class HybridDecision:
    """Combined decision from RL strategic + scripted tactical."""

    level: DecisionLevel
    strategic_action: str
    tactical_action: TacticalAction
    confidence: float
    rl_policy_used: bool
    tactical_reasoning: str


class HierarchicalHybridAI:
    """Hybrid AI combining RL (strategic) + scripted (tactical).

    Uses RL for high-level strategic decisions and scripted agents
    for well-defined tactical actions based on MCWL research.
    """

    def __init__(self, use_rl: bool = True):
        self.use_rl = use_rl
        self.strategy_history: list[dict[str, Any]] = []
        self._initialize_rl_agent()

    def _initialize_rl_agent(self) -> None:
        """Initialize RL agent for strategic decisions."""
        if self.use_rl:
            try:
                from strategify.rl.environment import GeopolEnv

                self.rl_env = GeopolEnv()
                self.rl_agent = None
            except ImportError:
                self.use_rl = False
                self.rl_env = None
        else:
            self.rl_env = None

    def make_decision(
        self,
        agent: Any,
        model: Any,
        observation: list[float],
    ) -> HybridDecision:
        """Make hierarchical decision combining strategic and tactical.

        1. Strategic level: Use RL (or heuristic) to determine overall approach
        2. Tactical level: Map to scripted tactical actions
        """
        strategic_action = self._get_strategic_decision(agent, model, observation)

        tactical_action = self._get_tactical_action(agent, model, strategic_action)

        return HybridDecision(
            level=DecisionLevel.STRATEGIC,
            strategic_action=strategic_action,
            tactical_action=tactical_action,
            confidence=0.7 if self.use_rl else 0.5,
            rl_policy_used=self.use_rl,
            tactical_reasoning=self._get_tactical_reasoning(tactical_action),
        )

    def _get_strategic_decision(
        self,
        agent: Any,
        model: Any,
        observation: list[float],
    ) -> str:
        """Get strategic decision at the operational level."""
        if self.use_rl and self.rl_agent is not None:
            return self._rl_decision(observation)

        return self._heuristic_strategic_decision(agent, model)

    def _rl_decision(self, observation: list[float]) -> str:
        """Use RL policy for strategic decision."""
        return "Escalate"

    def _heuristic_strategic_decision(
        self,
        agent: Any,
        model: Any,
    ) -> str:
        """Fallback heuristic for strategic decision."""
        military = getattr(agent, "military_power", 0.5)
        stability = getattr(agent, "stability", 0.5)

        if military > 0.7 and stability > 0.4:
            return "Escalate"
        elif stability < 0.3:
            return "Deescalate"
        else:
            return "Maintain"

    def _get_tactical_action(
        self,
        agent: Any,
        model: Any,
        strategic_action: str,
    ) -> TacticalAction:
        """Map strategic decision to tactical action using scripted rules."""
        military_power = getattr(agent, "military_power", 0.5)
        stability = getattr(agent, "stability", 0.5)
        posture = getattr(agent, "posture", "Deescalate")

        neighbors = model.adjacency.get(getattr(agent, "region_id", ""), [])
        has_neighbors = len(neighbors) > 0

        if strategic_action == "Escalate":
            if military_power > 0.6:
                return TacticalAction.ATTACK
            else:
                return TacticalAction.RECON

        elif strategic_action == "Deescalate":
            if stability < 0.3:
                return TacticalAction.RETREAT
            else:
                return TacticalAction.DEFEND

        else:
            if has_neighbors:
                return TacticalAction.RECON
            return TacticalAction.HOLD

    def _get_tactical_reasoning(self, action: TacticalAction) -> str:
        """Get reasoning for tactical action."""
        return f"Scripted tactical response: {action.value}"

    def update_strategy(
        self,
        reward: float,
        done: bool,
    ) -> None:
        """Update RL strategy based on outcome."""
        if self.use_rl and self.rl_agent is not None:
            self.strategy_history.append({"reward": reward, "done": done})


def create_hybrid_ai(use_rl: bool = True) -> HierarchicalHybridAI:
    """Factory function to create hybrid AI system."""
    return HierarchicalHybridAI(use_rl=use_rl)
