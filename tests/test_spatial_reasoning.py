"""Tests for spatial reasoning engine."""

from unittest.mock import MagicMock

from strategify.reasoning.spatial import (
    SpatialReasoningEngine,
    TerrainFeatures,
    integrate_spatial_reasoning,
)


def test_terrain_features_init():
    tf = TerrainFeatures(
        defensibility=0.8,
        concealment=0.7,
        mobility=0.6,
        key_terrain=True,
        chokepoint=False,
        elevation_advantage=100.0,
    )
    assert tf.defensibility == 0.8
    assert tf.key_terrain is True


def test_spatial_reasoning_engine_features():
    mock_agent = MagicMock()
    mock_agent.region_id = "alpha"
    mock_model = MagicMock()
    mock_model.adjacency = {"alpha": ["bravo", "charlie"]}

    features = SpatialReasoningEngine.get_terrain_features(mock_agent, mock_model)
    assert features.defensibility >= 0.0
    assert "alpha" in SpatialReasoningEngine.TERRAIN_CACHE


def test_calculate_tactical_advantage():
    agent_a = MagicMock()
    agent_a.region_id = "alpha"
    agent_b = MagicMock()
    agent_b.region_id = "bravo"

    mock_model = MagicMock()
    mock_model.adjacency = {"alpha": ["bravo"], "bravo": ["alpha"]}

    adv = SpatialReasoningEngine.calculate_tactical_advantage(agent_a, agent_b, mock_model)
    assert "position_score" in adv
    assert "flanking_score" in adv


def test_recommend_position():
    mock_model = MagicMock()
    mock_model.adjacency = {"alpha": ["bravo", "charlie"]}

    rec = SpatialReasoningEngine.recommend_position("alpha", "charlie", mock_model)
    assert "recommended" in rec


def test_integrate_spatial_reasoning():
    agent = MagicMock()
    agent.region_id = "alpha"
    agent.target_region = "bravo"

    target_agent = MagicMock()
    target_agent.region_id = "bravo"

    mock_model = MagicMock()
    mock_model.get_agent_by_region.return_value = target_agent
    mock_model.adjacency = {"alpha": ["bravo"]}

    base_decision = {"action": "attack"}
    res = integrate_spatial_reasoning(agent, mock_model, base_decision)
    assert "tactical_advantage" in res
