from unittest.mock import MagicMock

import pytest

from strategify.reasoning.diplomacy import DiplomacyGraph


@pytest.fixture
def diplomacy():
    model = MagicMock()
    agents = []
    for i in range(4):
        a = MagicMock()
        a.unique_id = i + 1
        agents.append(a)
    model.schedule.agents = agents
    graph = DiplomacyGraph(model)
    graph.update_relations()
    return graph


def test_graph_has_all_nodes(diplomacy):
    assert len(diplomacy.graph.nodes) == 4
    assert 1 in diplomacy.graph.nodes
    assert 4 in diplomacy.graph.nodes


def test_set_and_get_relation(diplomacy):
    diplomacy.set_relation(1, 2, 0.8)
    assert diplomacy.get_relation(1, 2) == 0.8
    assert diplomacy.get_relation(2, 1) == 0.8  # undirected


def test_get_relation_default_zero(diplomacy):
    assert diplomacy.get_relation(1, 3) == 0.0


def test_relation_clamped_to_range(diplomacy):
    diplomacy.set_relation(1, 2, 2.0)
    assert diplomacy.get_relation(1, 2) == 1.0
    diplomacy.set_relation(1, 3, -2.0)
    assert diplomacy.get_relation(1, 3) == -1.0


def test_get_allies_above_threshold(diplomacy):
    diplomacy.set_relation(1, 2, 0.8)
    diplomacy.set_relation(1, 3, 0.3)
    allies = diplomacy.get_allies(1, threshold=0.5)
    assert 2 in allies
    assert 3 not in allies


def test_get_allies_default_threshold(diplomacy):
    diplomacy.set_relation(1, 2, 0.5)
    diplomacy.set_relation(1, 3, 0.49)
    allies = diplomacy.get_allies(1)
    assert 2 in allies
    assert 3 not in allies


def test_get_allies_empty_for_no_edges(diplomacy):
    allies = diplomacy.get_allies(1)
    assert allies == []


def test_aggregate_allied_strength_includes_self(diplomacy):
    diplomacy.set_relation(1, 2, 1.0)
    for a in diplomacy.model.schedule.agents:
        a.capabilities = {"military": 0.5}
    diplomacy.model.schedule.agents[0].capabilities = {"military": 0.8}
    diplomacy.model.schedule.agents[1].capabilities = {"military": 0.3}
    total = diplomacy.get_aggregate_allied_strength(1)
    assert total == pytest.approx(0.8 + 0.3)


def test_aggregate_allied_strength_no_allies(diplomacy):
    for a in diplomacy.model.schedule.agents:
        a.capabilities = {"military": 0.5}
    diplomacy.model.schedule.agents[0].capabilities = {"military": 0.7}
    total = diplomacy.get_aggregate_allied_strength(1)
    assert total == pytest.approx(0.7)
