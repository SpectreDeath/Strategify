"""Tests for remaining analysis modules.

Tests alerts, forecasting, counterfactual, and comparison modules.
"""

from unittest.mock import MagicMock

import pandas as pd

from strategify.analysis.alerts import (
    AlertLevel,
    detect_contagion_spread,
    detect_escalation_spikes,
    detect_trend_reversals,
    run_early_warning,
)
from strategify.analysis.comparison import (
    collect_trajectories,
    compare_trajectories,
    extract_trajectory,
    trajectory_to_dataframe,
)
from strategify.analysis.counterfactual import (
    apply_intervention,
    compare_counterfactual,
    run_baseline,
    run_counterfactual,
)
from strategify.analysis.forecasting import (
    compute_forecast_confidence,
    detect_forecast_escalation,
    forecast_all_regions,
    forecast_arima,
)


class MockModel:
    """Mock model for testing."""

    def __init__(self, n_agents=4):
        self.schedule = MagicMock()
        self.n_agents = n_agents


class TestAlertLevel:
    """Tests for AlertLevel enum."""

    def test_alert_level_values(self):
        assert hasattr(AlertLevel, "NONE")
        assert hasattr(AlertLevel, "WATCH")
        assert hasattr(AlertLevel, "WARNING")
        assert hasattr(AlertLevel, "CRITICAL")


class TestDetectEscalationSpikes:
    """Tests for detect_escalation_spikes function."""

    def test_detect_spikes_returns_list(self):
        df = pd.DataFrame(
            {
                "RUS": [0, 1, 2, 3, 4],
                "UKR": [0, 0, 1, 2, 3],
            }
        )
        alerts = detect_escalation_spikes(df, threshold=1.5, window=2)
        assert isinstance(alerts, list)

    def test_detect_spikes_short_series(self):
        df = pd.DataFrame({"RUS": [0, 1]})
        alerts = detect_escalation_spikes(df)
        assert alerts == []


class TestDetectTrendReversals:
    """Tests for detect_trend_reversals function."""

    def test_detect_reversals_returns_list(self):
        df = pd.DataFrame({"RUS": [0, 1, 2, 1, 0]})
        reversals = detect_trend_reversals(df)
        assert isinstance(reversals, list)


class TestDetectContagionSpread:
    """Tests for detect_contagion_spread function."""

    def test_detect_contagion_imports(self):

        assert callable(detect_contagion_spread)


class TestRunEarlyWarning:
    """Tests for run_early_warning function."""

    def test_early_warning_imports(self):

        assert callable(run_early_warning)


class TestForecastArima:
    """Tests for forecast_arima function."""

    def test_forecast_arima_returns_dict(self):
        series = pd.Series([0, 1, 2, 3, 4])
        result = forecast_arima(series, steps=3)
        assert isinstance(result, dict)


class TestForecastAllRegions:
    """Tests for forecast_all_regions function."""

    def test_forecast_all_returns_dict(self):
        df = pd.DataFrame(
            {
                "RUS": [0, 1, 2, 3],
                "UKR": [0, 0, 1, 2],
            }
        )
        result = forecast_all_regions(df, steps=3)
        assert isinstance(result, dict)


class TestComputeForecastConfidence:
    """Tests for compute_forecast_confidence function."""

    def test_confidence_imports(self):

        assert callable(compute_forecast_confidence)


class TestDetectForecastEscalation:
    """Tests for detect_forecast_escalation function."""

    def test_detect_returns_list(self):
        df = pd.DataFrame({"RUS": [0, 1, 2, 3]})
        result = detect_forecast_escalation(df, threshold=2.5)
        assert isinstance(result, list)


class TestRunBaseline:
    """Tests for run_baseline function."""

    def test_baseline_imports(self):

        assert callable(run_baseline)


class TestApplyIntervention:
    """Tests for apply_intervention function."""

    def test_intervention_imports(self):

        assert callable(apply_intervention)


class TestRunCounterfactual:
    """Tests for run_counterfactual function."""

    def test_counterfactual_imports(self):

        assert callable(run_counterfactual)


class TestCompareCounterfactual:
    """Tests for compare_counterfactual function."""

    def test_compare_imports(self):

        assert callable(compare_counterfactual)


class TestExtractTrajectory:
    """Tests for extract_trajectory function."""

    def test_extract_imports(self):

        assert callable(extract_trajectory)


class TestCollectTrajectories:
    """Tests for collect_trajectories function."""

    def test_collect_imports(self):

        assert callable(collect_trajectories)


class TestCompareTrajectories:
    """Tests for compare_trajectories function."""

    def test_compare_imports(self):

        assert callable(compare_trajectories)


class TestTrajectoryToDataFrame:
    """Tests for trajectory_to_dataframe function."""

    def test_to_dataframe_imports(self):

        assert callable(trajectory_to_dataframe)
