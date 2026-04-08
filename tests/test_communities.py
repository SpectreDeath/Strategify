import pytest

from strategify.analysis.communities import (
    detect_communities,
    detect_communities_over_time,
    find_agent_community,
)
from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


def test_detect_communities_returns_dict(model):
    result = detect_communities(model)
    assert "communities" in result
    assert "num_communities" in result
    assert "modularity" in result


def test_communities_cover_all_agents(model):
    result = detect_communities(model)
    all_ids = set()
    for comm in result["communities"]:
        all_ids.update(comm)
    agent_ids = {a.unique_id for a in model.schedule.agents}
    assert all_ids == agent_ids


def test_num_communities_positive(model):
    result = detect_communities(model)
    assert result["num_communities"] >= 1


def test_modularity_in_range(model):
    result = detect_communities(model)
    # Modularity is typically in [-0.5, 1]
    assert -1.0 <= result["modularity"] <= 1.0


def test_detect_communities_over_time(model):
    history = detect_communities_over_time(model, n_steps=5)
    assert len(history) == 5
    for entry in history:
        assert "step" in entry
        assert "communities" in entry


def test_find_agent_community(model):
    result = detect_communities(model)
    agent_id = model.schedule.agents[0].unique_id
    comm_idx = find_agent_community(agent_id, result["communities"])
    assert comm_idx is not None
    assert agent_id in result["communities"][comm_idx]


def test_find_agent_community_not_found(model):
    result = detect_communities(model)
    assert find_agent_community(-999, result["communities"]) is None
