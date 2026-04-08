"""Tests for Phase 3: OSINT sources, comparison, alerts, calibration,
forecasting, counterfactuals, and reports."""

import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


@pytest.fixture
def stepped_model():
    m = GeopolModel()
    for _ in range(10):
        m.step()
    return m


# ---------------------------------------------------------------------------
# OSINT Sources (3.1)
# ---------------------------------------------------------------------------


class TestOSSources:
    def test_events_to_texts(self):
        from strategify.osint.sources import events_to_texts

        events = [
            {"title": "Crisis in region", "url": "http://example.com"},
            {"title": "Peace talks", "url": "http://example2.com"},
        ]
        texts = events_to_texts(events)
        assert texts == ["Crisis in region", "Peace talks"]

    def test_events_to_texts_empty(self):
        from strategify.osint.sources import events_to_texts

        assert events_to_texts([]) == []

    def test_compute_event_features_empty(self):
        from strategify.osint.sources import compute_event_features

        features = compute_event_features([])
        assert features["event_count"] == 0.0

    def test_compute_event_features(self):
        from strategify.osint.sources import compute_event_features

        events = [
            {"domain": "bbc.com", "seendate": "20260328T120000"},
            {"domain": "reuters.com", "seendate": "20260328T130000"},
        ]
        features = compute_event_features(events)
        assert features["event_count"] == 2.0
        assert features["unique_domains"] == 2.0

    def test_fetch_rss_feed_bad_url(self):
        from strategify.osint.sources import fetch_rss_feed

        result = fetch_rss_feed("http://invalid.example.com/feed.xml")
        assert result == []

    def test_fetch_gdelt_events_bad_query(self):
        from strategify.osint.sources import fetch_gdelt_events

        result = fetch_gdelt_events("", timespan="24h")
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Scenario Comparison (3.2)
# ---------------------------------------------------------------------------


class TestComparison:
    def test_extract_trajectory(self, model):
        from strategify.analysis.comparison import extract_trajectory

        model.step()
        t = extract_trajectory(model)
        assert "postures" in t
        assert "resources" in t
        assert "diplomacy_weights" in t
        assert len(t["postures"]) == 4

    def test_collect_trajectories(self, model):
        from strategify.analysis.comparison import collect_trajectories

        trajectories = collect_trajectories(model, n_steps=5)
        assert len(trajectories) == 5
        assert all("step" in t for t in trajectories)

    def test_compare_trajectories(self, model):
        from strategify.analysis.comparison import collect_trajectories, compare_trajectories

        t_a = collect_trajectories(GeopolModel(), n_steps=5)
        t_b = collect_trajectories(GeopolModel(), n_steps=5)
        comp = compare_trajectories(t_a, t_b)
        assert "escalation_divergence" in comp
        assert comp["escalation_divergence"] == 0.0  # deterministic

    def test_trajectory_to_dataframe(self, model):
        from strategify.analysis.comparison import collect_trajectories, trajectory_to_dataframe

        trajectories = collect_trajectories(model, n_steps=3)
        df = trajectory_to_dataframe(trajectories)
        assert len(df) == 3
        assert "step" in df.columns

    def test_multi_scenario_comparison(self, model):
        from strategify.analysis.comparison import (
            collect_trajectories,
            multi_scenario_comparison,
        )

        t_a = collect_trajectories(GeopolModel(), n_steps=3)
        t_b = collect_trajectories(GeopolModel(), n_steps=3)
        result = multi_scenario_comparison({"a": t_a, "b": t_b})
        assert ("a", "b") in result


# ---------------------------------------------------------------------------
# Early Warning (3.3)
# ---------------------------------------------------------------------------


class TestAlerts:
    def _make_ts(self):
        data = {
            "alpha": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0],
            "bravo": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        }
        return pd.DataFrame(data)

    def test_detect_escalation_spikes(self):
        from strategify.analysis.alerts import detect_escalation_spikes

        ts = self._make_ts()
        spikes = detect_escalation_spikes(ts, threshold=1.5, window=3)
        assert isinstance(spikes, list)

    def test_detect_trend_reversals(self):
        from strategify.analysis.alerts import detect_trend_reversals

        ts = self._make_ts()
        reversals = detect_trend_reversals(ts, window=3)
        assert isinstance(reversals, list)

    def test_detect_contagion_spread(self):
        from strategify.analysis.alerts import detect_contagion_spread

        data = {"alpha": [1.0, 1.0], "bravo": [1.0, 1.0], "charlie": [0.0, 0.0]}
        ts = pd.DataFrame(data)
        alerts = detect_contagion_spread(ts, step=1, threshold=2)
        assert len(alerts) == 1
        assert alerts[0]["count"] == 2

    def test_run_early_warning(self):
        from strategify.analysis.alerts import AlertLevel, run_early_warning

        ts = self._make_ts()
        report = run_early_warning(ts, current_step=3)
        assert report["overall_level"] in (
            AlertLevel.NONE,
            AlertLevel.WATCH,
            AlertLevel.WARNING,
            AlertLevel.CRITICAL,
        )
        assert "alert_count" in report


# ---------------------------------------------------------------------------
# Historical Calibration (3.4)
# ---------------------------------------------------------------------------


