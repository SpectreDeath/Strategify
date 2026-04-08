"""GeoJSON loader with Natural Earth / GADM support, region subsetting, and caching.

Provides a pipeline for loading world or regional geographic data,
subsetting to configured countries, mapping to internal region IDs,
reprojecting, and caching the processed result.

Usage::

    from strategify.geo.loader import GeoJSONLoader, RegionSubsetConfig

    config = RegionSubsetConfig(
        countries=["Ukraine", "Russia", "Belarus", "Poland"],
        id_map={"Ukraine": "alpha", "Russia": "bravo"},
        source="naturalearth",
        resolution="110m",
    )
    gdf = GeoJSONLoader.load(config)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import geopandas as gpd

from strategify.geo.adjacency import is_edge_neighbor

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache directory
# ---------------------------------------------------------------------------
_CACHE_DIR = Path(__file__).resolve().parent / ".cache"

# ---------------------------------------------------------------------------
# Data source URLs
# ---------------------------------------------------------------------------
_NATURALEARTH_URLS: dict[str, str] = {
    "110m": "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip",
    "50m": "https://naciscdn.org/naturalearth/50m/cultural/ne_50m_admin_0_countries.zip",
    "10m": "https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_0_countries.zip",
}


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
@dataclass
class RegionSubsetConfig:
    """Configuration for loading and subsetting geographic data.

    Attributes
    ----------
    countries:
        List of country names to include (matched against the source's
        name column).
    id_map:
        Mapping from country name to internal region ID. Countries not
        in this map keep their original name as the region ID.
    source:
        Data source: ``"naturalearth"`` or a path to a local GeoJSON /
        Shapefile.
    resolution:
        Natural Earth resolution: ``"110m"``, ``"50m"``, or ``"10m"``.
    crs:
        Target CRS for output geometries. Default ``"EPSG:4326"``.
    name_column:
        Column in the source data containing country names.
        Default ``"ADMIN"`` (Natural Earth).
    """

    countries: list[str] = field(default_factory=list)
    id_map: dict[str, str] = field(default_factory=dict)
    source: str = "naturalearth"
    resolution: str = "110m"
    crs: str = "EPSG:4326"
    name_column: str = "ADMIN"
    simplify_tolerance: float | None = None

    def cache_key(self) -> str:
        """Deterministic hash for caching."""
        blob = json.dumps(
            {
                "countries": sorted(self.countries),
                "id_map": dict(sorted(self.id_map.items())),
                "source": self.source,
                "resolution": self.resolution,
                "crs": self.crs,
                "name_column": self.name_column,
                "simplify_tolerance": self.simplify_tolerance,
            },
            sort_keys=True,
        )
        return hashlib.sha256(blob.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------
class GeoJSONLoader:
    """Load geographic data from Natural Earth or local files.

    Supports region subsetting, ID mapping, reprojection, and file-based
    caching for fast repeat loads.
    """

    @classmethod
    def load(cls, config: RegionSubsetConfig) -> gpd.GeoDataFrame:
        """Load, subset, and reproject geographic data.

        Parameters
        ----------
        config:
            RegionSubsetConfig describing what to load.

        Returns
        -------
        gpd.GeoDataFrame
            GeoDataFrame with columns ``region_id`` and ``geometry``,
            reprojected to the target CRS.
        """
        # Check cache first
        cached = cls._load_cache(config)
        if cached is not None:
            logger.info("Loaded %d regions from cache", len(cached))
            return cached

        # Load raw data
        raw = cls._load_raw(config)

        # Subset
        if config.countries:
            raw = cls._subset(raw, config)

        # Map IDs
        gdf = cls._map_ids(raw, config)

        # Reproject
        if config.crs and gdf.crs and str(gdf.crs) != config.crs:
            gdf = gdf.to_crs(config.crs)

        # Simplify geometries for performance
        if config.simplify_tolerance is not None:
            gdf = gdf.copy()
            gdf["geometry"] = gdf.geometry.simplify(
                config.simplify_tolerance, preserve_topology=True
            )

        # Keep only region_id + geometry
        gdf = gdf[["region_id", "geometry"]].copy()
        gdf = gdf.reset_index(drop=True)

        # Cache
        cls._save_cache(config, gdf)

        logger.info(
            "Loaded %d regions from %s (resolution=%s)",
            len(gdf),
            config.source,
            config.resolution,
        )
        return gdf

    @classmethod
    def load_from_geojson(cls, path: str | Path, target_crs: str | None = None) -> gpd.GeoDataFrame:
        """Load a local GeoJSON file, normalize to region_id + geometry, and optionally reproject.

        Parameters
        ----------
        path:
            Path to a GeoJSON file.
        target_crs:
            Optional target CRS (e.g., "EPSG:3857") to reproject the geometry.

        Returns
        -------
        gpd.GeoDataFrame
            Normalized GeoDataFrame with ``region_id`` column.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"GeoJSON not found: {path}")

        gdf = gpd.read_file(path)

        # Reproject if requested
        if target_crs and gdf.crs and str(gdf.crs) != target_crs:
            logger.info("Reprojecting %s to %s", path.name, target_crs)
            gdf = gdf.to_crs(target_crs)

        # Ensure region_id column exists
        if "region_id" not in gdf.columns:
            # Try common alternatives
            for col in ("name", "NAME", "ADMIN", "id", "ID"):
                if col in gdf.columns:
                    gdf["region_id"] = gdf[col]
                    break
            else:
                gdf["region_id"] = [f"region_{i}" for i in range(len(gdf))]

        return gdf[["region_id", "geometry"]].copy()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _load_raw(cls, config: RegionSubsetConfig) -> gpd.GeoDataFrame:
        """Load raw data from the configured source."""
        if config.source == "naturalearth":
            url = _NATURALEARTH_URLS.get(config.resolution)
            if url is None:
                raise ValueError(
                    f"Unknown Natural Earth resolution '{config.resolution}'. "
                    f"Choose from: {list(_NATURALEARTH_URLS.keys())}"
                )
            logger.info("Downloading Natural Earth %s data...", config.resolution)
            return gpd.read_file(url)
        else:
            # Treat as local file path
            path = Path(config.source)
            if not path.exists():
                raise FileNotFoundError(f"Source file not found: {path}")
            return gpd.read_file(path)

    @classmethod
    def _subset(cls, gdf: gpd.GeoDataFrame, config: RegionSubsetConfig) -> gpd.GeoDataFrame:
        """Filter to the configured countries."""
        mask = gdf[config.name_column].isin(config.countries)
        subset = gdf[mask].copy()
        if subset.empty:
            logger.warning(
                "No regions matched country list %s in column '%s'. Available: %s",
                config.countries,
                config.name_column,
                sorted(gdf[config.name_column].unique().tolist())[:20],
            )
        return subset

    @classmethod
    def _map_ids(cls, gdf: gpd.GeoDataFrame, config: RegionSubsetConfig) -> gpd.GeoDataFrame:
        """Map country names to internal region IDs."""
        if config.id_map:
            gdf = gdf.copy()
            gdf["region_id"] = (
                gdf[config.name_column].map(config.id_map).fillna(gdf[config.name_column])
            )
        else:
            gdf = gdf.copy()
            gdf["region_id"] = gdf[config.name_column]
        return gdf

    @classmethod
    def _cache_path(cls, config: RegionSubsetConfig) -> Path:
        """Return cache file path for a config."""
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return _CACHE_DIR / f"regions_{config.cache_key()}.geojson"

    @classmethod
    def _load_cache(cls, config: RegionSubsetConfig) -> gpd.GeoDataFrame | None:
        """Try to load a cached GeoDataFrame."""
        cache_path = cls._cache_path(config)
        if cache_path.exists():
            try:
                gdf = gpd.read_file(cache_path)
                if "region_id" in gdf.columns and len(gdf) > 0:
                    return gdf
            except Exception:
                logger.debug("Cache read failed for %s", cache_path)
        return None

    @classmethod
    def _save_cache(cls, config: RegionSubsetConfig, gdf: gpd.GeoDataFrame) -> None:
        """Save GeoDataFrame to cache."""
        cache_path = cls._cache_path(config)
        try:
            gdf.to_file(cache_path, driver="GeoJSON")
            logger.debug("Cached %d regions to %s", len(gdf), cache_path)
        except Exception as exc:
            logger.warning("Failed to write cache: %s", exc)


