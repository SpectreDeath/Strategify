"""RL Tournament script for Phase 10: Multi-Agent Tournament.

Runs episodes of GeopolEnv with different agent archetypes and computes metrics.
"""

from __future__ import annotations

import logging
import os
import sys

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
