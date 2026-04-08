"""Tests for N-player dispatch engine, coalition tracking, and payoff aggregation."""

import numpy as np
import pytest

from strategify.game_theory.coalition import (
    CoalitionStateTracker,
    MultiActorPayoffComputer,
    PairResult,
    PairwiseGameDispatchEngine,
)
from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


@pytest.fixture
def agents(model):
    return list(model.schedule.agents)


# ---------------------------------------------------------------------------
# PairwiseGameDispatchEngine
# ---------------------------------------------------------------------------


class TestPairwiseGameDispatchEngine:
    def test_dispatch_returns_results(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        assert len(results) == 6  # 4 choose 2 = 6 pairs

    def test_dispatch_pair_keys_sorted(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        for uid_a, uid_b in results:
            assert uid_a < uid_b

    def test_dispatch_pair_result_fields(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        for pair_key, result in results.items():
            assert isinstance(result, PairResult)
            assert result.uid_a == pair_key[0]
            assert result.uid_b == pair_key[1]
            assert result.action_a in ("Escalate", "Deescalate")
            assert result.action_b in ("Escalate", "Deescalate")
            assert isinstance(result.payoff_a, float)
            assert isinstance(result.payoff_b, float)
            assert result.sigma_a.shape == (2,)
            assert result.sigma_b.shape == (2,)

    def test_dispatch_all_game_types(self, agents):
        engine = PairwiseGameDispatchEngine()
        for game_name in ("escalation", "trade", "sanctions", "alliance", "military"):
            results = engine.dispatch(agents, game_name)
            assert len(results) == 6

    def test_dispatch_invalid_game(self, agents):
        engine = PairwiseGameDispatchEngine()
        with pytest.raises(KeyError, match="Unknown game"):
            engine.dispatch(agents, "nonexistent")

    def test_dispatch_deterministic(self, agents):
        import random

        random.seed(42)
        engine1 = PairwiseGameDispatchEngine()
        results1 = engine1.dispatch(agents, "escalation")

        random.seed(42)
        engine2 = PairwiseGameDispatchEngine()
        results2 = engine2.dispatch(agents, "escalation")

        for key in results1:
            assert results1[key].action_a == results2[key].action_a
            assert results1[key].action_b == results2[key].action_b

    def test_last_results(self, agents):
        engine = PairwiseGameDispatchEngine()
        assert engine.last_results == {}
        engine.dispatch(agents, "escalation")
        assert len(engine.last_results) == 6


# ---------------------------------------------------------------------------
# CoalitionStateTracker
# ---------------------------------------------------------------------------


class TestCoalitionStateTracker:
    def test_initial_state(self):
        tracker = CoalitionStateTracker()
        assert tracker.coalitions == []
        assert tracker.cooperation_scores == {}

    def test_update_creates_cooperation_scores(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        tracker = CoalitionStateTracker()
        tracker.update(results)
        assert len(tracker.cooperation_scores) > 0

    def test_coalition_summary(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        tracker = CoalitionStateTracker()
        tracker.update(results)
        summary = tracker.summary()
        assert "n_coalitions" in summary
        assert "coalitions" in summary
        assert isinstance(summary["coalitions"], list)

    def test_get_coalition(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        tracker = CoalitionStateTracker()
        tracker.update(results)
        # May or may not form coalitions depending on game results
        for agent in agents:
            coalition = tracker.get_coalition(agent.unique_id)
            if coalition is not None:
                assert agent.unique_id in coalition

    def test_get_coalition_allies_empty(self):
        tracker = CoalitionStateTracker()
        assert tracker.get_coalition_allies(999) == []

    def test_update_with_alliance_weights(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")

        # Create alliance weights
        weights = {}
        for pair_key in results:
            weights[pair_key] = 0.8  # strong alliance

        tracker = CoalitionStateTracker()
        tracker.update(results, alliance_weights=weights)
        assert len(tracker.cooperation_scores) > 0


# ---------------------------------------------------------------------------
# MultiActorPayoffComputer
# ---------------------------------------------------------------------------


class TestMultiActorPayoffComputer:
    def test_aggregate_returns_per_agent(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        agg = MultiActorPayoffComputer.aggregate(results)
        uids = {a.unique_id for a in agents}
        assert set(agg.keys()) == uids

    def test_aggregate_payoffs_sum(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        agg = MultiActorPayoffComputer.aggregate(results)

        # Each agent participates in 3 pairs, so aggregate should be sum of 3 payoffs
        for agent in agents:
            uid = agent.unique_id
            expected = 0.0
            for pair_key, result in results.items():
                if result.uid_a == uid:
                    expected += result.payoff_a
                elif result.uid_b == uid:
                    expected += result.payoff_b
            assert agg[uid] == pytest.approx(expected)

    def test_aggregate_with_weights(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        weights = {a.unique_id: 2.0 for a in agents}
        agg_weighted = MultiActorPayoffComputer.aggregate(results, weights=weights)
        agg_plain = MultiActorPayoffComputer.aggregate(results)
        for uid in agg_plain:
            assert agg_weighted[uid] == pytest.approx(agg_plain[uid] * 2.0)

    def test_aggregate_to_bias_range(self, agents):
        engine = PairwiseGameDispatchEngine()
        results = engine.dispatch(agents, "escalation")
        agg = MultiActorPayoffComputer.aggregate(results)
        for agent in agents:
            bias = MultiActorPayoffComputer.aggregate_to_bias(agg, agent.unique_id)
            assert -2.0 <= bias <= 2.0

    def test_aggregate_to_bias_zero_payoff(self):
        bias = MultiActorPayoffComputer.aggregate_to_bias({}, 999)
        assert bias == 0.0


# ---------------------------------------------------------------------------
# PairResult repr
# ---------------------------------------------------------------------------


class TestPairResult:
    def test_repr(self):
        r = PairResult(
            1, 2, "Escalate", "Deescalate", 5.0, 1.0, np.array([1.0, 0.0]), np.array([0.0, 1.0])
        )
        text = repr(r)
        assert "1-2" in text
        assert "Escalate" in text
        assert "Deescalate" in text
