"""OSINT sub-package: external data sources, adapters, caching, and sentiment analysis pipeline."""

from strategify.osint.adapters import (
    ACLEDAdapter,
    BaseAdapter,
    CrisisMonitorAdapter,
    GDELTAdapter,
    ReliefWebAdapter,
    WorldBankAdapter,
)
from strategify.osint.cache import SQLiteCache
from strategify.osint.features import (
    analyze_sentiment,
    analyze_texts_sentiment,
    compute_region_features,
)
from strategify.osint.pipeline import FeaturePipeline
from strategify.osint.sources import (
    compute_event_features,
    events_to_texts,
    fetch_gdelt_events,
    fetch_gdelt_for_regions,
    fetch_rss_feed,
)

__all__ = [
    # Features
    "analyze_sentiment",
    "analyze_texts_sentiment",
    "compute_region_features",
    # Sources
    "fetch_gdelt_events",
    "fetch_gdelt_for_regions",
    "fetch_rss_feed",
    "events_to_texts",
    "compute_event_features",
    # Adapters
    "BaseAdapter",
    "GDELTAdapter",
    "ACLEDAdapter",
    "WorldBankAdapter",
    "ReliefWebAdapter",
    "CrisisMonitorAdapter",
    # Cache
    "SQLiteCache",
    # Pipeline
    "FeaturePipeline",
]
