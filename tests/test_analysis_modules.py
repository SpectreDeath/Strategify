"""Tests for analysis modules.

Tests calibration, war_game, and alliance_forecast modules.
"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from strategify.analysis.alliance_forecast import (
    AllianceStability,
    BayesianAllianceTracker,
    compute_alliance_strength,
    predict_fracture_probability,
)
from strategify.analysis.calibration import (
    calibrate_parameters,
    compute_calibration_error,
    create_sample_historical_data,
    load_historical_crisis,
    timeline_to_dataframe,
)
from strategify.analysis.war_game import (
    AdversaryScenario,
    AdversaryType,
    WarGameResult,
    predict_adversary_response,
    run_war_game,
)


class MockModel:
    """Mock model for testing."""

    def __init__(self, n_agents=4):
        self.schedule = MagicMock()
        self.n_agents = n_agents
        self.relations = MagicMock()


class TestCalibrationFunctions:
    """Tests for calibration functions."""

    def test_create_sample_historical_data(self):
        data = create_sample_historical_data()
        assert data["name"] == "cuban_missile_crisis"
        assert "actors" in data
        assert "escalation_timeline" in data
        assert len(data["escalation_timeline"]) > 0

    def test_load_historical_crisis_cuban(self):
        data = load_historical_crisis("cuban_missile_crisis")
        assert data["name"] == "cuban_missile_crisis"

    def test_load_historical_crisis_invalid(self):
        with pytest.raises(FileNotFoundError):
            load_historical_crisis("nonexistent_crisis")

    def test_timeline_to_dataframe(self):
        timeline = [
            {"step": 0, "us": 0, "ussr": 0},
            {"step": 1, "us": 1, "ussr": 0},
            {"step": 2, "us": 1, "ussr": 1},
        ]
        df = timeline_to_dataframe(timeline)
        assert isinstance(df, pd.DataFrame)
        assert "us" in df.columns
        assert "ussr" in df.columns
        assert len(df) == 3


class TestComputeCalibrationError:
    """Tests for calibration error computation."""

    def test_compute_error_matching_columns(self):
        sim_ts = pd.DataFrame({"RUS": [0, 1, 2], "UKR": [0, 0, 1]})
        hist_ts = pd.DataFrame({"RUS": [0, 1, 1.5], "UKR": [0, 0.5, 1]})
        error = compute_calibration_error(sim_ts, hist_ts)
        assert isinstance(error, float)
        assert error >= 0

    def test_compute_error_with_mapping(self):
        sim_ts = pd.DataFrame({"alpha": [0, 1], "beta": [0, 0]})
        hist_ts = pd.DataFrame({"RUS": [0, 1], "POL": [0, 0]})
        error = compute_calibration_error(sim_ts, hist_ts, {"alpha": "RUS"})
        assert isinstance(error, float)

    def test_compute_error_none_hist_data(self):
        sim_ts = pd.DataFrame({"alpha": [0, 1]})
        hist_ts = pd.DataFrame({"other": [0, 1]})
        error = compute_calibration_error(sim_ts, hist_ts, {"alpha": "unknown"})
        assert error == float("inf")


class TestCalibrateParameters:
    """Tests for parameter calibration."""

    def test_calibrate_parameters_returns_dict(self):
        def mock_factory(**kwargs):
            return MockModel()

        historical_data = create_sample_historical_data()
        param_ranges = {"escalation_threshold": (0.3, 0.8)}

        result = calibrate_parameters(
            mock_factory,
            historical_data,
            param_ranges,
            n_samples=5,
            n_steps=3,
        )

        assert isinstance(result, dict)


class TestAdversaryTypes:
    """Tests for AdversaryType enum."""

    def test_adversary_types_values(self):
        assert AdversaryType.RATIONAL.value == "rational"
        assert AdversaryType.AGGRESSIVE.value == "aggressive"
        assert AdversaryType.DEFENSIVE.value == "defensive"
        assert AdversaryType.OPPORTUNISTIC.value == "opportunistic"
        assert AdversaryType.FATALISTIC.value == "fatalistic"


class TestAdversaryScenario:
    """Tests for AdversaryScenario."""

    def test_scenario_init(self):
        scenario = AdversaryScenario(
            scenario_id="test_1",
            description="Test scenario",
            probability=0.5,
            outcome_score=0.7,
        )
        assert scenario.scenario_id == "test_1"
        assert scenario.description == "Test scenario"
        assert scenario.probability == 0.5


class TestWarGameResult:
    """Tests for WarGameResult."""

    def test_result_init(self):
        result = WarGameResult(
            scenario_id="test_scenario",
            expected_outcome=0.5,
            worst_case=0.2,
            best_case=0.8,
            recommended_response="deescalate",
            scenarios=[],
        )
        assert result.scenario_id == "test_scenario"
        assert result.expected_outcome == 0.5


class TestPredictAdversaryResponse:
    """Tests for predict_adversary_response function."""

    def test_predict_response_imports(self):

        assert callable(predict_adversary_response)


class TestRunWarGame:
    """Tests for run_war_game function."""

    def test_run_war_game_imports(self):

        assert callable(run_war_game)


class TestComputeAllianceStrength:
    """Tests for compute_alliance_strength function."""

    def test_compute_strength_imports(self):

        assert callable(compute_alliance_strength)


class TestPredictFractureProbability:
    """Tests for predict_fracture_probability function."""

    def test_predict_fracture_imports(self):

        assert callable(predict_fracture_probability)


class TestAllianceStability:
    """Tests for AllianceStability dataclass."""

    def test_stability_init(self):
        stability = AllianceStability(
            region_id="RUS",
            stability_score=0.7,
            fracture_probability=0.3,
            risk_factors=["economic_trouble"],
            recommendations=["strengthen_alliance"],
        )

        assert stability.region_id == "RUS"
        assert stability.stability_score == 0.7
        assert stability.fracture_probability == 0.3


class TestBayesianAllianceTracker:
    """Tests for BayesianAllianceTracker."""

    def test_tracker_init(self):
        tracker = BayesianAllianceTracker()
        assert tracker.prior_alpha == 1.0
        assert tracker.prior_beta == 1.0

    def test_tracker_update(self):
        tracker = BayesianAllianceTracker()
        tracker.update(fracture_observed=False)
        assert tracker.posterior_alpha == 1.0
        assert tracker.posterior_beta == 2.0

    def test_tracker_get_probability(self):
        tracker = BayesianAllianceTracker()
        prob = tracker.get_probability()
        assert isinstance(prob, float)
        assert 0 <= prob <= 1
