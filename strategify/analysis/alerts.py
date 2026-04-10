"""Early warning system: anomaly detection on escalation trajectories.

Detects sudden escalation spikes, regime changes, and trend reversals
that may signal impending crisis.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class AlertLevel:
    """Alert severity levels."""

    NONE = "none"
    WATCH = "watch"
    WARNING = "warning"
    CRITICAL = "critical"


def detect_escalation_spikes(
    ts_df: pd.DataFrame,
    threshold: float = 2.0,
    window: int = 3,
) -> list[dict[str, Any]]:
    """Detect sudden spikes in escalation levels.

    Uses z-score against a rolling window to identify anomalous jumps.

    Parameters
    ----------
    ts_df:
        Wide DataFrame (steps x regions) with escalation values.
    threshold:
        Z-score threshold for spike detection.
    window:
        Rolling window size for mean/std calculation.

    Returns
    -------
    list[dict]
        Alerts with ``step``, ``region``, ``value``, ``z_score``, ``level``.
    """
    alerts = []
    if ts_df.shape[0] < window + 1:
        return alerts

    for region in ts_df.columns:
        series = ts_df[region].values
        for i in range(window, len(series)):
            window_vals = series[i - window : i]
            mean = np.mean(window_vals)
            std = np.std(window_vals)
            if std < 1e-10:
                continue
            z = (series[i] - mean) / std
            if z > threshold:
                level = (
                    AlertLevel.CRITICAL
                    if z > threshold * 2
                    else AlertLevel.WARNING
                    if z > threshold * 1.5
                    else AlertLevel.WATCH
                )
                alerts.append(
                    {
                        "step": i,
                        "region": region,
                        "value": float(series[i]),
                        "z_score": float(z),
                        "level": level,
                        "type": "escalation_spike",
                    }
                )
    return alerts


def detect_trend_reversals(
    ts_df: pd.DataFrame,
    window: int = 5,
) -> list[dict[str, Any]]:
    """Detect trend reversals (sustained escalation suddenly dropping or vice versa).

    Parameters
    ----------
    ts_df:
        Wide DataFrame (steps x regions).
    window:
        Minimum consecutive steps to establish a trend.

    Returns
    -------
    list[dict]
        Alerts with ``step``, ``region``, ``direction``, ``level``.
    """
    alerts = []
    if ts_df.shape[0] < window * 2:
        return alerts

    for region in ts_df.columns:
        series = ts_df[region].values
        for i in range(window, len(series)):
            # Check if previous window was a consistent trend
            prev = series[i - window : i]
            curr = series[i]

            prev_trend = np.mean(np.diff(prev)) if len(prev) > 1 else 0.0

            # Detect reversal: was trending up, now dropping
            if prev_trend > 0.05 and curr < prev[-1] - 0.3:
                alerts.append(
                    {
                        "step": i,
                        "region": region,
                        "direction": "deescalation_after_escalation",
                        "level": AlertLevel.WATCH,
                        "type": "trend_reversal",
                    }
                )
            # Detect escalation spike after calm: was trending down, now jumping
            elif prev_trend < -0.05 and curr > prev[-1] + 0.3:
                alerts.append(
                    {
                        "step": i,
                        "region": region,
                        "direction": "escalation_after_deescalation",
                        "level": AlertLevel.WARNING,
                        "type": "trend_reversal",
                    }
                )
    return alerts


def detect_contagion_spread(
    ts_df: pd.DataFrame,
    step: int,
    threshold: int = 2,
) -> list[dict[str, Any]]:
    """Detect when escalation spreads to multiple regions simultaneously.

    Parameters
    ----------
    ts_df:
        Wide DataFrame (steps x regions).
    step:
        Current step to check.
    threshold:
        Minimum number of escalating regions to trigger alert.

    Returns
    -------
    list[dict]
        Alerts if contagion threshold is met.
    """
    if step >= len(ts_df):
        return []

    row = ts_df.iloc[step]
    escalating = [col for col in ts_df.columns if row.get(col, 0) > 0.5]

    if len(escalating) >= threshold:
        return [
            {
                "step": step,
                "regions": escalating,
                "count": len(escalating),
                "level": (AlertLevel.CRITICAL if len(escalating) >= len(ts_df.columns) - 1 else AlertLevel.WARNING),
                "type": "contagion_spread",
            }
        ]
    return []


def run_early_warning(
    ts_df: pd.DataFrame,
    current_step: int | None = None,
    spike_threshold: float = 2.0,
    spike_window: int = 3,
    trend_window: int = 5,
    contagion_threshold: int = 2,
) -> dict[str, Any]:
    """Run all early warning checks and return a consolidated report.

    Parameters
    ----------
    ts_df:
        Wide DataFrame (steps x regions) with escalation values.
    current_step:
        If provided, also run contagion check at this step.

    Returns
    -------
    dict
        ``spikes``, ``reversals``, ``contagion``, ``overall_level``, ``alert_count``.
    """
    spikes = detect_escalation_spikes(ts_df, spike_threshold, spike_window)
    reversals = detect_trend_reversals(ts_df, trend_window)

    contagion = []
    if current_step is not None:
        contagion = detect_contagion_spread(ts_df, current_step, contagion_threshold)

    all_alerts = spikes + reversals + contagion

    # Determine overall level
    levels = [a["level"] for a in all_alerts]
    if AlertLevel.CRITICAL in levels:
        overall = AlertLevel.CRITICAL
    elif AlertLevel.WARNING in levels:
        overall = AlertLevel.WARNING
    elif AlertLevel.WATCH in levels:
        overall = AlertLevel.WATCH
    else:
        overall = AlertLevel.NONE

    return {
        "spikes": spikes,
        "reversals": reversals,
        "contagion": contagion,
        "overall_level": overall,
        "alert_count": len(all_alerts),
    }
