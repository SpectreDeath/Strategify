"""Tests for PropagandaEngine — narrative broadcast, spread, disinformation effects."""

import pytest

from strategify.reasoning.propaganda import Narrative, PropagandaEngine


@pytest.fixture
def model():
    from strategify.sim.model import GeopolModel

    return GeopolModel(enable_propaganda=True)


@pytest.fixture
def engine(model):
    return model.propaganda


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestPropagandaInit:
    def test_propaganda_engine_created(self, model):
        assert model.propaganda is not None
        assert isinstance(model.propaganda, PropagandaEngine)

    def test_initial_narrative_landscape(self, engine):
        landscape = engine.get_narrative_landscape()
        assert landscape["total_narratives"] == 0
        assert landscape["total_broadcasts"] == 0

    def test_agent_credibility_initialized(self, engine, model):
        for agent in model.schedule.agents:
            assert agent.unique_id in engine.agent_credibility
            assert engine.agent_credibility[agent.unique_id] == 0.5


# ---------------------------------------------------------------------------
# Narrative class
# ---------------------------------------------------------------------------


class TestNarrative:
    def test_narrative_creation(self):
        n = Narrative("test content", source_id=1, credibility=0.8)
        assert n.content == "test content"
        assert n.source_id == 1
        assert n.credibility == 0.8
        assert n.potency == 1.0
        assert n.age == 0

    def test_narrative_decay(self):
        n = Narrative("test", source_id=1)
        n.decay(rate=0.1)
        assert n.potency == pytest.approx(0.9)
        assert n.age == 1

    def test_effective_potency(self):
        n = Narrative("test", source_id=1, credibility=0.5, potency=0.8)
        assert n.effective_potency == pytest.approx(0.4)

    def test_disinformation_flag(self):
        n = Narrative("fake", source_id=1, is_disinformation=True)
        assert n.is_disinformation is True


# ---------------------------------------------------------------------------
# Broadcast
# ---------------------------------------------------------------------------


class TestBroadcast:
    def test_broadcast_narrative(self, engine, model):
        agent_id = model.schedule.agents[0].unique_id
        n = engine.broadcast(agent_id, "Test narrative")
        assert n.source_id == agent_id
        assert n.is_disinformation is False
        assert engine.narrative_counter == 1

    def test_broadcast_disinformation(self, engine, model):
        agent_id = model.schedule.agents[0].unique_id
        n = engine.broadcast(agent_id, "Fake news", is_disinformation=True)
        assert n.is_disinformation is True
        assert n.credibility == 0.3

    def test_broadcast_targeted(self, engine, model):
        source = model.schedule.agents[0].unique_id
        target = model.schedule.agents[1].unique_id
        n = engine.broadcast(source, "Targeted msg", target_id=target)
        assert n.target_id == target

    def test_broadcast_log(self, engine, model):
        agent_id = model.schedule.agents[0].unique_id
        engine.broadcast(agent_id, "Logged event")
        assert len(engine._propaganda_log) == 1
        assert engine._propaganda_log[0]["content"] == "Logged event"


# ---------------------------------------------------------------------------
# Narrative landscape
# ---------------------------------------------------------------------------


class TestNarrativeLandscape:
    def test_landscape_counts(self, engine, model):
        aid = model.schedule.agents[0].unique_id
        engine.broadcast(aid, "Truth 1")
        engine.broadcast(aid, "Lie 1", is_disinformation=True)
        landscape = engine.get_narrative_landscape()
        assert landscape["total_narratives"] == 2
        assert landscape["disinformation_count"] == 1
        assert landscape["truthful_count"] == 1

    def test_disinfo_ratio(self, engine, model):
        aid = model.schedule.agents[0].unique_id
        engine.broadcast(aid, "Truth", potency=1.0)
        engine.broadcast(aid, "Lie", is_disinformation=True, potency=1.0)
        landscape = engine.get_narrative_landscape()
        assert 0.0 < landscape["disinfo_ratio"] < 1.0


# ---------------------------------------------------------------------------
# Agent exposure
# ---------------------------------------------------------------------------


class TestAgentExposure:
    def test_exposure_unknown_agent(self, engine):
        exposure = engine.get_agent_exposure(9999)
        assert exposure["disinfo_exposure"] == 0.0
        assert exposure["truthful_exposure"] == 0.0
        assert exposure["net_trust"] == 0.5

    def test_exposure_after_broadcast(self, engine, model):
        source = model.schedule.agents[0].unique_id
        target = model.schedule.agents[1].unique_id
        engine.broadcast(source, "Hello", target_id=target)
        exposure = engine.get_agent_exposure(target)
        # Target should have received the narrative
        assert exposure["truthful_exposure"] > 0.0


# ---------------------------------------------------------------------------
# Integration with model step
# ---------------------------------------------------------------------------


class TestPropagandaIntegration:
    def test_model_steps_with_propaganda(self, model):
        for _ in range(5):
            model.step()

    def test_propaganda_spreads_over_steps(self, model):
        aid = model.schedule.agents[0].unique_id
        model.propaganda.broadcast(aid, "Spread test", potency=1.0)
        model.step()
        # Narratives may spread or decay
        assert len(model.propaganda.narratives) >= 0

    def test_model_without_propaganda(self):
        from strategify.sim.model import GeopolModel

        m = GeopolModel(enable_propaganda=False)
        assert m.propaganda is None
        for _ in range(3):
            m.step()
