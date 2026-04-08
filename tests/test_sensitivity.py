import pytest

from strategify.analysis.sensitivity import rank_parameters, run_sensitivity_analysis
from strategify.sim.model import GeopolModel


def _model_factory(**kwargs):
    """Create a model with configurable parameters."""
    # Override military strengths from kwargs
    model = GeopolModel()
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        military_key = f"{rid}_military"
        if military_key in kwargs:
            agent.capabilities["military"] = kwargs[military_key]
    return model


@pytest.mark.slow
def test_sensitivity_analysis_returns_results():
    """SALib integration returns valid Sobol indices."""
    param_ranges = {
        "alpha_military": (0.2, 1.0),
        "bravo_military": (0.2, 1.0),
    }
    results = run_sensitivity_analysis(
        _model_factory,
        param_ranges,
        n_samples=8,
        n_steps=5,
    )
    assert "S1" in results
    assert "ST" in results
    assert "alpha_military" in results["S1"]
    assert "bravo_military" in results["S1"]


@pytest.mark.slow
def test_sensitivity_analysis_S1_in_range():
    """First-order Sobol indices are in [0, 1].

    Requires at least 2 parameters for meaningful Sobol indices.
    """
    import math

    param_ranges = {
        "alpha_military": (0.2, 1.0),
        "bravo_military": (0.2, 1.0),
    }
    results = run_sensitivity_analysis(
        _model_factory,
        param_ranges,
        n_samples=8,
        n_steps=3,
    )
    for param, s1 in results["S1"].items():
        if math.isnan(s1):
            continue
        assert 0.0 <= s1 <= 1.0 + 1e-6, f"S1 for {param} = {s1}"


def test_rank_parameters():
    """Ranking sorts by ST in descending order."""
    sobol_results = {
        "S1": {"a": 0.3, "b": 0.1},
        "ST": {"a": 0.5, "b": 0.8},
        "S1_conf": {"a": 0.1, "b": 0.1},
        "ST_conf": {"a": 0.1, "b": 0.1},
    }
    ranked = rank_parameters(sobol_results)
    assert ranked[0][0] == "b"
    assert ranked[1][0] == "a"
