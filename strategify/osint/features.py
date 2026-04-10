"""OSINT feature pipeline with VADER sentiment analysis.

Analyzes geopolitical text (news headlines, reports, social media) to produce
per-region tension scores using VADER sentiment analysis.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)


class RegionMap(Protocol):
    """Protocol for objects that expose a list of region dicts."""

    @property
    def regions(self) -> list[dict[str, Any]]: ...


# Singleton analyzer instance
_analyzer: SentimentIntensityAnalyzer | None = None


def _get_analyzer() -> SentimentIntensityAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentIntensityAnalyzer()
    return _analyzer


def analyze_sentiment(text: str) -> dict[str, float]:
    """Analyze sentiment of a single text using VADER.

    Parameters
    ----------
    text:
        The text to analyze (headline, report, social media post).

    Returns
    -------
    dict
        VADER scores: {"neg", "neu", "pos", "compound"}.
        "compound" ranges from -1.0 (most negative) to 1.0 (most positive).
    """
    analyzer = _get_analyzer()
    return analyzer.polarity_scores(text)


def analyze_texts_sentiment(texts: list[str]) -> dict[str, float]:
    """Aggregate sentiment across multiple texts.

    Parameters
    ----------
    texts:
        List of text strings to analyze.

    Returns
    -------
    dict
        {"mean_compound": float, "min_compound": float, "max_compound": float,
         "tension_score": float}
        tension_score is derived from negative compound values (0=calm, 1=high tension).
    """
    if not texts:
        return {
            "mean_compound": 0.0,
            "min_compound": 0.0,
            "max_compound": 0.0,
            "tension_score": 0.0,
        }

    analyzer = _get_analyzer()
    compounds = [analyzer.polarity_scores(t)["compound"] for t in texts]

    mean_c = sum(compounds) / len(compounds)
    # Tension score: how negative the average sentiment is, normalized to [0, 1]
    # compound range is [-1, 1]. Map [-1, 0] -> [1, 0] for tension.
    tension = max(0.0, -mean_c)

    return {
        "mean_compound": mean_c,
        "min_compound": min(compounds),
        "max_compound": max(compounds),
        "tension_score": tension,
    }


def compute_region_features(
    world_map: RegionMap | object,
    region_texts: dict[str, list[str]] | None = None,
) -> dict[str, dict[str, float]]:
    """Compute numeric features per region, optionally using text sentiment.

    Parameters
    ----------
    world_map:
        Any object with a ``.regions`` attribute (list of dicts with ``region_id``).
    region_texts:
        Optional mapping of ``region_id`` -> list of text strings (news, reports).
        If provided, sentiment analysis augments the features.

    Returns
    -------
    dict
        Mapping ``region_id`` -> ``{feature_name: value}``.
    """
    if not hasattr(world_map, "regions"):
        raise TypeError(f"world_map must have a 'regions' attribute, got {type(world_map).__name__}")

    features = {}
    for region in world_map.regions:
        rid = region["region_id"]
        base = {
            "instability_index": 0.1,
            "economic_weight": 0.5,
        }

        if region_texts and rid in region_texts:
            sentiment = analyze_texts_sentiment(region_texts[rid])
            base["sentiment_compound"] = sentiment["mean_compound"]
            base["tension_score"] = sentiment["tension_score"]
        else:
            base["sentiment_compound"] = 0.0
            base["tension_score"] = 0.0

        features[rid] = base

    return features
