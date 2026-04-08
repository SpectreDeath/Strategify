import numpy as np
import pytest

from strategify.analysis.alliance_forecast import BayesianAllianceTracker
from strategify.analysis.strategic_risk import AdaptiveWeightLearner, get_adaptive_learner
from strategify.analysis.war_game import AdversaryType, predict_adversary_response
from strategify.game_theory.normal_form import NormalFormGame


class TestNormalFormGame:
    def test_creates_game(self):
        A = [[-2, 5], [1, 3]]
        B = [[-2, 1], [5, 3]]
        game = NormalFormGame(A, B)
        assert game.A.shape == (2, 2)
        assert game.B.shape == (2, 2)

    def test_payoff_matrices_are_numpy(self):
        game = NormalFormGame([[-2, 5], [1, 3]], [[-2, 1], [5, 3]])
        assert isinstance(game.A, np.ndarray)
        assert isinstance(game.B, np.ndarray)

    def test_nash_equilibria_exist(self):
        game = NormalFormGame([[-2, 5], [1, 3]], [[-2, 1], [5, 3]])
        eq = game.get_nash_equilibria()
        assert len(eq) > 0

    def test_select_equilibrium_deterministic(self):
        game = NormalFormGame([[-2, 5], [1, 3]], [[-2, 1], [5, 3]])
        eq1 = game.select_equilibrium()
        eq2 = game.select_equilibrium()
        np.testing.assert_array_equal(eq1[0], eq2[0])
        np.testing.assert_array_equal(eq1[1], eq2[1])

    def test_select_equilibrium_returns_pair(self):
        game = NormalFormGame([[-2, 5], [1, 3]], [[-2, 1], [5, 3]])
        sigma_row, sigma_col = game.select_equilibrium()
        assert len(sigma_row) == 2
        assert len(sigma_col) == 2

    def test_sample_action_returns_valid_action(self):
        strategy = np.array([0.5, 0.5])
        actions = ["Escalate", "Deescalate"]
        for _ in range(100):
            result = NormalFormGame.sample_action(strategy, actions)
            assert result in actions

    def test_sample_action_biased_toward_high_weight(self):
        strategy = np.array([1.0, 0.0])
        actions = ["Escalate", "Deescalate"]
        for _ in range(50):
            result = NormalFormGame.sample_action(strategy, actions)
            assert result == "Escalate"

    def test_uniform_fallback_when_no_equilibria(self):
        game = NormalFormGame([[0]], [[0]])
        sigma_row, sigma_col = game.select_equilibrium()
        np.testing.assert_array_almost_equal(sigma_row, [1.0])
        np.testing.assert_array_almost_equal(sigma_col, [1.0])

    def test_strategy_sums_to_one(self):
        game = NormalFormGame([[-2, 5], [1, 3]], [[-2, 1], [5, 3]])
        sigma_row, sigma_col = game.select_equilibrium()
        assert pytest.approx(sum(sigma_row), abs=1e-7) == 1.0
        assert pytest.approx(sum(sigma_col), abs=1e-7) == 1.0


class TestAdaptiveWeightLearner:
    def test_singleton_instance(self):
        AdaptiveWeightLearner.reset_instance()
        learner1 = get_adaptive_learner()
        learner2 = get_adaptive_learner()
        assert learner1 is learner2

    def test_initial_weights(self):
        AdaptiveWeightLearner.reset_instance()
        learner = get_adaptive_learner()
        weights = learner.get_weights()
        assert "posture" in weights
        assert "military" in weights
        assert pytest.approx(sum(weights.values()), abs=1e-6) == 1.0

    def test_update_adjusts_weights(self):
        AdaptiveWeightLearner.reset_instance()
        learner = get_adaptive_learner()
        initial = learner.get_weights().copy()

        for i in range(20):
            factors = [0.8, 0.6, 0.4, 0.2, 0.1]
            actual = 0.7
            predicted = 0.5 + i * 0.01
            learner.update(factors, actual, predicted)

        final = learner.get_weights()
        assert final != initial

    def test_weights_sum_to_one(self):
        AdaptiveWeightLearner.reset_instance()
        learner = get_adaptive_learner()
        for _ in range(50):
            factors = [0.5] * 5
            learner.update(factors, 0.5, 0.5)
        weights = learner.get_weights()
        assert pytest.approx(sum(weights.values()), abs=1e-6) == 1.0


class TestBayesianAllianceTracker:
    def test_initial_probability(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        assert tracker.get_probability() == 0.5

    def test_initial_uncertainty(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        assert tracker.get_uncertainty() == 1.0

    def test_mode_at_initial(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        assert tracker.get_mode() == 0.5

    def test_uncertainty_decreases_with_evidence(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        initial_uncertainty = tracker.get_uncertainty()

        for _ in range(20):
            tracker.update(True, 1)
        for _ in range(80):
            tracker.update(False, 1)

        final_uncertainty = tracker.get_uncertainty()
        assert final_uncertainty < initial_uncertainty

    def test_update_true_increases_alpha(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        tracker.update(True, 1)
        assert tracker.posterior_alpha == 2.0

    def test_update_false_increases_beta(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        tracker.update(False, 1)
        assert tracker.posterior_beta == 2.0

    def test_confidence_interval_in_range(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        for _ in range(50):
            tracker.update(False, 1)
        ci_low, ci_high = tracker.get_confidence_interval(0.95)
        assert 0.0 <= ci_low <= ci_high <= 1.0

    def test_reset(self):
        tracker = BayesianAllianceTracker(1.0, 1.0)
        for _ in range(10):
            tracker.update(True, 1)
        tracker.reset()
        assert tracker.posterior_alpha == 1.0
        assert tracker.posterior_beta == 1.0


class TestPredictAdversaryResponse:
    def test_predict_adversary_response_signature(self):
        import inspect

        sig = inspect.signature(predict_adversary_response)
        params = list(sig.parameters.keys())
        assert "model" in params
        assert "actor_id" in params
        assert "my_action" in params
        assert "adversary_type" in params
        assert "deterministic" in params
        assert "escalate_prob" in params

    def test_deterministic_fatalistic_high_prob(self):
        result = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.9,
        )
        assert result == "Escalate"

    def test_deterministic_fatalistic_low_prob(self):
        result = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.1,
        )
        assert result == "Deescalate"

    def test_deterministic_fatalistic_equal_prob(self):
        result = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.5,
        )
        assert result == "Escalate"

    def test_deterministic_fatalistic(self):
        result1 = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.7,
        )
        result2 = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.7,
        )
        assert result1 == result2

    def test_deterministic_high_prob(self):
        result = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.9,
        )
        assert result == "Escalate"

    def test_deterministic_low_prob(self):
        result = predict_adversary_response(
            None,
            "test",
            "Deescalate",
            AdversaryType.FATALISTIC,
            deterministic=True,
            escalate_prob=0.1,
        )
        assert result == "Deescalate"