# ---------------------------------------------------------------------------
# Adjacency builder
# ---------------------------------------------------------------------------
class AdjacencyBuilder:
    """Compute neighbor graph from a GeoDataFrame.

    Uses spatial joins and the shared ``is_edge_neighbor`` filter to
    produce an adjacency dict excluding corner-only contacts.
    """

    @classmethod
    def build(cls, gdf: gpd.GeoDataFrame) -> dict[str, list[str]]:
        """Build adjacency mapping from a GeoDataFrame.

        Parameters
        ----------
        gdf:
            GeoDataFrame with ``region_id`` and ``geometry`` columns.

        Returns
        -------
        dict[str, list[str]]
            ``{region_id: [neighbor_region_ids...]}`` containing only
            edge-sharing neighbors (no corner contacts).
        """
        adjacency: dict[str, list[str]] = {rid: [] for rid in gdf["region_id"]}

        ids = gdf["region_id"].tolist()
        geoms = gdf.geometry.tolist()

        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if is_edge_neighbor(geoms[i], geoms[j]):
                    adjacency[ids[i]].append(ids[j])
                    adjacency[ids[j]].append(ids[i])

        return adjacency

    @classmethod
    def adjacency_to_edges(cls, adjacency: dict[str, list[str]]) -> list[tuple[str, str]]:
        """Convert adjacency dict to sorted edge list (deduplicated).

        Returns
        -------
        list[tuple[str, str]]
            Sorted list of ``(region_a, region_b)`` pairs.
        """
        edges = set()
        for rid, neighbors in adjacency.items():
            for n in neighbors:
                edges.add(tuple(sorted((rid, n))))
        return sorted(edges)

    @classmethod
    def validate(
        cls,
        adjacency: dict[str, list[str]],
        expected_edges: list[tuple[str, str]],
        excluded_edges: list[tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Validate adjacency against expected and excluded edge lists.

        Returns
        -------
        dict
            ``{"valid": bool, "missing": [...], "unexpected": [...],
               "excluded_violations": [...]}``
        """
        actual_edges = set(cls.adjacency_to_edges(adjacency))
        expected_set = {tuple(sorted(e)) for e in expected_edges}
        excluded_set = {tuple(sorted(e)) for e in (excluded_edges or [])}

        missing = sorted(expected_set - actual_edges)
        unexpected = sorted(actual_edges - expected_set)
        excluded_violations = sorted(actual_edges & excluded_set)

        return {
            "valid": not missing and not excluded_violations,
            "missing": missing,
            "unexpected": unexpected,
            "excluded_violations": excluded_violations,
        }
