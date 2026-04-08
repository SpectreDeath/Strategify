"""Tests for geopolitical theory modules.

Covers theory implementations: Realpolitik, Democratic Peace, Power Transition,
Offensive Realism, Defensive Realism, Liberal Institutionalism, Constructivism.
"""

from unittest.mock import MagicMock

import pytest

from strategify.theory import (
    DEFAULT_REGISTRY,
    Constructivism,
    DefensiveRealism,
    DemocraticPeaceTheory,
    LiberalInstitutionalism,
    OffensiveRealism,
    PowerMetric,
    PowerTransitionTheory,
    RealpolitikTheory,
    TheoryRegistry,
    TheoryResult,
)


class MockAgent:
    """Mock agent for testing theories."""

    def __init__(self, region_id="RUS", personality="Neutral", posture="Deescalate"):
        self.region_id = region_id
        self.personality = personality
        self.posture = posture
        self.unique_id = 1
        self.capabilities = {"military": 0.7, "economic": 0.6}


class MockModel:
    """Mock model for testing theories."""

    def __init__(self, n_agents=4):
        self.n_agents = n_agents
        self.schedule = MagicMock()
        self.relations = MagicMock()
        self.trade_network = None
        self.influence_map = None
        self.env_manager = None

        agents = [
            MockAgent("RUS", "Aggressor", "Escalate"),
            MockAgent("UKR", "Pacifist", "Deescalate"),
            MockAgent("POL", "Tit-for-Tat", "Deescalate"),
            MockAgent("BLR", "Neutral", "Deescalate"),
        ]
        self.schedule.agents = agents[:n_agents]
        self.relations.get_allies = lambda uid: [2, 3] if uid == 1 else []
        self.relations.get_relation = lambda uid1, uid2: 0.5 if uid1 != uid2 else 0.0


class TestPowerMetric:
    """Tests for PowerMetric enum."""

    def test_power_metric_values(self):
        assert PowerMetric.MILITARY.value == "military"
        assert PowerMetric.ECONOMIC.value == "economic"
        assert PowerMetric.COMPOSITE.value == "composite"
        assert PowerMetric.GDP.value == "gdp"

    def test_power_metric_members(self):
        assert len(PowerMetric) == 4


class TestTheoryResult:
    """Tests for TheoryResult dataclass."""

    def test_theory_result_defaults(self):
        result = TheoryResult(
            theory="Test",
            recommended_action="deescalate",
            confidence=0.8,
            rationale="Test rationale",
        )
        assert result.power_assessment == {}

    def test_theory_result_with_power_assessment(self):
        result = TheoryResult(
            theory="Test",
            recommended_action="deescalate",
            confidence=0.8,
            rationale="Test rationale",
            power_assessment={"military": 0.7, "economic": 0.6},
        )
        assert result.power_assessment == {"military": 0.7, "economic": 0.6}


