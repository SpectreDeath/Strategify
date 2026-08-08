"""OSINT sub-package: external data sources, adapters, caching, and sentiment analysis pipeline."""

from strategify.osint.adapters import (
    ACLEDAdapter,
    BaseAdapter,
    CrisisMonitorAdapter,
    GDELTAdapter,
    ReliefWebAdapter,
    WikipediaEventAdapter,
    WorldBankAdapter,
)
from strategify.osint.cache import SQLiteCache
from strategify.osint.cdc_soda_adapter import CDCSodaApiAdapter, SoQLQuery
from strategify.osint.epidemiology_adapter import (
    EpidemiologyDataAdapter,
    GDELTEpidemicFilter,
    OWIDDataAdapter,
    WHOApiAdapter,
)
from strategify.osint.features import (
    analyze_sentiment,
    analyze_texts_sentiment,
    compute_region_features,
)
from strategify.osint.live_feed import OSINTEvent, StrategifyLiveFeed
from strategify.osint.nih_reporter_adapter import NIHGrantProject, NIHReporterApiAdapter
from strategify.osint.pipeline import FeaturePipeline
from strategify.osint.pipeline_integration import PipelineFitOutcome, SoQLToFitterPipeline
from strategify.osint.rate_limiter import FederalApiCacheThrottle
from strategify.osint.rxnorm_adapter import RxNormApiAdapter, RxNormConcept
from strategify.osint.sources import (
    compute_event_features,
    events_to_texts,
    fetch_gdelt_events,
    fetch_gdelt_for_regions,
    fetch_rss_feed,
)
from strategify.osint.surveillance_adapters import (
    CDCCfaAdapter,
    CDCNNDSSAdapter,
    CDCWonderAdapter,
    HealthDataGovAdapter,
    NextstrainGenomicAdapter,
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
    "WikipediaEventAdapter",
    "EpidemiologyDataAdapter",
    "WHOApiAdapter",
    "OWIDDataAdapter",
    "GDELTEpidemicFilter",
    "CDCWonderAdapter",
    "CDCNNDSSAdapter",
    "CDCCfaAdapter",
    "HealthDataGovAdapter",
    "NextstrainGenomicAdapter",
    "CDCSodaApiAdapter",
    "SoQLQuery",
    "NIHReporterApiAdapter",
    "NIHGrantProject",
    "RxNormApiAdapter",
    "RxNormConcept",
    "FederalApiCacheThrottle",
    "SoQLToFitterPipeline",
    "PipelineFitOutcome",
    "StrategifyLiveFeed",
    "OSINTEvent",
    # Cache
    "SQLiteCache",
    # Pipeline
    "FeaturePipeline",
]
