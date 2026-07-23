"""Unified Multi-Domain Strategic Wargaming Engine.

Synthesizes Kinetic Operations, Electronic Warfare, Cyber/Information Deception,
Economic Sanctions, Diplomatic Bargaining, and Epidemiological Contagion into a
single synchronized multi-agent simulation step loop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from strategify.epidemiology.seir import SEIRHEngine
from strategify.military.electronic_warfare import EMSpectrumManager
from strategify.reasoning.deception import DeceptionEngine
from strategify.reasoning.economics import TradeNetwork
from strategify.reasoning.negotiation import DiplomaticNegotiator

logger = logging.getLogger(__name__)


class MockWargameAgent:
    """Agent wrapper for wargame domain subsystems."""

    def __init__(self, region_id: str) -> None:
        self.region_id = region_id
        self.unique_id = region_id
        self.posture = "Neutral"
        self.capabilities = {"military": 0.8, "economic": 0.7, "diplomatic": 0.6}


@dataclass
class DomainStateSnapshot:
    """State snapshot across all 5 strategic domains."""

    step: int
    military_readiness: dict[str, float]
    spectrum_control_pct: dict[str, float]
    cyber_deception_index: float
    gdp_growth_rate: dict[str, float]
    diplomatic_tensions: float
    epidemic_infections: dict[str, float]


@dataclass
class WargameRunResult:
    """Final outcome of a multi-domain wargame simulation run."""

    total_steps: int
    actor_scores: dict[str, float]
    history: list[DomainStateSnapshot]
    winner: str


class MultiDomainWargameEngine:
    """Engine synthesizing all 5 strategic domain subsystems.

    Parameters
    ----------
    actors : list[str]
        Participating actor/country names (e.g. ['Blue', 'Red']).
    """

    def __init__(self, actors: list[str] | None = None) -> None:
        self.actors = actors or ["BlueLand", "RedNation"]
        self.step_count = 0

        self.agents = {actor: MockWargameAgent(actor) for actor in self.actors}

        # Subsystems
        self.em_manager = EMSpectrumManager(owner_id="HQ")
        self.deception_engines = {actor: DeceptionEngine(agent=self.agents[actor]) for actor in self.actors}
        self.econ_model = TradeNetwork()
        self.negotiators = {actor: DiplomaticNegotiator(agent=self.agents[actor]) for actor in self.actors}
        self.epidemic_engines: dict[str, SEIRHEngine] = {
            actor: SEIRHEngine(population=500_000, initial_infected=10) for actor in self.actors
        }

        self.actor_scores: dict[str, float] = dict.fromkeys(self.actors, 100.0)
        self.history: list[DomainStateSnapshot] = []

    def step(self) -> DomainStateSnapshot:
        """Advance multi-domain wargame simulation loop by 1 step."""
        self.step_count += 1

        # 1. Kinetic & Electronic Warfare Spectrum
        spectrum_ctrl = {}
        for idx, actor in enumerate(self.actors):
            freq = 225.0 + idx * 50.0
            alloc = self.em_manager.allocate_frequency(system=actor, frequency=freq, bandwidth=20.0)
            spectrum_ctrl[actor] = 100.0 if alloc.get("allocated") else 50.0

        # 2. Cyber & Information Deception
        actor0 = self.actors[0]
        target = self.actors[1] if len(self.actors) > 1 else self.actors[0]
        deception_signal = self.deception_engines[actor0].create_feint(target_id=target, purported_posture="Invade")

        # 3. Macroeconomic Sanctions & Growth
        gdp_rates = {}
        for actor in self.actors:
            gdp_rates[actor] = 0.02  # Baseline 2% growth rate

        # 4. Diplomatic Bargaining
        offer = self.negotiators[actor0].propose_deal(receiver_agent=self.agents[target])

        # 5. Public Health & Epidemiological Contagion
        infections = {}
        military_readiness = {}
        for actor in self.actors:
            eng = self.epidemic_engines[actor]
            eng.step(dt_days=1.0, npi_effectiveness=0.3, vaccination_rate=0.1)
            infections[actor] = float(eng.infectious)

            # Cross-domain compound effect: Infections degrade military readiness
            readiness = max(0.0, 100.0 - (eng.infectious / eng.population) * 200.0)
            military_readiness[actor] = readiness

            # Score update
            self.actor_scores[actor] += gdp_rates[actor] * 10.0 - (eng.infectious / 1000.0)

        snapshot = DomainStateSnapshot(
            step=self.step_count,
            military_readiness=military_readiness,
            spectrum_control_pct=spectrum_ctrl,
            cyber_deception_index=float(deception_signal.credibility),
            gdp_growth_rate=gdp_rates,
            diplomatic_tensions=float(offer.territorial_concession),
            epidemic_infections=infections,
        )
        self.history.append(snapshot)

        logger.info("MultiDomainWargameEngine executed Step %d across %d actors", self.step_count, len(self.actors))
        return snapshot

    def get_state_snapshot(self) -> DomainStateSnapshot:
        """Return current state snapshot or compute initial snapshot if history is empty."""
        if self.history:
            return self.history[-1]

        # Initial baseline snapshot
        return DomainStateSnapshot(
            step=self.step_count,
            military_readiness=dict.fromkeys(self.actors, 100.0),
            spectrum_control_pct=dict.fromkeys(self.actors, 50.0),
            cyber_deception_index=0.5,
            gdp_growth_rate=dict.fromkeys(self.actors, 0.02),
            diplomatic_tensions=0.3,
            epidemic_infections=dict.fromkeys(self.actors, 10.0),
        )

    def run_wargame(self, total_steps: int = 10) -> WargameRunResult:
        """Run multi-domain simulation for a fixed number of steps.

        Parameters
        ----------
        total_steps : int
            Number of steps to simulate.

        Returns
        -------
        WargameRunResult
            Final wargame outcome and trajectory history.
        """
        for _ in range(total_steps):
            self.step()

        winner = max(self.actor_scores, key=lambda a: self.actor_scores[a])

        return WargameRunResult(
            total_steps=self.step_count,
            actor_scores=self.actor_scores,
            history=self.history,
            winner=winner,
        )
