"""NormalFormGame: thin wrapper around nashpy for 2-player games."""

from __future__ import annotations

import random

import nashpy as nash
import numpy as np


class NormalFormGame:
    """Wrapper around ``nashpy.Game`` for a 2-player normal-form game.

    Parameters
    ----------
    A:
        Row player payoff matrix (n_actions_row × n_actions_col).
    B:
        Column player payoff matrix (same shape as A).
    """

    def __init__(
        self,
        A: np.ndarray | list,
        B: np.ndarray | list,
    ) -> None:
        self.A = np.array(A, dtype=float)
        self.B = np.array(B, dtype=float)
        self._game = nash.Game(self.A, self.B)

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def get_nash_equilibria(self) -> list[tuple[np.ndarray, np.ndarray]]:
        """Return all Nash equilibria via support enumeration.

        Returns a list of ``(sigma_row, sigma_col)`` mixed strategy pairs.
        """
        return list(self._game.support_enumeration())

    def select_equilibrium(self) -> tuple[np.ndarray, np.ndarray]:
        """Pick the first equilibrium (index 0) for deterministic behaviour.

        Falls back to a uniform mixed strategy over all actions when the
        list is empty.
        """
        equilibria = self.get_nash_equilibria()
        if equilibria:
            return equilibria[0]
        # Uniform fallback
        n_row = self.A.shape[0]
        n_col = self.B.shape[1]
        sigma_row = np.ones(n_row) / n_row
        sigma_col = np.ones(n_col) / n_col
        return sigma_row, sigma_col

    @staticmethod
    def sample_action(strategy: np.ndarray, actions: list[str]) -> str:
        """Sample one action string using the given mixed strategy weights.

        Parameters
        ----------
        strategy:
            Probability vector (must sum to 1 and match ``len(actions)``).
        actions:
            Action labels in the same order as the strategy entries.
        """
        # Clip negative floating-point deviations from nashpy and re-normalize
        strat = np.clip(strategy, 0.0, 1.0)
        total = strat.sum()
        if total < 1e-12:
            # Degenerate case: uniform fallback
            return random.choice(actions)
        strat = strat / total
        return random.choices(actions, weights=strat.tolist(), k=1)[0]

    @classmethod
    def from_capabilities(
        cls,
        base_A: np.ndarray,
        base_B: np.ndarray,
        cap_row: dict[str, float],
        cap_col: dict[str, float],
        scaling: str = "log_ratio",
    ) -> NormalFormGame:
        """Create a game with payoffs scaled by relative capabilities.

        Parameters
        ----------
        base_A, base_B:
            Baseline payoff matrices.
        cap_row, cap_col:
            Capability dicts (e.g. ``{"military": 0.8, "economic": 0.4}``).
        scaling:
            Scaling function. ``"log_ratio"`` uses
            ``log(1 + cap_row / cap_col)``.

        Returns
        -------
        NormalFormGame
            A new game with dynamically scaled payoffs.
        """
        A = np.array(base_A, dtype=float)
        B = np.array(base_B, dtype=float)

        if scaling == "log_ratio":
            import math

            row_mil = cap_row.get("military", 0.5)
            col_mil = cap_col.get("military", 0.5)
            if col_mil < 1e-6:
                col_mil = 1e-6
            ratio = row_mil / col_mil
            row_factor = math.log(1.0 + ratio)
            col_factor = math.log(1.0 + 1.0 / ratio) if ratio > 1e-6 else math.log(1.0 + 1e6)

            A = A * row_factor
            B = B * col_factor

        return cls(A, B)
