"""Phase 3: Strategic Diplomacy — memory, signaling, and multilateral summits.

Provides three components that extend the base DiplomacyGraph with cognitive
and multi-agent negotiation capabilities:

- ``DiplomaticMemory``: Tracks historical interactions (betrayals, aid,
  broken promises) that bias future coalition weights.
- ``StrategicSignaling``: Non-binding threat/promise signals that influence
  opponent perception before game-theoretic dispatch.
- ``MultilateralSummit``: 3-4 player game solver with heuristic fallback
  for alliance/NATO/BRICS scenarios.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Any

from strategify.game_theory.normal_form import NormalFormGame

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Diplomatic Memory
# ---------------------------------------------------------------------------


class InteractionType(Enum):
    """Types of historical diplomatic interactions."""

    COOPERATED = "cooperated"
    BETRAYED = "betrayed"
    AIDED = "aided"
    THREATENED = "threatened"
    PROMISE_KEPT = "promise_kept"
    PROMISE_BROKEN = "promise_broken"
    SANCTIONED = "sanctioned"


@dataclass
class MemoryEntry:
    """A single historical interaction record."""

    step: int
    partner_id: int
    interaction: InteractionType
    value: float = 0.0  # magnitude of the interaction
    detail: str = ""


class DiplomaticMemory:
    """Tracks historical interactions between agents.

    Memory decays over time and biases future cooperation/trust scores.
    Each agent has its own memory ledger keyed by partner ID.

    Parameters
    ----------
    model:
        The parent GeopolModel.
    decay_rate:
        Per-step decay factor for memory influence (0.0 = no decay,
        1.0 = instant forget). Default 0.05 (5% per step).
    """

    def __init__(self, model: Any, decay_rate: float = 0.05) -> None:
        self.model = model
        self.decay_rate = decay_rate
        # _memory[agent_uid][partner_uid] = list[MemoryEntry]
        self._memory: dict[int, dict[int, list[MemoryEntry]]] = {}

    def initialize(self) -> None:
        """Set up empty memory for all agents."""
        for agent in self.model.schedule.agents:
            self._memory[agent.unique_id] = {}

    def record(
        self,
        agent_id: int,
        partner_id: int,
        interaction: InteractionType,
        value: float = 0.0,
        detail: str = "",
    ) -> None:
        """Record a diplomatic interaction.

        Parameters
        ----------
        agent_id:
            The agent who experienced the interaction.
        partner_id:
            The other agent involved.
        interaction:
            Type of interaction.
        value:
            Magnitude/importance of the interaction.
        detail:
            Optional description.
        """
        step = self.model.schedule.steps
        entry = MemoryEntry(
            step=step,
            partner_id=partner_id,
            interaction=interaction,
            value=value,
            detail=detail,
        )
        self._memory.setdefault(agent_id, {}).setdefault(partner_id, []).append(entry)

    def step(self) -> None:
        """Decay old memories. Call once per simulation step."""
        current_step = self.model.schedule.steps
        for agent_memories in self._memory.values():
            for partner_id, entries in agent_memories.items():
                # Remove entries older than 50 steps (memory horizon)
                agent_memories[partner_id] = [e for e in entries if current_step - e.step <= 50]

    def get_trust_score(self, agent_id: int, partner_id: int) -> float:
        """Compute a trust score in [-1, 1] based on memory.

        Positive = trustworthy (cooperation, aid, kept promises).
        Negative = untrustworthy (betrayal, broken promises, threats).
        Decayed by time elapsed since each interaction.
        """
        entries = self._memory.get(agent_id, {}).get(partner_id, [])
        if not entries:
            return 0.0

        current_step = self.model.schedule.steps
        score = 0.0

        for entry in entries:
            age = current_step - entry.step
            decay = (1.0 - self.decay_rate) ** age

            if entry.interaction == InteractionType.COOPERATED:
                score += 0.1 * decay
            elif entry.interaction == InteractionType.BETRAYED:
                score -= 0.3 * decay
            elif entry.interaction == InteractionType.AIDED:
                score += 0.15 * decay
            elif entry.interaction == InteractionType.THREATENED:
                score -= 0.2 * decay
            elif entry.interaction == InteractionType.PROMISE_KEPT:
                score += 0.2 * decay
            elif entry.interaction == InteractionType.PROMISE_BROKEN:
                score -= 0.4 * decay
            elif entry.interaction == InteractionType.SANCTIONED:
                score -= 0.25 * decay

        return max(-1.0, min(1.0, score))

    def get_bias(self, agent_id: int, partner_id: int) -> float:
        """Return a decision bias from memory, in [-0.5, 0.5].

        Suitable for adding to the agent's adjustment calculation.
        Positive bias encourages cooperation, negative encourages aggression.
        """
        trust = self.get_trust_score(agent_id, partner_id)
        return trust * 0.5

    def get_recent_interactions(self, agent_id: int, n: int = 5) -> list[MemoryEntry]:
        """Return the N most recent interactions for an agent."""
        all_entries = []
        for entries in self._memory.get(agent_id, {}).values():
            all_entries.extend(entries)
        all_entries.sort(key=lambda e: e.step, reverse=True)
        return all_entries[:n]

    def summary(self) -> dict[str, Any]:
        """Return memory system summary."""
        total_entries = sum(
            len(entries) for agent_mem in self._memory.values() for entries in agent_mem.values()
        )
        return {
            "total_entries": total_entries,
            "agents_tracked": len(self._memory),
            "decay_rate": self.decay_rate,
        }


# ---------------------------------------------------------------------------
# Strategic Signaling
# ---------------------------------------------------------------------------


class SignalType(Enum):
    """Types of non-binding diplomatic signals."""

    THREAT = "threat"
    PROMISE = "promise"
    WARNING = "warning"
    REASSURANCE = "reassurance"


@dataclass
class Signal:
    """A non-binding diplomatic signal between agents."""

    sender_id: int
    receiver_id: int
    signal_type: SignalType
    step: int
    content: str = ""
    credibility: float = 0.5  # 0 = not credible, 1 = fully credible
    fulfilled: bool | None = None  # None = pending, True/False = resolved


class StrategicSignaling:
    """Manages non-binding diplomatic signals (cheap talk).

    Agents can send threats or promises before game-theoretic dispatch.
    Signals don't directly alter payoffs but influence perception and
    can be tracked for credibility scoring.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self._signals: list[Signal] = []
        self._credibility: dict[int, float] = {}  # uid → credibility score

    def initialize(self) -> None:
        """Set up credibility tracking for all agents."""
        for agent in self.model.schedule.agents:
            self._credibility[agent.unique_id] = 0.5

    def send_signal(
        self,
        sender_id: int,
        receiver_id: int,
        signal_type: SignalType,
        content: str = "",
    ) -> Signal:
        """Send a non-binding signal to another agent.

        Parameters
        ----------
        sender_id:
            Sending agent's unique ID.
        receiver_id:
            Receiving agent's unique ID.
        signal_type:
            Type of signal.
        content:
            Optional description.

        Returns
        -------
        Signal
            The created signal object.
        """
        step = self.model.schedule.steps
        credibility = self._credibility.get(sender_id, 0.5)
        signal = Signal(
            sender_id=sender_id,
            receiver_id=receiver_id,
            signal_type=signal_type,
            step=step,
            content=content,
            credibility=credibility,
        )
        self._signals.append(signal)

        # Record in memory if available
        memory = getattr(self.model, "diplomatic_memory", None)
        if memory is not None and signal_type == SignalType.THREAT:
            memory.record(
                receiver_id,
                sender_id,
                InteractionType.THREATENED,
                value=credibility,
                detail=content,
            )

        return signal

    def resolve_signals(self) -> None:
        """Check pending signals against actual outcomes and update credibility.

        Called at the end of each step to evaluate whether threats/promises
        were fulfilled.
        """
        current_step = self.model.schedule.steps
        agents_by_uid = {a.unique_id: a for a in self.model.schedule.agents}

        for signal in self._signals:
            if signal.fulfilled is not None:
                continue  # already resolved
            if signal.step >= current_step:
                continue  # too recent to evaluate

            sender = agents_by_uid.get(signal.sender_id)
            receiver = agents_by_uid.get(signal.receiver_id)
            if sender is None or receiver is None:
                continue

            # Evaluate based on signal type
            if signal.signal_type == SignalType.THREAT:
                # Threat fulfilled if receiver de-escalated
                if receiver.posture == "Deescalate":
                    signal.fulfilled = True
                    self._adjust_credibility(signal.sender_id, 0.05)
                elif receiver.posture == "Escalate":
                    signal.fulfilled = False
                    self._adjust_credibility(signal.sender_id, -0.1)

            elif signal.signal_type == SignalType.PROMISE:
                # Promise fulfilled if sender cooperated (de-escalated)
                if sender.posture == "Deescalate":
                    signal.fulfilled = True
                    self._adjust_credibility(signal.sender_id, 0.05)
                    memory = getattr(self.model, "diplomatic_memory", None)
                    if memory is not None:
                        memory.record(
                            receiver.posture == "Deescalate",
                            signal.sender_id,
                            InteractionType.PROMISE_KEPT,
                        )
                else:
                    signal.fulfilled = False
                    self._adjust_credibility(signal.sender_id, -0.1)
                    memory = getattr(self.model, "diplomatic_memory", None)
                    if memory is not None:
                        memory.record(
                            signal.receiver_id,
                            signal.sender_id,
                            InteractionType.PROMISE_BROKEN,
                        )

    def _adjust_credibility(self, agent_id: int, delta: float) -> None:
        """Adjust an agent's credibility score."""
        current = self._credibility.get(agent_id, 0.5)
        self._credibility[agent_id] = max(0.0, min(1.0, current + delta))

    def get_credibility(self, agent_id: int) -> float:
        """Return an agent's current credibility score."""
        return self._credibility.get(agent_id, 0.5)

    def get_pending_signals(self, agent_id: int | None = None) -> list[Signal]:
        """Return unresolved signals, optionally filtered by agent."""
        return [
            s
            for s in self._signals
            if s.fulfilled is None
            and (agent_id is None or s.sender_id == agent_id or s.receiver_id == agent_id)
        ]

    def get_perception_modifier(self, observer_id: int, target_id: int) -> float:
        """Return a perception modifier based on signals from target.

        Negative = target has been threatening (observer should be cautious).
        Positive = target has been reassuring (observer can relax).
        """
        recent = [
            s
            for s in self._signals
            if s.sender_id == target_id
            and s.receiver_id == observer_id
            and self.model.schedule.steps - s.step <= 5
        ]
        modifier = 0.0
        for s in recent:
            if s.signal_type == SignalType.THREAT:
                modifier -= 0.2 * s.credibility
            elif s.signal_type == SignalType.REASSURANCE:
                modifier += 0.15 * s.credibility
            elif s.signal_type == SignalType.WARNING:
                modifier -= 0.1 * s.credibility
        return max(-0.5, min(0.5, modifier))

    def summary(self) -> dict[str, Any]:
        """Return signaling system summary."""
        pending = len([s for s in self._signals if s.fulfilled is None])
        resolved = len([s for s in self._signals if s.fulfilled is not None])
        return {
            "total_signals": len(self._signals),
            "pending": pending,
            "resolved": resolved,
            "avg_credibility": (sum(self._credibility.values()) / max(1, len(self._credibility))),
        }


