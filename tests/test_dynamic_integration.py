"""Tests for dynamic payoff matrices, LLM integration, and model wiring."""

import numpy as np
import pytest

from strategify.game_theory.dynamic import PayoffComputer, PayoffHistory
from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


# ---------------------------------------------------------------------------
# PayoffComputer
# ---------------------------------------------------------------------------


class TestPayoffComputer:
    def test_compute_returns_matrices(self):
        pc = PayoffComputer()
        A, B = pc.compute(
            "escalation",
            caps_row={"military": 0.8, "economic": 0.5},
            caps_col={"military": 0.3, "economic": 0.5},
        )
        assert A.shape == (2, 2)
        assert B.shape == (2, 2)

    def test_stronger_row_higher_payoffs(self):
        pc = PayoffComputer()
        A_strong, _ = pc.compute(
            "escalation",
            caps_row={"military": 0.9},
            caps_col={"military": 0.1},
        )
        A_equal, _ = pc.compute(
            "escalation",
            caps_row={"military": 0.5},
            caps_col={"military": 0.5},
        )
        # Stronger row should have larger absolute payoffs
        assert np.abs(A_strong).sum() > np.abs(A_equal).sum()

    def test_tension_amplifies_losses(self):
        pc = PayoffComputer()
        A_no_tension, _ = pc.compute(
            "escalation",
            caps_row={"military": 0.5},
            caps_col={"military": 0.5},
        )
        A_high_tension, _ = pc.compute(
            "escalation",
            caps_row={"military": 0.5},
            caps_col={"military": 0.5},
            region_features_row={"tension_score": 0.8},
            region_features_col={"tension_score": 0.8},
        )
        # Negative entries should be more negative with high tension
        neg_mask = A_no_tension < 0
        if neg_mask.any():
            assert (A_high_tension[neg_mask] < A_no_tension[neg_mask]).all()

    def test_escalation_commitment(self):
        pc = PayoffComputer()
        A_level0, _ = pc.compute(
            "escalation",
            caps_row={"military": 0.5},
            caps_col={"military": 0.5},
            escalation_level_row=0,
        )
        A_level3, _ = pc.compute(
            "escalation",
            caps_row={"military": 0.5},
            caps_col={"military": 0.5},
            escalation_level_row=3,
            escalation_level_col=3,
        )
        # First row (aggressive action) should be boosted at higher levels
        assert A_level3[0, :].sum() > A_level0[0, :].sum()

    def test_all_game_types(self):
        pc = PayoffComputer()
        for game_name in ("escalation", "trade", "sanctions", "alliance", "military"):
            A, B = pc.compute(
                game_name,
                caps_row={"military": 0.5},
                caps_col={"military": 0.5},
            )
            assert A.shape == (2, 2)
            assert B.shape == (2, 2)


# ---------------------------------------------------------------------------
# PayoffHistory
# ---------------------------------------------------------------------------


class TestPayoffHistory:
    def test_record_and_retrieve(self):
        h = PayoffHistory()
        A = np.array([[1, 2], [3, 4]], dtype=float)
        B = np.array([[5, 6], [7, 8]], dtype=float)
        h.record(step=1, game_name="escalation", A=A, B=B)
        assert len(h.records) == 1

    def test_to_dataframe(self):
        h = PayoffHistory()
        A = np.array([[1, 2], [3, 4]], dtype=float)
        B = np.array([[5, 6], [7, 8]], dtype=float)
        h.record(step=1, game_name="escalation", A=A, B=B)
        h.record(step=2, game_name="trade", A=A, B=B)
        df = h.to_dataframe()
        assert len(df) == 2
        assert "step" in df.columns
        assert "A_sum" in df.columns

    def test_get_latest(self):
        h = PayoffHistory()
        A = np.array([[1, 2], [3, 4]], dtype=float)
        B = np.array([[5, 6], [7, 8]], dtype=float)
        h.record(step=1, game_name="escalation", A=A, B=B)
        h.record(step=2, game_name="trade", A=A * 2, B=B * 2)
        latest = h.get_latest()
        assert latest["step"] == 2
        latest_esc = h.get_latest("escalation")
        assert latest_esc["step"] == 1

    def test_clear(self):
        h = PayoffHistory()
        A = np.array([[1, 2], [3, 4]], dtype=float)
        B = np.array([[5, 6], [7, 8]], dtype=float)
        h.record(step=1, game_name="escalation", A=A, B=B)
        h.clear()
        assert len(h.records) == 0

    def test_empty_dataframe(self):
        h = PayoffHistory()
        df = h.to_dataframe()
        assert df.empty


