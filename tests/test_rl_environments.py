"""Unit tests for Strategify Reinforcement Learning (RL) environment wrappers."""

from __future__ import annotations

from strategify.rl.environment import GeopolEnv


class TestRLEnvironments:
    def test_env_initialization(self):
        env = GeopolEnv(num_agents=2, max_steps=10)
        assert env is not None
        assert env.action_space is not None
        assert env.observation_space is not None

    def test_env_reset(self):
        env = GeopolEnv(num_agents=2, max_steps=10)
        obs, info = env.reset(seed=42)
        assert obs is not None
        assert isinstance(info, dict)

    def test_env_step_rollout(self):
        env = GeopolEnv(num_agents=2, max_steps=5)
        obs, _ = env.reset(seed=42)

        for step in range(5):
            actions = {agent_id: env.action_space.sample() for agent_id in env.agents}
            next_obs, rewards, terminations, truncations, infos = env.step(actions)
            assert isinstance(rewards, dict)
            if any(terminations.values()) or any(truncations.values()):
                break
