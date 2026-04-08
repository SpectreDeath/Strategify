from strategify.sim.model import GeopolModel


def test_model_creates_4_agents(model):
    assert len(model.schedule.agents) == 4


def test_model_has_diplomacy_graph(model):
    assert model.relations is not None


def test_model_step_runs_without_error(model):
    for _ in range(5):
        model.step()


def test_model_deterministic():
    model1 = GeopolModel()
    model2 = GeopolModel()
    for _ in range(10):
        model1.step()
        model2.step()
    postures1 = {a.region_id: a.posture for a in model1.schedule.agents}
    postures2 = {a.region_id: a.posture for a in model2.schedule.agents}
    assert postures1 == postures2


def test_all_agents_have_posture(model):
    model.step()
    for agent in model.schedule.agents:
        assert agent.posture in ("Escalate", "Deescalate")


def test_all_agents_have_region_id(model):
    for agent in model.schedule.agents:
        assert hasattr(agent, "region_id")
        assert agent.region_id in ("alpha", "bravo", "charlie", "delta")


def test_all_agents_have_capabilities(model):
    for agent in model.schedule.agents:
        assert hasattr(agent, "capabilities")
        assert "military" in agent.capabilities
        assert "economic" in agent.capabilities


def test_all_agents_have_personality(model):
    valid_personalities = {"Aggressor", "Pacifist", "Tit-for-Tat", "Neutral"}
    for agent in model.schedule.agents:
        assert agent.personality in valid_personalities


def test_data_collector_captures_all_agents(model):
    for _ in range(3):
        model.step()
    df = model.datacollector.get_agent_vars_dataframe()
    agent_ids = df.index.get_level_values("AgentID").unique()
    assert len(agent_ids) == 4


def test_data_collector_records_posture(model):
    model.step()
    df = model.datacollector.get_agent_vars_dataframe()
    assert "posture" in df.columns
    assert "region_id" in df.columns


def test_influence_map_cached_after_step(model):
    model.step()
    assert model.influence_map is not None


def test_model_region_resources_independent():
    """Model instances should not share mutable region_resources."""
    model1 = GeopolModel()
    model2 = GeopolModel()
    model1.region_resources["alpha"] = 999.0
    assert model2.region_resources["alpha"] != 999.0


def test_model_accepts_n_steps():
    model = GeopolModel(n_steps=10)
    assert model.n_steps == 10


def test_agents_have_valid_roles(model):
    for agent in model.schedule.agents:
        assert agent.role in ("row", "col")


# ---------------------------------------------------------------------------
# Settings / color utilities
# ---------------------------------------------------------------------------


def test_get_region_color_known():
    from strategify.config.settings import get_region_color

    assert get_region_color("alpha") == "blue"
    assert get_region_color("bravo") == "red"


def test_get_region_color_unknown_auto_assigns():
    from strategify.config.settings import get_region_color

    color = get_region_color("totally_new_region")
    assert color is not None
    assert len(color) > 0


def test_get_region_color_consistent():
    from strategify.config.settings import get_region_color

    c1 = get_region_color("consistent_test_region")
    c2 = get_region_color("consistent_test_region")
    assert c1 == c2


def test_get_region_hex_color_known():
    from strategify.config.settings import get_region_hex_color

    hex_color = get_region_hex_color("alpha")
    assert hex_color.startswith("#")


def test_get_region_hex_color_unknown():
    from strategify.config.settings import get_region_hex_color

    hex_color = get_region_hex_color("unknown_region")
    assert hex_color.startswith("#")
