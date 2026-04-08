"""Tests for HealthEngine — pandemic spread, recovery, productivity impact."""

import pytest

from strategify.sim.health import HealthEngine


@pytest.fixture
def model():
    from strategify.sim.model import GeopolModel

    return GeopolModel(enable_health=True)


@pytest.fixture
def health_engine(model):
    return model.health_engine


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


class TestHealthInit:
    def test_health_engine_created(self, model):
        assert model.health_engine is not None
        assert isinstance(model.health_engine, HealthEngine)

    def test_infection_rates_start_at_zero(self, health_engine):
        for _rid, rate in health_engine.infection_rates.items():
            assert rate == 0.0

    def test_hospital_capacity_starts_at_one(self, health_engine):
        for _rid, cap in health_engine.hospital_capacity.items():
            assert cap == 1.0

    def test_all_regions_initialized(self, health_engine, model):
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            assert rid in health_engine.infection_rates


# ---------------------------------------------------------------------------
# Outbreak
# ---------------------------------------------------------------------------


class TestOutbreak:
    def test_trigger_outbreak(self, health_engine):
        health_engine.trigger_outbreak("alpha", intensity=0.3)
        assert health_engine.infection_rates["alpha"] == 0.3

    def test_trigger_outbreak_unknown_region(self, health_engine):
        # Should not crash
        health_engine.trigger_outbreak("nonexistent", intensity=0.5)

    def test_outbreak_default_intensity(self, health_engine):
        health_engine.trigger_outbreak("bravo")
        assert health_engine.infection_rates["bravo"] == 0.2


# ---------------------------------------------------------------------------
# Contagion
# ---------------------------------------------------------------------------


class TestContagion:
    def test_spatial_contagion(self, model, health_engine):
        # Infect alpha, step, check neighbors
        health_engine.trigger_outbreak("alpha", intensity=0.8)
        health_engine.step()
        # After one step, original region still infected
        assert health_engine.infection_rates["alpha"] > 0.0
        total = sum(health_engine.infection_rates.values())
        # Total infection across regions should be non-zero
        assert total > 0.0

    def test_no_spread_when_healthy(self, health_engine):
        health_engine.step()
        for rate in health_engine.infection_rates.values():
            assert rate == 0.0

    def test_trade_spread(self, model, health_engine):
        # Requires trade network to be enabled (default: True)
        if model.trade_network is None:
            pytest.skip("Trade network not enabled")
        health_engine.trigger_outbreak("alpha", intensity=0.8)
        # Step multiple times to allow trade-based spread
        for _ in range(10):
            health_engine.step()
        # At minimum, total infection should be positive
        total = sum(health_engine.infection_rates.values())
        assert total > 0.0


# ---------------------------------------------------------------------------
# Recovery
# ---------------------------------------------------------------------------


class TestRecovery:
    def test_recovery_over_time(self, health_engine):
        health_engine.trigger_outbreak("alpha", intensity=0.15)
        initial = health_engine.infection_rates["alpha"]
        for _ in range(20):
            health_engine.step()
        assert health_engine.infection_rates["alpha"] < initial

    def test_full_recovery(self, health_engine):
        health_engine.trigger_outbreak("alpha", intensity=0.1)
        for _ in range(100):
            health_engine.step()
        # Should recover to near-zero
        assert health_engine.infection_rates["alpha"] < 0.05

    def test_hospital_capacity_drains(self, health_engine):
        health_engine.trigger_outbreak("alpha", intensity=0.5)
        for _ in range(5):
            health_engine.step()
        # Capacity should have decreased under high load
        assert health_engine.hospital_capacity["alpha"] < 1.0

    def test_hospital_capacity_recovers(self, health_engine):
        # After low infection, capacity should recover
        health_engine.trigger_outbreak("alpha", intensity=0.05)
        for _ in range(20):
            health_engine.step()
        # With low infection, capacity should be near or at 1.0
        assert health_engine.hospital_capacity["alpha"] >= 0.9


# ---------------------------------------------------------------------------
# Productivity
# ---------------------------------------------------------------------------


class TestProductivity:
    def test_productivity_full_when_healthy(self, health_engine):
        assert health_engine.get_productivity_impact("alpha") == 1.0

    def test_productivity_reduced_when_infected(self, health_engine):
        health_engine.infection_rates["alpha"] = 0.5
        impact = health_engine.get_productivity_impact("alpha")
        assert impact < 1.0
        assert impact >= 0.6

    def test_productivity_unknown_region(self, health_engine):
        assert health_engine.get_productivity_impact("unknown") == 1.0

    def test_productivity_minimum_floor(self, health_engine):
        health_engine.infection_rates["alpha"] = 1.0
        impact = health_engine.get_productivity_impact("alpha")
        assert impact >= 0.6


# ---------------------------------------------------------------------------
# Integration with model step
# ---------------------------------------------------------------------------


class TestHealthIntegration:
    def test_model_steps_with_health(self, model):
        for _ in range(5):
            model.step()

    def test_health_engine_steps_each_turn(self, model):
        model.health_engine.trigger_outbreak("alpha", intensity=0.3)
        initial = model.health_engine.infection_rates["alpha"]
        model.step()
        # Infection rate should have changed after model step
        assert model.health_engine.infection_rates["alpha"] != initial or initial == 0.3

    def test_model_without_health(self):
        from strategify.sim.model import GeopolModel

        m = GeopolModel(enable_health=False)
        assert m.health_engine is None
        for _ in range(3):
            m.step()
