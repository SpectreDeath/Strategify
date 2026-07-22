"""Game-Theoretic Strategy vs Pathogen Evolution.

Formulates public health strategy as a 2-player strategic matrix game
between State Policy vs Pathogen Mutation / Spread.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

from strategify.game_theory.normal_form import NormalFormGame

logger = logging.getLogger(__name__)


# State Actions: 0: LaissezFaire, 1: TargetedQuarantine, 2: MassVaccination, 3: FullLockdown
STATE_ACTIONS = ["LaissezFaire", "TargetedQuarantine", "MassVaccination", "FullLockdown"]

# Pathogen Actions: 0: SilentSpread, 1: HighTransmission, 2: VaccineEvasion, 3: SevereOutbreak
PATHOGEN_ACTIONS = ["SilentSpread", "HighTransmission", "VaccineEvasion", "SevereOutbreak"]


class BioStrategyGame:
    """Matrix game modeling State Health Policy vs Pathogen Evolution.

    State seeks to minimize mortality & GDP drag.
    Pathogen seeks to maximize effective transmission.
    """

    def __init__(self) -> None:
        # Payoff matrix for State Actor A (maximize health & economy)
        # Columns represent Pathogen Actions
        self.state_payoffs = [
            [0.8, 0.2, 0.1, -1.0],  # LaissezFaire
            [0.6, 0.7, 0.4, 0.2],  # TargetedQuarantine
            [0.9, 0.8, 0.5, 0.6],  # MassVaccination
            [0.2, 0.3, 0.2, 0.1],  # FullLockdown
        ]

        # Payoff matrix for Pathogen B (zero-sum or competitive)
        self.pathogen_payoffs = [
            [-0.8, -0.2, -0.1, 1.0],
            [-0.6, -0.7, -0.4, -0.2],
            [-0.9, -0.8, -0.5, -0.6],
            [-0.2, -0.3, -0.2, -0.1],
        ]

    def solve_optimal_policy(self, current_rt: float, gdp_budget: float) -> str:
        """Derive Nash equilibrium biodefense policy for state actor.

        Parameters
        ----------
        current_rt : float
            Current effective reproduction number Rt.
        gdp_budget : float
            Available economic capability.

        Returns
        -------
        str
            Optimal state health action string.
        """
        payoffs_a = np.array(self.state_payoffs)
        payoffs_b = np.array(self.pathogen_payoffs)

        # Dynamic adjustments based on Rt pressure
        if current_rt > 2.0:
            # Shift payoffs to favor lockdowns and quarantines
            payoffs_a[3, :] += 0.5
            payoffs_a[1, :] += 0.3
        elif current_rt < 1.0:
            # Shift payoffs to favor LaissezFaire
            payoffs_a[0, :] += 0.4

        game = NormalFormGame(payoffs_a, payoffs_b)
        sigma_row, _ = game.select_equilibrium()
        chosen_action = game.sample_action(sigma_row, STATE_ACTIONS)

        logger.info("BioStrategyGame solved optimal state action: '%s' (Rt: %.2f)", chosen_action, current_rt)
        return chosen_action