class TestCalibration:
    def test_create_sample_historical_data(self):
        from strategify.analysis.calibration import create_sample_historical_data

        data = create_sample_historical_data()
        assert data["name"] == "cuban_missile_crisis"
        assert "escalation_timeline" in data
        assert len(data["escalation_timeline"]) == 8

    def test_load_historical_crisis(self):
        from strategify.analysis.calibration import load_historical_crisis

        data = load_historical_crisis("cuban_missile_crisis")
        assert data["name"] == "cuban_missile_crisis"

    def test_load_historical_crisis_not_found(self):
        from strategify.analysis.calibration import load_historical_crisis

        with pytest.raises(FileNotFoundError):
            load_historical_crisis("nonexistent")

    def test_timeline_to_dataframe(self):
        from strategify.analysis.calibration import (
            create_sample_historical_data,
            timeline_to_dataframe,
        )

        data = create_sample_historical_data()
        df = timeline_to_dataframe(data["escalation_timeline"])
        assert len(df) == 8
        assert "us" in df.columns

    def test_compute_calibration_error(self):
        from strategify.analysis.calibration import compute_calibration_error

        sim = pd.DataFrame({"a": [0.0, 1.0, 1.0], "b": [0.0, 0.0, 0.0]})
        hist = pd.DataFrame({"a": [0.0, 0.5, 1.0], "b": [0.0, 0.0, 0.0]})
        error = compute_calibration_error(sim, hist)
        assert error > 0


# ---------------------------------------------------------------------------
# Forecasting (3.5)
# ---------------------------------------------------------------------------


class TestForecasting:
    def test_forecast_arima(self):
        from strategify.analysis.forecasting import forecast_arima

        series = pd.Series([0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        result = forecast_arima(series, steps=3)
        assert len(result["forecast"]) == 3

    def test_forecast_arima_insufficient_data(self):
        from strategify.analysis.forecasting import forecast_arima

        series = pd.Series([0.0, 1.0])
        result = forecast_arima(series, steps=3)
        assert result["model_summary"] == "Insufficient data"

    def test_forecast_all_regions(self):
        from strategify.analysis.forecasting import forecast_all_regions

        ts = pd.DataFrame({"a": [0.0] * 8, "b": [0.0] * 8})
        results = forecast_all_regions(ts, steps=3)
        assert "a" in results
        assert "b" in results

    def test_detect_forecast_escalation(self):
        from strategify.analysis.forecasting import detect_forecast_escalation

        results = {
            "a": {"forecast": np.array([0.1, 0.8, 0.9])},
            "b": {"forecast": np.array([0.0, 0.1, 0.2])},
        }
        alerts = detect_forecast_escalation(results, threshold=0.5)
        assert len(alerts) == 1
        assert alerts[0]["region"] == "a"


# ---------------------------------------------------------------------------
# Counterfactual (3.6)
# ---------------------------------------------------------------------------


class TestCounterfactual:
    def test_run_baseline(self):
        from strategify.analysis.counterfactual import run_baseline

        result = run_baseline(lambda: GeopolModel(), n_steps=3)
        assert "trajectories" in result
        assert len(result["trajectories"]) == 3

    def test_run_counterfactual(self):
        from strategify.analysis.counterfactual import run_counterfactual

        interventions = [{"type": "set_posture", "region": "alpha", "posture": "Deescalate"}]
        result = run_counterfactual(lambda: GeopolModel(), 1, interventions, n_steps=3)
        assert result["intervention_step"] == 1
        assert len(result["trajectories"]) == 3

    def test_compare_counterfactual(self):
        from strategify.analysis.counterfactual import (
            compare_counterfactual,
            run_baseline,
            run_counterfactual,
        )

        baseline = run_baseline(lambda: GeopolModel(), n_steps=3)
        cf = run_counterfactual(lambda: GeopolModel(), 1, [], n_steps=3)
        comp = compare_counterfactual(baseline, cf)
        assert "escalation_diff" in comp

    def test_systematic_counterfactuals(self):
        from strategify.analysis.counterfactual import systematic_counterfactuals

        configs = [
            [{"type": "set_posture", "region": "alpha", "posture": "Escalate"}],
            [{"type": "set_resource", "region": "alpha", "value": 3.0}],
        ]
        results = systematic_counterfactuals(lambda: GeopolModel(), 1, configs, n_steps=3)
        assert len(results) == 2
        assert all("comparison" in r for r in results)


# ---------------------------------------------------------------------------
# Report Generation (3.7)
# ---------------------------------------------------------------------------


class TestReports:
    def test_generate_report(self, stepped_model):
        from strategify.viz.reports import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_report(stepped_model, Path(tmpdir) / "report.html")
            assert path.exists()
            content = path.read_text()
            assert "Actor Status" in content
            assert "Diplomatic Relations" in content

    def test_generate_report_includes_economics(self, stepped_model):
        from strategify.viz.reports import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_report(stepped_model, Path(tmpdir) / "report.html")
            content = path.read_text()
            assert "Economic Overview" in content

    def test_generate_report_includes_escalation(self, stepped_model):
        from strategify.viz.reports import generate_report

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_report(stepped_model, Path(tmpdir) / "report.html")
            content = path.read_text()
            assert "Escalation Ladder" in content
