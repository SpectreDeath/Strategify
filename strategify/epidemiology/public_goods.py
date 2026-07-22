"""Public Goods Games & Social Dilemmas in Disease Mitigation.

Models N-player public goods games (PGGs) for public health interventions
(vaccination compliance, mask mandates, antibiotic stewardship) and defection thresholds.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PublicGoodsResult:
    """Outcome of N-player public goods game round."""

    num_contributors: int
    num_defectors: int
    total_public_pool: float
    contributor_payoff: float
    defector_payoff: float
    defection_threshold_crossed: bool


class PublicGoodsGame:
    """N-player Public Goods Game for disease mitigation compliance.

    Parameters
    ----------
    group_size_n : int
        Number N of players in the interaction group (default: 10).
    synergy_factor_r : float
        Multiplier factor r for public pool (default: 3.0).
    cost_of_contribution_c : float
        Individual cost c of contributing/mitigating (default: 1.0).
    defection_threshold : float
        Fraction of defectors above which public health system fails (default: 0.4).
    """

    def __init__(
        self,
        group_size_n: int = 10,
        synergy_factor_r: float = 3.0,
        cost_of_contribution_c: float = 1.0,
        defection_threshold: float = 0.4,
    ) -> None:
        self.group_size_n = group_size_n
        self.synergy_factor_r = synergy_factor_r
        self.cost_of_contribution_c = cost_of_contribution_c
        self.defection_threshold = defection_threshold

    def calculate_payoffs(self, num_contributors: int) -> tuple[float, float]:
        """Calculate payoffs for contributors vs defectors.

        Parameters
        ----------
        num_contributors : int
            Number of players contributing to public health pool.

        Returns
        -------
        tuple[float, float]
            (contributor_payoff, defector_payoff).
        """
        n = max(1, self.group_size_n)
        k = max(0, min(n, num_contributors))

        # Total pool enhanced by synergy factor r
        public_benefit = (k * self.cost_of_contribution_c * self.synergy_factor_r) / n

        contributor_payoff = public_benefit - self.cost_of_contribution_c
        defector_payoff = public_benefit

        return contributor_payoff, defector_payoff

    def simulate_group_round(self, contributor_fraction: float) -> PublicGoodsResult:
        """Simulate a round of N-player public goods interaction.

        Parameters
        ----------
        contributor_fraction : float
            Fraction x of population contributing [0.0, 1.0].

        Returns
        -------
        PublicGoodsResult
            Round result metrics.
        """
        frac = max(0.0, min(1.0, contributor_fraction))
        k = int(round(frac * self.group_size_n))
        defectors = self.group_size_n - k

        c_payoff, d_payoff = self.calculate_payoffs(k)
        defector_frac = defectors / max(1, self.group_size_n)
        threshold_crossed = defector_frac >= self.defection_threshold

        logger.info(
            "PublicGoodsGame: %d/%d contributors -> C_payoff: %.2f, D_payoff: %.2f (Threshold Crossed: %s)",
            k,
            self.group_size_n,
            c_payoff,
            d_payoff,
            threshold_crossed,
        )

        return PublicGoodsResult(
            num_contributors=k,
            num_defectors=defectors,
            total_public_pool=k * self.cost_of_contribution_c * self.synergy_factor_r,
            contributor_payoff=c_payoff,
            defector_payoff=d_payoff,
            defection_threshold_crossed=threshold_crossed,
        )
