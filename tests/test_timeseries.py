import pandas as pd
import pytest

from strategify.analysis.timeseries import (
    fit_var_model,
    granger_causality_test,
    pairwise_granger_causality,
    prepare_agent_timeseries,
)
from strategify.sim.model import GeopolModel


@pytest.fixture
def ts_data():
    model = GeopolModel()
    for _ in range(30):
        model.step()
    df = model.datacollector.get_agent_vars_dataframe()
    return prepare_agent_timeseries(df)


def test_prepare_agent_timeseries(ts_data):
    assert isinstance(ts_data, pd.DataFrame)
    assert ts_data.shape[0] == 30  # 30 steps
    assert ts_data.shape[1] == 4  # 4 regions
    assert set(ts_data.columns) == {"alpha", "bravo", "charlie", "delta"}


def test_fit_var_model(ts_data):
    result = fit_var_model(ts_data, maxlags=2)
    assert "optimal_lags" in result
    assert "forecast" in result
    assert result["optimal_lags"] >= 0
    assert "model_summary" in result


def test_granger_causality_test(ts_data):
    result = granger_causality_test(ts_data, "alpha", "bravo", maxlag=2)
    assert "causes" in result
    assert "p_value" in result
    assert "test_stat" in result
    assert isinstance(result["causes"], bool)


def test_granger_causality_missing_column(ts_data):
    result = granger_causality_test(ts_data, "alpha", "nonexistent")
    assert result["causes"] is False
    assert result["p_value"] == 1.0


def test_pairwise_granger_causality(ts_data):
    results = pairwise_granger_causality(ts_data, maxlag=2)
    # Should have 4*3=12 pairs
    assert len(results) == 12
    for (cause, effect), result in results.items():
        assert cause != effect
        assert "causes" in result
