"""Tests for scenario configuration loading."""

from pathlib import Path

import pytest

from strategify.config.scenarios import (
    list_scenarios,
    load_scenario,
    scenario_to_configs,
)


def test_list_scenarios_returns_names():
    scenarios = list_scenarios()
    assert "default" in scenarios
    assert "detente" in scenarios
    assert "arms_race" in scenarios


def test_load_default_scenario():
    data = load_scenario("default")
    assert data["name"] == "eastern_europe_crisis"
    assert "actors" in data
    assert "region_resources" in data
    assert "alliances" in data
    assert len(data["actors"]) == 4


def test_load_scenario_by_path():
    scenarios_dir = Path(__file__).resolve().parent.parent / "strategify" / "geo" / "scenarios"
    data = load_scenario(scenarios_dir / "default.json")
    assert data["name"] == "eastern_europe_crisis"


def test_load_scenario_not_found():
    with pytest.raises(FileNotFoundError, match="Scenario not found"):
        load_scenario("nonexistent")


def test_scenario_to_configs():
    data = load_scenario("default")
    actor_configs, region_resources, alliances = scenario_to_configs(data)

    assert "alpha" in actor_configs
    assert actor_configs["alpha"]["caps"]["military"] == 0.8
    assert actor_configs["alpha"]["personality"] == "Aggressor"

    assert "bravo" in region_resources
    assert region_resources["bravo"] == 2.0

    assert len(alliances) == 3
    assert alliances[0] == ("alpha", "bravo", 1.0)


def test_detente_scenario_configs():
    data = load_scenario("detente")
    actor_configs, region_resources, alliances = scenario_to_configs(data)

    # Detente scenario has balanced capabilities
    for rid in ("alpha", "bravo", "charlie", "delta"):
        assert actor_configs[rid]["caps"]["military"] == 0.5
        assert actor_configs[rid]["caps"]["economic"] == 0.5

    # All alliances are positive
    for _, _, weight in alliances:
        assert weight > 0


def test_arms_race_scenario_configs():
    data = load_scenario("arms_race")
    actor_configs, _, alliances = scenario_to_configs(data)

    assert actor_configs["bravo"]["personality"] == "Aggressor"
    assert actor_configs["bravo"]["caps"]["military"] == 0.9

    # Has both positive and negative alliances
    weights = [w for _, _, w in alliances]
    assert any(w > 0 for w in weights)
    assert any(w < 0 for w in weights)


def test_model_loads_scenario():
    """GeopolModel can load from a scenario file."""
    from strategify.sim.model import GeopolModel

    model = GeopolModel(scenario="default")
    assert model.scenario_name == "eastern_europe_crisis"
    assert len(model.schedule.agents) == 4


def test_model_scenario_determinism():
    """Same scenario produces identical results across runs."""
    from strategify.sim.model import GeopolModel

    m1 = GeopolModel(scenario="detente")
    m2 = GeopolModel(scenario="detente")
    for _ in range(5):
        m1.step()
        m2.step()
    p1 = {a.region_id: a.posture for a in m1.schedule.agents}
    p2 = {a.region_id: a.posture for a in m2.schedule.agents}
    assert p1 == p2
