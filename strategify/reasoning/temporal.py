"""Temporal dynamics: seasons, election cycles, economic cycles.

Modifies agent parameters and decision-making based on time-dependent
cycles that reflect real-world geopolitical dynamics.
"""

from __future__ import annotations

import logging
import math
from typing import Any

logger = logging.getLogger(__name__)


class Season:
    """Season types affecting military and economic operations."""

    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"


# Season modifiers: (military_modifier, economic_modifier)
SEASON_MODIFIERS: dict[str, tuple[float, float]] = {
    Season.SPRING: (1.0, 1.1),
    Season.SUMMER: (1.2, 1.0),
    Season.AUTUMN: (0.9, 1.1),
    Season.WINTER: (0.6, 0.8),
}

SEASON_ORDER = [Season.SPRING, Season.SUMMER, Season.AUTUMN, Season.WINTER]


class TemporalDynamics:
    """Manages time-dependent modifications to the simulation.

    Tracks seasons, election cycles, and economic cycles, and applies
    appropriate modifiers to agent capabilities and decision-making.

    Parameters
    ----------
    model:
        The parent GeopolModel.
    steps_per_year:
        Number of simulation steps per simulated year.
    """

    def __init__(self, model: Any, steps_per_year: int = 4) -> None:
        self.model = model
        self.steps_per_year = max(1, steps_per_year)
        self._step: int = 0

        # Seasons
        self.current_season: str = Season.SPRING

        # Election cycles: {agent_uid: {"period": int, "phase": float}}
        self.election_cycles: dict[int, dict[str, Any]] = {}

        # Economic cycles: phase 0-1 (0=recession, 0.5=recovery, 1=peak)
        self.economic_phase: float = 0.5
        self.economic_period: int = 8  # steps per economic cycle

        # Base capabilities snapshot (before temporal modifiers)
        self._base_capabilities: dict[int, dict[str, float]] = {}

    def initialize(self) -> None:
        """Set up initial temporal state from model agents."""
        for agent in self.model.schedule.agents:
            uid = agent.unique_id
            self._base_capabilities[uid] = dict(agent.capabilities)

            # Random election period per agent (3-7 years)
            import random

            period = random.randint(3, 7) * self.steps_per_year
            self.election_cycles[uid] = {
                "period": period,
                "phase": random.random(),
                "in_election": False,
            }

    def step(self) -> None:
        """Advance temporal dynamics by one step."""
        self._step += 1

        # Update season
        season_idx = (self._step // self.steps_per_year) % 4
        self.current_season = SEASON_ORDER[season_idx]

        # Update economic cycle
        self.economic_phase = (math.sin(2 * math.pi * self._step / self.economic_period) + 1) / 2

        # Update election cycles and apply all modifiers
        self._apply_modifiers()

    def _apply_modifiers(self) -> None:
        """Apply temporal modifiers to agent capabilities."""
        mil_mod, eco_mod = SEASON_MODIFIERS[self.current_season]

        # Economic cycle modifier: maps phase to multiplier
        eco_cycle_mod = 0.7 + 0.6 * self.economic_phase  # 0.7 to 1.3

        for agent in self.model.schedule.agents:
            uid = agent.unique_id
            base = self._base_capabilities.get(uid, agent.capabilities)

            # Election modifier
            election = self.election_cycles.get(uid, {})
            period = election.get("period", 4)
            election_progress = (self._step % period) / period
            in_election = election_progress > 0.9
            election["in_election"] = in_election
            election_mod = 1.1 if in_election else 1.0  # Election = higher military

            # Apply combined modifiers
            agent.capabilities["military"] = min(
                1.0, base.get("military", 0.5) * mil_mod * election_mod
            )
            agent.capabilities["economic"] = min(
                1.0, base.get("economic", 0.5) * eco_mod * eco_cycle_mod
            )

    def get_season(self) -> str:
        """Return current season name."""
        return self.current_season

    def get_economic_phase(self) -> float:
        """Return current economic cycle phase [0, 1]."""
        return self.economic_phase

    def get_economic_description(self) -> str:
        """Return human-readable economic phase description."""
        if self.economic_phase < 0.25:
            return "recession"
        elif self.economic_phase < 0.5:
            return "recovery"
        elif self.economic_phase < 0.75:
            return "expansion"
        else:
            return "peak"

    def is_election_season(self, unique_id: int) -> bool:
        """Check if an agent is currently in an election."""
        return self.election_cycles.get(unique_id, {}).get("in_election", False)

    def get_season_modifier(self) -> tuple[float, float]:
        """Return current (military, economic) season modifier."""
        return SEASON_MODIFIERS[self.current_season]

    def summary(self) -> dict[str, Any]:
        """Return temporal state summary."""
        agents_in_election = sum(
            1 for e in self.election_cycles.values() if e.get("in_election", False)
        )
        return {
            "step": self._step,
            "season": self.current_season,
            "economic_phase": self.economic_phase,
            "economic_description": self.get_economic_description(),
            "agents_in_election": agents_in_election,
            "season_military_modifier": SEASON_MODIFIERS[self.current_season][0],
            "season_economic_modifier": SEASON_MODIFIERS[self.current_season][1],
        }
