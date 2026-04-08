---
name: strategify-rl-development
description: Use when working with reinforcement learning components, training agents, or evaluating RL policies
---

# Geopol-Sim RL Development Skill

## RL Environment

### PettingZoo AEC Environment

The RL environment is in `strategify/rl/environment.py`:

```python
from strategify.rl.environment import GeopolEnv

# Create environment
env = GeopolEnv(
    scenario="default",
    enable_economics=True,
    enable_escalation_ladder=True,
)

# Reset - returns initial observations
observations = env.reset()

# Step - take action for all agents
actions = {"RUS": 0, "UKR": 1, "POL": 2, "BLR": 0}
observations, rewards, terminations, truncations, infos = env.step(actions)

# Observation space: Dict of Box spaces for each agent
# Action space: Discrete(5) per agent (escalation levels)
```

### Environment Features

| Feature | Description |
|---------|-------------|
| Observation | Agent capabilities, escalation levels, alliance strengths, neighbor states |
| Actions | 5 escalation levels (0-4) |
| Rewards | Based on conflict outcomes, alliance changes, stability |
| Termination | All agents agree to peace or max steps reached |
| Truncation | Max steps (100) |

## Training

### Basic Training

```python
from strategify.rl.training import train_ppo

# Train PPO agent
results = train_ppo(
    env_fn=lambda: GeopolEnv(scenario="default"),
    total_timesteps=100000,
    save_path="models/ppo_geopol",
)
```

### Custom Training Loop

```python
from strategify.rl.training import TrainingConfig
from strategify.rl.environment import GeopolEnv

config = TrainingConfig(
    lr=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
)

env = GeopolEnv()
agent = PPOAgent(config)

for episode in range(100):
    obs = env.reset()
    done = False
    while not done:
        actions = {aid: agent.act(obs[aid]) for aid in obs}
        obs, rewards, terms, truncs, infos = env.step(actions)
        for aid, r in rewards.items():
            agent.store(aid, r)
        done = all(terms.values()) or all(truncs.values())
    agent.train()
```

## Tournament

### Run Tournament

```python
from strategify.rl.tournament import run_tournament

results = run_tournament(
    agents=[
        ("PPO", "models/ppo_v1"),
        ("Random", "random"),
        (" TitForTat", "axelrod:TitForTat"),
    ],
    n_episodes=50,
    scenario="default",
)

print(results.rankings)
```

### Agent Types

| Agent | Description |
|-------|-------------|
| `"random"` | Random actions |
| `"axelrod:Aggressive"` | Always escalates |
| `"axelrod:TitForTat"` | Copies opponent's last move |
| `"axelrod:Grudger"` | Escalates if opponent ever escalated |
| `"ppo:path/to/model"` | Trained PPO agent |

## Evaluation

### Evaluate Trained Agent

```python
from strategify.rl.evaluation import evaluate_agent

stats = evaluate_agent(
    agent_path="models/ppo_geopol",
    env_fn=lambda: GeopolEnv(scenario="default"),
    n_episodes=100,
)

print(f"Mean reward: {stats['mean_reward']:.2f}")
print(f"Std reward: {stats['std_reward']:.2f}")
print(f"Win rate: {stats['win_rate']:.2%}")
```

### Metrics Tracked

- Total reward
- Episode length
- Escalation frequency
- Alliance changes
- Final state comparison

## Testing RL Components

```bash
# Run RL tests
pytest tests/test_rl_env.py -v
pytest tests/test_rl_tournament.py -v
```

### Mock Testing

For unit tests without heavy computation:

```python
from unittest.mock import patch, MagicMock
import pytest

class TestRLEnvironment:
    @pytest.fixture
    def mock_env(self):
        with patch('strategify.rl.environment.GeopolEnv') as mock:
            yield mock
    
    def test_env_init(self, mock_env):
        env = GeopolEnv(scenario="default")
        assert env is not None
```
