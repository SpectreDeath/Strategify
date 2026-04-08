import numpy as np

from strategify.analysis.optimization import GeopolResourceProblem, optimize_resources
from strategify.sim.model import GeopolModel


def _model_factory(military_fracs=None):
    """Create a GeopolModel with optional military fraction overrides."""
    model = GeopolModel()
    if military_fracs is not None:
        for i, agent in enumerate(model.schedule.agents):
            frac = military_fracs[i % len(military_fracs)]
            agent.capabilities["military"] = float(frac)
            agent.capabilities["economic"] = 1.0 - float(frac)
    return model


def test_problem_creation():
    problem = GeopolResourceProblem(_model_factory, n_regions=4, n_steps=3)
    assert problem.n_var == 4
    assert problem.n_obj == 3
    assert problem.xl is not None
    assert problem.xu is not None


def test_problem_bounds():
    problem = GeopolResourceProblem(_model_factory, n_regions=4, n_steps=3)
    assert np.allclose(problem.xl, 0.1)
    assert np.allclose(problem.xu, 0.9)


def test_optimize_returns_valid_structure():
    result = optimize_resources(
        _model_factory,
        n_regions=4,
        n_generations=2,
        pop_size=4,
    )
    assert "pareto_front" in result
    assert "solutions" in result
    assert "n_solutions" in result
    assert isinstance(result["n_solutions"], int)
    assert result["n_solutions"] >= 0


def test_optimize_solutions_have_correct_shape():
    result = optimize_resources(
        _model_factory,
        n_regions=4,
        n_generations=2,
        pop_size=4,
    )
    if result["n_solutions"] > 0:
        assert result["pareto_front"].shape[1] == 3  # 3 objectives
        assert result["solutions"].shape[1] == 4  # 4 decision variables


def test_optimize_solutions_within_bounds():
    result = optimize_resources(
        _model_factory,
        n_regions=4,
        n_generations=2,
        pop_size=4,
    )
    if result["n_solutions"] > 0:
        assert np.all(result["solutions"] >= 0.1)
        assert np.all(result["solutions"] <= 0.9)
