"""Tests for the escalation ladder."""

import pytest

from strategify.agents.escalation import EscalationLevel
from strategify.sim.model import GeopolModel


@pytest.fixture
def ladder_model():
    """Model with escalation ladder enabled."""
    return GeopolModel(enable_escalation_ladder=True)


@pytest.fixture
def no_ladder_model():
    """Model without escalation ladder."""
    return GeopolModel(enable_escalation_ladder=False)


def test_escalation_ladder_initialized(ladder_model):
    assert ladder_model.escalation_ladder is not None
    assert len(ladder_model.escalation_ladder.levels) == 4


def test_all_agents_start_at_cooperative(ladder_model):
    for agent in ladder_model.schedule.agents:
        level = ladder_model.escalation_ladder.get_level(agent.unique_id)
        assert level == EscalationLevel.Cooperative


def test_escalation_ladder_not_initialized(no_ladder_model):
    assert no_ladder_model.escalation_ladder is None


def test_level_names(ladder_model):
    for agent in ladder_model.schedule.agents:
        name = ladder_model.escalation_ladder.get_level_name(agent.unique_id)
        assert name == "Cooperative"
        numeric = ladder_model.escalation_ladder.get_numeric_level(agent.unique_id)
        assert numeric == 0


def test_single_step_transition_allowed(ladder_model):
    agent = ladder_model.schedule.agents[0]
    uid = agent.unique_id
    assert ladder_model.escalation_ladder.can_transition(uid, EscalationLevel.Diplomatic)
    assert not ladder_model.escalation_ladder.can_transition(uid, EscalationLevel.Economic)
    assert not ladder_model.escalation_ladder.can_transition(uid, EscalationLevel.Military)


def test_set_level_single_step(ladder_model):
    agent = ladder_model.schedule.agents[0]
    uid = agent.unique_id
    cost = ladder_model.escalation_ladder.set_level(uid, EscalationLevel.Diplomatic)
    assert ladder_model.escalation_ladder.get_level(uid) == EscalationLevel.Diplomatic
    assert cost == pytest.approx(0.1)


def test_set_level_blocked_skip(ladder_model):
    agent = ladder_model.schedule.agents[0]
    uid = agent.unique_id
    cost = ladder_model.escalation_ladder.set_level(uid, EscalationLevel.Economic)
    assert ladder_model.escalation_ladder.get_level(uid) == EscalationLevel.Cooperative
    assert cost == 0.0


def test_deescalation_cost(ladder_model):
    agent = ladder_model.schedule.agents[0]
    uid = agent.unique_id
    ladder_model.escalation_ladder.set_level(uid, EscalationLevel.Diplomatic)
    cost = ladder_model.escalation_ladder.set_level(uid, EscalationLevel.Cooperative)
    assert cost == pytest.approx(-0.05)


def test_set_level_by_name(ladder_model):
    agent = ladder_model.schedule.agents[0]
    uid = agent.unique_id
    cost = ladder_model.escalation_ladder.set_level_by_name(uid, "Diplomatic")
    assert ladder_model.escalation_ladder.get_level_name(uid) == "Diplomatic"
    assert cost == pytest.approx(0.1)


def test_set_level_by_name_invalid(ladder_model):
    agent = ladder_model.schedule.agents[0]
    cost = ladder_model.escalation_ladder.set_level_by_name(agent.unique_id, "Invalid")
    assert cost == 0.0


def test_escalation_pressure_no_neighbors(ladder_model):
    agent = ladder_model.schedule.agents[0]
    pressure = ladder_model.escalation_ladder.get_escalation_pressure(agent.unique_id)
    assert 0.0 <= pressure <= 1.0


def test_get_max_level(ladder_model):
    assert ladder_model.escalation_ladder.get_max_level() == EscalationLevel.Cooperative


def test_summary(ladder_model):
    summary = ladder_model.escalation_ladder.summary()
    assert len(summary) == 4
    for rid, data in summary.items():
        assert data["level"] == "Cooperative"
        assert data["numeric"] == 0
        assert data["total_cost"] == 0.0


def test_model_steps_with_ladder(ladder_model):
    for _ in range(5):
        ladder_model.step()


def test_escalation_level_enum():
    assert int(EscalationLevel.Cooperative) == 0
    assert int(EscalationLevel.Diplomatic) == 1
    assert int(EscalationLevel.Economic) == 2
    assert int(EscalationLevel.Military) == 3
