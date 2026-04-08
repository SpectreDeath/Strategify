"""Sensitivity analysis for geopolitical simulation parameters.

Uses SALib to compute Sobol indices, identifying which parameters
(military strength, economic weight, alliance commitment) most
influence simulation outcomes.
"""

from __future__ import annotations

import numpy as np
from SALib.analyze import sobol as sobol_analyze
from SALib.sample import sobol as sobol_sample


def run_sensitivity_analysis(
    model_factory,
    param_ranges: dict[str, tuple[float, float]],
    n_samples: int = 64,
    n_steps: int = 10,
    metric_fn=None,
) -> dict:
    """Run global sensitivity analysis on simulation parameters.

    Parameters
    ----------
    model_factory:
        Callable that accepts keyword params and returns a GeopolModel.
    param_ranges:
        Dict of param_name -> (low, high) bounds.
        Example: {"alpha_military": (0.1, 1.0), "bravo_military": (0.1, 1.0)}
    n_samples:
        Base sample size for Saltelli sampling (actual runs = n_samples * (2D + 2)).
    n_steps:
        Number of simulation steps per run.
    metric_fn:
        Callable(model) -> float. Default: count of Escalate postures at final step.

    Returns
    -------
    dict
        SALib Sobol analysis results with S1, ST, S1_conf, ST_conf.
    """
    param_names = list(param_ranges.keys())
    bounds = [param_ranges[k] for k in param_names]
    problem = {
        "num_vars": len(param_names),
        "names": param_names,
        "bounds": bounds,
    }

    # Generate samples
    param_values = sobol_sample.sample(problem, n_samples, calc_second_order=False)

    if metric_fn is None:

        def metric_fn(model):
            return sum(1 for a in model.schedule.agents if a.posture == "Escalate")

    # Run model for each sample
    Y = np.zeros(param_values.shape[0])
    for i, params in enumerate(param_values):
        kwargs = dict(zip(param_names, params, strict=False))
        model = model_factory(**kwargs)
        for _ in range(n_steps):
            model.step()
        Y[i] = metric_fn(model)

    # Analyze
    Si = sobol_analyze.analyze(problem, Y, calc_second_order=False)
    return {
        "S1": dict(zip(param_names, Si["S1"], strict=False)),
        "ST": dict(zip(param_names, Si["ST"], strict=False)),
        "S1_conf": dict(zip(param_names, Si["S1_conf"], strict=False)),
        "ST_conf": dict(zip(param_names, Si["ST_conf"], strict=False)),
    }


def rank_parameters(sobol_results: dict) -> list[tuple[str, float]]:
    """Rank parameters by total-order Sobol index (ST).

    Higher ST = more influence on output variance.
    """
    st = sobol_results["ST"]
    return sorted(st.items(), key=lambda x: x[1], reverse=True)
