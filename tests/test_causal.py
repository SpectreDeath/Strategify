import pandas as pd
import pytest

from strategify.analysis.causal import (
    build_causal_data,
    estimate_escalation_effect,
    pairwise_causal_effects,
)
from strategify.sim.model import GeopolModel


@pytest.fixture
def causal_df():
    model = GeopolModel()
    return build_causal_data(model, n_steps=20)


def test_build_causal_data(causal_df):
    assert isinstance(causal_df, pd.DataFrame)
    assert "military" in causal_df.columns
    assert "escalation" in causal_df.columns
    assert "region_id" in causal_df.columns
    assert len(causal_df) == 20 * 4  # 20 steps * 4 agents


def test_estimate_escalation_effect(causal_df):
    result = estimate_escalation_effect(causal_df, "alpha", "bravo")
    assert "effect" in result
    assert "method" in result
    assert "significant" in result
    assert isinstance(result["effect"], float)


def test_estimate_effect_missing_region(causal_df):
    result = estimate_escalation_effect(causal_df, "nonexistent", "bravo")
    assert result["effect"] == 0.0


def test_pairwise_causal_effects(causal_df):
    results = pairwise_causal_effects(causal_df)
    # 4 regions * 3 others = 12 pairs
    assert len(results) == 12
    for (treat, outcome), result in results.items():
        assert treat != outcome
        assert "effect" in result
