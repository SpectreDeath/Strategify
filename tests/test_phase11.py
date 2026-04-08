"""Tests for Phase 11: Agent registry, military influence, faction normalization, terrain."""


from strategify.sim.conflict import ConflictEngine
from strategify.sim.model import GeopolModel

# ---------------------------------------------------------------------------
# Agent registry
# ---------------------------------------------------------------------------


class TestAgentRegistry:
    def test_registry_populated(self):
        model = GeopolModel()
        assert hasattr(model, "_agent_registry")
        assert len(model._agent_registry) == 4

    def test_get_agent_by_region(self):
        model = GeopolModel()
        agent = model.get_agent_by_region("alpha")
        assert agent is not None
        assert agent.region_id == "alpha"

    def test_get_agent_by_region_unknown(self):
        model = GeopolModel()
        assert model.get_agent_by_region("nonexistent") is None

    def test_registry_consistent_with_schedule(self):
        model = GeopolModel()
        for rid, agent in model._agent_registry.items():
            assert agent.region_id == rid
            assert agent in model.schedule.agents

    def test_registry_all_regions(self):
        model = GeopolModel()
        for rid in ("alpha", "bravo", "charlie", "delta"):
            assert rid in model._agent_registry


# ---------------------------------------------------------------------------
# Military influence on decisions
# ---------------------------------------------------------------------------


class TestMilitaryInfluence:
    def test_military_bias_in_decide(self):
        model = GeopolModel()
        alpha = model.get_agent_by_region("alpha")
        # Alpha has mil_cap 0.8, should have some military bias
        decision = alpha.decide()
        assert "action" in decision

    def test_alpha_has_more_military_capability(self):
        """Alpha (mil_cap 0.8) should have more military power than bravo (0.3)."""
        model = GeopolModel()
        alpha = model.get_agent_by_region("alpha")
        bravo = model.get_agent_by_region("bravo")
        # Check capabilities first
        assert alpha.capabilities["military"] > bravo.capabilities["military"]
        # Alpha should have more units
        assert len(alpha.military.units) > len(bravo.military.units)

    def test_total_power_positive(self):
        model = GeopolModel()
        for agent in model.schedule.agents:
            if hasattr(agent, "military"):
                assert agent.military.get_total_power() > 0


# ---------------------------------------------------------------------------
# Faction power normalization
# ---------------------------------------------------------------------------


class TestFactionNormalization:
    def test_faction_powers_sum_to_one_initially(self):
        model = GeopolModel()
        for agent in model.schedule.agents:
            if hasattr(agent, "factions"):
                total = sum(f.power for f in agent.factions)
                assert abs(total - 1.0) < 0.01

    def test_faction_powers_normalized_after_reform(self):
        """After a domestic reform, powers should still sum to ~1.0."""
        model = GeopolModel()
        alpha = model.get_agent_by_region("alpha")
        # Force low stability to trigger reform
        alpha.stability = 0.1
        alpha._update_stability("Escalate")
        total = sum(f.power for f in alpha.factions)
        assert abs(total - 1.0) < 0.01, f"Faction powers sum to {total}, expected ~1.0"

    def test_multiple_reforms_keep_normalized(self):
        model = GeopolModel()
        alpha = model.get_agent_by_region("alpha")
        for _ in range(10):
            alpha.stability = 0.1
            alpha._update_stability("Escalate")
        total = sum(f.power for f in alpha.factions)
        assert abs(total - 1.0) < 0.01


# ---------------------------------------------------------------------------
# Terrain resolution
# ---------------------------------------------------------------------------


class TestTerrainResolution:
    def test_default_terrain_is_plain(self):
        model = GeopolModel()
        engine = ConflictEngine(model)
        assert engine._get_terrain("alpha") == "Plain"
        assert engine._get_terrain("nonexistent") == "Plain"

    def test_terrain_override(self):
        model = GeopolModel()
        engine = ConflictEngine(model, terrain_overrides={"alpha": "Mountain"})
        assert engine._get_terrain("alpha") == "Mountain"
        assert engine._get_terrain("bravo") == "Plain"

    def test_terrain_from_geojson_column(self):
        """If region_gdf has a 'terrain' column, use it."""
        model = GeopolModel()
        # Add a terrain column to the GeoDataFrame
        model.region_gdf["terrain"] = "Forest"
        engine = ConflictEngine(model)
        assert engine._get_terrain("alpha") == "Forest"

    def test_terrain_override_takes_priority(self):
        model = GeopolModel()
        model.region_gdf["terrain"] = "Forest"
        engine = ConflictEngine(model, terrain_overrides={"alpha": "Urban"})
        assert engine._get_terrain("alpha") == "Urban"
        assert engine._get_terrain("bravo") == "Forest"


# ---------------------------------------------------------------------------
# Non-state actor uses registry
# ---------------------------------------------------------------------------


class TestNonStateRegistry:
    def test_non_state_actor_finds_target(self):
        model = GeopolModel(enable_non_state_actors=True)
        from strategify.agents.non_state import NonStateActor

        nsa = next(a for a in model.schedule.agents if isinstance(a, NonStateActor))
        # Should not crash when looking up target region
        nsa.step()
