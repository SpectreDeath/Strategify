"""Multi-objective optimization of geopolitical strategies using pymoo.

Finds Pareto-optimal resource allocation strategies balancing
competing national objectives (military vs. economic vs. diplomacy).
"""

from __future__ import annotations

import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize as pymoo_minimize


class GeopolResourceProblem(Problem):
    """Multi-objective problem: maximize stability while minimizing escalation.

    Decision variables: resource allocation per region (military fraction).
    Objectives:
        1. Minimize total escalation events (stability)
        2. Maximize economic output
        3. Minimize diplomatic friction (alliance disruption)
    """

    def __init__(self, model_factory, n_regions: int = 4, n_steps: int = 10):
        self.model_factory = model_factory
        self.n_regions = n_regions
        self.n_steps = n_steps

        # Decision variables: military fraction per region [0.1, 0.9]
        super().__init__(
            n_var=n_regions,
            n_obj=3,
            n_constr=0,
            xl=np.full(n_regions, 0.1),
            xu=np.full(n_regions, 0.9),
        )

    def _evaluate(self, X, out, *args, **kwargs):
        F = np.zeros((X.shape[0], self.n_obj))

        for i, military_fracs in enumerate(X):
            model = self.model_factory(military_fracs=military_fracs)

            escalations = 0
            economic_total = 0.0
            alliance_friction = 0.0

            for _ in range(self.n_steps):
                model.step()

            for agent in model.schedule.agents:
                if agent.posture == "Escalate":
                    escalations += 1
                economic_total += agent.capabilities.get("economic", 0.5)

            # Alliance friction: count edges with weight < 0
            for _, _, data in model.relations.graph.edges(data=True):
                if data.get("weight", 0) < 0:
                    alliance_friction += abs(data["weight"])

            F[i, 0] = escalations  # minimize
            F[i, 1] = -economic_total  # minimize (negative = maximize)
            F[i, 2] = alliance_friction  # minimize

        out["F"] = F


def optimize_resources(
    model_factory,
    n_regions: int = 4,
    n_generations: int = 10,
    pop_size: int = 20,
) -> dict:
    """Find Pareto-optimal resource allocations.

    Parameters
    ----------
    model_factory:
        Callable(military_fracs=ndarray) -> GeopolModel.
    n_regions:
        Number of regions to optimize.
    n_generations:
        Number of NSGA2 generations.
    pop_size:
        Population size.

    Returns
    -------
    dict
        {"pareto_front": np.ndarray, "solutions": np.ndarray, "n_solutions": int}
    """
    problem = GeopolResourceProblem(model_factory, n_regions=n_regions)

    algorithm = NSGA2(
        pop_size=pop_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
    )

    res = pymoo_minimize(
        problem,
        algorithm,
        ("n_gen", n_generations),
        seed=42,
        verbose=False,
    )

    return {
        "pareto_front": res.F,
        "solutions": res.X,
        "n_solutions": len(res.F) if res.F is not None else 0,
    }
