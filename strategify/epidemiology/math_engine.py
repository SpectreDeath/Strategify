"""Next-Generation Matrix Operator & Advanced Mathematical Epidemiology.

Calculates the exact basic reproduction number R0 = rho(F * V^-1) via the
spectral radius of the Next-Generation Operator (Brauer et al. / Martcheva).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class NextGenResult:
    """Result of Next-Generation Matrix calculation."""

    r0: float  # Basic reproduction number (spectral radius)
    next_gen_matrix: np.ndarray  # F * V^-1 matrix
    is_stable_disease_free: bool  # True if R0 < 1.0


class NextGenMatrixOperator:
    """Next-Generation Matrix Operator for calculating R0 and equilibrium stability.

    Computes R0 = max(abs(eigenvalues(F * V^-1))) where F is the transmission
    matrix and V is the compartmental transition matrix.
    """

    def compute_r0(
        self,
        transmission_matrix_f: list[list[float]] | np.ndarray,
        transition_matrix_v: list[list[float]] | np.ndarray,
    ) -> NextGenResult:
        """Compute R0 using next-generation matrix operator K = F * V^-1.

        Parameters
        ----------
        transmission_matrix_f : list[list[float]] | np.ndarray
            Matrix of new infection rates into infected compartments (F).
        transition_matrix_v : list[list[float]] | np.ndarray
            Matrix of net outflow transitions from infected compartments (V).

        Returns
        -------
        NextGenResult
            Calculated R0, next-generation matrix, and stability assertion.
        """
        f_arr = np.array(transmission_matrix_f, dtype=float)
        v_arr = np.array(transition_matrix_v, dtype=float)

        # Invert transition matrix V
        v_inv = np.linalg.inv(v_arr)

        # Compute Next-Generation Operator K = F * V^-1
        k_matrix = np.matmul(f_arr, v_inv)

        # Calculate spectral radius (largest absolute eigenvalue)
        eigenvalues = np.linalg.eigvals(k_matrix)
        r0 = float(np.max(np.abs(eigenvalues)))

        is_stable = r0 < 1.0

        logger.info("Next-Gen Operator calculated R0 = %.4f (Disease-Free Equilibrium Stable: %s)", r0, is_stable)

        return NextGenResult(
            r0=r0,
            next_gen_matrix=k_matrix,
            is_stable_disease_free=is_stable,
        )

    def compute_sir_r0(
        self,
        beta: float,
        gamma: float,
    ) -> float:
        """Compute analytical R0 for standard SIR model (R0 = beta / gamma).

        Parameters
        ----------
        beta : float
            Transmission rate.
        gamma : float
            Recovery rate.

        Returns
        -------
        float
            Basic reproduction number R0.
        """
        f = np.array([[beta]])
        v = np.array([[gamma]])
        res = self.compute_r0(f, v)
        return res.r0
