"""Tests for visualization modules.

Tests choropleth, maps, export, and network visualizations.
"""

from unittest.mock import MagicMock

import pytest

from strategify.config.settings import get_region_hex_color
from strategify.viz.choropleth import _ESCALATION_CMAP, _POSTURE_CMAP, HeadlessChoropleth


class MockAgent:
    """Mock agent for viz tests."""

    def __init__(self, region_id="RUS", posture="Deescalate"):
        self.region_id = region_id
        self.posture = posture
        self.unique_id = 1
        self.capabilities = {"military": 0.5, "economic": 0.5}
        self.stability = 0.8


class MockModel:
    """Mock model for viz tests."""

    def __init__(self, n_agents=4):
        self.schedule = MagicMock()
        self.n_agents = n_agents
        self.schedule.agents = [
            MockAgent("RUS", "Escalate"),
            MockAgent("UKR", "Deescalate"),
            MockAgent("POL", "Deescalate"),
            MockAgent("BLR", "Deescalate"),
        ][:n_agents]


class TestHeadlessChoropleth:
    """Tests for HeadlessChoropleth."""

    @pytest.fixture
    def mock_model(self):
        return MockModel()

    def test_init(self, mock_model):
        renderer = HeadlessChoropleth(mock_model)
        assert renderer.model == mock_model
        assert renderer.color_mode == "posture"

    def test_init_custom_color_mode(self, mock_model):
        renderer = HeadlessChoropleth(mock_model, color_mode="escalation_level")
        assert renderer.color_mode == "escalation_level"

    def test_init_custom_figsize(self, mock_model):
        renderer = HeadlessChoropleth(mock_model, figsize=(12, 10))
        assert renderer.figsize == (12, 10)

    def test_escation_cmap_keys(self):
        assert "Cooperative" in _ESCALATION_CMAP
        assert "Diplomatic" in _ESCALATION_CMAP
        assert "Economic" in _ESCALATION_CMAP
        assert "Military" in _ESCALATION_CMAP

    def test_posture_cmap_keys(self):
        assert "Escalate" in _POSTURE_CMAP
        assert "Deescalate" in _POSTURE_CMAP


class TestGetRegionHexColor:
    """Tests for get_region_hex_color."""

    def test_known_region(self):
        color = get_region_hex_color("RUS")
        assert isinstance(color, str)
        assert color.startswith("#")

    def test_unknown_region(self):
        color = get_region_hex_color("UNKNOWN")
        assert isinstance(color, str)
        assert color.startswith("#")


class TestVizConstants:
    """Tests for visualization constants."""

    def test_color_format(self):
        for _, color in _POSTURE_CMAP.items():
            assert color.startswith("#")
            assert len(color) == 7

    def test_escalation_colors_valid(self):
        for _, color in _ESCALATION_CMAP.items():
            assert color.startswith("#")
            assert len(color) == 7
