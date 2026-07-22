"""Multi-Compartment SEIRH Epidemiological Model & Pathogen Engine.

Models Susceptible (S), Exposed (E), Infectious (I), Hospitalized (H),
Recovered (R), and Deceased (D) compartment dynamics alongside pathogen mutations.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PathogenVariant:
    """Pathogen variant characteristics."""

    name: str
    r0: float = 2.5  # Basic reproduction number
    incubation_period: float = 5.0  # Days in Exposed compartment
    infectious_period: float = 7.0  # Days in Infectious compartment
    hospitalization_rate: float = 0.05  # Fraction needing ICU/hospital
    fatality_rate: float = 0.01  # Case fatality rate
    vaccine_evasion: float = 0.0  # Immune evasion [0.0, 1.0]


class SEIRHEngine:
    """Epidemiological simulation engine for a single region.

    Parameters
    ----------
    population : int
        Total initial population.
    initial_infected : int
        Initial infectious cases.
    variant : PathogenVariant | None
        Initial pathogen strain (default: Wildtype).
    """

    def __init__(
        self,
        population: int = 1_000_000,
        initial_infected: int = 10,
        variant: PathogenVariant | None = None,
    ) -> None:
        self.population = population
        self.variant = variant or PathogenVariant(name="Wildtype")

        # Compartments
        self.susceptible = float(population - initial_infected)
        self.exposed = 0.0
        self.infectious = float(initial_infected)
        self.hospitalized = 0.0
        self.recovered = 0.0
        self.deceased = 0.0

        # Effective Reproduction Rate Rt history
        self.rt_history: list[float] = []

    def compute_effective_rt(self, npi_effectiveness: float = 0.0, vaccination_rate: float = 0.0) -> float:
        """Calculate effective reproduction number Rt considering NPIs and immunity.

        Parameters
        ----------
        npi_effectiveness : float
            Reduction in transmission from NPIs [0.0, 1.0].
        vaccination_rate : float
            Fraction of population vaccinated [0.0, 1.0].

        Returns
        -------
        float
            Effective reproduction number Rt.
        """
        effective_susceptible_pct = max(
            0.0,
            (self.susceptible / max(self.population, 1))
            * (1.0 - vaccination_rate * (1.0 - self.variant.vaccine_evasion)),
        )
        rt = self.variant.r0 * (1.0 - npi_effectiveness) * effective_susceptible_pct
        self.rt_history.append(rt)
        return rt

    def step(self, dt_days: float = 1.0, npi_effectiveness: float = 0.0, vaccination_rate: float = 0.0) -> dict[str, float]:
        """Advance SEIRH compartment states by dt_days.

        Parameters
        ----------
        dt_days : float
            Time step in days (default: 1.0).
        npi_effectiveness : float
            NPI transmission reduction [0.0, 1.0].
        vaccination_rate : float
            Vaccine immunity fraction [0.0, 1.0].

        Returns
        -------
        dict
            Updated compartment counts.
        """
        rt = self.compute_effective_rt(npi_effectiveness, vaccination_rate)

        # Transmission rate beta = Rt / infectious_period
        beta = rt / max(self.variant.infectious_period, 0.1)
        sigma = 1.0 / max(self.variant.incubation_period, 0.1)
        gamma = 1.0 / max(self.variant.infectious_period, 0.1)

        # Transition equations
        new_exposed = beta * (self.susceptible * self.infectious / max(self.population, 1)) * dt_days
        new_infectious = sigma * self.exposed * dt_days
        new_outcomes = gamma * self.infectious * dt_days

        new_hospitalized = new_outcomes * self.variant.hospitalization_rate
        new_recovered = new_outcomes * (1.0 - self.variant.hospitalization_rate - self.variant.fatality_rate)
        new_deceased = new_outcomes * self.variant.fatality_rate

        # Update compartments
        self.susceptible = max(0.0, self.susceptible - new_exposed)
        self.exposed = max(0.0, self.exposed + new_exposed - new_infectious)
        self.infectious = max(0.0, self.infectious + new_infectious - new_outcomes)
        self.hospitalized = max(0.0, self.hospitalized + new_hospitalized - (0.2 * self.hospitalized * dt_days))
        self.recovered += max(0.0, new_recovered)
        self.deceased += max(0.0, new_deceased)

        # Check potential pathogen mutation (0.5% chance per step)
        if random.random() < 0.005:
            self._mutate_variant()

        return {
            "susceptible": self.susceptible,
            "exposed": self.exposed,
            "infectious": self.infectious,
            "hospitalized": self.hospitalized,
            "recovered": self.recovered,
            "deceased": self.deceased,
            "rt": rt,
        }

    def _mutate_variant(self) -> None:
        """Mutate pathogen variant into a new strain."""
        new_r0 = self.variant.r0 * random.uniform(1.05, 1.25)
        new_evasion = min(0.9, self.variant.vaccine_evasion + random.uniform(0.1, 0.25))

        self.variant = PathogenVariant(
            name=f"Variant-{random.randint(100, 999)}",
            r0=new_r0,
            incubation_period=self.variant.incubation_period,
            infectious_period=self.variant.infectious_period,
            hospitalization_rate=min(0.2, self.variant.hospitalization_rate * 1.1),
            fatality_rate=min(0.1, self.variant.fatality_rate * 1.1),
            vaccine_evasion=new_evasion,
        )
        logger.info(
            "Pathogen mutated into %s (R0: %.2f, Vaccine Evasion: %.2f)",
            self.variant.name,
            self.variant.r0,
            self.variant.vaccine_evasion,
        )
