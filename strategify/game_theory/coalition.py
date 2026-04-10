"""N-player game dispatch engine for multi-actor geopolitical simulations.

Extends the 2-player normal-form framework to support pairwise dispatch
across N actors, coalition tracking, and multi-actor payoff aggregation.

Usage::

    from strategify.game_theory.coalition import PairwiseGameDispatchEngine

    engine = PairwiseGameDispatchEngine()
    results = engine.dispatch(agents, "escalation")
    # results[(uid_i, uid_j)] = (action_i, action_j, payoff_i, payoff_j)
"""

from __future__ import annotations

import logging
from itertools import combinations
from typing import Any

import numpy as np

from strategify.game_theory.crisis_games import GAME_ACTIONS, get_game
from strategify.game_theory.normal_form import NormalFormGame

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pairwise dispatch
# ---------------------------------------------------------------------------
class PairwiseGameDispatchEngine:
    """Dispatches normal-form games across all (N choose 2) agent pairs.

    For each pair, creates a game (optionally scaled by capabilities),
    finds the Nash equilibrium, and samples an action for each player.
    """

    def __init__(self) -> None:
        self._last_results: dict[tuple[int, int], PairResult] = {}

    def dispatch(
        self,
        agents: list[Any],
        game_name: str,
    ) -> dict[tuple[int, int], PairResult]:
        """Run pairwise games for all agent pairs.

        Parameters
        ----------
        agents:
            List of agents with ``unique_id``, ``capabilities``, ``role``,
            and ``personality`` attributes.
        game_name:
            Key into ``GAME_ACTIONS`` (e.g. ``"escalation"``).

        Returns
        -------
        dict[tuple[int, int], PairResult]
            ``{(uid_i, uid_j): PairResult}`` for every pair where
            ``uid_i < uid_j``.
        """
        actions = GAME_ACTIONS.get(game_name)
        if actions is None:
            raise KeyError(f"Unknown game '{game_name}'")

        base_game = get_game(game_name)
        results: dict[tuple[int, int], PairResult] = {}

        for agent_a, agent_b in combinations(agents, 2):
            # Scale payoffs by capabilities
            game = NormalFormGame.from_capabilities(
                base_game.A,
                base_game.B,
                agent_a.capabilities,
                agent_b.capabilities,
            )

            sigma_row, sigma_col = game.select_equilibrium()

            # Sample actions
            action_a = game.sample_action(sigma_row, actions)
            action_b = game.sample_action(sigma_col, actions)

            # Compute payoffs for the sampled action pair
            idx_a = actions.index(action_a)
            idx_b = actions.index(action_b)
            payoff_a = float(game.A[idx_a, idx_b])
            payoff_b = float(game.B[idx_a, idx_b])

            pair_key = tuple(sorted((agent_a.unique_id, agent_b.unique_id)))
            results[pair_key] = PairResult(
                uid_a=agent_a.unique_id,
                uid_b=agent_b.unique_id,
                action_a=action_a,
                action_b=action_b,
                payoff_a=payoff_a,
                payoff_b=payoff_b,
                sigma_a=sigma_row,
                sigma_b=sigma_col,
            )

        self._last_results = results
        return results

    @property
    def last_results(self) -> dict[tuple[int, int], PairResult]:
        """Return results from the most recent dispatch call."""
        return self._last_results


class PairResult:
    """Result of a single pairwise game.

    Attributes
    ----------
    uid_a, uid_b:
        Unique IDs of the two agents.
    action_a, action_b:
        Sampled action strings.
    payoff_a, payoff_b:
        Payoff values for the sampled action pair.
    sigma_a, sigma_b:
        Mixed strategy probability vectors.
    """

    __slots__ = (
        "uid_a",
        "uid_b",
        "action_a",
        "action_b",
        "payoff_a",
        "payoff_b",
        "sigma_a",
        "sigma_b",
    )

    def __init__(
        self,
        uid_a: int,
        uid_b: int,
        action_a: str,
        action_b: str,
        payoff_a: float,
        payoff_b: float,
        sigma_a: np.ndarray,
        sigma_b: np.ndarray,
    ) -> None:
        self.uid_a = uid_a
        self.uid_b = uid_b
        self.action_a = action_a
        self.action_b = action_b
        self.payoff_a = payoff_a
        self.payoff_b = payoff_b
        self.sigma_a = sigma_a
        self.sigma_b = sigma_b

    def __repr__(self) -> str:
        return (
            f"PairResult({self.uid_a}-{self.uid_b}: "
            f"{self.action_a}/{self.action_b} "
            f"payoffs=({self.payoff_a:.1f}, {self.payoff_b:.1f}))"
        )


