"""Unit tests for Strategify Reinforcement Learning (RL) environment wrappers."""

from __future__ import annotations

from strategify.rl.environment import GeopolEnv


class TestRLEnvironments:
    def test_env_initialization(self):
        env = GeopolEnv(n_steps=10)
        assert env is not None
        assert env.n_steps == 10

    def test_env_reset(self):
        env = GeopolEnv(n_steps=10)
        assert env is not None
        assert env.n_steps == 10

    def test_env_step_rollout(self):
        env = GeopolEnv(n_steps=5)
        assert env is not None
        assert env.n_steps == 5
