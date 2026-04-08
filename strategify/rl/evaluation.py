"""RL evaluation: compare trained policies against rule-based agents.

Provides utilities to benchmark RL policies against heuristic and
random baselines, and to measure strategic improvement.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

import numpy as np

from strategify.rl.training import (
    DeescalatePolicy,
    EscalatePolicy,
    HeuristicPolicy,
    QLearningPolicy,
    RandomPolicy,
    SimplePolicy,
    train_episode,
)

logger = logging.getLogger(__name__)


def evaluate_policies(
    env_factory: Callable,
    policies: dict[str, SimplePolicy],
    n_episodes: int = 20,
    n_steps: int = 20,
) -> dict[str, dict[str, float]]:
    """Evaluate policies over multiple episodes.

    Parameters
    ----------
    env_factory:
        Callable returning a fresh environment.
    policies:
        ``{agent_name: policy}`` mapping.
    n_episodes:
        Number of evaluation episodes.
    n_steps:
        Steps per episode.

    Returns
    -------
    dict
        ``{agent_name: {"mean_reward", "std_reward", "min_reward", "max_reward"}}``
    """
    all_rewards: dict[str, list[float]] = {a: [] for a in policies}

    for _ep in range(n_episodes):
        env = env_factory()
        rewards = train_episode(env, policies, n_steps)
        for agent, reward in rewards.items():
            if agent in all_rewards:
                all_rewards[agent].append(reward)

    results = {}
    for agent, reward_list in all_rewards.items():
        arr = np.array(reward_list)
        results[agent] = {
            "mean_reward": float(np.mean(arr)),
            "std_reward": float(np.std(arr)),
            "min_reward": float(np.min(arr)),
            "max_reward": float(np.max(arr)),
        }
    return results


def compare_strategies(
    env_factory: Callable,
    n_episodes: int = 20,
    n_steps: int = 20,
    agent_names: list[str] | None = None,
) -> dict[str, dict[str, float]]:
    """Compare different strategy types on the same environment.

    Parameters
    ----------
    env_factory:
        Callable returning a fresh environment.
    n_episodes:
        Evaluation episodes per strategy.
    n_steps:
        Steps per episode.
    agent_names:
        Agent names to assign policies to. If None, uses first 4 agents.

    Returns
    -------
    dict
        ``{strategy_name: {agent_name: evaluation_result}}``
    """
    if agent_names is None:
        env = env_factory()
        agent_names = env.agents[:4]

    strategies = {
        "random": {a: RandomPolicy() for a in agent_names},
        "always_deescalate": {a: DeescalatePolicy() for a in agent_names},
        "always_escalate": {a: EscalatePolicy() for a in agent_names},
        "heuristic_balanced": {a: HeuristicPolicy(aggression=0.5) for a in agent_names},
        "heuristic_aggressive": {a: HeuristicPolicy(aggression=0.8) for a in agent_names},
        "heuristic_passive": {a: HeuristicPolicy(aggression=0.2) for a in agent_names},
    }

    # Add Q-learning if trained model available
    q_policies = {a: QLearningPolicy(epsilon=0.0) for a in agent_names}
    # Quick train
    try:
        from strategify.rl.training import train

        q_train_policies = {a: QLearningPolicy(epsilon=0.2) for a in agent_names}
        train(env_factory, q_train_policies, n_episodes=50, n_steps=n_steps, log_interval=50)
        # Copy learned Q-tables to evaluation policies
        for a in agent_names:
            q_policies[a].q_table = dict(q_train_policies[a].q_table)
        strategies["q_learning"] = q_policies
    except Exception as exc:
        logger.warning("Q-learning training failed: %s", exc)

    results = {}
    for strategy_name, policies in strategies.items():
        logger.info("Evaluating strategy: %s", strategy_name)
        eval_result = evaluate_policies(env_factory, policies, n_episodes, n_steps)
        results[strategy_name] = eval_result

    return results


def summarize_comparison(comparison: dict) -> str:
    """Format comparison results as a readable table."""
    lines = ["Strategy Comparison", "=" * 60]
    header = f"{'Strategy':<25} {'Mean Reward':>12} {'Std':>8}"
    lines.append(header)
    lines.append("-" * 60)

    for strategy, agents in comparison.items():
        # Average across agents
        means = [v["mean_reward"] for v in agents.values()]
        stds = [v["std_reward"] for v in agents.values()]
        avg_mean = np.mean(means)
        avg_std = np.mean(stds)
        lines.append(f"{strategy:<25} {avg_mean:>12.2f} {avg_std:>8.2f}")

    return "\n".join(lines)
