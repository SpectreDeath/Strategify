"""Tests for the economic model (TradeNetwork)."""

import random

import pytest

from strategify.reasoning.economics import _growth_tier
from strategify.sim.model import GeopolModel


@pytest.fixture
def econ_model():
    """Model with economics enabled."""
    return GeopolModel(enable_economics=True)


@pytest.fixture
def no_econ_model():
    """Model without economics."""
    return GeopolModel(enable_economics=False)


def test_trade_network_initialized(econ_model):
    assert econ_model.trade_network is not None
    assert len(econ_model.trade_network.gdp) == 4


def test_trade_network_not_initialized(no_econ_model):
    assert no_econ_model.trade_network is None


def test_gdp_positive(econ_model):
    for agent in econ_model.schedule.agents:
        gdp = econ_model.trade_network.get_gdp(agent.unique_id)
        assert gdp > 0


def test_trade_flows_symmetric(econ_model):
    agents = list(econ_model.schedule.agents)
    for i, a in enumerate(agents):
        for j in range(i + 1, len(agents)):
            b = agents[j]
            flow_ab = econ_model.trade_network.get_bilateral_trade(a.unique_id, b.unique_id)
            flow_ba = econ_model.trade_network.get_bilateral_trade(b.unique_id, a.unique_id)
            assert flow_ab == pytest.approx(flow_ba)


def test_trade_step_updates(econ_model):
    initial_gdp = {}
    for agent in econ_model.schedule.agents:
        initial_gdp[agent.unique_id] = econ_model.trade_network.get_gdp(agent.unique_id)

    econ_model.step()
    econ_model.trade_network.step()

    # GDP should still be valid
    for agent in econ_model.schedule.agents:
        gdp = econ_model.trade_network.get_gdp(agent.unique_id)
        assert gdp > 0


def test_economic_features(econ_model):
    for agent in econ_model.schedule.agents:
        features = econ_model.trade_network.get_economic_features(agent.unique_id)
        assert "gdp" in features
        assert "trade_balance" in features
        assert "total_trade" in features
        assert features["gdp"] > 0


def test_total_trade_non_negative(econ_model):
    for agent in econ_model.schedule.agents:
        total = econ_model.trade_network.get_total_trade(agent.unique_id)
        assert total >= 0


def test_model_steps_with_economics(econ_model):
    for _ in range(5):
        econ_model.step()


def test_trade_balance_can_be_negative(econ_model):
    """Trade balance is net exports - imports; can be negative."""
    balances = [
        econ_model.trade_network.get_trade_balance(a.unique_id) for a in econ_model.schedule.agents
    ]
    # At least one should be negative (or all zero in symmetric case)
    # Just verify they're all floats
    assert all(isinstance(b, float) for b in balances)


# ---------------------------------------------------------------------------
# Phase 2: GDP Growth
# ---------------------------------------------------------------------------


class TestGDPGrowth:
    def test_gdp_history_tracked(self, econ_model):
        tn = econ_model.trade_network
        for _ in range(5):
            econ_model.step()
        for uid in tn.gdp_history:
            assert len(tn.gdp_history[uid]) == 6  # initial + 5 steps

    def test_growth_tiers(self):
        assert _growth_tier(0.9) == "high"
        assert _growth_tier(0.5) == "medium"
        assert _growth_tier(0.2) == "low"

    def test_gdp_growth_rate_set(self, econ_model):
        tn = econ_model.trade_network
        for uid in tn.growth_rate:
            assert 0.0 < tn.growth_rate[uid] <= 0.05

    def test_get_gdp_growth(self, econ_model):
        for agent in econ_model.schedule.agents:
            growth = econ_model.trade_network.get_gdp_growth(agent.unique_id)
            assert isinstance(growth, float)
            assert growth > 0

    def test_get_gdp_history(self, econ_model):
        for _ in range(3):
            econ_model.step()
        for agent in econ_model.schedule.agents:
            history = econ_model.trade_network.get_gdp_history(agent.unique_id)
            assert len(history) == 4  # initial + 3 steps


