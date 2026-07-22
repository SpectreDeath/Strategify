"""Coupled Evolutionary Game Dynamics & Replicator ODE Solvers.

Solves continuous-time coupled SIR transmission differential equations with
replicator dynamics governing population strategy frequency (dx/dt = x(1-x)(fC - fD)).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

logger = logging.getLogger(__name__)


@dataclass
class ReplicatorSolution:
    """Trajectory solution of coupled EGT-SIR system."""

    t: np.ndarray
    susceptible: np.ndarray
    infected: np.ndarray
    recovered: np.ndarray
    cooperation_fraction: np.ndarray  # Fraction x of population cooperating/mitigating


class ReplicatorDynamicsODE:
    """Coupled SIR and Replicator Dynamics ODE solver.

    Governs:
    dS/dt = -beta(x) * S * I
    dI/dt = beta(x) * S * I - gamma * I
    dR/dt = gamma * I
    dx/dt = x * (1 - x) * (f_cooperate - f_defect)

    Parameters
    ----------
    beta_baseline : float
        Transmission rate without mitigation (default: 0.5).
    beta_mitigated : float
        Transmission rate when cooperating (default: 0.1).
    gamma : float
        Recovery rate (default: 0.1).
    cost_of_disease : float
        Payoff penalty Cd for contracting disease (default: 1.0).
    cost_of_mitigation : float
        Payoff penalty Cm for cooperating/quarantining (default: 0.2).
    """

    def __init__(
        self,
        beta_baseline: float = 0.5,
        beta_mitigated: float = 0.1,
        gamma: float = 0.1,
        cost_of_disease: float = 1.0,
        cost_of_mitigation: float = 0.2,
    ) -> None:
        self.beta_baseline = beta_baseline
        self.beta_mitigated = beta_mitigated
        self.gamma = gamma
        self.cost_of_disease = cost_of_disease
        self.cost_of_mitigation = cost_of_mitigation

    def system_derivatives(self, t: float, y: list[float]) -> list[float]:
        """Compute ODE derivatives [ds_dt, di_dt, dr_dt, dx_dt]."""
        s_pop, i_pop, r_pop, x_coop = y

        # Effective transmission rate based on cooperation fraction x
        beta_eff = (1.0 - x_coop) * self.beta_baseline + x_coop * self.beta_mitigated

        # SIR derivatives
        ds_dt = -beta_eff * s_pop * i_pop
        di_dt = beta_eff * s_pop * i_pop - self.gamma * i_pop
        dr_dt = self.gamma * i_pop

        # Payoffs:
        # f_cooperate (C) = -cost_of_mitigation
        # f_defect (D) = - (perceived risk of infection) * cost_of_disease
        payoff_cooperate = -self.cost_of_mitigation
        payoff_defect = - (i_pop * self.beta_baseline) * self.cost_of_disease

        # Replicator dynamics: dx/dt = x * (1 - x) * (f_C - f_D)
        dx_dt = x_coop * (1.0 - x_coop) * (payoff_cooperate - payoff_defect)

        return [ds_dt, di_dt, dr_dt, dx_dt]

    def solve(
        self,
        initial_state: tuple[float, float, float, float] = (0.99, 0.01, 0.0, 0.5),
        t_span: tuple[float, float] = (0.0, 50.0),
        n_eval_points: int = 200,
    ) -> ReplicatorSolution:
        """Solve continuous coupled ODE system using scipy.integrate.solve_ivp.

        Parameters
        ----------
        initial_state : tuple[float, float, float, float]
            Initial (S0, I0, R0, x0).
        t_span : tuple[float, float]
            Time range for integration (t_start, t_end).
        n_eval_points : int
            Number of output time points.

        Returns
        -------
        ReplicatorSolution
            Integrated trajectory arrays.
        """
        t_eval = np.linspace(t_span[0], t_span[1], n_eval_points)
        sol = solve_ivp(
            fun=self.system_derivatives,
            t_span=t_span,
            y0=list(initial_state),
            t_eval=t_eval,
            method="RK45",
        )

        logger.info("ReplicatorDynamicsODE integrated successfully over t_span %s", t_span)

        return ReplicatorSolution(
            t=sol.t,
            susceptible=sol.y[0],
            infected=sol.y[1],
            recovered=sol.y[2],
            cooperation_fraction=sol.y[3],
        )