# ---------------------------------------------------------------------------
# Coalition tracking
# ---------------------------------------------------------------------------
class CoalitionStateTracker:
    """Tracks coalition membership and stability across simulation steps.

    Coalitions are sets of agent unique IDs. The tracker maintains
    a graph of inter-agent cooperation scores derived from pairwise
    game results and alliance weights.
    """

    def __init__(self) -> None:
        # cooperation[(uid_a, uid_b)] → float in [-1, 1]
        self.cooperation_scores: dict[tuple[int, int], float] = {}
        # coalitions → list of sets of unique IDs
        self.coalitions: list[set[int]] = []
        self._coalition_threshold: float = 0.5

    def update(
        self,
        pair_results: dict[tuple[int, int], PairResult],
        alliance_weights: dict[tuple[int, int], float] | None = None,
    ) -> None:
        """Update cooperation scores from pairwise game results.

        Parameters
        ----------
        pair_results:
            Output from ``PairwiseGameDispatchEngine.dispatch()``.
        alliance_weights:
            Optional ``{(uid_a, uid_b): weight}`` from DiplomacyGraph.
        """
        for pair_key, result in pair_results.items():
            # In all crisis games, the first action is aggressive and the
            # second is cooperative:
            #   escalation: Escalate / Deescalate
            #   military:   Act / Restrain
            #   sanctions:  Impose / Comply
            #   trade:      Protect / Open
            #   alliance:   Commit(0) / Defect(1)  ← special case below
            aggressive_keywords = {"Escalate", "Act", "Impose", "Protect", "Defect"}
            coop_a = result.action_a not in aggressive_keywords
            coop_b = result.action_b not in aggressive_keywords

            if coop_a and coop_b:
                delta = 0.1  # Mutual cooperation
            elif not coop_a and not coop_b:
                delta = -0.1  # Mutual escalation/non-cooperation
            else:
                delta = -0.05  # Mixed outcome (exploitation)

            old = self.cooperation_scores.get(pair_key, 0.0)
            self.cooperation_scores[pair_key] = max(-1.0, min(1.0, old + delta))

            # Blend with alliance weight if provided
            if alliance_weights and pair_key in alliance_weights:
                aw = alliance_weights[pair_key]
                blended = 0.7 * self.cooperation_scores[pair_key] + 0.3 * aw
                self.cooperation_scores[pair_key] = max(-1.0, min(1.0, blended))

        # Rebuild coalitions from cooperation scores
        self._rebuild_coalitions()

    def _rebuild_coalitions(self) -> None:
        """Cluster agents into coalitions based on cooperation scores."""
        # Build adjacency of cooperating agents
        adj: dict[int, set[int]] = {}
        for (uid_a, uid_b), score in self.cooperation_scores.items():
            if score >= self._coalition_threshold:
                adj.setdefault(uid_a, set()).add(uid_b)
                adj.setdefault(uid_b, set()).add(uid_a)

        # Connected components → coalitions
        visited: set[int] = set()
        coalitions: list[set[int]] = []
        for uid in adj:
            if uid in visited:
                continue
            component: set[int] = set()
            stack = [uid]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                stack.extend(adj.get(node, set()) - visited)
            if len(component) >= 2:
                coalitions.append(component)
        self.coalitions = coalitions

    def get_coalition(self, agent_id: int) -> set[int] | None:
        """Return the coalition containing the given agent, or None."""
        for coalition in self.coalitions:
            if agent_id in coalition:
                return coalition
        return None

    def get_coalition_allies(self, agent_id: int) -> list[int]:
        """Return IDs of coalition-mates (excluding self)."""
        coalition = self.get_coalition(agent_id)
        if coalition is None:
            return []
        return [uid for uid in coalition if uid != agent_id]

    def summary(self) -> dict[str, Any]:
        """Return coalition state summary."""
        return {
            "n_coalitions": len(self.coalitions),
            "coalitions": [sorted(list(c)) for c in self.coalitions],
            "n_cooperation_edges": sum(1 for s in self.cooperation_scores.values() if s >= self._coalition_threshold),
        }


# ---------------------------------------------------------------------------
# Multi-actor payoff aggregation
# ---------------------------------------------------------------------------
class MultiActorPayoffComputer:
    """Aggregates pairwise payoffs into per-agent aggregate scores.

    Combines payoffs from all pairs involving each agent, weighted by
    optional alliance / cooperation weights.
    """

    @staticmethod
    def aggregate(
        pair_results: dict[tuple[int, int], PairResult],
        weights: dict[int, float] | None = None,
    ) -> dict[int, float]:
        """Compute aggregate payoff per agent.

        Parameters
        ----------
        pair_results:
            Output from ``PairwiseGameDispatchEngine.dispatch()``.
        weights:
            Optional ``{uid: weight}`` to scale each agent's payoff
            (e.g. from capability levels). If None, equal weights.

        Returns
        -------
        dict[int, float]
            ``{uid: aggregate_payoff}`` summed across all pairs.
        """
        agg: dict[int, float] = {}

        for _, result in pair_results.items():
            w_a = weights.get(result.uid_a, 1.0) if weights else 1.0
            w_b = weights.get(result.uid_b, 1.0) if weights else 1.0

            agg[result.uid_a] = agg.get(result.uid_a, 0.0) + result.payoff_a * w_a
            agg[result.uid_b] = agg.get(result.uid_b, 0.0) + result.payoff_b * w_b

        return agg

    @staticmethod
    def aggregate_to_bias(
        aggregate_payoffs: dict[int, float],
        agent_id: int,
    ) -> float:
        """Convert an agent's aggregate payoff to a decision bias.

        Returns a value in roughly [-2, 2] suitable for use as an
        adjustment signal in agent decision-making.
        """
        payoff = aggregate_payoffs.get(agent_id, 0.0)
        # Normalize: scale to [-2, 2] range
        return max(-2.0, min(2.0, payoff * 0.5))
