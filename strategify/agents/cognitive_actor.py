from __future__ import annotations

import logging
from typing import Any

from strategify.agents.state_actor import StateActorAgent
from strategify.reasoning.llm import LLMDecisionEngine

logger = logging.getLogger(__name__)

class CognitiveActorAgent(StateActorAgent):
    """An advanced state actor that relies on an LLM, Prolog, and Clojure for decisions.
    
    This agent overrides the default Nash equilibrium decision matrix and delegates
    the strategic evaluation entirely to an AI orchestrator (built on LLMs).
    """

    def __init__(self, unique_id: int, model: Any, **kwargs: Any) -> None:
        super().__init__(unique_id, model, **kwargs)
        self.decision_engine = LLMDecisionEngine(provider="openai", model="gpt-4o-mini")

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
        else:
            if self.posture in ["Invade", "Escalate"]:
                self.posture = "Withdraw"
            else:
                self.posture = "Observe"
                
        return {"action": action_str, "reasoning": reasoning}
