"""Tests for Phase 3: Strategic Diplomacy (memory, signaling, multilateral summits)."""

import random

import pytest

from strategify.reasoning.diplomacy_phase3 import (
    DiplomaticMemory,
    InteractionType,
    MultilateralSummit,
    SignalType,
    StrategicSignaling,
)
from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


@pytest.fixture
def memory(model):
    m = DiplomaticMemory(model, decay_rate=0.05)
    m.initialize()
    return m


@pytest.fixture
def signaling(model):
    s = StrategicSignaling(model)
    s.initialize()
    return s


# ---------------------------------------------------------------------------
# DiplomaticMemory
# ---------------------------------------------------------------------------


class TestDiplomaticMemory:
    def test_initial_state(self, memory):
        assert memory.summary()["total_entries"] == 0
        assert memory.summary()["agents_tracked"] == 4

    def test_record_interaction(self, memory, model):
        agents = list(model.schedule.agents)
        memory.record(
            agents[0].unique_id,
            agents[1].unique_id,
            InteractionType.COOPERATED,
            value=0.5,
        )
        assert memory.summary()["total_entries"] == 1

    def test_trust_score_positive(self, memory, model):
        agents = list(model.schedule.agents)
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        memory.record(uid_a, uid_b, InteractionType.COOPERATED)
        trust = memory.get_trust_score(uid_a, uid_b)
        assert trust > 0

    def test_trust_score_negative(self, memory, model):
        agents = list(model.schedule.agents)
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        memory.record(uid_a, uid_b, InteractionType.BETRAYED)
        trust = memory.get_trust_score(uid_a, uid_b)
        assert trust < 0

    def test_trust_score_no_memory(self, memory, model):
        agents = list(model.schedule.agents)
        assert memory.get_trust_score(agents[0].unique_id, agents[1].unique_id) == 0.0

    def test_memory_decays(self, memory, model):
        agents = list(model.schedule.agents)
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        memory.record(uid_a, uid_b, InteractionType.COOPERATED)
        initial_trust = memory.get_trust_score(uid_a, uid_b)
        # Simulate several steps
        for _ in range(10):
            model.schedule.steps += 1
            memory.step()
        decayed_trust = memory.get_trust_score(uid_a, uid_b)
        assert decayed_trust < initial_trust

    def test_promise_broken_stronger_than_betrayed(self, memory, model):
        agents = list(model.schedule.agents)
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        memory.record(uid_a, uid_b, InteractionType.PROMISE_BROKEN)
        trust_broken = memory.get_trust_score(uid_a, uid_b)

        memory2 = DiplomaticMemory(model)
        memory2.initialize()
        memory2.record(uid_a, uid_b, InteractionType.BETRAYED)
        trust_betrayed = memory2.get_trust_score(uid_a, uid_b)

        assert trust_broken < trust_betrayed

    def test_get_bias(self, memory, model):
        agents = list(model.schedule.agents)
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        memory.record(uid_a, uid_b, InteractionType.COOPERATED)
        bias = memory.get_bias(uid_a, uid_b)
        assert -0.5 <= bias <= 0.5

    def test_get_recent_interactions(self, memory, model):
        agents = list(model.schedule.agents)
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        for _ in range(10):
            memory.record(uid_a, uid_b, InteractionType.COOPERATED)
        recent = memory.get_recent_interactions(uid_a, n=3)
        assert len(recent) == 3

    def test_memory_in_model(self, model):
        assert model.diplomatic_memory is not None
        assert model.signaling is not None
        assert model.summit is not None


# ---------------------------------------------------------------------------
# StrategicSignaling
# ---------------------------------------------------------------------------


