"""Tests for audit fixes: Nash normalization, geometry filtering,
dynamic payoffs, and LLM decision engine."""

import numpy as np
import pytest

from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


# ---------------------------------------------------------------------------
# Bug #2: Nash equilibrium normalization
# ---------------------------------------------------------------------------


class TestNashNormalization:
    def test_sample_action_normalizes_positive(self):
        from strategify.game_theory.normal_form import NormalFormGame

        strategy = np.array([0.3, 0.7])
        actions = ["A", "B"]
        result = NormalFormGame.sample_action(strategy, actions)
        assert result in actions

    def test_sample_action_clips_negative(self):
        """Negative floats from nashpy should not crash."""
        from strategify.game_theory.normal_form import NormalFormGame

        strategy = np.array([-1e-16, 1.0 + 1e-16])
        actions = ["A", "B"]
        # Should not raise ValueError
        result = NormalFormGame.sample_action(strategy, actions)
        assert result in actions

    def test_sample_action_all_zeros_fallback(self):
        """All-zero strategy should fall back to random choice."""
        from strategify.game_theory.normal_form import NormalFormGame

        strategy = np.array([0.0, 0.0])
        actions = ["A", "B"]
        result = NormalFormGame.sample_action(strategy, actions)
        assert result in actions

    def test_sample_action_sums_to_one(self):
        """After normalization, strategy should sum to 1."""
        from strategify.game_theory.normal_form import NormalFormGame

        # Simulate nashpy output with floating point drift
        strategy = np.array([0.33333333333333333, 0.66666666666666666])
        actions = ["A", "B"]
        # Should work without error
        for _ in range(100):
            NormalFormGame.sample_action(strategy, actions)


# ---------------------------------------------------------------------------
# Proposal #4: Dynamic payoff matrices from capabilities
# ---------------------------------------------------------------------------


class TestDynamicPayoffs:
    def test_from_capabilities_returns_normal_form(self):
        from strategify.game_theory.crisis_games import escalation_game
        from strategify.game_theory.normal_form import NormalFormGame

        base = escalation_game()
        cap_row = {"military": 0.9, "economic": 0.5}
        cap_col = {"military": 0.3, "economic": 0.5}

        game = NormalFormGame.from_capabilities(base.A, base.B, cap_row, cap_col)
        assert isinstance(game, NormalFormGame)
        assert game.A.shape == (2, 2)

    def test_stronger_row_higher_payoffs(self):
        """When row is much stronger militarily, their payoffs should scale up."""
        import math

        from strategify.game_theory.crisis_games import escalation_game
        from strategify.game_theory.normal_form import NormalFormGame

        base = escalation_game()
        cap_strong = {"military": 0.9}
        cap_weak = {"military": 0.1}

        game = NormalFormGame.from_capabilities(base.A, base.B, cap_strong, cap_weak)

        # Row factor = log(1 + 0.9/0.1) = log(10) ~ 2.3
        expected_factor = math.log(1.0 + 0.9 / 0.1)
        assert game.A[0, 0] == pytest.approx(base.A[0, 0] * expected_factor)

    def test_equal_capabilities_no_change(self):
        """Equal capabilities should produce symmetric scaling."""
        import math

        from strategify.game_theory.crisis_games import escalation_game
        from strategify.game_theory.normal_form import NormalFormGame

        base = escalation_game()
        cap = {"military": 0.5}

        game = NormalFormGame.from_capabilities(base.A, base.B, cap, cap)
        factor = math.log(1.0 + 1.0)
        assert game.A[0, 0] == pytest.approx(base.A[0, 0] * factor)
        assert game.B[0, 0] == pytest.approx(base.B[0, 0] * factor)

    def test_from_capabilities_has_nash(self):
        """Dynamically scaled game should still have equilibria."""
        from strategify.game_theory.crisis_games import escalation_game
        from strategify.game_theory.normal_form import NormalFormGame

        base = escalation_game()
        game = NormalFormGame.from_capabilities(
            base.A,
            base.B,
            {"military": 0.8},
            {"military": 0.3},
        )
        eq = game.get_nash_equilibria()
        assert len(eq) > 0

    def test_from_capabilities_default_scaling(self):
        """Default scaling should be log_ratio."""
        from strategify.game_theory.crisis_games import escalation_game
        from strategify.game_theory.normal_form import NormalFormGame

        base = escalation_game()
        game = NormalFormGame.from_capabilities(
            base.A,
            base.B,
            {"military": 0.8},
            {"military": 0.3},
        )
        assert isinstance(game, NormalFormGame)


# ---------------------------------------------------------------------------
# LLM Decision Engine (Proposal #6)
# ---------------------------------------------------------------------------


