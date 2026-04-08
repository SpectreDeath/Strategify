"""Causal inference on simulation outcomes using OLS regression.

Estimate causal effects of geopolitical interventions (alliance changes,
resource shifts) on simulation outcomes using backdoor adjustment via OLS.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def build_causal_data(model, n_steps: int = 30) -> pd.DataFrame:
    """Run simulation and collect data for causal analysis.

    Parameters
    ----------
    model:
        A GeopolModel instance.
    n_steps:
        Number of steps to simulate.

    Returns
    -------
    pd.DataFrame
        Rows per step per agent with columns for treatment/outcome variables.
    """
    records = []
    for step in range(n_steps):
        # Record state before step
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            records.append(
                {
                    "step": step,
                    "region_id": rid,
                    "military": agent.capabilities.get("military", 0.5),
                    "economic": agent.capabilities.get("economic", 0.5),
                    "escalation": 1.0 if agent.posture == "Escalate" else 0.0,
                }
            )
        model.step()

    return pd.DataFrame(records)


def estimate_escalation_effect(
    df: pd.DataFrame,
    treatment_region: str,
    outcome_region: str,
) -> dict:
    """Estimate the causal effect of a region's military on another's escalation.

    Uses a simple backdoor adjustment: regress outcome on treatment,
    controlling for confounders.

    Parameters
    ----------
    df:
        Causal data from build_causal_data().
    treatment_region:
        Region whose military strength is the treatment.
    outcome_region:
        Region whose escalation is the outcome.

    Returns
    -------
    dict
        {"effect": float, "method": str, "significant": bool}
    """
    import statsmodels.api as sm

    treatment_data = df[df["region_id"] == treatment_region]["military"].values
    outcome_data = df[df["region_id"] == outcome_region]["escalation"].values

    min_len = min(len(treatment_data), len(outcome_data))
    treatment_data = treatment_data[:min_len]
    outcome_data = outcome_data[:min_len]

    if min_len < 5:
        return {"effect": 0.0, "method": "insufficient_data", "significant": False}

    # Simple OLS: outcome ~ treatment
    X = sm.add_constant(treatment_data)

    # Check for degenerate case (no variance in treatment)
    if np.std(treatment_data) < 1e-10:
        return {"effect": 0.0, "method": "no_variance", "significant": False}

    model = sm.OLS(outcome_data, X).fit()

    if len(model.params) < 2:
        return {"effect": 0.0, "method": "insufficient_params", "significant": False}

    return {
        "effect": model.params[1],
        "std_error": model.bse[1],
        "p_value": model.pvalues[1],
        "r_squared": model.rsquared,
        "method": "OLS_backdoor_adjustment",
        "significant": model.pvalues[1] < 0.05,
    }


def pairwise_causal_effects(df: pd.DataFrame) -> dict:
    """Estimate causal effects between all region pairs.

    Returns dict of {(treatment_region, outcome_region): result}.
    """
    regions = df["region_id"].unique().tolist()
    results = {}
    for treat in regions:
        for outcome in regions:
            if treat != outcome:
                results[(treat, outcome)] = estimate_escalation_effect(df, treat, outcome)
    return results
