"""Pontryagin Optimal Control Solver for Epidemic Interventions.

Solves continuous optimal control problems minimizing disease mortality and mitigation effort:
min_{u(t) in [0, 1]} J = integral_0^T [ C_d * I(t) + 0.5 * w * u(t)^2 ] dt
subject to state dynamics dS/dt, dI/dt, dR/dt using forward-backward sweep iterations.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class OptimalControlResult:
    """Optimal control trajectory solution."""

    t: np.ndarray
    susceptible: np.ndarray
    infected: np.ndarray
    recovered: np.ndarray
    optimal_control_u: np.ndarray  # Optimal NPI intervention profile u(t) in [0, 1]
    objective_cost_j: float  # Total cost functional J value


class OptimalControlSolver:
    """Pontryagin Optimal Control Solver for public health policy profiles.

    Parameters
    ----------
    beta_max : float
        Baseline unmitigated transmission rate (default: 0.5).
    gamma : float
        Recovery rate (default: 0.1).
    cost_disease_cd : float
        Weight Cd for disease burden cost (default: 10.0).
    cost_effort_w : float
        Weight w for NPI intervention effort penalty (default: 1.0).
    """

    def __init__(
        self,
        beta_max: float = 0.5,
        gamma: float = 0.1,
        cost_disease_cd: float = 10.0,
        cost_effort_w: float = 1.0,
    ) -> None:
        self.beta_max = beta_max
        self.gamma = gamma
        self.cost_disease_cd = cost_disease_cd
        self.cost_effort_w = cost_effort_w

    def solve_forward_backward_sweep(
        self,
        initial_state: tuple[float, float, float] = (0.99, 0.01, 0.0),
        t_span: tuple[float, float] = (0.0, 30.0),
        n_steps: int = 100,
        max_iterations: int = 50,
        tolerance: float = 1e-4,
    ) -> OptimalControlResult:
        """Solve optimal control u*(t) profile via Forward-Backward Sweep Method.

        Parameters
        ----------
        initial_state : tuple[float, float, float]
            Initial (S0, I0, R0).
        t_span : tuple[float, float]
            Time horizon [0, T].
        n_steps : int
            Number of discrete time grid steps.
        max_iterations : int
            Maximum sweep iterations.
        tolerance : float
            Convergence tolerance.

        Returns
        -------
        OptimalControlResult
            Optimal trajectories and minimum cost J.
        """
        t = np.linspace(t_span[0], t_span[1], n_steps)
        dt = (t_span[1] - t_span[0]) / (n_steps - 1)

        # Initial control guess u(t) = 0
        u = np.zeros(n_steps)
        s = np.zeros(n_steps)
        i_arr = np.zeros(n_steps)
        r = np.zeros(n_steps)

        lambda_s = np.zeros(n_steps)
        lambda_i = np.zeros(n_steps)
        lambda_r = np.zeros(n_steps)

        s[0], i_arr[0], r[0] = initial_state

        for iteration in range(max_iterations):
            u_old = u.copy()

            # 1. Forward sweep for state equations S, I, R
            for k in range(n_steps - 1):
                beta_eff = self.beta_max * (1.0 - u[k])
                s[k + 1] = max(0.0, s[k] - dt * beta_eff * s[k] * i_arr[k])
                i_arr[k + 1] = max(0.0, i_arr[k] + dt * (beta_eff * s[k] * i_arr[k] - self.gamma * i_arr[k]))
                r[k + 1] = r[k] + dt * self.gamma * i_arr[k]

            # 2. Backward sweep for costate equations lambda_S, lambda_I, lambda_R
            # Terminal conditions: lambda_S(T) = lambda_I(T) = lambda_R(T) = 0
            lambda_s[-1] = 0.0
            lambda_i[-1] = 0.0
            lambda_r[-1] = 0.0

            for k in range(n_steps - 2, -1, -1):
                beta_eff = self.beta_max * (1.0 - u[k])
                d_lambda_s = (lambda_s[k + 1] - lambda_i[k + 1]) * beta_eff * i_arr[k]
                d_lambda_i = -self.cost_disease_cd + (lambda_s[k + 1] - lambda_i[k + 1]) * beta_eff * s[k] + lambda_i[k + 1] * self.gamma - lambda_r[k + 1] * self.gamma

                lambda_s[k] = lambda_s[k + 1] - dt * d_lambda_s
                lambda_i[k] = lambda_i[k + 1] - dt * d_lambda_i

            # 3. Update optimal control u*(t) = min(1, max(0, (lambda_I - lambda_S) * beta_max * S * I / w))
            u_star = ((lambda_i - lambda_s) * self.beta_max * s * i_arr) / max(self.cost_effort_w, 1e-4)
            u = 0.5 * u + 0.5 * np.clip(u_star, 0.0, 1.0)  # Convex combination update

            # Check convergence
            diff = np.linalg.norm(u - u_old)
            if diff < tolerance:
                logger.info("OptimalControlSolver converged in %d iterations (diff: %.6f)", iteration + 1, diff)
                break

        # Compute total cost J = sum dt * [ Cd * I + 0.5 * w * u^2 ]
        j_cost = float(np.sum(dt * (self.cost_disease_cd * i_arr + 0.5 * self.cost_effort_w * (u ** 2))))

        return OptimalControlResult(
            t=t,
            susceptible=s,
            infected=i_arr,
            recovered=r,
            optimal_control_u=u,
            objective_cost_j=j_cost,
        )
