from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from strategify.agents.state_actor import StateActorAgent
from strategify.reasoning.llm import LLMDecisionEngine

logger = logging.getLogger(__name__)

_MAX_LOG_ENTRIES = 100


class CognitiveActorAgent(StateActorAgent):
    """An advanced state actor that relies on an LLM, Prolog, and Clojure for decisions.

    This agent overrides the default Nash equilibrium decision matrix and delegates
    the strategic evaluation entirely to an AI orchestrator (built on LLMs).
    """

    def __init__(self, unique_id: int, model: Any, **kwargs: Any) -> None:
        super().__init__(unique_id, model, **kwargs)
        self.decision_engine = LLMDecisionEngine(provider="openai", model="gpt-4o-mini")
        # XAI state: rolling audit log and live epistemic beliefs
        self.decision_log: list[dict[str, Any]] = []
        self.epistemic_beliefs: dict[str, Any] = {}

    def decide(self) -> dict[str, Any]:
        """Override the game-theoretic decider with a cognitive reasoning engine."""

        # Build the full subjective state packet
        state_packet = {
            "region_id": self.region_id,
            "military": self.military.get_total_power(),
            "economic": self.capabilities.get("economic", 0.5),
            "posture": self.posture,
            "escalation_level": getattr(self, "escalation_level", 0.0),
            "personality": self.personality,
            "un_seat": getattr(self, "un_seat_type", "Non-Permanent"),
            "health_level": self.demographics.health_index if hasattr(self, "demographics") else 1.0,
        }

        # Gather Osint and Intelligence
        if self.model.osint_pipeline:
            # Optionally summarize osint
            pass

        # Add relationships
        allies = self.model.relations.get_allies(self.unique_id)
        enemies = self.model.relations.get_rivals(self.unique_id)
        state_packet["allies"] = [self.model.schedule.agents[a].region_id for a in allies]
        state_packet["enemies"] = [self.model.schedule.agents[e].region_id for e in enemies]

        # Snapshot epistemic beliefs for XAI
        self.epistemic_beliefs = {
            "posture": self.posture,
            "escalation_level": state_packet["escalation_level"],
            "military_power": round(state_packet["military"], 3),
            "economic_power": round(state_packet["economic"], 3),
            "ally_count": len(state_packet["allies"]),
            "enemy_count": len(state_packet["enemies"]),
            "personality": self.personality,
        }

        # Query the orchestration engine
        logger.info(f"[{self.region_id}] Querying Cognitive Engine...")
        decision_result = self.decision_engine.query_or_fallback(state_packet)

        # Map the LLM action back to simulation postures
        action_str = decision_result.get("action", "Deescalate")
        reasoning = decision_result.get("reasoning", "")

        logger.info(f"[{self.region_id}] Cognitive Decision: {action_str} - Reason: {reasoning}")

        if action_str == "Escalate":
            if self.posture == "Observe":
                self.posture = "Deploy"
            elif self.posture == "Deploy":
                self.posture = "Escalate"
            elif self.posture == "Escalate":
                self.posture = "Invade"
        elif self.posture in ["Invade", "Escalate"]:
            self.posture = "Withdraw"
        else:
            self.posture = "Observe"

        # Append to rolling decision audit log
        log_entry: dict[str, Any] = {
            "step": self.model.schedule.steps,
            "timestamp": datetime.now(UTC).isoformat(),
            "action": action_str,
            "new_posture": self.posture,
            "reasoning": reasoning,
            "prompt_snippet": f"Region: {self.region_id}. Posture: {state_packet['posture']}. Military: {state_packet['military']:.2f}.",
        }
        self.decision_log.append(log_entry)
        if len(self.decision_log) > _MAX_LOG_ENTRIES:
            self.decision_log = self.decision_log[-_MAX_LOG_ENTRIES:]

        return {"action": action_str, "reasoning": reasoning}
