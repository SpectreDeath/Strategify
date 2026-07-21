"""Strategic Goal & Multi-Horizon Lookahead Planner.

Enables agents to select long-term strategic doctrines and simulate
multi-step forward lookahead tree searches to select optimal actions.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class StrategicDoctrine(Enum):
    """Long-term strategic doctrines for state actors."""

    HEGEMONY = "hegemony"  # Maximize regional military dominance
    BALANCE_OF_POWER = "balance_of_power"  # Prevent any single hegemon
    ECONOMIC_PREEMINENCE = "economic_preeminence"  # Maximize trade & wealth
    DEFENSIVE_TERRITORIAL = "defensive_territorial"  # Secure borders & stability
    ISOLATIONISM = "isolationism"  # Minimize foreign entanglements


class StrategicPlanner:
    """Multi-horizon lookahead planner for strategic decision-making.

    Parameters
    ----------
    agent : Any
        The StateActorAgent owning this planner.
    doctrine : StrategicDoctrine
        The long-term doctrine guiding evaluation metrics.
    lookahead_depth : int
        Number of forward simulation steps to evaluate (default: 3).
    """

    def __init__(
        self,
        agent: Any,
        doctrine: StrategicDoctrine = StrategicDoctrine.BALANCE_OF_POWER,
        lookahead_depth: int = 3,
    ) -> None:
        self.agent = agent
        self.doctrine = doctrine
        self.lookahead_depth = lookahead_depth
        self.active_plan: list[str] = []

    def evaluate_lookahead_payoff(self, action: str, depth: int = 3) -> float:
        """Evaluate expected cumulative payoff for an action over depth steps.

        Parameters
        ----------
        action : str
            The candidate action string (e.g. 'Invade', 'Deescalate', 'Trade').
        depth : int
            Steps of forward lookahead.

        Returns
        -------
        float
            Evaluated payoff score.
        """
        base_score = 0.0
        mil_cap = self.agent.capabilities.get("military", 0.5)
        econ_cap = self.agent.capabilities.get("economic", 0.5)
        stability = getattr(self.agent, "stability", 1.0)

        # Doctrine-specific weighting
        if self.doctrine == StrategicDoctrine.HEGEMONY:
            if action in ("Invade", "Escalate", "Deploy"):
                base_score += mil_cap * 2.0
            elif action == "Deescalate":
                base_score -= 0.5
        elif self.doctrine == StrategicDoctrine.ECONOMIC_PREEMINENCE:
            if action in ("Trade", "Cooperate", "Open"):
                base_score += econ_cap * 2.5
            elif action in ("Invade", "Sanctions"):
                base_score -= 1.0
        elif self.doctrine == StrategicDoctrine.DEFENSIVE_TERRITORIAL:
            if action in ("Patrol", "Fortify", "Deescalate"):
                base_score += stability * 1.5
            elif action == "Invade":
                base_score -= 1.5
        elif self.doctrine == StrategicDoctrine.ISOLATIONISM:
            if action == "Deescalate":
                base_score += 2.0
            elif action in ("Invade", "Deploy", "Sanctions"):
                base_score -= 2.0
        elif action == "Deploy":
            base_score += 1.0
        elif action == "Deescalate":
            base_score += 0.5

        # Discounted multi-step projection (decay factor gamma = 0.8)
        discounted_total = sum(base_score * (0.8**step) for step in range(depth))
        return discounted_total

    def select_best_action(self, candidate_actions: list[str]) -> str:
        """Select the action yielding the highest lookahead payoff.

        Parameters
        ----------
        candidate_actions : list[str]
            List of potential actions to evaluate.

        Returns
        -------
        str
            Optimal action according to lookahead search.
        """
        if not candidate_actions:
            return "Deescalate"

        scores = {act: self.evaluate_lookahead_payoff(act, self.lookahead_depth) for act in candidate_actions}
        best_action = max(scores, key=scores.get)
        logger.debug(
            "Agent %s (%s) selected action %s with score %.2f",
            self.agent.unique_id,
            self.doctrine.value,
            best_action,
            scores[best_action],
        )
        return best_action
