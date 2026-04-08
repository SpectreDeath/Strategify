"""Forecasting: ARIMA-based projections on simulation time series.

Extends the VAR model capabilities with univariate ARIMA forecasting
and confidence interval estimation for each region.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def forecast_arima(
    series: pd.Series,
    steps: int = 5,
    order: tuple[int, int, int] = (1, 0, 0),
) -> dict:
    """Forecast a univariate time series using ARIMA.

    Parameters
    ----------
    series:
        Time series (e.g. escalation values for one region).
    steps:
        Number of steps to forecast.
    order:
        ARIMA (p, d, q) order.

    Returns
    -------
    dict
        ``forecast``, ``conf_int``, ``model_summary``, ``aic``.
    """
    from statsmodels.tsa.arima.model import ARIMA

    if len(series) < 5:
        return {
            "forecast": np.full(steps, series.mean() if len(series) > 0 else 0.0),
            "conf_int": None,
            "model_summary": "Insufficient data",
            "aic": None,
        }

    try:
        model = ARIMA(series, order=order)
        results = model.fit()
        forecast_result = results.get_forecast(steps=steps)
        forecast = forecast_result.predicted_mean.values
        conf_int = forecast_result.conf_int().values

        return {
            "forecast": forecast,
            "conf_int": conf_int,
            "model_summary": str(results.summary()),
            "aic": float(results.aic),
        }
    except Exception as exc:
        logger.warning("ARIMA forecast failed: %s", exc)
        return {
            "forecast": np.full(steps, series.mean()),
            "conf_int": None,
            "model_summary": f"Failed: {exc}",
            "aic": None,
        }


def forecast_all_regions(
    ts_df: pd.DataFrame,
    steps: int = 5,
    order: tuple[int, int, int] = (1, 0, 0),
) -> dict[str, dict]:
    """Forecast escalation for all regions.

    Parameters
    ----------
    ts_df:
        Wide DataFrame (steps x regions).
    steps:
        Number of steps to forecast.
    order:
        ARIMA (p, d, q) order.

    Returns
    -------
    dict
        ``{region_id: forecast_result}``
    """
    results = {}
    for region in ts_df.columns:
        results[region] = forecast_arima(ts_df[region], steps=steps, order=order)
    return results


def compute_forecast_confidence(
    forecast_results: dict[str, dict],
) -> dict[str, dict]:
    """Extract confidence intervals from forecast results.

    Returns
    -------
    dict
        ``{region_id: {"lower": list, "upper": list, "point": list}}``
    """
    out = {}
    for region, result in forecast_results.items():
        conf = result.get("conf_int")
        if conf is not None and len(conf) > 0:
            out[region] = {
                "lower": conf[:, 0].tolist(),
                "upper": conf[:, 1].tolist(),
                "point": result["forecast"].tolist(),
            }
        else:
            out[region] = {
                "lower": result["forecast"].tolist(),
                "upper": result["forecast"].tolist(),
                "point": result["forecast"].tolist(),
            }
    return out


def detect_forecast_escalation(
    forecast_results: dict[str, dict],
    threshold: float = 0.5,
) -> list[dict]:
    """Identify regions where forecasted escalation exceeds threshold.

    Parameters
    ----------
    forecast_results:
        From ``forecast_all_regions()``.
    threshold:
        Escalation threshold (0-1 scale).

    Returns
    -------
    list[dict]
        Alerts with ``region``, ``max_forecast``, ``step``.
    """
    alerts = []
    for region, result in forecast_results.items():
        forecast = result.get("forecast", np.array([]))
        if len(forecast) == 0:
            continue
        max_val = float(np.max(forecast))
        if max_val > threshold:
            max_step = int(np.argmax(forecast))
            alerts.append(
                {
                    "region": region,
                    "max_forecast": max_val,
                    "step": max_step,
                }
            )
    return sorted(alerts, key=lambda x: x["max_forecast"], reverse=True)