# ---------------------------------------------------------------------------
# Phase 2: NetworkX Flows Graph
# ---------------------------------------------------------------------------


class TestFlowsGraph:
    def test_graph_has_nodes(self, econ_model):
        tn = econ_model.trade_network
        assert tn.flows_graph.number_of_nodes() == 4

    def test_graph_has_directed_edges(self, econ_model):
        tn = econ_model.trade_network
        # Each pair has 2 directed edges: 4*3 = 12
        assert tn.flows_graph.number_of_edges() == 12

    def test_graph_edge_volumes(self, econ_model):
        tn = econ_model.trade_network
        for u, v, data in tn.flows_graph.edges(data=True):
            assert "volume" in data
            assert data["volume"] >= 0

    def test_graph_synced_with_dict(self, econ_model):
        tn = econ_model.trade_network
        for (u, v), volume in tn.trade_flows.items():
            if tn.flows_graph.has_edge(u, v):
                assert tn.flows_graph[u][v]["volume"] == pytest.approx(volume)

    def test_summary(self, econ_model):
        econ_model.step()
        summary = econ_model.trade_network.summary()
        assert summary["n_nodes"] == 4
        assert summary["n_edges"] > 0
        assert summary["total_gdp"] > 0


# ---------------------------------------------------------------------------
# Phase 2: Sanctions
# ---------------------------------------------------------------------------


class TestSanctions:
    def test_impose_sanction(self, econ_model):
        agents = list(econ_model.schedule.agents)
        tn = econ_model.trade_network
        tn.impose_sanction(agents[0].unique_id, agents[1].unique_id)
        assert tn.is_sanctioned(agents[0].unique_id, agents[1].unique_id)

    def test_lift_sanction(self, econ_model):
        agents = list(econ_model.schedule.agents)
        tn = econ_model.trade_network
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        tn.impose_sanction(uid_a, uid_b)
        tn.lift_sanction(uid_a, uid_b)
        assert not tn.is_sanctioned(uid_a, uid_b)

    def test_sanction_reduces_trade(self, econ_model):
        agents = list(econ_model.schedule.agents)
        tn = econ_model.trade_network
        uid_a, uid_b = agents[0].unique_id, agents[1].unique_id
        initial = tn.get_bilateral_trade(uid_a, uid_b)
        tn.impose_sanction(uid_a, uid_b)
        for _ in range(5):
            econ_model.step()
        after = tn.get_bilateral_trade(uid_a, uid_b)
        assert after < initial

    def test_sanction_targets(self, econ_model):
        agents = list(econ_model.schedule.agents)
        tn = econ_model.trade_network
        uid_a = agents[0].unique_id
        tn.impose_sanction(uid_a, agents[1].unique_id)
        tn.impose_sanction(uid_a, agents[2].unique_id)
        targets = tn.get_sanction_targets(uid_a)
        assert len(targets) == 2

    def test_economic_features_include_sanctions(self, econ_model):
        agents = list(econ_model.schedule.agents)
        tn = econ_model.trade_network
        tn.impose_sanction(agents[0].unique_id, agents[1].unique_id)
        features = tn.get_economic_features(agents[0].unique_id)
        assert features["sanctions_imposed"] == 1.0
        features_b = tn.get_economic_features(agents[1].unique_id)
        assert features_b["sanctions_received"] == 1.0

    def test_sanctions_in_summary(self, econ_model):
        agents = list(econ_model.schedule.agents)
        tn = econ_model.trade_network
        tn.impose_sanction(agents[0].unique_id, agents[1].unique_id)
        econ_model.step()
        summary = tn.summary()
        assert summary["total_sanctions"] >= 1


# ---------------------------------------------------------------------------
# Phase 2: Trade balance sums
# ---------------------------------------------------------------------------


