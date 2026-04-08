"""Concrete state actor agent that uses Nash equilibrium to make decisions.

Supports multiple game types (escalation, trade, sanctions, alliance, military)
and integrates with the escalation ladder and economic model.
"""

from __future__ import annotations

import logging
from typing import Any

from shapely.geometry import base as shp_base

from strategify.agents.base import BaseActorAgent
from strategify.agents.factions import get_default_factions
from strategify.agents.military import MilitaryComponent
from strategify.config.settings import (
    CONTAGION_WEIGHT,
    INFLUENCE_WEIGHT,
    PERSONALITY_BIAS_BASE,
    RESOURCE_BASELINE,
)
from strategify.game_theory.crisis_games import (
    GAME_REGISTRY,
    get_game,
    get_game_actions,
)
from strategify.reasoning.strategies import DiplomacyStrategy

logger = logging.getLogger(__name__)


class StateActorAgent(BaseActorAgent):
    """A state-level actor that plays game-theoretic decisions each turn.

    Each step the agent:
    1. Evaluates the current situation (influence, economics, escalation pressure).
    2. Plays pairwise games against key opponents using multiple game types.
    3. Aggregates results to choose an overall posture.
    4. Updates its escalation level on the ladder.

    Parameters
    ----------
    unique_id, model, geometry, crs:
        Forwarded to ``BaseActorAgent``.
    """

    def __init__(
        self,
        unique_id: int,
        model: Any,
        geometry: shp_base.BaseGeometry,
        crs: str,
    ) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.posture: str = "Deescalate"

        # Will be provided or overridden by GeopolModel after creation
        if not hasattr(self, "region_id"):
            self.region_id = "unknown"
        self.role: str = "row"
        self.personality: str = "Neutral"
        self.capabilities: dict = {"military": 0.5, "economic": 0.5}
        self.last_opponent_action: str | None = None
        self._diplomacy_strategy: DiplomacyStrategy | None = None

        # Military capabilities
        self.military = MilitaryComponent(self)

        # Phase 7: Domestic Politics
        self.factions = get_default_factions()
        self.stability: float = 1.0

        # Multi-game: games this agent participates in
        self.active_games: list[str] = ["escalation"]
        if self.capabilities.get("military", 0.5) > 0.7:
            self.active_games.append("cyber")

    # ------------------------------------------------------------------
    # Decision-making
    # ------------------------------------------------------------------

    def decide(self) -> dict:
        """Sample an action using dynamic multi-game reasoning."""
        imap = self.model.influence_map
        if imap is None:
            from strategify.reasoning.influence import InfluenceMap

            imap = InfluenceMap(self.model)
            imap.compute()

        # 1. Spatial & Alliance Reasoning
        net_inf = imap.get_net_influence(self.region_id, self.unique_id)
        contagion = imap.get_contagion_level(self.region_id)
        resources = self.model.region_resources.get(self.region_id, RESOURCE_BASELINE)

        # 2. Economic features (if trade network exists)
        economic_bias = 0.0
        if hasattr(self.model, "trade_network") and self.model.trade_network is not None:
            econ = self.model.trade_network.get_economic_features(self.unique_id)
            economic_bias = econ.get("trade_balance", 0.0) * 0.5

        # 2b. OSINT features (if pipeline enabled)
        osint_bias = 0.0
        if self.model.osint_features:
            region_osint = self.model.osint_features.get(self.region_id, {})
            osint_bias = region_osint.get("tension_score", 0.0) * 0.5

        # 3. Escalation pressure (if ladder exists)
        escalation_pressure = 0.0
        if hasattr(self.model, "escalation_ladder") and self.model.escalation_ladder is not None:
            escalation_pressure = self.model.escalation_ladder.get_escalation_pressure(
                self.unique_id
            )

        # 4. Resource pressure (if env_manager exists)
        resource_pressure = 0.0
        if hasattr(self.model, "env_manager") and self.model.env_manager is not None:
            resource_pressure = self.model.env_manager.get_resource_pressure(self.region_id)

        # 5. Identify primary opponent
        rival_id = self._find_primary_rival(imap)
        if rival_id:
            rival_agent = self.model._agent_registry.get(rival_id)
            if rival_agent is None:
                # Fallback for non-registry agents (orgs, etc.)
                rival_agent = next(
                    (a for a in self.model.schedule.agents if a.unique_id == rival_id),
                    None,
                )
            if rival_agent is not None:
                self.last_opponent_action = rival_agent.posture

        # 5b. Military strength bias — agents with more/better units are more confident
        military_power = self.military.get_total_power()
        military_bias = min(1.0, military_power / 10.0) * 0.5  # 10 power = +0.5

        # 5c. Diplomacy Strategy (Axelrod-based)
        if self._diplomacy_strategy is None:
            self._diplomacy_strategy = DiplomacyStrategy(self.personality)
        strategy_action = self._diplomacy_strategy.decide(self.last_opponent_action)
        personality_bias = (
            PERSONALITY_BIAS_BASE if strategy_action == "Escalate" else -PERSONALITY_BIAS_BASE
        )

        # 6. Multi-game evaluation
        game_scores = self._evaluate_games(rival_id)

        # 6b. Coalition bias (if tracker exists)
        coalition_bias = 0.0
        if hasattr(self.model, "coalition_tracker") and self.model.coalition_tracker is not None:
            allies = self.model.coalition_tracker.get_coalition_allies(self.unique_id)
            if allies:
                # If we have coalition allies, we are biased towards de-escalation
                # (cooperation) as a baseline, assuming coalitions are cooperative.
                coalition_bias = -0.5

        # 7. Aggregate all signals
        adjustment = (
            (net_inf * INFLUENCE_WEIGHT)
            + (contagion * CONTAGION_WEIGHT)
            + (resources - RESOURCE_BASELINE)
            + personality_bias
            + economic_bias
            + osint_bias
            + coalition_bias
            + military_bias
            - (escalation_pressure * 2.0)
            + (resource_pressure * 1.5)
            + game_scores.get("escalation_bias", 0.0)
        )

        # 8. Use the primary game (escalation) for final decision
        game = get_game("escalation")
        actions = get_game_actions("escalation")

        A_adj = game.A.copy()
        B_adj = game.B.copy()

        if self.role == "row":
            A_adj[0, :] += adjustment
        else:
            B_adj[:, 0] += adjustment

        from strategify.game_theory.normal_form import NormalFormGame

        dynamic_game = NormalFormGame(A_adj, B_adj)
        sigma_row, sigma_col = dynamic_game.select_equilibrium()
        strategy = sigma_row if self.role == "row" else sigma_col
        chosen = dynamic_game.sample_action(strategy, actions)

        # 8b. Optional LLM override
        llm_engine = getattr(self.model, "llm_engine", None)
        if llm_engine is not None:
            state_packet = {
                "region_id": self.region_id,
                "posture": self.posture,
                "personality": self.personality,
                "capabilities": self.capabilities,
                "nash_action": chosen,
                "net_influence": net_inf,
                "contagion": contagion,
                "economic_bias": economic_bias,
                "osint_bias": osint_bias,
                "adjustment": adjustment,
            }
            llm_result = llm_engine.query_or_fallback(state_packet, fallback_action=chosen)
            if llm_result["action"] in actions:
                chosen = llm_result["action"]

        # 9. Determine escalation level change
        escalation_action = self._decide_escalation_level(adjustment, chosen)

        # 10. Update Internal Stability (Phase 7)
        self._update_stability(chosen)

        return {
            "action": chosen,
            "escalation_action": escalation_action,
            "game_scores": game_scores,
            "stability": self.stability,
        }

    def _find_primary_rival(self, imap) -> int | None:
        """Find the primary rival (highest non-allied influence)."""
        if imap is None or not hasattr(imap, "influence_data"):
            return None
        rival_id = None
        max_rival_inf = -1.0
        for uid, inf in imap.influence_data.get(self.region_id, {}).items():
            if (
                uid != self.unique_id
                and uid not in self.model.relations.get_allies(self.unique_id)
                and inf > max_rival_inf
            ):
                max_rival_inf = inf
                rival_id = uid

        # Fallback: pick any non-allied agent as a potential target
        if rival_id is None:
            for agent in self.model.schedule.agents:
                if (
                    agent.unique_id != self.unique_id
                    and agent.unique_id not in self.model.relations.get_allies(self.unique_id)
                ):
                    return agent.unique_id

        return rival_id

    def _evaluate_games(self, rival_id: int | None) -> dict[str, float]:
        """Evaluate all active games and return aggregated scores.

        Returns a dict with per-game biases that feed into the main adjustment.
        """
        scores: dict[str, float] = {}

        for game_name in self.active_games:
            if game_name not in GAME_REGISTRY:
                continue

            game = get_game(game_name)
            actions = get_game_actions(game_name)

            # Apply personality bias
            A_adj = game.A.copy()
            B_adj = game.B.copy()

            # Personality skews toward first action (aggressive) or second (cooperative)
            if self.personality == "Aggressor":
                bias = 0.5
            elif self.personality == "Pacifist":
                bias = -0.5
            else:
                bias = 0.0

            if self.role == "row":
                A_adj[0, :] += bias
            else:
                B_adj[:, 0] += bias

            from strategify.game_theory.normal_form import NormalFormGame

            dynamic_game = NormalFormGame(A_adj, B_adj)
            sigma_row, sigma_col = dynamic_game.select_equilibrium()
            strategy = sigma_row if self.role == "row" else sigma_col
            chosen = dynamic_game.sample_action(strategy, actions)

            # Score: positive if chose aggressive (first) action
            scores[f"{game_name}_choice"] = 1.0 if chosen == actions[0] else 0.0

        # Aggregate: escalation game drives the main bias
        if "escalation_choice" in scores:
            scores["escalation_bias"] = 1.0 if scores["escalation_choice"] == 1.0 else -1.0
        else:
            scores["escalation_bias"] = 0.0

        return scores

    def _decide_escalation_level(self, adjustment: float, action: str) -> str | None:
        """Decide whether to change escalation level on the ladder."""
        ladder = getattr(self.model, "escalation_ladder", None)
        if ladder is None:
            return None

        current_level = ladder.get_level(self.unique_id)

        # Escalate on the ladder if adjustment strongly positive
        if action == "Escalate" and adjustment > 1.0:
            from strategify.agents.escalation import EscalationLevel

            target = EscalationLevel(min(int(current_level) + 1, 3))
            ladder.set_level(self.unique_id, target)
            return f"escalate_to_{target.name}"

        # De-escalate on the ladder if adjustment strongly negative
        if action == "Deescalate" and adjustment < -1.0:
            from strategify.agents.escalation import EscalationLevel

            target = EscalationLevel(max(int(current_level) - 1, 0))
            ladder.set_level(self.unique_id, target)
            return f"deescalate_to_{target.name}"

        return None

    # ------------------------------------------------------------------
    # Action application
    # ------------------------------------------------------------------

    def _apply(self, action: dict) -> None:
        super()._apply(action)
        self.posture = action["action"]
        # Step military component (logistics, readiness recovery)
        self.military.step()

        # Phase 8: Cyber Warfare effects
        game_scores = action.get("game_scores", {})
        if game_scores.get("cyber_choice") == 1.0:  # 1.0 = CyberAttack
            # Find primary rival and hit their stability — O(1) via registry
            imap = self.model.influence_map
            rival_id = self._find_primary_rival(imap)
            if rival_id:
                rival_agent = self.model._agent_registry.get(rival_id)
                if rival_agent is None:
                    rival_agent = next(
                        (a for a in self.model.schedule.agents if a.unique_id == rival_id), None
                    )
                if rival_agent and hasattr(rival_agent, "stability"):
                    logger.info(
                        "Agent %s launched CyberAttack on %s!",
                        self.region_id,
                        rival_agent.region_id,
                    )
                    rival_agent.stability = max(0.0, rival_agent.stability - 0.05)

    def _update_stability(self, action: str) -> None:
        """Calculate and update political stability based on chosen action."""
        # Baseline stability = sum(faction power if supports action)
        support = sum(f.power for f in self.factions if f.supports(action))

        # Stability is a weighted moving average
        self.stability = (self.stability * 0.7) + (support * 0.3)

        # Phase 9: Resource pressure hits stability
        if hasattr(self.model, "env_manager"):
            pressure = self.model.env_manager.get_resource_pressure(self.region_id)
            self.stability = max(0.0, self.stability - (pressure * 0.05))

        # Low stability event
        if self.stability < 0.4:
            logger.warning(
                "Agent %s: Low political stability (%.2f)! Domestic reform triggered.",
                self.region_id,
                self.stability,
            )
            # Re-balance factions slightly as a 'reform'
            for f in self.factions:
                f.power = max(0.1, f.power + self.model.random.uniform(-0.1, 0.1))
            # Normalize faction powers so they sum to 1.0
            total = sum(f.power for f in self.factions) or 1.0
            for f in self.factions:
                f.power /= total
            self.stability = 0.5  # Reset slightly
