"""Dynamic payoff matrices computed from capabilities and region state.

Instead of using hardcoded payoff matrices, this module computes matrices
as a function of current actor capabilities, region resources, tension
scores, and escalation levels. Payoff history is logged for analysis.

Usage::

    from strategify.game_theory.dynamic import PayoffComputer, PayoffHistory

    computer = PayoffComputer()
    A, B = computer.compute("escalation", caps_row, caps_col, region_features)
    history = PayoffHistory()
    history.record(step=1, game_name="escalation", A=A, B=B)
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np
import pandas as pd

from strategify.game_theory.crisis_games import get_game

logger = logging.getLogger(__name__)


class PayoffComputer:
    """Computes payoff matrices from current actor and region state.

    Takes base payoff matrices and scales them by capability ratios,
    tension levels, and escalation state.
    """

    def compute(
        self,
        game_name: str,
        caps_row: dict[str, float],
        caps_col: dict[str, float],
        region_features_row: dict[str, float] | None = None,
        region_features_col: dict[str, float] | None = None,
        escalation_level_row: int = 0,
        escalation_level_col: int = 0,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Compute dynamic payoff matrices.

        Parameters
        ----------
        game_name:
            Key into ``GAME_ACTIONS``.
        caps_row, caps_col:
            Capability dicts (e.g. ``{"military": 0.8, "economic": 0.4}``).
        region_features_row, region_features_col:
            Optional OSINT/region features with keys like
            ``tension_score``, ``event_count``, etc.
        escalation_level_row, escalation_level_col:
            Escalation ladder levels (0-3).

        Returns
        -------
        tuple[np.ndarray, np.ndarray]
            ``(A, B)`` payoff matrices scaled by current state.
        """
        base = get_game(game_name)
        A = base.A.copy().astype(float)
        B = base.B.copy().astype(float)

        # 1. Capability scaling (log-ratio)
        A, B = self._scale_by_capabilities(A, B, caps_row, caps_col)

        # 2. Tension scaling
        A, B = self._scale_by_tension(A, B, region_features_row, region_features_col)

        # 3. Escalation level scaling
        A, B = self._scale_by_escalation(A, B, escalation_level_row, escalation_level_col)

        return A, B

    @staticmethod
    def _scale_by_capabilities(
        A: np.ndarray,
        B: np.ndarray,
        caps_row: dict[str, float],
        caps_col: dict[str, float],
    ) -> tuple[np.ndarray, np.ndarray]:
        """Scale payoffs by log-ratio of military capabilities."""
        row_mil = caps_row.get("military", 0.5)
        col_mil = caps_col.get("military", 0.5)
        col_mil = max(col_mil, 1e-6)
        ratio = row_mil / col_mil

        if ratio > 1e-6:
            row_factor = math.log(1.0 + ratio)
            col_factor = math.log(1.0 + 1.0 / ratio)
        else:
            row_factor = math.log(1.0 + 1e6)
            col_factor = 0.0

        return A * row_factor, B * col_factor

    @staticmethod
    def _scale_by_tension(
        A: np.ndarray,
        B: np.ndarray,
        features_row: dict[str, float] | None,
        features_col: dict[str, float] | None,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Scale payoffs by regional tension.

        High tension amplifies negative payoffs (mutual escalation
        becomes more costly) and increases the reward for deescalation.
        """
        tension_row = (features_row or {}).get("tension_score", 0.0)
        tension_col = (features_col or {}).get("tension_score", 0.0)
        avg_tension = (tension_row + tension_col) / 2.0

        # Tension amplifies losses: scale negative entries by (1 + tension)
        # and positive entries by (1 - 0.5 * tension)
        neg_mask = A < 0
        pos_mask = A >= 0
        A[neg_mask] *= 1.0 + avg_tension
        A[pos_mask] *= 1.0 - 0.3 * avg_tension

        neg_mask = B < 0
        pos_mask = B >= 0
        B[neg_mask] *= 1.0 + avg_tension
        B[pos_mask] *= 1.0 - 0.3 * avg_tension

        return A, B

    @staticmethod
    def _scale_by_escalation(
        A: np.ndarray,
        B: np.ndarray,
        level_row: int,
        level_col: int,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Scale payoffs by escalation ladder levels.

        Higher escalation levels make mutual escalation slightly less
        costly (sunk cost) and increase the payoff for unilateral
        escalation (commitment effect).
        """
        avg_level = (level_row + level_col) / 2.0
        # At higher levels, reduce the penalty for mutual escalation
        # (players are already committed)
        commitment_factor = 1.0 + 0.1 * avg_level

        # Row 0 = aggressive action; boost it with commitment
        A[0, :] *= commitment_factor
        B[:, 0] *= commitment_factor

        return A, B


class PayoffHistory:
    """Logs per-step payoff matrices for analysis and visualization.

    Stores (step, game_name, A, B) tuples and can export to a DataFrame.
    """

    def __init__(self) -> None:
        self._records: list[dict[str, Any]] = []

    def record(
        self,
        step: int,
        game_name: str,
        A: np.ndarray,
        B: np.ndarray,
        agent_id: int | None = None,
        opponent_id: int | None = None,
    ) -> None:
        """Record a payoff matrix snapshot.

        Parameters
        ----------
        step:
            Simulation step number.
        game_name:
            Name of the game.
        A, B:
            Payoff matrices.
        agent_id, opponent_id:
            Optional agent IDs for per-pair tracking.
        """
        self._records.append(
            {
                "step": step,
                "game_name": game_name,
                "agent_id": agent_id,
                "opponent_id": opponent_id,
                "A": A.tolist(),
                "B": B.tolist(),
                "A_sum": float(A.sum()),
                "B_sum": float(B.sum()),
                "A_trace": float(np.trace(A)),
                "B_trace": float(np.trace(B)),
            }
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Export history as a DataFrame."""
        if not self._records:
            return pd.DataFrame()
        return pd.DataFrame(self._records)

    def get_latest(self, game_name: str | None = None) -> dict[str, Any] | None:
        """Return the most recent record, optionally filtered by game."""
        for record in reversed(self._records):
            if game_name is None or record["game_name"] == game_name:
                return record
        return None

    @property
    def records(self) -> list[dict[str, Any]]:
        """Return all records."""
        return list(self._records)

    def clear(self) -> None:
        """Clear all history."""
        self._records.clear()