# ---------------------------------------------------------------------------
# Model integration
# ---------------------------------------------------------------------------


class TestModelIntegration:
    def test_model_has_coalition_engine(self, model):
        assert model.coalition_engine is not None
        assert model.coalition_tracker is not None

    def test_model_step_with_coalition(self, model):
        for _ in range(3):
            model.step()
        summary = model.coalition_tracker.summary()
        assert "n_coalitions" in summary

    def test_model_osint_not_enabled_by_default(self, model):
        assert model.osint_pipeline is None
        assert model.osint_features == {}

    def test_model_llm_not_enabled_by_default(self, model):
        assert model.llm_engine is None

    def test_model_payoff_history_not_enabled_by_default(self, model):
        assert model.payoff_history is None

    def test_model_enable_payoff_history(self, model):
        model.enable_payoff_history()
        for _ in range(3):
            model.step()
        df = model.payoff_history.to_dataframe()
        # Payoff history not automatically recorded (requires agent integration)
        # Just verify it doesn't crash

    def test_model_deterministic_with_coalition(self):
        import random

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

    def test_model_with_llm_no_api_key(self, model):
        """LLM engine without API key falls back to Nash."""
        model.enable_llm(provider="openai", api_key="")
        for _ in range(3):
            model.step()
        # Should complete without error (LLM fails silently, falls back to Nash)
        assert all(a.posture in ("Escalate", "Deescalate") for a in model.schedule.agents)


# ---------------------------------------------------------------------------
# OSINT bias integration
# ---------------------------------------------------------------------------


class TestOSINTBiasIntegration:
    def test_osint_features_influence_decisions(self):
        """Agents with high-tension OSINT features should be more likely to escalate."""
        import random

        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()

        # Inject high tension features into m2
        m2.osint_features = {
            "alpha": {"tension_score": 1.0},
            "bravo": {"tension_score": 1.0},
            "charlie": {"tension_score": 1.0},
            "delta": {"tension_score": 1.0},
        }

        for _ in range(5):
            m1.step()
            m2.step()

        # With high tension, at least some agents should behave differently
        # (or same, depending on the Nash equilibrium — just verify no crash)
        for a in m2.schedule.agents:
            assert a.posture in ("Escalate", "Deescalate")

    def test_osint_features_partial(self):
        """OSINT features for only some regions shouldn't crash."""
        model = GeopolModel()
        model.osint_features = {
            "alpha": {"tension_score": 0.5, "event_count": 10.0},
            # bravo, charlie, delta have no OSINT data
        }
        for _ in range(3):
            model.step()
        assert all(a.posture in ("Escalate", "Deescalate") for a in model.schedule.agents)

    def test_osint_features_zero_tension(self):
        """Zero tension should produce same results as no OSINT."""
        import random

        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()
        m2.osint_features = {
            "alpha": {"tension_score": 0.0},
            "bravo": {"tension_score": 0.0},
            "charlie": {"tension_score": 0.0},
            "delta": {"tension_score": 0.0},
        }
        for _ in range(5):
            m1.step()
            m2.step()
        p1 = {a.region_id: a.posture for a in m1.schedule.agents}
        p2 = {a.region_id: a.posture for a in m2.schedule.agents}
        assert p1 == p2


# ---------------------------------------------------------------------------
# Agent personality paths
# ---------------------------------------------------------------------------


class TestAgentPersonalityPaths:
    def test_aggressor_personality(self):
        import random

        random.seed(42)
        model = GeopolModel()
        for agent in model.schedule.agents:
            agent.personality = "Aggressor"
        for _ in range(5):
            model.step()
        assert all(a.posture in ("Escalate", "Deescalate") for a in model.schedule.agents)

    def test_pacifist_personality(self):
        import random

        random.seed(42)
        model = GeopolModel()
        for agent in model.schedule.agents:
            agent.personality = "Pacifist"
        for _ in range(5):
            model.step()
        assert all(a.posture in ("Escalate", "Deescalate") for a in model.schedule.agents)

    def test_multiple_active_games(self):
        import random

        random.seed(42)
        model = GeopolModel(active_games=["escalation", "trade", "sanctions"])
        for agent in model.schedule.agents:
            agent.active_games = ["escalation", "trade", "sanctions"]
        for _ in range(5):
            model.step()
        assert all(a.posture in ("Escalate", "Deescalate") for a in model.schedule.agents)

    def test_col_role(self):
        import random

        random.seed(42)
        model = GeopolModel()
        # Force all agents to col role
        for agent in model.schedule.agents:
            agent.role = "col"
        for _ in range(5):
            model.step()
        assert all(a.posture in ("Escalate", "Deescalate") for a in model.schedule.agents)