class TestRealpolitikTheory:
    """Tests for RealpolitikTheory."""

    @pytest.fixture
    def theory(self):
        return RealpolitikTheory()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Realpolitik"

    def test_theory_description(self, theory):
        assert theory.description == "Power politics and balance of power"

    def test_evaluate_balance_action(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Deescalate")
        agent.capabilities = {"military": 0.3, "economic": 0.3}
        result = theory.evaluate(agent, mock_model)
        assert result.theory == "Realpolitik"
        assert result.confidence > 0

    def test_evaluate_exploit_action(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Deescalate")
        agent.capabilities = {"military": 1.0, "economic": 1.0}
        result = theory.evaluate(agent, mock_model)
        assert result.recommended_action in ("exploit", "balance", "maintain")

    def test_evaluate_maintain_action(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Deescalate")
        agent.capabilities = {"military": 0.6, "economic": 0.6}
        result = theory.evaluate(agent, mock_model)
        assert result.recommended_action in ("balance", "exploit", "maintain")

    def test_calculate_power_military(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.8, "economic": 0.5}
        power = theory.calculate_power(agent, mock_model, PowerMetric.MILITARY)
        assert 0 <= power <= 2.0

    def test_calculate_power_economic(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.5, "economic": 0.8}
        power = theory.calculate_power(agent, mock_model, PowerMetric.ECONOMIC)
        assert 0 <= power <= 2.0

    def test_calculate_power_composite(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.6, "economic": 0.7}
        power = theory.calculate_power(agent, mock_model, PowerMetric.COMPOSITE)
        assert 0 <= power <= 2.0


class TestDemocraticPeaceTheory:
    """Tests for DemocraticPeaceTheory."""

    @pytest.fixture
    def theory(self):
        return DemocraticPeaceTheory()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Democratic Peace"

    def test_evaluate_pacifist_agent(self, theory, mock_model):
        agent = MockAgent("RUS", "Pacifist", "Deescalate")
        result = theory.evaluate(agent, mock_model)
        assert result.recommended_action == "deescalate"
        assert result.confidence == 0.9

    def test_evaluate_with_democratic_rival(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Escalate")
        result = theory.evaluate(agent, mock_model)
        assert result.theory == "Democratic Peace"

    def test_calculate_power_with_inst_bonus(self, theory, mock_model):
        agent = MockAgent("RUS", "Pacifist", "Deescalate")
        agent.capabilities = {"military": 0.5, "economic": 0.5}
        power = theory.calculate_power(agent, mock_model)
        assert power > 0.5


class TestPowerTransitionTheory:
    """Tests for PowerTransitionTheory."""

    @pytest.fixture
    def theory(self):
        return PowerTransitionTheory()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Power Transition"

    def test_evaluate_status_quo_power(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Deescalate")
        agent.capabilities = {"military": 1.0, "economic": 1.0}
        result = theory.evaluate(agent, mock_model)
        assert result.theory == "Power Transition"

    def test_evaluate_approaching_parity(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Deescalate")
        agent.capabilities = {"military": 0.4, "economic": 0.4}
        result = theory.evaluate(agent, mock_model)
        assert result.recommended_action in ("expand", "bide", "consolidate")

    def test_calculate_power_growth_boost(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.5, "economic": 0.5}
        power = theory.calculate_power(agent, mock_model)
        assert power > 0


class TestOffensiveRealism:
    """Tests for OffensiveRealism."""

    @pytest.fixture
    def theory(self):
        return OffensiveRealism()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Offensive Realism"

    def test_evaluate_aggressor_with_advantage(self, theory, mock_model):
        agent = MockAgent("RUS", "Aggressor", "Deescalate")
        agent.capabilities = {"military": 1.0, "economic": 1.0}
        result = theory.evaluate(agent, mock_model)
        assert result.theory == "Offensive Realism"

    def test_calculate_power_military_weighted(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.8, "economic": 0.2}
        power = theory.calculate_power(agent, mock_model)
        assert power > 0.5


class TestDefensiveRealism:
    """Tests for DefensiveRealism."""

    @pytest.fixture
    def theory(self):
        return DefensiveRealism()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Defensive Realism"

    def test_evaluate_insufficient_alliances(self, theory, mock_model):
        agent = MockAgent("RUS", "Neutral", "Deescalate")
        result = theory.evaluate(agent, mock_model)
        assert result.recommended_action in ("balance", "maintain")

    def test_calculate_power_adequacy_threshold(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.3, "economic": 0.5}
        power = theory.calculate_power(agent, mock_model)
        assert power >= 0.3


class TestLiberalInstitutionalism:
    """Tests for LiberalInstitutionalism."""

    @pytest.fixture
    def theory(self):
        return LiberalInstitutionalism()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Liberal Institutionalism"

    def test_evaluate_cooperate_trade(self, theory, mock_model):
        mock_model.trade_network = MagicMock()
        mock_model.trade_network.get_trade_balance = lambda uid: 10.0
        agent = MockAgent()
        result = theory.evaluate(agent, mock_model)
        assert result.theory == "Liberal Institutionalism"

    def test_calculate_power_with_network_bonus(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.5, "economic": 0.5}
        power = theory.calculate_power(agent, mock_model)
        assert power >= 0.5


class TestConstructivism:
    """Tests for Constructivism."""

    @pytest.fixture
    def theory(self):
        return Constructivism()

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_theory_name(self, theory):
        assert theory.name == "Constructivism"

    def test_evaluate_identity_based(self, theory, mock_model):
        agent = MockAgent("RUS", "Aggressor", "Escalate")
        result = theory.evaluate(agent, mock_model)
        assert result.theory == "Constructivism"

    def test_calculate_power_identity_bonus(self, theory, mock_model):
        agent = MockAgent()
        agent.capabilities = {"military": 0.5, "economic": 0.5}
        power = theory.calculate_power(agent, mock_model)
        assert power > 0


class TestTheoryRegistry:
    """Tests for TheoryRegistry."""

    def test_registry_init(self):
        registry = TheoryRegistry()
        assert len(registry._theories) > 0

    def test_registry_register(self):
        registry = TheoryRegistry()
        theory = RealpolitikTheory()
        registry.register(theory)
        assert theory.name in registry._theories

    def test_registry_get(self):
        registry = TheoryRegistry()
        theory = registry.get("Realpolitik")
        assert theory is not None
        assert theory.name == "Realpolitik"

    def test_registry_decide(self):
        registry = TheoryRegistry()
        model = MockModel()
        agent = MockAgent()
        result = registry.decide(agent, model, "RUS")
        assert isinstance(result, TheoryResult)


class TestDefaultRegistry:
    """Tests for default registry."""

    def test_default_registry_exists(self):
        assert DEFAULT_REGISTRY is not None
        assert len(DEFAULT_REGISTRY.list_theories()) > 0

    def test_default_registry_list_theories(self):
        theories = DEFAULT_REGISTRY.list_theories()
        assert "Realpolitik" in theories
        assert "Democratic Peace" in theories

    def test_default_registry_get(self):
        theory = DEFAULT_REGISTRY.get("Realpolitik")
        assert theory is not None
        assert theory.name == "Realpolitik"

    def test_default_registry_decide(self):
        model = MockModel()
        agent = MockAgent()
        result = DEFAULT_REGISTRY.decide(agent, model, "Realpolitik")
        assert isinstance(result, TheoryResult)