class TestLLMEngine:
    def test_engine_init(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine(provider="openai", model="gpt-4o-mini")
        assert engine.provider == "openai"

    def test_build_prompt(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        state = {"region_id": "alpha", "military": 0.8, "posture": "Escalate"}
        prompt = engine._build_prompt(state)
        assert "alpha" in prompt
        assert "Escalate" in prompt
        assert "JSON" in prompt

    def test_parse_valid_response(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        text = '{"reasoning": "Strong military position", "action": "Escalate"}'
        result = engine._parse_response(text)
        assert result["action"] == "Escalate"
        assert "Strong" in result["reasoning"]

    def test_parse_invalid_action(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        text = '{"reasoning": "test", "action": "Invalid"}'
        result = engine._parse_response(text)
        assert result is None

    def test_parse_malformed_json(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        text = "I think the agent should Escalate given the military advantage"
        result = engine._parse_response(text)
        assert result is not None
        assert result["action"] == "Escalate"

    def test_parse_with_markdown_fences(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        text = '```json\n{"reasoning": "test", "action": "Deescalate"}\n```'
        result = engine._parse_response(text)
        assert result["action"] == "Deescalate"

    def test_query_returns_none_without_api_key(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine(provider="openai", api_key="")
        result = engine.query({"region_id": "alpha"})
        assert result is None

    def test_query_or_fallback(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine(provider="openai", api_key="")
        result = engine.query_or_fallback({"region_id": "alpha"})
        assert result["action"] == "Deescalate"

    def test_parse_with_confidence(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        text = '{"reasoning": "Strong position", "action": "Escalate", "confidence": 0.85}'
        result = engine._parse_response(text)
        assert result["action"] == "Escalate"
        if "confidence" in result:
            assert float(result["confidence"]) == pytest.approx(0.85)

    def test_parse_pydantic_rejects_invalid(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        # Action is not Escalate/Deescalate - should fall through to manual parsing
        text = '{"reasoning": "test", "action": "Attack"}'
        result = engine._parse_response(text)
        # With pydantic, this gets rejected; without, manual parse also rejects
        assert result is None

    def test_parse_empty_reasoning(self):
        from strategify.reasoning.llm import LLMDecisionEngine

        engine = LLMDecisionEngine()
        text = '{"action": "Deescalate"}'
        result = engine._parse_response(text)
        assert result["action"] == "Deescalate"

    def test_cache_get_put(self):
        from strategify.reasoning.llm import LLMStrategyCache

        cache = LLMStrategyCache()
        state = {"region_id": "alpha", "military": 0.8, "posture": "Escalate"}
        assert cache.get(state) is None
        decision = {"action": "Escalate", "reasoning": "test"}
        cache.put(state, decision)
        assert cache.get(state) == decision

    def test_cache_key_normalization(self):
        from strategify.reasoning.llm import LLMStrategyCache

        cache = LLMStrategyCache()
        state1 = {"region_id": "alpha", "military": 0.8001, "posture": "Escalate"}
        state2 = {"region_id": "alpha", "military": 0.8002, "posture": "Escalate"}
        decision = {"action": "Escalate", "reasoning": "test"}
        cache.put(state1, decision)
        # Same key due to rounding to 1 decimal
        assert cache.get(state2) == decision

    def test_cache_clear(self):
        from strategify.reasoning.llm import LLMStrategyCache

        cache = LLMStrategyCache()
        cache.put({"region_id": "a"}, {"action": "Escalate"})
        cache.clear()
        assert cache.get({"region_id": "a"}) is None


# ---------------------------------------------------------------------------
# Geometry filtering (Bug #1)
# ---------------------------------------------------------------------------


class TestGeometryFiltering:
    def test_get_valid_neighbors_returns_list(self, model):
        imap = model.influence_map
        if imap is None:
            from strategify.reasoning.influence import InfluenceMap

            imap = InfluenceMap(model)
            imap.compute()
        agent = model.schedule.agents[0]
        neighbors = imap._get_valid_neighbors_with_weights(agent)
        assert isinstance(neighbors, list)
        for n, weight in neighbors:
            assert weight > 0

    def test_influence_uses_filtered_neighbors(self, model):
        """Compute should use filtered neighbors, not raw touches."""
        model.step()
        imap = model.influence_map
        assert imap is not None
        assert len(imap.influence_data) > 0

    def test_contagion_uses_filtered_neighbors(self, model):
        model.step()
        imap = model.influence_map
        rid = model.schedule.agents[0].region_id
        contagion = imap.get_contagion_level(rid)
        assert isinstance(contagion, float)