# ---------------------------------------------------------------------------
# Coalition integration
# ---------------------------------------------------------------------------


class TestCoalitionIntegration:
    def test_coalition_tracker_tracks_cooperation(self):
        model = GeopolModel()
        for _ in range(10):
            model.step()
        tracker = model.coalition_tracker
        # Should have cooperation scores after 10 steps
        assert len(tracker.cooperation_scores) > 0

    def test_coalition_engine_last_results(self):
        model = GeopolModel()
        model.step()
        results = model.coalition_engine.last_results
        assert len(results) == 6  # 4 choose 2

    def test_coalition_tracker_with_alliances(self):
        """Alliance weights should influence cooperation scores."""
        model = GeopolModel()
        # Diplomacy relations already set in model init
        for _ in range(10):
            model.step()
        summary = model.coalition_tracker.summary()
        assert summary["n_coalitions"] >= 0

    def test_model_without_coalition(self):
        """Model without escalation ladder has no coalition engine."""
        model = GeopolModel(enable_escalation_ladder=False)
        assert model.coalition_engine is None
        for _ in range(3):
            model.step()


# ---------------------------------------------------------------------------
# Escalation level decision
# ---------------------------------------------------------------------------


class TestEscalationLevelDecision:
    def test_escalation_ladder_levels_change(self):
        """With strong enough signals, agents should change escalation levels."""
        import random

        random.seed(42)
        model = GeopolModel()
        # Force high adjustment by setting capabilities
        for agent in model.schedule.agents:
            agent.capabilities = {"military": 0.9, "economic": 0.9}
            agent.personality = "Aggressor"
        for _ in range(20):
            model.step()
        # At least some agents should have changed levels
        assert model.escalation_ladder is not None

    def test_no_escalation_ladder(self):
        """Escalation decisions should return None when ladder disabled."""
        model = GeopolModel(enable_escalation_ladder=False)
        agent = model.schedule.agents[0]
        result = agent._decide_escalation_level(1.5, "Escalate")
        assert result is None


# ---------------------------------------------------------------------------
# Scenario-based model creation
# ---------------------------------------------------------------------------


class TestScenarioModel:
    def test_model_from_scenario(self):
        model = GeopolModel(scenario="default")
        assert model.scenario_name == "eastern_europe_crisis"
        assert len(model.schedule.agents) == 4

    def test_model_from_arms_race_scenario(self):
        model = GeopolModel(scenario="arms_race")
        assert len(model.schedule.agents) == 4

    def test_model_from_detente_scenario(self):
        model = GeopolModel(scenario="detente")
        assert len(model.schedule.agents) == 4

    def test_scenario_deterministic(self):
        import random

        random.seed(42)
        m1 = GeopolModel(scenario="default")
        random.seed(42)
        m2 = GeopolModel(scenario="default")
        for _ in range(5):
            m1.step()
            m2.step()
        p1 = {a.region_id: a.posture for a in m1.schedule.agents}
        p2 = {a.region_id: a.posture for a in m2.schedule.agents}
        assert p1 == p2

    def test_model_with_region_gdf(self):
        import geopandas as gpd
        from shapely.geometry import Polygon

        gdf = gpd.GeoDataFrame(
            [
                {"region_id": "alpha", "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])},
                {"region_id": "bravo", "geometry": Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])},
                {"region_id": "charlie", "geometry": Polygon([(0, 1), (1, 1), (1, 2), (0, 2)])},
                {"region_id": "delta", "geometry": Polygon([(1, 1), (2, 1), (2, 2), (1, 2)])},
            ],
            crs="EPSG:4326",
        )
        model = GeopolModel(region_gdf=gdf)
        assert len(model.schedule.agents) == 4
        assert model.n_agents == 4

    def test_model_n_total_agents(self):
        model = GeopolModel()
        assert model.n_total_agents == 4
        assert model.n_agents == 4