# ---------------------------------------------------------------------------
# Multilateral Summit
# ---------------------------------------------------------------------------


class MultilateralSummit:
    """Solves N-player games for alliance and coalition scenarios.

    Uses a heuristic approximation for N > 2 players by computing
    pairwise payoffs and aggregating via coalition membership weights.
    Falls back to the existing 2-player Nash solver embedded in each
    pairwise interaction.
    """

    def __init__(self, model: Any) -> None:
        self.model = model

    def solve_summit(
        self,
        participant_ids: list[int],
        base_game: NormalFormGame,
        coalition_weights: dict[tuple[int, int], float] | None = None,
    ) -> dict[int, str]:
        """Solve a multilateral game for a group of participants.

        For 2 participants, uses direct Nash equilibrium.
        For 3-4 participants, uses pairwise dispatch with coalition-weighted
        aggregation.

        Parameters
        ----------
        participant_ids:
            List of agent unique IDs participating in the summit.
        base_game:
            The 2-player base game to apply pairwise.
        coalition_weights:
            Optional ``{(uid_a, uid_b): weight}`` for coalition bias.

        Returns
        -------
        dict[int, str]
            ``{agent_id: action}`` for each participant.
        """
        n = len(participant_ids)
        if n < 2:
            return {uid: "Deescalate" for uid in participant_ids}

        if n == 2:
            return self._solve_pair(participant_ids[0], participant_ids[1], base_game)

        # N > 2: pairwise dispatch with aggregation
        actions_map = list(GAME_ACTIONS_FALLBACK)
        vote_scores: dict[int, dict[str, float]] = {
            uid: {a: 0.0 for a in actions_map} for uid in participant_ids
        }

        for uid_a, uid_b in combinations(participant_ids, 2):
            pair_result = self._solve_pair(uid_a, uid_b, base_game)
            weight = 1.0
            if coalition_weights:
                pair_key = tuple(sorted((uid_a, uid_b)))
                weight = coalition_weights.get(pair_key, 1.0)

            action_a = pair_result[uid_a]
            action_b = pair_result[uid_b]
            vote_scores[uid_a][action_a] += weight
            vote_scores[uid_b][action_b] += weight

        # Each agent picks the action with highest weighted vote
        result = {}
        for uid in participant_ids:
            scores = vote_scores[uid]
            result[uid] = max(scores, key=scores.get)

        return result

    def _solve_pair(self, uid_a: int, uid_b: int, base_game: NormalFormGame) -> dict[int, str]:
        """Solve a 2-player sub-game."""
        actions = GAME_ACTIONS_FALLBACK
        sigma_row, sigma_col = base_game.select_equilibrium()
        action_a = base_game.sample_action(sigma_row, actions)
        action_b = base_game.sample_action(sigma_col, actions)
        return {uid_a: action_a, uid_b: action_b}

    def run_alliance_summit(
        self,
        alliance_members: list[int],
        external_threat_id: int | None = None,
    ) -> dict[str, Any]:
        """Run a summit for an alliance facing an external threat.

        Parameters
        ----------
        alliance_members:
            Agent IDs in the alliance.
        external_threat_id:
            Optional agent ID of the external threat.

        Returns
        -------
        dict
            ``{"decisions": {uid: action}, "consensus": bool, "alliance_cohesion": float}``
        """
        from strategify.game_theory.crisis_games import get_game

        base_game = get_game("escalation")
        decisions = self.solve_summit(alliance_members, base_game)

        # Check consensus
        actions = [decisions[uid] for uid in alliance_members]
        consensus = len(set(actions)) == 1

        # Alliance cohesion: fraction that chose the majority action
        if actions:
            majority_action = max(set(actions), key=actions.count)
            cohesion = actions.count(majority_action) / len(actions)
        else:
            cohesion = 1.0

        return {
            "decisions": decisions,
            "consensus": consensus,
            "alliance_cohesion": cohesion,
        }


# Fallback actions for summit when game actions aren't available
GAME_ACTIONS_FALLBACK = ["Escalate", "Deescalate"]
