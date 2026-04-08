"""Tests for dynamics module.

Tests FactionalPolitics, IdeologyModel, and PublicOpinion classes.
"""

from unittest.mock import MagicMock

import pytest

from strategify.dynamics import (
    Faction,
    FactionalPolitics,
    FactionType,
    IdeologyAxis,
    IdeologyModel,
    PublicOpinion,
)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, personality="Neutral"):
        self.personality = personality
        self.region_id = "RUS"
        self.unique_id = 1
        self.capabilities = {"military": 0.5, "economic": 0.5}
        self.posture = "Deescalate"


class MockModel:
    """Mock model for testing."""

    def __init__(self):
        self.schedule = MagicMock()
        self.schedule.agents = [MockAgent()]


class TestFactionType:
    """Tests for FactionType enum."""

    def test_faction_types_exist(self):
        assert FactionType.MILITARY.value == "military"
        assert FactionType.ECONOMIC.value == "economic"
        assert FactionType.DIPLOMATIC.value == "diplomatic"
        assert FactionType.SECURITY.value == "security"
        assert FactionType.INTELLIGENCE.value == "intelligence"
        assert FactionType.PROPAGANDA.value == "propaganda"


class TestIdeologyAxis:
    """Tests for IdeologyAxis enum."""

    def test_ideology_axes_exist(self):
        assert IdeologyAxis.LEFT_RIGHT.value == "left_right"
        assert IdeologyAxis.NATIONALIST.value == "nationalist"
        assert IdeologyAxis.HAWK_DOVE.value == "hawk_dove"


class TestFaction:
    """Tests for Faction dataclass."""

    def test_faction_init(self):
        faction = Faction(
            faction_type=FactionType.MILITARY,
            power=0.5,
            preferred_posture="Escalate",
            key_people=["General"],
            policy_preferences={"defense": 0.8},
        )
        assert faction.faction_type == FactionType.MILITARY
        assert faction.power == 0.5
        assert faction.preferred_posture == "Escalate"


class TestFactionalPolitics:
    """Tests for FactionalPolitics class."""

    @pytest.fixture
    def aggressor_agent(self):
        return MockAgent(personality="Aggressor")

    @pytest.fixture
    def pacifist_agent(self):
        return MockAgent(personality="Pacifist")

    @pytest.fixture
    def neutral_agent(self):
        return MockAgent(personality="Neutral")

    def test_factional_politics_init_aggressor(self, aggressor_agent):
        fp = FactionalPolitics(aggressor_agent)
        assert len(fp.get_factions()) == 4

    def test_factional_politics_init_pacifist(self, pacifist_agent):
        fp = FactionalPolitics(pacifist_agent)
        assert len(fp.get_factions()) == 4

    def test_get_dominant_faction_aggressor(self, aggressor_agent):
        fp = FactionalPolitics(aggressor_agent)
        assert fp.get_dominant_faction() == FactionType.MILITARY

    def test_get_dominant_posture_aggressor(self, aggressor_agent):
        fp = FactionalPolitics(aggressor_agent)
        assert fp.get_dominant_posture() == "Escalate"

    def test_get_dominant_faction_pacifist(self, pacifist_agent):
        fp = FactionalPolitics(pacifist_agent)
        assert fp.get_dominant_faction() == FactionType.ECONOMIC

    def test_apply_external_shock_military_defeat(self, aggressor_agent):
        fp = FactionalPolitics(aggressor_agent)
        initial_diplomatic_power = sum(
            f.power for f in fp.get_factions() if f.faction_type == FactionType.DIPLOMATIC
        )
        fp.apply_external_shock("military_defeat", magnitude=0.2)
        new_diplomatic_power = sum(
            f.power for f in fp.get_factions() if f.faction_type == FactionType.DIPLOMATIC
        )
        assert new_diplomatic_power > initial_diplomatic_power

    def test_get_faction_balance_hawk_dominant(self, aggressor_agent):
        fp = FactionalPolitics(aggressor_agent)
        assert fp.get_faction_balance() == "hawk_dominant"

    def test_get_faction_balance_dove_dominant(self, pacifist_agent):
        fp = FactionalPolitics(pacifist_agent)
        assert fp.get_faction_balance() == "dove_dominant"


class TestIdeologyModel:
    """Tests for IdeologyModel class."""

    def test_ideology_init_aggressor(self):
        ideology = IdeologyModel(personality="Aggressor")
        hawk_pos = ideology.get_position(IdeologyAxis.HAWK_DOVE)
        assert isinstance(hawk_pos, (float, int)) and hawk_pos > 0.5

    def test_ideology_init_pacifist(self):
        ideology = IdeologyModel(personality="Pacifist")
        hawk_pos = ideology.get_position(IdeologyAxis.HAWK_DOVE)
        assert isinstance(hawk_pos, (float, int)) and hawk_pos < 0.5

    def test_ideology_init_neutral(self):
        ideology = IdeologyModel(personality="Neutral")
        pos = ideology.get_position()
        assert isinstance(pos, dict)

    def test_ideology_get_ideology_label(self):
        ideology = IdeologyModel(personality="Aggressor")
        label = ideology.get_ideology_label()
        assert isinstance(label, str)
        assert len(label) > 0


class TestPublicOpinion:
    """Tests for PublicOpinion class."""

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_public_opinion_init(self, mock_model):
        agent = MockAgent()
        po = PublicOpinion(mock_model, "RUS")
        assert po is not None

    def test_get_approval_rating(self, mock_model):
        agent = MockAgent()
        po = PublicOpinion(mock_model, "RUS")
        rating = po.get_approval_rating()
        assert isinstance(rating, (float, int))
        assert 0 <= rating <= 1

    def test_get_trend(self, mock_model):
        agent = MockAgent()
        mock_model.schedule.agents = [agent]
        po = PublicOpinion(mock_model, "RUS")
        trend = po.get_trend()
        assert isinstance(trend, str)
        assert trend in ("rising", "falling", "stable")

    def test_update_approval(self, mock_model):
        agent = MockAgent()
        mock_model.schedule.agents = [agent]
        po = PublicOpinion(mock_model, "RUS")
        po.update_approval()
        assert len(po._approval_history) > 1
