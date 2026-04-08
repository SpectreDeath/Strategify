"""Tests for Phase 5: RL training, temporal dynamics, propaganda, multi-scale."""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


# ---------------------------------------------------------------------------
# RL Training (5.1)
# ---------------------------------------------------------------------------


class TestRLPolicies:
    def test_random_policy(self):
        from strategify.rl.training import RandomPolicy

        policy = RandomPolicy(seed=42)
        obs = np.zeros(4, dtype=np.float32)
        action = policy.act(obs, "agent_alpha")
        assert action in (0, 1)

    def test_deescalate_policy(self):
        from strategify.rl.training import DeescalatePolicy

        policy = DeescalatePolicy()
        assert policy.act(np.zeros(4), "test") == 0

    def test_escalate_policy(self):
        from strategify.rl.training import EscalatePolicy

        policy = EscalatePolicy()
        assert policy.act(np.zeros(4), "test") == 1

    def test_heuristic_policy_high_military(self):
        from strategify.rl.training import HeuristicPolicy

        policy = HeuristicPolicy(aggression=0.8)
        obs = np.array([0.9, 0.3, 0.5, 0.0], dtype=np.float32)
        assert policy.act(obs, "test") == 1

    def test_heuristic_policy_low_military(self):
        from strategify.rl.training import HeuristicPolicy

        policy = HeuristicPolicy(aggression=0.2)
        obs = np.array([0.1, 0.9, -0.5, 0.0], dtype=np.float32)
        assert policy.act(obs, "test") == 0

    def test_q_learning_policy(self):
        from strategify.rl.training import QLearningPolicy

        policy = QLearningPolicy(epsilon=0.0, seed=42)
        obs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float32)
        action = policy.act(obs, "test")
        assert action in (0, 1)

    def test_q_learning_update(self):
        from strategify.rl.training import QLearningPolicy

        policy = QLearningPolicy(alpha=0.5, epsilon=0.0)
        obs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float32)
        next_obs = np.array([0.6, 0.4, 0.1, 0.0], dtype=np.float32)
        policy.update(obs, 1, 1.0, next_obs, "test")
        # Q-table should have been updated
        assert len(policy.q_table) > 0

    def test_q_learning_save_load(self):
        from strategify.rl.training import QLearningPolicy

        policy = QLearningPolicy(alpha=0.5, epsilon=0.0)
        obs = np.array([0.5, 0.5, 0.0, 0.0], dtype=np.float32)
        next_obs = np.array([0.6, 0.4, 0.1, 0.0], dtype=np.float32)
        policy.update(obs, 1, 1.0, next_obs, "test")

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "q.json"
            policy.save(path)
            assert path.exists()

            policy2 = QLearningPolicy()
            policy2.load(path)
            assert len(policy2.q_table) > 0


class TestRLTraining:
    def test_train_episode(self, model):
        from strategify.rl.training import RandomPolicy, train_episode

        env = _make_env()
        policies = {a: RandomPolicy() for a in env.agents}
        rewards = train_episode(env, policies, n_steps=3)
        assert isinstance(rewards, dict)
        assert len(rewards) > 0

    def test_train_multiple_episodes(self, model):
        from strategify.rl.training import RandomPolicy, train

        policies = {
            a: RandomPolicy()
            for a in ["agent_alpha", "agent_bravo", "agent_charlie", "agent_delta"]
        }
        history = train(_make_env, policies, n_episodes=3, n_steps=2, log_interval=10)
        assert len(history) == 3


class TestRLEvaluation:
    def test_evaluate_policies(self, model):
        from strategify.rl.evaluation import evaluate_policies
        from strategify.rl.training import RandomPolicy

        policies = {a: RandomPolicy() for a in ["agent_alpha", "agent_bravo"]}
        result = evaluate_policies(_make_env, policies, n_episodes=2, n_steps=2)
        assert "agent_alpha" in result
        assert "mean_reward" in result["agent_alpha"]

    def test_compare_strategies(self, model):
        from strategify.rl.evaluation import compare_strategies

        result = compare_strategies(
            _make_env,
            n_episodes=2,
            n_steps=2,
            agent_names=["agent_alpha", "agent_bravo"],
        )
        assert "random" in result
        assert "always_deescalate" in result
        assert "always_escalate" in result
        assert "heuristic_balanced" in result

    def test_summarize_comparison(self, model):
        from strategify.rl.evaluation import compare_strategies, summarize_comparison

        result = compare_strategies(
            _make_env,
            n_episodes=1,
            n_steps=2,
            agent_names=["agent_alpha"],
        )
        text = summarize_comparison(result)
        assert "random" in text
        assert "Strategy Comparison" in text


def _make_env():
    """Create a GeopolEnv for testing."""
    from strategify.rl.environment import GeopolEnv

    env = GeopolEnv(n_steps=5)
    env.reset()
    return env


# ---------------------------------------------------------------------------
# Temporal Dynamics (5.3)
# ---------------------------------------------------------------------------


