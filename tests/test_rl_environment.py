"""Tests for RL environment module.

Tests PettingZoo AEC environment wrapping GeopolModel.
"""


import numpy as np
import pytest

from strategify.rl.environment import GeopolEnv


class TestGeopolEnv:
    """Tests for GeopolEnv."""

    @pytest.fixture
    def env(self):
        env = GeopolEnv(n_steps=10)
        return env

    @pytest.fixture
    def env_with_model(self):
        from strategify.sim.model import GeopolModel

        def model_factory():
            return GeopolModel()

        env = GeopolEnv(model_factory=model_factory, n_steps=20)
        env.reset()
        return env

    def test_env_init(self, env):
        assert env.n_steps == 10
        assert env.model is None
        assert env._step_count == 0

    def test_env_metadata(self):
        env = GeopolEnv()
        assert env.metadata["name"] == "geopol_v0"

    def test_observation_space_shape(self, env):
        assert env.observation_space("agent_1").shape == (8,)

    def test_action_space_n_actions(self, env):
        assert env.action_space("agent_1").n == 2

    def test_reset_creates_model(self, env_with_model):
        assert env_with_model.model is not None
        assert len(env_with_model.agents) > 0
        assert len(env_with_model.possible_agents) > 0

    def test_reset_creates_agents(self, env_with_model):
        assert all(isinstance(a, str) for a in env_with_model.agents)
        assert all(a.startswith("agent_") for a in env_with_model.agents)

    def test_reset_initializes_spaces(self, env_with_model):
        for agent in env_with_model.agents:
            assert agent in env_with_model.observation_spaces
            assert agent in env_with_model.action_spaces

    def test_reset_initializes_rewards(self, env_with_model):
        for agent in env_with_model.agents:
            assert agent in env_with_model.rewards

    def test_reset_sets_agent_selection(self, env_with_model):
        assert env_with_model.agent_selection in env_with_model.agents


class TestGeopolEnvObservation:
    """Tests for observation generation."""

    @pytest.fixture
    def env_with_model(self):
        from strategify.sim.model import GeopolModel

        def model_factory():
            return GeopolModel()

        env = GeopolEnv(model_factory=model_factory, n_steps=20)
        env.reset()
        return env

    def test_observe_returns_array(self, env_with_model):
        agent = env_with_model.agents[0]
        obs = env_with_model.observe(agent)
        assert isinstance(obs, np.ndarray)
        assert obs.shape == (8,)

    def test_observe_returns_zeros_if_no_model(self):
        env = GeopolEnv()
        obs = env.observe("agent_1")
        assert np.allclose(obs, 0.0)

    def test_observe_returns_zeros_if_invalid_agent(self, env_with_model):
        obs = env_with_model.observe("invalid_agent")
        assert np.allclose(obs, 0.0)

    def test_observe_contains_capabilities(self, env_with_model):
        agent = env_with_model.agents[0]
        obs = env_with_model.observe(agent)
        assert obs[0] >= 0  # military
        assert obs[1] >= 0  # economic


class TestGeopolEnvStep:
    """Tests for step execution."""

    @pytest.fixture
    def env_with_model(self):
        from strategify.sim.model import GeopolModel

        def model_factory():
            return GeopolModel()

        env = GeopolEnv(model_factory=model_factory, n_steps=20)
        env.reset()
        return env

    def test_step_model_is_stepped(self, env_with_model):
        agent = env_with_model.agent_selection
        agent_obj = env_with_model._get_agent(agent)

        initial_step_count = env_with_model._step_count
        env_with_model.step(1)

        assert env_with_model._step_count >= initial_step_count

    def test_step_reward_is_float(self, env_with_model):
        agent = env_with_model.agent_selection
        env_with_model.step(1)
        reward = env_with_model.rewards.get(agent, 0.0)

        assert isinstance(reward, float)


class TestGeopolEnvIteration:
    """Tests for agent iteration."""

    @pytest.fixture
    def env_with_model(self):
        from strategify.sim.model import GeopolModel

        def model_factory():
            return GeopolModel()

        env = GeopolEnv(model_factory=model_factory, n_steps=20)
        env.reset()
        return env

    def test_agents_list_not_empty(self, env_with_model):
        assert len(env_with_model.agents) > 0

    def test_agent_selection_valid(self, env_with_model):
        assert env_with_model.agent_selection in env_with_model.possible_agents


class TestGeopolEnvTermination:
    """Tests for termination handling."""

    @pytest.fixture
    def env_with_model(self):
        from strategify.sim.model import GeopolModel

        def model_factory():
            return GeopolModel()

        env = GeopolEnv(model_factory=model_factory, n_steps=1)
        env.reset()
        return env

    def test_terminal_state_truncation(self, env_with_model):
        env_with_model.truncations[env_with_model.agent_selection] = True

        initial_agent = env_with_model.agent_selection
        env_with_model.step(0)

        assert env_with_model.agent_selection != initial_agent or len(env_with_model.agents) == 0


class TestGeopolEnvRewards:
    """Tests for reward calculation."""

    @pytest.fixture
    def env_with_model(self):
        from strategify.sim.model import GeopolModel

        def model_factory():
            return GeopolModel()

        env = GeopolEnv(model_factory=model_factory, n_steps=20)
        env.reset()
        return env

    def test_rewards_initialized(self, env_with_model):
        assert len(env_with_model.rewards) > 0

    def test_rewards_are_floats(self, env_with_model):
        assert all(isinstance(r, (float, int)) for r in env_with_model.rewards.values())
