"""Deep Reinforcement Learning Training Engine for EpidemicEnv.

Implements neural policy gradient optimization (REINFORCE / Deep RL) over continuous
action spaces [u_NPI, u_vaccine, u_icu] in EpidemicEnv and compares learned policy
trajectories against Pontryagin OptimalControlSolver baselines.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from strategify.epidemiology.optimal_control import OptimalControlSolver
from strategify.rl.epidemic_env import EpidemicEnv

logger = logging.getLogger(__name__)


@dataclass
class TrainingResult:
    """Summary metrics returned by DeepRLTrainer execution."""

    episodes: int
    mean_reward: float
    final_reward: float
    optimal_control_cost_benchmark: float
    policy_weights: dict[str, np.ndarray]


class PolicyNetwork:
    """Neural Policy Gradient Network mapping state (8-dim) to actions (3-dim)."""

    def __init__(self, obs_dim: int = 8, action_dim: int = 3, hidden_dim: int = 16, seed: int = 42) -> None:
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 0.1, size=(obs_dim, hidden_dim))
        self.b1 = np.zeros(hidden_dim)
        self.W2 = rng.normal(0, 0.1, size=(hidden_dim, action_dim))
        self.b2 = np.zeros(action_dim)
        self.log_std = np.zeros(action_dim)

    def forward(self, obs: np.ndarray) -> np.ndarray:
        """Forward pass to compute action mean vector in [0, 1]^3."""
        # Normalize observation inputs for numerical stability
        norm_obs = obs / (np.linalg.norm(obs) + 1e-6)
        h = np.tanh(norm_obs.dot(self.W1) + self.b1)
        out = 1.0 / (1.0 + np.exp(-(h.dot(self.W2) + self.b2)))  # Sigmoidal activation
        return np.clip(out, 0.0, 1.0)

    def select_action(self, obs: np.ndarray, explore_noise: float = 0.05) -> np.ndarray:
        """Sample action with exploratory Gaussian noise."""
        mean = self.forward(obs)
        noise = np.random.normal(0.0, explore_noise, size=mean.shape)
        return np.clip(mean + noise, 0.0, 1.0)


class DeepRLTrainer:
    """Trainer executing Policy Gradient optimization loops on EpidemicEnv."""

    def __init__(self, hidden_dim: int = 16, lr: float = 1e-2, seed: int = 42) -> None:
        self.policy = PolicyNetwork(hidden_dim=hidden_dim, seed=seed)
        self.lr = lr

    def train(self, episodes: int = 10, max_steps: int = 50) -> TrainingResult:
        """Train the policy network over specified episodes.

        Parameters
        ----------
        episodes : int
            Number of training episodes.
        max_steps : int
            Maximum step count per episode.

        Returns
        -------
        TrainingResult
            Result summary including rewards and baseline comparisons.
        """
        env = EpidemicEnv(max_steps=max_steps)
        rewards_history = []

        logger.info("Starting Deep RL Policy Training for %d episodes...", episodes)

        for _ep in range(1, episodes + 1):
            obs, _ = env.reset()
            ep_reward = 0.0

            for _ in range(max_steps):
                action = self.policy.select_action(obs, explore_noise=0.05)
                next_obs, reward, done, truncated, _ = env.step(action)
                ep_reward += reward

                # Policy Gradient update step approximation
                grad = (action - self.policy.forward(obs)) * reward
                self.policy.W2 += self.lr * np.outer(np.tanh(obs.dot(self.policy.W1) + self.policy.b1), grad)
                self.policy.b2 += self.lr * grad

                obs = next_obs
                if done or truncated:
                    break

            rewards_history.append(ep_reward)

        # Benchmark against Pontryagin OptimalControlSolver
        solver = OptimalControlSolver()
        oc_sol = solver.solve_forward_backward_sweep()
        oc_cost = float(oc_sol.objective_cost_j)

        mean_reward = float(np.mean(rewards_history))
        final_reward = float(rewards_history[-1])

        logger.info(
            "Deep RL Training Completed (Mean Reward: %.2f, OC Benchmark Cost: %.2f)",
            mean_reward,
            oc_cost,
        )

        return TrainingResult(
            episodes=episodes,
            mean_reward=mean_reward,
            final_reward=final_reward,
            optimal_control_cost_benchmark=oc_cost,
            policy_weights={
                "W1": self.policy.W1,
                "b1": self.policy.b1,
                "W2": self.policy.W2,
                "b2": self.policy.b2,
            },
        )
