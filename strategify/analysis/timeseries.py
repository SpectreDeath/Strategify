"""Time series analysis of simulation outputs using statsmodels.

Provides VAR models, Granger causality tests, and trend analysis
for multi-agent simulation output DataFrames.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import InfeasibleTestError
from statsmodels.tsa.api import VAR
from statsmodels.tsa.stattools import grangercausalitytests


def prepare_agent_timeseries(df: pd.DataFrame) -> pd.DataFrame:
    """Convert Mesa DataCollector agent DataFrame to a wide time series.

    Parameters
    ----------
    df:
        DataFrame from model.datacollector.get_agent_vars_dataframe()
        with MultiIndex (Step, AgentID) and columns [posture, region_id].

    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame: rows=steps, columns=region_id, values=escalation (0/1).
    """
    df_reset = df.reset_index()
    df_reset["escalation"] = (df_reset["posture"] == "Escalate").astype(float)
    pivot = df_reset.pivot_table(index="Step", columns="region_id", values="escalation", aggfunc="first")
    return pivot.fillna(0.0)


def fit_var_model(ts_df: pd.DataFrame, maxlags: int = 3) -> dict:
    """Fit a Vector Autoregression model to multi-region time series.

    Parameters
    ----------
    ts_df:
        Wide-format DataFrame (steps x regions).
    maxlags:
        Maximum number of lags to consider.

    Returns
    -------
    dict
        {"model_summary": str, "optimal_lags": int, "forecast": np.ndarray}
    """
    if ts_df.shape[0] < maxlags + 2:
        return {
            "model_summary": "Insufficient data",
            "optimal_lags": 0,
            "forecast": np.array([]),
        }

    # Remove columns with zero variance (breaks VAR)
    ts_df = ts_df.loc[:, ts_df.std() > 1e-10]
    if ts_df.shape[1] < 2:
        return {
            "model_summary": "Insufficient variance",
            "optimal_lags": 0,
            "forecast": np.array([]),
        }

    model = VAR(ts_df)
    try:
        results = model.fit(maxlags=maxlags, ic="aic")
        forecast = results.forecast(ts_df.values[-results.k_ar :], steps=3)
    except (np.linalg.LinAlgError, ValueError):
        return {
            "model_summary": "VAR fitting failed",
            "optimal_lags": 0,
            "forecast": np.array([]),
        }

    return {
        "model_summary": str(results.summary()),
        "optimal_lags": results.k_ar,
        "forecast": forecast,
        "regions": list(ts_df.columns),
    }


def granger_causality_test(
    ts_df: pd.DataFrame,
    cause: str,
    effect: str,
    maxlag: int = 3,
) -> dict:
    """Test whether changes in 'cause' region Granger-cause changes in 'effect'.

    Parameters
    ----------
    ts_df:
        Wide-format DataFrame (steps x regions).
    cause:
        Region ID of the potential cause.
    effect:
        Region ID of the potential effect.
    maxlag:
        Maximum lag for the test.

    Returns
    -------
    dict
        {"causes": bool, "p_value": float, "test_stat": float}
    """
    if cause not in ts_df.columns or effect not in ts_df.columns:
        return {"causes": False, "p_value": 1.0, "test_stat": 0.0}

    data = ts_df[[effect, cause]].dropna()
    if len(data) < maxlag + 2:
        return {"causes": False, "p_value": 1.0, "test_stat": 0.0}

    try:
        result = grangercausalitytests(data, maxlag=maxlag, verbose=False)
        # Use the first lag result for the test
        p_value = result[1][0]["ssr_ftest"][1]
        test_stat = result[1][0]["ssr_ftest"][0]
        return {
            "causes": p_value < 0.05,
            "p_value": p_value,
            "test_stat": test_stat,
        }
    except (ValueError, KeyError, IndexError, InfeasibleTestError):
        return {"causes": False, "p_value": 1.0, "test_stat": 0.0}


def pairwise_granger_causality(ts_df: pd.DataFrame, maxlag: int = 3) -> dict:
    """Run Granger causality tests for all region pairs.

    Returns a dict of {(cause, effect): test_result}.
    """
    results = {}
    regions = list(ts_df.columns)
    for cause in regions:
        for effect in regions:
            if cause != effect:
                results[(cause, effect)] = granger_causality_test(ts_df, cause, effect, maxlag)
    return results
