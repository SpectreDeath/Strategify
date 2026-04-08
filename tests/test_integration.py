"""Integration tests for full analysis pipelines."""

import pytest

from strategify.analysis.optimization import optimize_resources
from strategify.analysis.sensitivity import rank_parameters, run_sensitivity_analysis
from strategify.sim.model import GeopolModel


def _model_factory(**kwargs):
    model = GeopolModel()
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        military_key = f"{rid}_military"
        if military_key in kwargs:
            agent.capabilities["military"] = kwargs[military_key]
    return model


def _resource_factory(military_fracs=None):
    model = GeopolModel()
    if military_fracs is not None:
        for i, agent in enumerate(model.schedule.agents):
            frac = military_fracs[i % len(military_fracs)]
            agent.capabilities["military"] = float(frac)
            agent.capabilities["economic"] = 1.0 - float(frac)
    return model


@pytest.mark.slow
class TestSensitivityPipeline:
    def test_full_sensitivity_pipeline(self):
        """End-to-end Sobol sensitivity analysis."""
        param_ranges = {
            "alpha_military": (0.2, 1.0),
            "bravo_military": (0.2, 1.0),
        }
        results = run_sensitivity_analysis(
            _model_factory,
            param_ranges,
            n_samples=4,
            n_steps=3,
        )
        assert "S1" in results
        assert "ST" in results
        assert "alpha_military" in results["S1"]
        assert "bravo_military" in results["S1"]

    def test_sensitivity_ranking_sorted(self):
        """Verify ranking returns sorted results."""
        param_ranges = {
            "alpha_military": (0.2, 1.0),
            "bravo_military": (0.2, 1.0),
        }
        results = run_sensitivity_analysis(
            _model_factory,
            param_ranges,
            n_samples=4,
            n_steps=3,
        )
        ranked = rank_parameters(results)
        assert len(ranked) == 2
        assert ranked[0][0] in ["alpha_military", "bravo_military"]
        assert ranked[1][0] in ["alpha_military", "bravo_military"]


class TestOptimizationPipeline:
    def test_full_optimization_pipeline(self):
        """End-to-end NSGA2 optimization."""
        result = optimize_resources(
            _resource_factory,
            n_regions=4,
            n_generations=2,
            pop_size=4,
        )
        assert "pareto_front" in result
        assert "solutions" in result
        assert "n_solutions" in result
        assert result["n_solutions"] >= 0

    def test_optimization_solutions_within_bounds(self):
        """Verify solutions respect bounds."""
        result = optimize_resources(
            _resource_factory,
            n_regions=4,
            n_generations=2,
            pop_size=4,
        )
        if result["n_solutions"] > 0:
            import numpy as np

            assert np.all(result["solutions"] >= 0.1)
            assert np.all(result["solutions"] <= 0.9)
