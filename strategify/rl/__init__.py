"""Reinforcement learning: environment, training, evaluation, and epidemiology RL benchmarks."""

from strategify.rl.benchmark import BenchmarkComparisonResult, RLControlBenchmark
from strategify.rl.epidemic_env import EpidemicEnv
from strategify.rl.environment import GeopolEnv
from strategify.rl.evaluation import (
    compare_strategies,
    evaluate_policies,
    summarize_comparison,
)
from strategify.rl.training import (
    DeescalatePolicy,
    EscalatePolicy,
    HeuristicPolicy,
    QLearningPolicy,
    RandomPolicy,
    SimplePolicy,
    train,
    train_episode,
)

__all__ = [
    "GeopolEnv",
    "EpidemicEnv",
    "RLControlBenchmark",
    "BenchmarkComparisonResult",
    "train",
    "train_episode",
    "SimplePolicy",
    "RandomPolicy",
    "HeuristicPolicy",
    "EscalatePolicy",
    "DeescalatePolicy",
    "QLearningPolicy",
    "evaluate_policies",
    "compare_strategies",
    "summarize_comparison",
]