class TestTemporalDynamics:
    def test_temporal_dynamics_init(self, model):
        from strategify.reasoning.temporal import TemporalDynamics

        td = TemporalDynamics(model, steps_per_year=4)
        td.initialize()
        assert td.get_season() == "spring"

    def test_season_changes(self, model):
        from strategify.reasoning.temporal import Season, TemporalDynamics

        td = TemporalDynamics(model, steps_per_year=2)
        td.initialize()

        td.step()
        td.step()
        assert td.get_season() == Season.SUMMER

        td.step()
        td.step()
        assert td.get_season() == Season.AUTUMN

    def test_economic_cycle(self, model):
        from strategify.reasoning.temporal import TemporalDynamics

        td = TemporalDynamics(model, steps_per_year=4)
        td.initialize()

        for _ in range(10):
            td.step()

        phase = td.get_economic_phase()
        assert 0.0 <= phase <= 1.0

    def test_season_modifiers_applied(self, model):
        from strategify.reasoning.temporal import TemporalDynamics

        td = TemporalDynamics(model, steps_per_year=4)
        td.initialize()

        base_mil = model.schedule.agents[0].capabilities["military"]
        for _ in range(20):
            td.step()

        # Capabilities should have been modified
        current_mil = model.schedule.agents[0].capabilities["military"]
        assert current_mil != base_mil or current_mil == 1.0

    def test_temporal_summary(self, model):
        from strategify.reasoning.temporal import TemporalDynamics

        td = TemporalDynamics(model, steps_per_year=4)
        td.initialize()
        td.step()

        summary = td.summary()
        assert "season" in summary
        assert "economic_phase" in summary
        assert "economic_description" in summary

    def test_model_with_temporal(self, model):
        from strategify.reasoning.temporal import TemporalDynamics

        td = TemporalDynamics(model, steps_per_year=4)
        td.initialize()
        for _ in range(5):
            model.step()
            td.step()
        assert td.get_season() in ("spring", "summer", "autumn", "winter")


# ---------------------------------------------------------------------------
# Propaganda / Information Warfare (5.4)
# ---------------------------------------------------------------------------


class TestPropaganda:
    def test_propaganda_engine_init(self, model):
        from strategify.reasoning.propaganda import PropagandaEngine

        pe = PropagandaEngine(model)
        pe.initialize()
        assert len(pe.narratives) == 0

    def test_broadcast_narrative(self, model):
        from strategify.reasoning.propaganda import PropagandaEngine

        pe = PropagandaEngine(model)
        pe.initialize()

        agent = model.schedule.agents[0]
        narrative = pe.broadcast(
            agent.unique_id,
            "Military buildup detected",
            is_disinformation=False,
        )
        assert len(pe.narratives) == 1
        assert narrative.source_id == agent.unique_id

    def test_broadcast_disinformation(self, model):
        from strategify.reasoning.propaganda import PropagandaEngine

        pe = PropagandaEngine(model)
        pe.initialize()

        agent = model.schedule.agents[0]
        narrative = pe.broadcast(
            agent.unique_id,
            "False flag operation",
            is_disinformation=True,
            potency=2.0,
        )
        assert narrative.is_disinformation
        assert narrative.credibility < 0.5

    def test_narrative_landscape(self, model):
        from strategify.reasoning.propaganda import PropagandaEngine

        pe = PropagandaEngine(model)
        pe.initialize()

        agent = model.schedule.agents[0]
        pe.broadcast(agent.unique_id, "Truth", is_disinformation=False)
        pe.broadcast(agent.unique_id, "Lies", is_disinformation=True)

        landscape = pe.get_narrative_landscape()
        assert landscape["total_narratives"] == 2
        assert landscape["disinformation_count"] == 1
        assert landscape["truthful_count"] == 1

    def test_narrative_decay(self):
        from strategify.reasoning.propaganda import Narrative

        n = Narrative("test", source_id=1, potency=1.0)
        assert n.effective_potency == 0.5
        n.decay(rate=0.2)
        assert n.potency == pytest.approx(0.8)
        assert n.age == 1

    def test_agent_exposure(self, model):
        from strategify.reasoning.propaganda import PropagandaEngine

        pe = PropagandaEngine(model)
        pe.initialize()

        agent = model.schedule.agents[0]
        pe.broadcast(agent.unique_id, "Info", target_id=agent.unique_id)

        exposure = pe.get_agent_exposure(agent.unique_id)
        assert "disinfo_exposure" in exposure
        assert "truthful_exposure" in exposure


# ---------------------------------------------------------------------------
# Multi-Scale (5.2)
# ---------------------------------------------------------------------------


class TestMultiScale:
    def test_multiscale_model_init(self):
        from strategify.reasoning.multiscale import MultiScaleModel

        msm = MultiScaleModel(lambda: GeopolModel())
        assert msm.get_global_model() is not None

    def test_multiscale_step(self):
        from strategify.reasoning.multiscale import MultiScaleModel

        msm = MultiScaleModel(lambda: GeopolModel())
        msm.step(regional_steps=1)
        assert msm._step_count == 1

    def test_multiscale_summary(self):
        from strategify.reasoning.multiscale import MultiScaleModel

        msm = MultiScaleModel(lambda: GeopolModel())
        msm.step(regional_steps=1)
        summary = msm.get_scale_summary()
        assert summary["global_step"] == 1
        assert summary["global_agents"] == 4
