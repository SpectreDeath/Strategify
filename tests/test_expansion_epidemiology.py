"""Tests for Spatial Metapopulation, Optimal Control, and Gymnasium EpidemicEnv."""

import numpy as np

from strategify.epidemiology.metapopulation import MetapopulationODE
from strategify.epidemiology.optimal_control import OptimalControlSolver
from strategify.rl.epidemic_env import EpidemicEnv


def test_metapopulation_vectorized_ode():
    # 3-node linear graph: 0 <-> 1 <-> 2
    adj = [
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 1.0],
        [0.0, 1.0, 0.0],
    ]
    pops = [100_000, 200_000, 150_000]

    solver = MetapopulationODE(adjacency_matrix=adj, populations=pops, mobility_coupling=0.02)

    s0 = [0.99, 0.99, 0.99]
    i0 = [0.01, 0.0, 0.0]  # Infection seeded only at Node 0
    x0 = [0.5, 0.5, 0.5]

    solution = solver.solve(
        initial_susceptible=s0,
        initial_infected=i0,
        initial_cooperation=x0,
        t_span=(0.0, 15.0),
        n_eval_points=30,
    )

    assert solution.susceptible_matrix.shape == (30, 3)
    assert solution.infected_matrix.shape == (30, 3)

    # Cross-node transmission should seed infection at Node 1 and Node 2
    assert solution.infected_matrix[-1, 1] > 0.0
    assert solution.infected_matrix[-1, 2] > 0.0


def test_optimal_control_solver_forward_backward_sweep():
    solver = OptimalControlSolver(beta_max=0.5, gamma=0.1, cost_disease_cd=10.0, cost_effort_w=1.0)
    result = solver.solve_forward_backward_sweep(
        initial_state=(0.99, 0.01, 0.0),
        t_span=(0.0, 10.0),
        n_steps=20,
        max_iterations=15,
    )

    assert len(result.t) == 20
    assert len(result.optimal_control_u) == 20
    assert result.objective_cost_j > 0.0
    assert np.all(result.optimal_control_u >= 0.0)
    assert np.all(result.optimal_control_u <= 1.0)


def test_gymnasium_epidemic_env():
    env = EpidemicEnv(population=100_000, max_steps=10)
    obs, info = env.reset()

    assert obs.shape == (8,)
    assert 0.0 <= obs[0] <= 1.0  # Susceptible fraction

    # Apply continuous action [u_NPI, u_vax, u_icu]
    action = [0.8, 0.5, 0.3]
    next_obs, reward, terminated, truncated, step_info = env.step(action)

    assert next_obs.shape == (8,)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "rt" in step_info
