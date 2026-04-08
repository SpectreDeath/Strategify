"""OSINT feature pipeline: orchestrates adapters, sentiment, and caching.

Provides a ``FeaturePipeline`` that fetches events from configured
adapters, runs sentiment analysis, computes per-region features, and
caches results for fast repeat queries.

Usage::

    from strategify.osint.pipeline import FeaturePipeline

    pipeline = FeaturePipeline(region_keywords={
        "alpha": ["Ukraine", "Kyiv"],
        "bravo": ["Russia", "Moscow"],
    })
    features = pipeline.compute()
    # features["alpha"] = {"tension_score": 0.3, "event_count": 12, ...}
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any

from strategify.osint.adapters import (
    BaseAdapter,
    GDELTAdapter,
)
from strategify.osint.cache import SQLiteCache
from strategify.osint.features import analyze_texts_sentiment

logger = logging.getLogger(__name__)


class FeaturePipeline:
    """Orchestrates OSINT data fetching, processing, and caching.

    Parameters
    ----------
    region_keywords:
        ``{region_id: [keyword, ...]}`` for adapter queries.
    adapters:
        List of adapter instances. Defaults to ``[GDELTAdapter()]``.
    cache_ttl:
        Cache time-to-live in seconds. Default 3600 (1 hour).
    cache_path:
        Optional path for the SQLite cache file.
    """

    def __init__(
        self,
        region_keywords: dict[str, list[str]] | None = None,
        adapters: list[BaseAdapter] | None = None,
        cache_ttl: int = 3600,
        cache_path: str | None = None,
    ) -> None:
        self.region_keywords = region_keywords or {}
        self.adapters = adapters or [GDELTAdapter()]
        self.cache_ttl = cache_ttl
        self._cache = SQLiteCache(cache_path)
        self._events: dict[str, list[dict[str, Any]]] = {}
        self._features: dict[str, dict[str, float]] = {}

    def compute(
        self,
        region_keywords: dict[str, list[str]] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, dict[str, float]]:
        """Fetch events and compute per-region features.

        Parameters
        ----------
        region_keywords:
            Override the instance's region_keywords for this call.
        force_refresh:
            If True, ignore cache and fetch fresh data.

        Returns
        -------
        dict[str, dict[str, float]]
            ``{region_id: {feature_name: value}}``.
        """
        keywords = region_keywords or self.region_keywords

        if not keywords:
            logger.warning("No region keywords configured, returning empty features")
            return {}

        cache_key = self._make_cache_key(keywords)

        # Check cache
        if not force_refresh:
            cached = self._cache.get(cache_key)
            if cached is not None:
                logger.info("Loaded features from cache for %d regions", len(cached))
                self._features = cached
                return cached

        # Fetch events from all adapters
        all_events: dict[str, list[dict[str, Any]]] = {rid: [] for rid in keywords}
        for adapter in self.adapters:
            try:
                events = adapter.fetch(keywords)
                for event in events:
                    rid = event.get("region_id", "")
                    if rid in all_events:
                        all_events[rid].append(event)
                logger.info("%s: fetched %d events", adapter.name, len(events))
            except Exception as exc:
                logger.warning("%s adapter failed: %s", adapter.name, exc)

        self._events = all_events

        # Compute features per region
        features: dict[str, dict[str, float]] = {}
        for region_id, events in all_events.items():
            region_features = self._compute_region_features(region_id, events)
            features[region_id] = region_features

        self._features = features

        # Cache results
        self._cache.put(cache_key, features, ttl=self.cache_ttl)

        return features

    def get_events(self, region_id: str) -> list[dict[str, Any]]:
        """Return raw events for a region (from last compute)."""
        return self._events.get(region_id, [])

    def get_features(self, region_id: str) -> dict[str, float]:
        """Return computed features for a region (from last compute)."""
        return self._features.get(region_id, {})

    def get_all_features(self) -> dict[str, dict[str, float]]:
        """Return all computed features."""
        return dict(self._features)

    def _compute_region_features(
        self, region_id: str, events: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Compute feature dict from events for a single region."""
        texts = [e["text"] for e in events if e.get("text")]

        # Sentiment
        sentiment = (
            analyze_texts_sentiment(texts)
            if texts
            else {
                "mean_compound": 0.0,
                "tension_score": 0.0,
            }
        )

        # Event counts by type
        event_types: dict[str, int] = {}
        for e in events:
            etype = e.get("event_type", "unknown")
            event_types[etype] = event_types.get(etype, 0) + 1

        # Value aggregations (e.g., fatalities from ACLED)
        values = [e["value"] for e in events if e.get("value") is not None]
        total_value = sum(values) if values else 0.0

        return {
            "event_count": float(len(events)),
            "tension_score": sentiment.get("tension_score", 0.0),
            "sentiment_compound": sentiment.get("mean_compound", 0.0),
            "conflict_count": float(event_types.get("conflict", 0)),
            "diplomacy_count": float(event_types.get("diplomacy", 0)),
            "economic_count": float(event_types.get("economic", 0)),
            "protest_count": float(event_types.get("protest", 0)),
            "total_value": total_value,
        }

    @staticmethod
    def _make_cache_key(keywords: dict[str, list[str]]) -> str:
        """Create a deterministic cache key from region keywords."""
        blob = json.dumps(
            {k: sorted(v) for k, v in sorted(keywords.items())},
            sort_keys=True,
        )
        return f"osint_features_{hashlib.sha256(blob.encode()).hexdigest()[:16]}"

    def summary(self) -> dict[str, Any]:
        """Return pipeline summary."""
        total_events = sum(len(events) for events in self._events.values())
        adapter_names = [a.name for a in self.adapters]
        return {
            "adapters": adapter_names,
            "regions": list(self._features.keys()),
            "total_events": total_events,
            "cache_stats": self._cache.stats(),
        }
