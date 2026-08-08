"""Vectorized Spatial Metapopulation Network ODE Solver.

Solves continuous-time coupled SIR and replicator dynamics across K-node regional graphs,
coupling local transmission with cross-node spatial gravity mobility fluxes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp

logger = logging.getLogger(__name__)


@dataclass
class MetapopulationSolution:
    """Trajectory solution across K-node spatial metapopulation graph."""

    t: np.ndarray
    susceptible_matrix: np.ndarray  # Shape: (num_time_points, num_nodes)
    infected_matrix: np.ndarray  # Shape: (num_time_points, num_nodes)
    recovered_matrix: np.ndarray  # Shape: (num_time_points, num_nodes)
    cooperation_matrix: np.ndarray  # Shape: (num_time_points, num_nodes)


class MetapopulationODE:
    """Vectorized Metapopulation ODE solver for graph network nodes.

    Parameters
    ----------
    adjacency_matrix : np.ndarray
        K x K spatial graph adjacency matrix.
    populations : list[float] | np.ndarray
        Population denominator per node.
    beta_baseline : float
        Baseline transmission rate without mitigation (default: 0.5).
    beta_mitigated : float
        Mitigated transmission rate (default: 0.1).
    gamma : float
        Recovery rate (default: 0.1).
    mobility_coupling : float
        Inter-node mobility coupling strength factor (default: 0.05).
    """

    def __init__(
        self,
        adjacency_matrix: list[list[float]] | np.ndarray,
        populations: list[float] | np.ndarray,
        beta_baseline: float = 0.5,
        beta_mitigated: float = 0.1,
        gamma: float = 0.1,
        mobility_coupling: float = 0.05,
    ) -> None:
        self.adj = np.array(adjacency_matrix, dtype=float)
        self.pops = np.array(populations, dtype=float)
        self.num_nodes = len(self.pops)
        self.beta_baseline = beta_baseline
        self.beta_mitigated = beta_mitigated
        self.gamma = gamma
        self.mobility_coupling = mobility_coupling

    def system_derivatives(self, t: float, y_flat: list[float] | np.ndarray) -> list[float]:
        """Compute ODE derivatives across all K nodes.

        y_flat is a 1D array of size 4K: [S_0..S_{K-1}, I_0..I_{K-1}, R_0..R_{K-1}, x_0..x_{K-1}].
        """
        k = self.num_nodes
        s_arr = np.array(y_flat[:k])
        i_arr = np.array(y_flat[k : 2 * k])
        _r_arr = np.array(y_flat[2 * k : 3 * k])
        x_arr = np.array(y_flat[3 * k : 4 * k])

        beta_eff = (1.0 - x_arr) * self.beta_baseline + x_arr * self.beta_mitigated

        # Local transmission derivatives
        ds_dt = -beta_eff * s_arr * i_arr
        di_dt = beta_eff * s_arr * i_arr - self.gamma * i_arr
        dr_dt = self.gamma * i_arr

        # Cross-node spatial mobility infection seeding
        for i in range(k):
            cross_infection = 0.0
            for j in range(k):
                if self.adj[i, j] > 0:
                    cross_infection += self.mobility_coupling * self.adj[i, j] * s_arr[i] * i_arr[j]
            ds_dt[i] -= cross_infection
            di_dt[i] += cross_infection

        # Replicator dynamics per node: dx_i/dt = x_i * (1 - x_i) * (f_C - f_D)
        payoff_c = -0.2
        payoff_d = -(i_arr * self.beta_baseline) * 1.0
        dx_dt = x_arr * (1.0 - x_arr) * (payoff_c - payoff_d)

        return list(np.concatenate([ds_dt, di_dt, dr_dt, dx_dt]))

    def solve(
        self,
        initial_susceptible: list[float] | np.ndarray,
        initial_infected: list[float] | np.ndarray,
        initial_cooperation: list[float] | np.ndarray,
        t_span: tuple[float, float] = (0.0, 30.0),
        n_eval_points: int = 100,
    ) -> MetapopulationSolution:
        """Solve continuous spatial ODE system using scipy.integrate.solve_ivp.

        Parameters
        ----------
        initial_susceptible : list[float] | np.ndarray
            Initial S for each node.
        initial_infected : list[float] | np.ndarray
            Initial I for each node.
        initial_cooperation : list[float] | np.ndarray
            Initial x for each node.
        t_span : tuple[float, float]
            Time integration span.
        n_eval_points : int
            Output points count.

        Returns
        -------
        MetapopulationSolution
            Node trajectory matrices.
        """
        k = self.num_nodes
        s0 = np.array(initial_susceptible, dtype=float)
        i0 = np.array(initial_infected, dtype=float)
        r0 = np.zeros(k, dtype=float)
        x0 = np.array(initial_cooperation, dtype=float)

        y0 = np.concatenate([s0, i0, r0, x0])
        t_eval = np.linspace(t_span[0], t_span[1], n_eval_points)

        sol = solve_ivp(
            fun=self.system_derivatives,
            t_span=t_span,
            y0=y0,
            t_eval=t_eval,
            method="RK45",
        )

        logger.info("MetapopulationODE integrated across %d nodes over t_span %s", k, t_span)

        return MetapopulationSolution(
            t=sol.t,
            susceptible_matrix=sol.y[:k].T,
            infected_matrix=sol.y[k : 2 * k].T,
            recovered_matrix=sol.y[2 * k : 3 * k].T,
            cooperation_matrix=sol.y[3 * k : 4 * k].T,
        )
