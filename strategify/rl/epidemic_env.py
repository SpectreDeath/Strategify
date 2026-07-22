"""Gymnasium RL Environment for Public Health Policy & Biodefense.

Subclasses gymnasium.Env to expose continuous observation and action spaces
for training RL agents (PPO, DDPG, SAC) against dynamic pathogen environments.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
    GYM_AVAILABLE = True
except ImportError:
    GYM_AVAILABLE = False
    # Fallback minimal Gym spaces for testing environments without gymnasium installed
    class DummySpace:
        def __init__(self, shape: tuple[int, ...], low: float = 0.0, high: float = 1.0) -> None:
            self.shape = shape
            self.low = low
            self.high = high

    class DummySpaces:
        Box = DummySpace

    spaces = DummySpaces()
    class DummyEnv:
        pass
    gym = type("gym", (), {"Env": DummyEnv})()

from strategify.epidemiology.countermeasures import BioDefenseComponent
from strategify.epidemiology.seir import SEIRHEngine

logger = logging.getLogger(__name__)


class EpidemicEnv(gym.Env):
    """Gymnasium Environment for Epidemiological Policy Control.

    Observation Space (Box 8):
    [S, E, I, H, R, x_cooperation, Rt, ICU_capacity_pct]

    Action Space (Box 3):
    [u_NPI, u_vaccine_funding, u_icu_expansion] in [0, 1]^3
    """

    metadata = {"render_modes": ["human"]}

    def __init__(self, population: int = 1_000_000, max_steps: int = 100) -> None:
        super().__init__()
        self.population = population
        self.max_steps = max_steps
        self.current_step = 0

        # Continuous Spaces
        if GYM_AVAILABLE:
            self.observation_space = spaces.Box(
                low=0.0,
                high=np.finfo(np.float32).max,
                shape=(8,),
                dtype=np.float32,
            )
            self.action_space = spaces.Box(
                low=0.0,
                high=1.0,
                shape=(3,),
                dtype=np.float32,
            )
        else:
            self.observation_space = spaces.Box(shape=(8,))
            self.action_space = spaces.Box(shape=(3,))

        self.reset()

    def reset(self, seed: int | None = None, options: dict[str, Any] | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset environment to initial state."""
        self.current_step = 0
        self.seir_engine = SEIRHEngine(population=self.population, initial_infected=20)

        # Mock agent wrapper for biodefense component
        class AgentWrapper:
            region_id = "ENV-01"
            capabilities = {"economic": 0.8}

        self.biodefense = BioDefenseComponent(AgentWrapper())
        obs = self._get_obs()
        return obs, {}

    def _get_obs(self) -> np.ndarray:
        """Construct 8-element continuous observation array."""
        rt = self.seir_engine.compute_effective_rt(
            npi_effectiveness=self.biodefense.status.npi_level,
            vaccination_rate=self.biodefense.status.vaccination_rate,
        )
        icu_pct = self.seir_engine.hospitalized / max(1.0, self.population * 0.05 * self.biodefense.status.icu_capacity)

        obs = np.array(
            [
                self.seir_engine.susceptible / self.population,
                self.seir_engine.exposed / self.population,
                self.seir_engine.infectious / self.population,
                self.seir_engine.hospitalized / self.population,
                self.seir_engine.recovered / self.population,
                self.biodefense.status.vaccination_rate,
                rt,
                icu_pct,
            ],
            dtype=np.float32,
        )
        return obs

    def step(self, action: np.ndarray | list[float]) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        """Advance simulation step by applying action vector [u_NPI, u_vax, u_icu].

        Parameters
        ----------
        action : np.ndarray | list[float]
            Continuous action vector in [0.0, 1.0]^3.

        Returns
        -------
        tuple
            (observation, reward, terminated, truncated, info)
        """
        self.current_step += 1
        act = np.clip(action, 0.0, 1.0)

        u_npi, u_vax, u_icu = float(act[0]), float(act[1]), float(act[2])

        # Apply policies
        gdp_drag = self.biodefense.set_npi_policy(u_npi)
        if u_vax > 0.1:
            self.biodefense.fund_vaccine_rd(u_vax * 0.5)
            self.biodefense.execute_vaccination_campaign(u_vax * 0.02)
        if u_icu > 0.1:
            self.biodefense.expand_icu_capacity(u_icu * 0.1)

        # Advance continuous compartment engine
        self.seir_engine.step(
            dt_days=1.0,
            npi_effectiveness=self.biodefense.status.npi_level,
            vaccination_rate=self.biodefense.status.vaccination_rate,
        )

        obs = self._get_obs()

        # Reward: - (disease cost + gdp drag + ICU overload penalty)
        cost_infection = (self.seir_engine.infectious / self.population) * 100.0
        cost_icu_overload = max(0.0, obs[7] - 1.0) * 50.0
        reward = float(-(cost_infection + gdp_drag * 10.0 + cost_icu_overload))

        terminated = self.seir_engine.infectious < 1.0
        truncated = self.current_step >= self.max_steps

        info = {
            "rt": float(obs[6]),
            "gdp_drag": gdp_drag,
            "deceased": self.seir_engine.deceased,
        }

        return obs, reward, terminated, truncated, info
