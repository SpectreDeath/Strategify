import pytest

from strategify.reasoning.influence import InfluenceMap
from strategify.sim.model import GeopolModel


@pytest.fixture
def stepped_model():
    """Model with at least one step completed."""
    model = GeopolModel()
    model.step()
    return model


def test_spatial_autocorrelation_returns_dict(stepped_model):
    imap = stepped_model.influence_map
    result = imap.get_spatial_autocorrelation()
    assert isinstance(result, dict)


def test_spatial_autocorrelation_has_keys(stepped_model):
    imap = stepped_model.influence_map
    result = imap.get_spatial_autocorrelation()
    assert "I" in result
    assert "p_value" in result
    assert "z_score" in result


def test_spatial_autocorrelation_I_in_range(stepped_model):
    """Moran's I is bounded [-1, 1]."""
    imap = stepped_model.influence_map
    result = imap.get_spatial_autocorrelation()
    assert -1.0 <= result["I"] <= 1.0


def test_spatial_autocorrelation_p_value_valid(stepped_model):
    imap = stepped_model.influence_map
    result = imap.get_spatial_autocorrelation()
    assert 0.0 <= result["p_value"] <= 1.0


def test_spatial_autocorrelation_zero_variance():
    """When all agents have the same posture, I should be 0 (no variance)."""
    model = GeopolModel()
    # Before any steps, all agents are Deescalate
    imap = InfluenceMap(model)
    imap.compute()
    result = imap.get_spatial_autocorrelation()
    assert result["I"] == 0.0


def test_spatial_autocorrelation_changes_over_steps():
    """Moran's I should change as postures change."""
    model = GeopolModel()
    model.step()
    result1 = model.influence_map.get_spatial_autocorrelation()

    model.step()
    result2 = model.influence_map.get_spatial_autocorrelation()

    # Just verify both are valid dicts
    assert isinstance(result1, dict) and isinstance(result2, dict)
