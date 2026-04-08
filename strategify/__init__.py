"""strategify — Geopolitical simulation framework (Mesa 2 ABM + Nash equilibrium)."""

from strategify.agents.base import BaseActorAgent
from strategify.agents.state_actor import StateActorAgent
from strategify.config.scenarios import (
    DEFAULT_ACTOR_CONFIGS,
    DEFAULT_ALLIANCES,
    DEFAULT_REGION_RESOURCES,
)
from strategify.config.settings import DEFAULT_N_STEPS, RANDOM_SEED, REAL_WORLD_GEOJSON
from strategify.game_theory.crisis_games import escalation_game
from strategify.game_theory.normal_form import NormalFormGame
from strategify.sim.model import GeopolModel

__all__ = [
    "BaseActorAgent",
    "StateActorAgent",
    "DEFAULT_ACTOR_CONFIGS",
    "DEFAULT_ALLIANCES",
    "DEFAULT_REGION_RESOURCES",
    "REAL_WORLD_GEOJSON",
    "RANDOM_SEED",
    "DEFAULT_N_STEPS",
    "NormalFormGame",
    "escalation_game",
    "GeopolModel",
]