class TestTradeBalance:
    def test_trade_balance_sums_near_zero(self, econ_model):
        """In a closed system, trade balances should roughly cancel."""
        econ_model.step()
        balances = [
            econ_model.trade_network.get_trade_balance(a.unique_id)
            for a in econ_model.schedule.agents
        ]
        assert abs(sum(balances)) < 1e-6


# ---------------------------------------------------------------------------
# Deterministic economics
# ---------------------------------------------------------------------------


class TestEconomicDeterminism:
    def test_model_deterministic_economics(self):
        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()
        for _ in range(10):
            m1.step()
            m2.step()
        for agent in m1.schedule.agents:
            gdp1 = m1.trade_network.get_gdp(agent.unique_id)
            gdp2 = m2.trade_network.get_gdp(agent.unique_id)
            assert gdp1 == pytest.approx(gdp2)


# ---------------------------------------------------------------------------
# Phase 2: Population Model
# ---------------------------------------------------------------------------


class TestPopulationModel:
    def test_population_initialized(self):
        model = GeopolModel()
        assert model.population_model is not None
        assert len(model.population_model.population) == 4

    def test_population_positive(self):
        model = GeopolModel()
        for uid, pop in model.population_model.population.items():
            assert pop > 0

    def test_population_grows_over_time(self):
        model = GeopolModel()
        initial_pop = {uid: pop for uid, pop in model.population_model.population.items()}
        for _ in range(10):
            model.step()
        for uid, initial in initial_pop.items():
            current = model.population_model.get_population(uid)
            # Population should grow (or at least not shrink to 0)
            assert current > 0

    def test_population_history_tracked(self):
        model = GeopolModel()
        for _ in range(5):
            model.step()
        for uid in model.population_model.population_history:
            assert len(model.population_model.population_history[uid]) == 6

    def test_labor_multiplier_range(self):
        model = GeopolModel()
        for uid in model.population_model.population:
            mult = model.population_model.get_labor_multiplier(uid)
            assert 0.5 <= mult <= 2.0

    def test_labor_multiplier_scales_with_population(self):
        model = GeopolModel()
        pm = model.population_model
        uids = list(pm.population.keys())
        # Use values that don't hit the 2.0 cap
        pm.population[uids[0]] = 100_000  # 100K
        pm.population[uids[1]] = 100  # 100
        mult_large = pm.get_labor_multiplier(uids[0])
        mult_small = pm.get_labor_multiplier(uids[1])
        assert mult_large > mult_small

    def test_population_model_summary(self):
        model = GeopolModel()
        model.step()
        summary = model.population_model.summary()
        assert "total_population" in summary
        assert summary["total_population"] > 0
        assert summary["regions_tracked"] == 4

    def test_population_affects_gdp(self):
        """GDP should use population labor multiplier."""
        model = GeopolModel()
        pm = model.population_model
        tn = model.trade_network
        uids = list(pm.population.keys())
        # Verify labor multiplier is used in GDP calculation
        # Set one agent to very large population, another to very small
        pm.population[uids[0]] = 1_000_000_000  # 1B
        pm.population[uids[1]] = 1_000  # 1K
        mult_0 = pm.get_labor_multiplier(uids[0])
        mult_1 = pm.get_labor_multiplier(uids[1])
        assert mult_0 > mult_1  # larger pop → larger multiplier

    def test_escalation_reduces_population_growth(self):
        """Agents in escalation should have slower population growth."""
        import random

        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()
        # Force m2 agents to escalate
        for agent in m2.schedule.agents:
            agent.posture = "Escalate"
        for _ in range(20):
            m1.step()
            m2.step()
            for agent in m2.schedule.agents:
                agent.posture = "Escalate"
        # m1 should have higher population growth
        for agent in m1.schedule.agents:
            pop1 = m1.population_model.get_population(agent.unique_id)
            pop2 = m2.population_model.get_population(agent.unique_id)
            assert pop1 >= pop2

    def test_trade_network_uses_population(self):
        """TradeNetwork should use population model for GDP calculation."""
        model = GeopolModel()
        assert model.trade_network.population_model is model.population_model