class TestStrategicSignaling:
    def test_initial_state(self, signaling):
        summary = signaling.summary()
        assert summary["total_signals"] == 0

    def test_send_threat(self, signaling, model):
        agents = list(model.schedule.agents)
        signal = signaling.send_signal(
            agents[0].unique_id,
            agents[1].unique_id,
            SignalType.THREAT,
            content="Back off or face consequences",
        )
        assert signal.signal_type == SignalType.THREAT
        assert signaling.summary()["total_signals"] == 1

    def test_send_promise(self, signaling, model):
        agents = list(model.schedule.agents)
        signal = signaling.send_signal(
            agents[0].unique_id,
            agents[1].unique_id,
            SignalType.PROMISE,
            content="We will cooperate if you do",
        )
        assert signal.signal_type == SignalType.PROMISE

    def test_credibility_initial(self, signaling, model):
        agents = list(model.schedule.agents)
        assert signaling.get_credibility(agents[0].unique_id) == 0.5

    def test_get_pending_signals(self, signaling, model):
        agents = list(model.schedule.agents)
        signaling.send_signal(
            agents[0].unique_id,
            agents[1].unique_id,
            SignalType.THREAT,
        )
        pending = signaling.get_pending_signals()
        assert len(pending) == 1
        assert pending[0].fulfilled is None

    def test_perception_modifier_threat(self, signaling, model):
        agents = list(model.schedule.agents)
        signaling.send_signal(
            agents[0].unique_id,
            agents[1].unique_id,
            SignalType.THREAT,
        )
        modifier = signaling.get_perception_modifier(agents[1].unique_id, agents[0].unique_id)
        assert modifier < 0  # threat makes observer cautious

    def test_perception_modifier_reassurance(self, signaling, model):
        agents = list(model.schedule.agents)
        signaling.send_signal(
            agents[0].unique_id,
            agents[1].unique_id,
            SignalType.REASSURANCE,
        )
        modifier = signaling.get_perception_modifier(agents[1].unique_id, agents[0].unique_id)
        assert modifier > 0  # reassurance relaxes observer


# ---------------------------------------------------------------------------
# MultilateralSummit
# ---------------------------------------------------------------------------


class TestMultilateralSummit:
    def test_two_player_summit(self, model):
        agents = list(model.schedule.agents)
        summit = MultilateralSummit(model)
        from strategify.game_theory.crisis_games import get_game

        base_game = get_game("escalation")
        result = summit.solve_summit([agents[0].unique_id, agents[1].unique_id], base_game)
        assert len(result) == 2
        for uid, action in result.items():
            assert action in ("Escalate", "Deescalate")

    def test_three_player_summit(self, model):
        agents = list(model.schedule.agents)
        summit = MultilateralSummit(model)
        from strategify.game_theory.crisis_games import get_game

        base_game = get_game("escalation")
        result = summit.solve_summit([a.unique_id for a in agents[:3]], base_game)
        assert len(result) == 3

    def test_four_player_summit(self, model):
        agents = list(model.schedule.agents)
        summit = MultilateralSummit(model)
        from strategify.game_theory.crisis_games import get_game

        base_game = get_game("escalation")
        result = summit.solve_summit([a.unique_id for a in agents], base_game)
        assert len(result) == 4

    def test_alliance_summit(self, model):
        agents = list(model.schedule.agents)
        summit = MultilateralSummit(model)
        result = summit.run_alliance_summit([a.unique_id for a in agents[:3]])
        assert "decisions" in result
        assert "consensus" in result
        assert "alliance_cohesion" in result
        assert 0.0 <= result["alliance_cohesion"] <= 1.0

    def test_single_participant(self, model):
        agents = list(model.schedule.agents)
        summit = MultilateralSummit(model)
        result = summit.solve_summit([agents[0].unique_id], None)
        assert result[agents[0].unique_id] == "Deescalate"


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------


class TestDiplomacyIntegration:
    def test_model_step_with_diplomacy(self, model):
        for _ in range(5):
            model.step()
        memory_summary = model.diplomatic_memory.summary()
        assert memory_summary["agents_tracked"] == 4

    def test_model_without_escalation_has_no_diplomacy(self):
        model = GeopolModel(enable_escalation_ladder=False)
        assert model.diplomatic_memory is None
        assert model.signaling is None
        assert model.summit is None

    def test_deterministic_with_diplomacy(self):
        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()
        for _ in range(5):
            m1.step()
            m2.step()
        p1 = {a.region_id: a.posture for a in m1.schedule.agents}
        p2 = {a.region_id: a.posture for a in m2.schedule.agents}
        assert p1 == p2
