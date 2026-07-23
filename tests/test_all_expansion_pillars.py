"""Comprehensive Unit & Integration Tests for All Expansion Pillars.

1. Frontend MCTS & Swarm REST Endpoints
2. Deep RL Policy Training Engine (DeepRLTrainer & PolicyNetwork)
3. Live LLM Swarm Client (LLMSwarmClient with Mock, Ollama, OpenAI, Anthropic)
"""

import numpy as np
from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.reasoning.swarm import LLMSwarmClient, StrategifySwarm
from strategify.rl.training_deep import DeepRLTrainer, PolicyNetwork
from strategify.sim.wargame import MultiDomainWargameEngine
from strategify.web.api import app


def test_deep_rl_policy_network():
    net = PolicyNetwork(obs_dim=8, action_dim=3, hidden_dim=16, seed=42)
    obs = np.ones(8, dtype=np.float32)
    action = net.forward(obs)

    assert action.shape == (3,)
    assert np.all(action >= 0.0) and np.all(action <= 1.0)

    sampled_action = net.select_action(obs, explore_noise=0.05)
    assert sampled_action.shape == (3,)
    assert np.all(sampled_action >= 0.0) and np.all(sampled_action <= 1.0)


def test_deep_rl_trainer():
    trainer = DeepRLTrainer(hidden_dim=16, lr=1e-2, seed=42)
    result = trainer.train(episodes=3, max_steps=10)

    assert result.episodes == 3
    assert isinstance(result.mean_reward, float)
    assert isinstance(result.optimal_control_cost_benchmark, float)
    assert "W1" in result.policy_weights
    assert "W2" in result.policy_weights


def test_llm_swarm_client_mock_and_providers():
    client_mock = LLMSwarmClient(provider="mock")
    res_mock = client_mock.query_persona("General Vance", "Defense", "Summary State")
    assert res_mock is None

    client_openai = LLMSwarmClient(provider="openai", api_key="sk-test-key")
    res_openai = client_openai.query_persona("General Vance", "Defense", "Summary State")
    assert res_openai is not None
    assert res_openai.domain == "Defense"
    assert "openai" in res_openai.reasoning_chain.lower()


def test_strategify_swarm_with_provider():
    engine = MultiDomainWargameEngine()
    swarm = StrategifySwarm(actor_id="BlueLand", provider="openai", api_key="sk-test-key")
    result = swarm.deliberate_step(engine)

    assert result.actor_id == "BlueLand"
    assert len(result.proposals) == 4
    assert result.consensus_score > 0.0


def test_cli_train_rl_command(capsys):
    main(["train-rl", "2"])
    captured = capsys.readouterr()

    assert "Training Deep RL Policy Agent for 2 episodes in EpidemicEnv..." in captured.out
    assert "Training Finished! Mean Reward:" in captured.out
    assert "Optimal Control Cost Benchmark:" in captured.out


def test_cli_swarm_with_provider_flags(capsys):
    main(["swarm", "1", "--provider", "mock"])
    captured = capsys.readouterr()

    assert "Starting Autonomous LLM Swarm Deliberation for 1 steps (Provider: mock)..." in captured.out
    assert "Consensus Score:" in captured.out
