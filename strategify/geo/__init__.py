"""Geo sub-package: world map and geospatial utilities."""

from strategify.config.settings import GEO_DIR, REAL_WORLD_GEOJSON
from strategify.geo.adjacency import is_edge_neighbor
from strategify.geo.loader import AdjacencyBuilder, GeoJSONLoader, RegionSubsetConfig
from strategify.geo.real_data import (
    LiveDataUpdater,
    RealWorldDataCollector,
    RegionData,
    create_data_collector,
)

__all__ = [
    "REAL_WORLD_GEOJSON",
    "GEO_DIR",
    "is_edge_neighbor",
    "GeoJSONLoader",
    "RegionSubsetConfig",
    "AdjacencyBuilder",
    "RealWorldDataCollector",
    "RegionData",
    "LiveDataUpdater",
    "create_data_collector",
]
