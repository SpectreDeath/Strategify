"""RL Tournament script for Phase 10: Multi-Agent Tournament.

Runs episodes of GeopolEnv with different agent archetypes and computes metrics.
Supports self-play training mode for AlphaZero-style improvement.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass, field
from typing import Any

import numpy as np

# Ensure we can import strategify
sys.path.append(os.getcwd())

from strategify.rl.environment import GeopolEnv

# Configure logging
logging.basicConfig(level=logging.WARNING)


class RandomPolicy:
    def __call__(self, obs):
        return np.random.randint(0, 2)


class HawkPolicy:
    def __call__(self, obs):
        return 1  # Always Escalate


class DovePolicy:
    def __call__(self, obs):
        return 0  # Always Deescalate


class SelfPlayPolicy:
    """Adaptive policy that learns from previous games (AlphaZero-style)."""

    def __init__(self, name: str):
        self.name = name
        self.policy_weights = np.array([0.5, 0.5])
        self.game_history: list[dict[str, Any]] = []

    def __call__(self, obs):
        return np.random.choice([0, 1], p=self.policy_weights)

    def update_from_result(self, result: dict[str, Any]) -> None:
        """Update policy based on game outcome."""
        self.game_history.append(result)

        if len(self.game_history) >= 5:
            wins = sum(1 for g in self.game_history[-5:] if g.get("won", False))
            win_rate = wins / 5

            if win_rate > 0.6:
                self.policy_weights[1] = min(0.9, self.policy_weights[1] + 0.1)
            elif win_rate < 0.4:
                self.policy_weights[0] = min(0.9, self.policy_weights[0] + 0.1)

            total = self.policy_weights.sum()
            self.policy_weights /= total


@dataclass
class SelfPlayConfig:
    """Configuration for self-play tournament."""

    n_iterations: int = 10
    games_per_iteration: int = 5
    temperature: float = 1.0
    early_stop_threshold: float = 0.8


class SelfPlayTournament:
    """AlphaZero-style self-play tournament for agent improvement."""

    def __init__(self, config: SelfPlayConfig | None = None):
        self.config = config or SelfPlayConfig()
        self.policies: dict[str, SelfPlayPolicy] = {}
        self.best_policy: SelfPlayPolicy | None = None
        self.iteration_history: list[dict[str, Any]] = []

    def add_player(self, name: str) -> SelfPlayPolicy:
        """Add a self-play agent."""
        policy = SelfPlayPolicy(name)
        self.policies[name] = policy
        return policy

    def run_iteration(self) -> dict[str, Any]:
        """Run one iteration of self-play."""
        results = {}

        for name, policy in self.policies.items():
            wins = 0
            total_reward = 0.0

            for _ in range(self.config.games_per_iteration):
                result = self._play_game(policy)
                wins += result["won"]
                total_reward += result["reward"]

            results[name] = {
                "wins": wins,
                "win_rate": wins / self.config.games_per_iteration,
                "avg_reward": total_reward / self.config.games_per_iteration,
            }

            policy.update_from_result({"won": result["won"], "reward": result["reward"]})

        return results

    def _play_game(self, player_policy: SelfPlayPolicy) -> dict[str, Any]:
        """Play a single game against a random opponent."""
        env = GeopolEnv(n_steps=10)
        env.reset()

        player_reward = 0.0

        for agent in env.agent_iter():
            obs, reward, term, trunc, _ = env.last()

            if agent == player_policy.name:
                action = player_policy(obs)
            else:
                action = np.random.randint(0, 2)

            env.step(action)

            if agent == player_policy.name:
                player_reward += reward

            if term or trunc:
                break

        return {"won": player_reward > -5, "reward": player_reward}

    def train(self) -> dict[str, Any]:
        """Run full self-play training."""
        for i in range(self.config.n_iterations):
            results = self.run_iteration()

            best_this_iter = max(results.items(), key=lambda x: x[1]["win_rate"])

            if self.best_policy is None or best_this_iter[1]["win_rate"] > 0.6:
                self.best_policy = self.policies[best_this_iter[0]]

            self.iteration_history.append(
                {
                    "iteration": i + 1,
                    "results": results,
                    "best_player": best_this_iter[0],
                }
            )

            if best_this_iter[1]["win_rate"] >= self.config.early_stop_threshold:
                break

        return {
            "total_iterations": len(self.iteration_history),
            "best_policy": self.best_policy.name if self.best_policy else None,
            "history": self.iteration_history,
        }


archetypes = {
    "agent_alpha": HawkPolicy(),
    "agent_bravo": DovePolicy(),
    "agent_charlie": RandomPolicy(),
    "agent_delta": RandomPolicy(),
}

env = GeopolEnv(n_steps=10)


def run_tournament(n_episodes=5):
    print(f"--- Running Phase 10 RL Tournament ({n_episodes} Episodes) ---")

    total_rewards = {a: 0.0 for a in archetypes}
    final_stabilities = {a: 0.0 for a in archetypes}

    for _ in range(n_episodes):
        env.reset()
        episode_reward = {a: 0.0 for a in env.agents}

        for agent in env.agent_iter():
            observation, reward, termination, truncation, info = env.last()

            if termination or truncation:
                action = None
            else:
                policy = archetypes.get(agent, RandomPolicy())
                action = policy(observation)

            env.step(action)
            if agent in episode_reward:
                episode_reward[agent] += reward

        # Record results
        for a in env.agents:
            if a in total_rewards:
                total_rewards[a] += episode_reward[a]
                # Get stability from mesa agent
                mesa_agent = env._get_agent(a)
                if mesa_agent:
                    final_stabilities[a] += getattr(mesa_agent, "stability", 0.0)

    print("\nTournament Results (Averages):")
    for a in archetypes:
        avg_r = total_rewards[a] / n_episodes
        avg_s = final_stabilities[a] / n_episodes
        policy_name = archetypes[a].__class__.__name__
        print(f"  {a}: Reward={avg_r:>6.2f}, Stability={avg_s:>4.2f} ({policy_name})")


if __name__ == "__main__":
    run_tournament()
