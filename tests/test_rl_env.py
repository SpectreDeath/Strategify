import tempfile
from pathlib import Path

import numpy as np

from strategify.rl.environment import GeopolEnv
from strategify.rl.training import QLearningPolicy


def test_env_creation():
    env = GeopolEnv(n_steps=5)
    assert env.n_steps == 5


def test_env_reset():
    env = GeopolEnv(n_steps=5)
    env.reset()
    assert env.model is not None
    assert len(env.agents) == 4
    assert env._step_count == 0


def test_env_observe():
    env = GeopolEnv(n_steps=5)
    env.reset()
    obs = env.observe(env.agents[0])
    assert isinstance(obs, np.ndarray)
    assert obs.shape == (8,)


def test_env_step():
    env = GeopolEnv(n_steps=5)
    env.reset()
    env.step(0)  # Deescalate
    assert isinstance(env.rewards[env.agents[0]], (int, float))


def test_env_action_space():
    env = GeopolEnv(n_steps=5)
    env.reset()
    space = env.action_space(env.agents[0])
    assert space.n == 2  # Discrete(2)


def test_env_termination():
    env = GeopolEnv(n_steps=2)
    env.reset()
    # Step through all agents twice (2 full cycles = n_steps)
    for _ in range(len(env.agents) * 2):
        env.step(0)
    # After n_steps, agents should be terminated
    assert env._step_count >= 2


# ---------------------------------------------------------------------------
# Q-learning save/load roundtrip (regression for eval() → ast.literal_eval fix)
# ---------------------------------------------------------------------------


def test_qlearning_save_load_roundtrip():
    policy = QLearningPolicy(seed=42)
    # Populate Q-table with some entries
    obs = np.array([0.5, 0.3, -0.1, 0.7, 0.9, 0.2])
    for _ in range(10):
        action = policy.act(obs, "agent_0")
        policy.update(obs, action, 1.0, obs, "agent_0")

    original_keys = set(policy.q_table.keys())
    original_values = {k: v.copy() for k, v in policy.q_table.items()}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name

    try:
        policy.save(path)
        loaded = QLearningPolicy(seed=99)
        loaded.load(path)
        assert set(loaded.q_table.keys()) == original_keys
        for k in original_keys:
            np.testing.assert_array_equal(loaded.q_table[k], original_values[k])
    finally:
        Path(path).unlink(missing_ok=True)
