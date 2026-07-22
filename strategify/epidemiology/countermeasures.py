"""Biodefense Countermeasures & Public Health Policy Engine.

Models Non-Pharmaceutical Interventions (NPIs: Lockdowns, Border Closures, Tracing),
Pharmaceutical Interventions (Vaccine R&D, Mass Vaccination, ICU Expansion),
and their economic GDP impact trade-offs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BiodefenseStatus:
    """Status of biodefense policy & health infrastructure."""

    npi_level: float = 0.0  # NPI rigor [0.0, 1.0] (0.0 = Open, 1.0 = Lockdown)
    vaccination_rate: float = 0.0  # Fraction vaccinated [0.0, 1.0]
    vaccine_rd_progress: float = 0.0  # Vaccine development progress [0.0, 1.0]
    icu_capacity: float = 1.0  # ICU capacity multiplier
    economic_gdp_drag: float = 0.0  # Economic loss from NPIs [0.0, 1.0]


class BioDefenseComponent:
    """Biodefense component attached to StateActorAgent.

    Parameters
    ----------
    agent : Any
        The StateActorAgent owning this component.
    """

    def __init__(self, agent: Any) -> None:
        self.agent = agent
        self.status = BiodefenseStatus()

    def set_npi_policy(self, npi_level: float) -> float:
        """Set Non-Pharmaceutical Intervention (NPI) level.

        Parameters
        ----------
        npi_level : float
            NPI level [0.0, 1.0].

        Returns
        -------
        float
            Calculated GDP drag resulting from NPIs.
        """
        self.status.npi_level = max(0.0, min(1.0, npi_level))
        # GDP drag scales non-linearly with NPI lockdown level
        self.status.economic_gdp_drag = (self.status.npi_level ** 1.5) * 0.25
        logger.info("Agent %s set NPI level to %.2f (GDP drag: %.2f)", self.agent.region_id, self.status.npi_level, self.status.economic_gdp_drag)
        return self.status.economic_gdp_drag

    def fund_vaccine_rd(self, budget_allocation: float = 0.1) -> float:
        """Allocate budget to accelerate vaccine R&D progress.

        Parameters
        ----------
        budget_allocation : float
            Fraction of economic capability allocated [0.0, 1.0].

        Returns
        -------
        float
            Updated vaccine R&D progress.
        """
        econ_cap = self.agent.capabilities.get("economic", 0.5)
        progress_gain = (econ_cap * budget_allocation) * 0.2
        self.status.vaccine_rd_progress = min(1.0, self.status.vaccine_rd_progress + progress_gain)
        logger.info("Agent %s vaccine R&D progress: %.2f", self.agent.region_id, self.status.vaccine_rd_progress)
        return self.status.vaccine_rd_progress

    def execute_vaccination_campaign(self, roll_out_pct: float = 0.05) -> float:
        """Execute mass vaccination campaign if vaccine is ready.

        Parameters
        ----------
        roll_out_pct : float
            Population percentage vaccinated per step.

        Returns
        -------
        float
            Updated total vaccination rate.
        """
        if self.status.vaccine_rd_progress < 0.5:
            logger.info("Agent %s vaccine not sufficiently developed for rollout.", self.agent.region_id)
            return self.status.vaccination_rate

        self.status.vaccination_rate = min(1.0, self.status.vaccination_rate + roll_out_pct)
        logger.info("Agent %s total vaccination rate: %.2f", self.agent.region_id, self.status.vaccination_rate)
        return self.status.vaccination_rate

    def expand_icu_capacity(self, expansion_factor: float = 0.2) -> float:
        """Expand hospital & ICU bed capacity to prevent system overload."""
        self.status.icu_capacity += expansion_factor
        logger.info("Agent %s expanded ICU capacity to %.2f", self.agent.region_id, self.status.icu_capacity)
        return self.status.icu_capacity
