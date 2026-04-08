import pytest

from strategify.reasoning.influence import InfluenceMap
from strategify.sim.model import GeopolModel


@pytest.fixture
def model_and_imap():
    model = GeopolModel()
    imap = InfluenceMap(model)
    imap.compute()
    return model, imap


def test_influence_data_populated(model_and_imap):
    model, imap = model_and_imap
    assert len(imap.influence_data) == 4


def test_influence_data_no_key_collision(model_and_imap):
    model, imap = model_and_imap
    region_ids = {getattr(a, "region_id", "unknown") for a in model.schedule.agents}
    for rid in region_ids:
        assert rid in imap.influence_data


def test_influence_data_has_agent_entries(model_and_imap):
    model, imap = model_and_imap
    for rid, agent_dict in imap.influence_data.items():
        assert len(agent_dict) > 0, f"Region {rid} has no influence entries"


def test_contagion_data_initialized(model_and_imap):
    model, imap = model_and_imap
    for rid, val in imap.contagion_data.items():
        assert val >= 0.0


def test_net_influence_returns_float(model_and_imap):
    model, imap = model_and_imap
    agent = model.schedule.agents[0]
    result = imap.get_net_influence(agent.region_id, agent.unique_id)
    assert isinstance(result, float)


def test_distances_from_origin(model_and_imap):
    model, imap = model_and_imap
    agent = model.schedule.agents[0]
    origin = getattr(agent, "region_id", "unknown")
    distances = imap._calculate_distances(origin)
    assert distances[origin] == 0
    assert all(d > 0 for rid, d in distances.items() if rid != origin)


def test_contagion_level_returns_float(model_and_imap):
    model, imap = model_and_imap
    agent = model.schedule.agents[0]
    result = imap.get_contagion_level(agent.region_id)
    assert isinstance(result, float)


def test_influence_cached_on_model_step():
    model = GeopolModel()
    assert model.influence_map is None
    model.step()
    assert model.influence_map is not None
    assert len(model.influence_map.influence_data) == 4
