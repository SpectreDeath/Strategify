"""RL training loop: train multi-agent policies on the GeopolEnv.

Provides simple training utilities without requiring heavy RL libraries.
Includes random, heuristic, and basic Q-learning baselines.
"""

from __future__ import annotations

import ast
import json
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)


class SimplePolicy:
    """Base class for RL policies."""

    def act(self, observation: np.ndarray, agent_id: str) -> int:
        """Return action (0=Deescalate, 1=Escalate)."""
        raise NotImplementedError

    def update(
        self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, agent_id: str
    ) -> None:
        """Update policy from experience."""
        pass

    def save(self, path: str | Path) -> None:
        """Save policy parameters."""
        raise NotImplementedError

    def load(self, path: str | Path) -> None:
        """Load policy parameters."""
        raise NotImplementedError


class RandomPolicy(SimplePolicy):
    """Random action policy (baseline)."""

    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    def act(self, observation: np.ndarray, agent_id: str) -> int:
        return int(self.rng.integers(0, 2))


class DeescalatePolicy(SimplePolicy):
    """Always de-escalate (pacifist baseline)."""

    def act(self, observation: np.ndarray, agent_id: str) -> int:
        return 0


class EscalatePolicy(SimplePolicy):
    """Always escalate (aggressive baseline)."""

    def act(self, observation: np.ndarray, agent_id: str) -> int:
        return 1


class HeuristicPolicy(SimplePolicy):
    """Heuristic policy based on observation features.

    Escalates when military strength is high and opponents are escalating.
    De-escalates when economic strength is low or allies are peaceful.
    """

    def __init__(self, aggression: float = 0.5):
        self.aggression = aggression

    def act(self, observation: np.ndarray, agent_id: str) -> int:
        military = observation[0]
        economic = observation[1]
        net_inf = observation[2]
        escalation = observation[3]

        # Score: positive favors escalation
        score = (
            (military - 0.5) * self.aggression
            - (economic - 0.5) * (1 - self.aggression)
            + net_inf * 0.3
            + escalation * 0.2
        )
        return 1 if score > 0 else 0


class QLearningPolicy(SimplePolicy):
    """Tabular Q-learning policy with discretized observations.

    Discretizes the continuous observation space into bins for
    tractable Q-table storage.
    """

    def __init__(
        self,
        n_bins: int = 4,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.1,
        seed: int = 42,
    ):
        self.n_bins = n_bins
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.rng = np.random.default_rng(seed)
        self.q_table: dict[tuple, np.ndarray] = {}

    def _discretize(self, obs: np.ndarray) -> tuple:
        """Discretize continuous observation to bin indices."""
        bins = np.linspace(-1.0, 2.0, self.n_bins + 1)
        return tuple(int(np.digitize(o, bins)) for o in obs)

    def _get_q(self, state: tuple) -> np.ndarray:
        if state not in self.q_table:
            self.q_table[state] = np.zeros(2)
        return self.q_table[state]

    def act(self, observation: np.ndarray, agent_id: str) -> int:
        state = self._discretize(observation)
        if self.rng.random() < self.epsilon:
            return int(self.rng.integers(0, 2))
        q = self._get_q(state)
        return int(np.argmax(q))

    def update(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        next_obs: np.ndarray,
        agent_id: str,
    ) -> None:
        state = self._discretize(obs)
        next_state = self._discretize(next_obs)
        q = self._get_q(state)
        next_q = self._get_q(next_state)
        q[action] += self.alpha * (reward + self.gamma * np.max(next_q) - q[action])

    def save(self, path: str | Path) -> None:
        path = Path(path)
        data = {str(k): v.tolist() for k, v in self.q_table.items()}
        with open(path, "w") as f:
            json.dump(data, f)

    def load(self, path: str | Path) -> None:
        path = Path(path)
        with open(path) as f:
            data = json.load(f)
        self.q_table = {tuple(ast.literal_eval(k)): np.array(v) for k, v in data.items()}


def train_episode(
    env: Any,
    policies: dict[str, SimplePolicy],
    n_steps: int = 20,
) -> dict[str, float]:
    """Run one training episode.

    Parameters
    ----------
    env:
        PettingZoo AEC environment.
    policies:
        ``{agent_name: policy}`` mapping.
    n_steps:
        Maximum steps per episode.

    Returns
    -------
    dict
        ``{agent_name: total_reward}``
    """
    env.reset()
    total_rewards: dict[str, float] = {a: 0.0 for a in env.agents}

    for _ in range(n_steps * len(env.agents)):
        agent = env.agent_selection
        if env.terminations.get(agent, True):
            break

        obs, reward, term, trunc, info = env.last(observe=True)

        policy = policies.get(agent, RandomPolicy())
        action = policy.act(obs, agent)
        env.step(action)

        # Get next observation for learning
        next_obs = env.observe(agent)
        policy.update(obs, action, reward, next_obs, agent)
        total_rewards[agent] = total_rewards.get(agent, 0.0) + reward

    return total_rewards


def train(
    env_factory: Callable,
    policies: dict[str, SimplePolicy],
    n_episodes: int = 100,
    n_steps: int = 20,
    log_interval: int = 10,
) -> list[dict[str, float]]:
    """Train policies over multiple episodes.

    Parameters
    ----------
    env_factory:
        Callable returning a fresh environment.
    policies:
        ``{agent_name: policy}`` mapping.
    n_episodes:
        Number of training episodes.
    n_steps:
        Steps per episode.
    log_interval:
        Log every N episodes.

    Returns
    -------
    list[dict]
        Per-episode reward summaries.
    """
    history = []
    for ep in range(n_episodes):
        env = env_factory()
        rewards = train_episode(env, policies, n_steps)
        history.append(rewards)

        if (ep + 1) % log_interval == 0:
            avg = {k: np.mean([h.get(k, 0) for h in history[-log_interval:]]) for k in policies}
            logger.info("Episode %d: %s", ep + 1, {k: f"{v:.2f}" for k, v in avg.items()})

    return history
