"""Tests for GeoJSON loader, region subsetting, and adjacency builder."""


import geopandas as gpd
import pytest
from shapely.geometry import Polygon

from strategify.geo.adjacency import is_edge_neighbor
from strategify.geo.loader import AdjacencyBuilder, GeoJSONLoader, RegionSubsetConfig

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def demo_gdf():
    """GeoDataFrame matching regions_demo.geojson layout."""
    geoms = {
        "alpha": Polygon([(0, 1), (1, 1), (1, 2), (0, 2)]),
        "bravo": Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
        "charlie": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
        "delta": Polygon([(1, 0), (2, 0), (2, 1), (1, 1)]),
    }
    return gpd.GeoDataFrame(
        [{"region_id": rid, "geometry": geom} for rid, geom in geoms.items()],
        crs="EPSG:4326",
    )


# ---------------------------------------------------------------------------
# RegionSubsetConfig
# ---------------------------------------------------------------------------


class TestRegionSubsetConfig:
    def test_cache_key_deterministic(self):
        c1 = RegionSubsetConfig(countries=["A", "B"], id_map={"A": "x"}, source="naturalearth")
        c2 = RegionSubsetConfig(countries=["A", "B"], id_map={"A": "x"}, source="naturalearth")
        assert c1.cache_key() == c2.cache_key()

    def test_cache_key_differs_with_different_config(self):
        c1 = RegionSubsetConfig(countries=["A"], source="naturalearth")
        c2 = RegionSubsetConfig(countries=["B"], source="naturalearth")
        assert c1.cache_key() != c2.cache_key()

    def test_default_values(self):
        c = RegionSubsetConfig()
        assert c.countries == []
        assert c.source == "naturalearth"
        assert c.resolution == "110m"
        assert c.crs == "EPSG:4326"


# ---------------------------------------------------------------------------
# GeoJSONLoader
# ---------------------------------------------------------------------------


class TestGeoJSONLoader:
    def test_load_from_geojson(self, tmp_path):
        geojson = tmp_path / "test.geojson"
        gdf = gpd.GeoDataFrame(
            [
                {"name": "RegionA", "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])},
                {"name": "RegionB", "geometry": Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])},
            ],
            crs="EPSG:4326",
        )
        gdf.to_file(geojson, driver="GeoJSON")

        result = GeoJSONLoader.load_from_geojson(geojson)
        assert "region_id" in result.columns
        assert "geometry" in result.columns
        assert len(result) == 2
        assert set(result["region_id"]) == {"RegionA", "RegionB"}

    def test_load_from_geojson_uses_region_id_if_present(self, tmp_path):
        geojson = tmp_path / "test.geojson"
        gdf = gpd.GeoDataFrame(
            [
                {"region_id": "alpha", "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])},
            ],
            crs="EPSG:4326",
        )
        gdf.to_file(geojson, driver="GeoJSON")

        result = GeoJSONLoader.load_from_geojson(geojson)
        assert result["region_id"].iloc[0] == "alpha"

    def test_load_from_geojson_missing_file(self):
        with pytest.raises(FileNotFoundError, match="GeoJSON not found"):
            GeoJSONLoader.load_from_geojson("/nonexistent/file.geojson")

    def test_load_local_geojson(self, tmp_path):
        geojson = tmp_path / "local.geojson"
        gdf = gpd.GeoDataFrame(
            [
                {"ADMIN": "CountryA", "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])},
                {"ADMIN": "CountryB", "geometry": Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])},
            ],
            crs="EPSG:4326",
        )
        gdf.to_file(geojson, driver="GeoJSON")

        config = RegionSubsetConfig(
            countries=["CountryA", "CountryB"],
            id_map={"CountryA": "alpha", "CountryB": "bravo"},
            source=str(geojson),
        )
        result = GeoJSONLoader.load(config)
        assert len(result) == 2
        assert set(result["region_id"]) == {"alpha", "bravo"}
        assert list(result.columns) == ["region_id", "geometry"]

    def test_load_local_subset(self, tmp_path):
        geojson = tmp_path / "local.geojson"
        gdf = gpd.GeoDataFrame(
            [
                {"ADMIN": "CountryA", "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])},
                {"ADMIN": "CountryB", "geometry": Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])},
                {"ADMIN": "CountryC", "geometry": Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])},
            ],
            crs="EPSG:4326",
        )
        gdf.to_file(geojson, driver="GeoJSON")

        config = RegionSubsetConfig(
            countries=["CountryA", "CountryC"],
            source=str(geojson),
        )
        result = GeoJSONLoader.load(config)
        assert len(result) == 2
        assert set(result["region_id"]) == {"CountryA", "CountryC"}

    def test_load_caching(self, tmp_path):
        geojson = tmp_path / "local.geojson"
        gdf = gpd.GeoDataFrame(
            [{"ADMIN": "A", "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])}],
            crs="EPSG:4326",
        )
        gdf.to_file(geojson, driver="GeoJSON")

        config = RegionSubsetConfig(
            countries=["A"],
            id_map={"A": "alpha"},
            source=str(geojson),
        )

        result1 = GeoJSONLoader.load(config)
        result2 = GeoJSONLoader.load(config)
        assert len(result1) == len(result2)
        assert set(result1["region_id"]) == set(result2["region_id"])


# ---------------------------------------------------------------------------
# AdjacencyBuilder
# ---------------------------------------------------------------------------


class TestAdjacencyBuilder:
    def test_build_demo_adjacency(self, demo_gdf):
        adjacency = AdjacencyBuilder.build(demo_gdf)
        # Expected edge neighbors only (no corner contacts)
        assert "bravo" in adjacency["alpha"]
        assert "charlie" in adjacency["alpha"]
        assert "delta" not in adjacency["alpha"]  # corner only
        assert "charlie" not in adjacency["bravo"]  # corner only
        assert "delta" in adjacency["bravo"]
        assert "delta" in adjacency["charlie"]

    def test_build_symmetric(self, demo_gdf):
        adjacency = AdjacencyBuilder.build(demo_gdf)
        for rid, neighbors in adjacency.items():
            for n in neighbors:
                assert rid in adjacency[n]

    def test_adjacency_to_edges(self, demo_gdf):
        adjacency = AdjacencyBuilder.build(demo_gdf)
        edges = AdjacencyBuilder.adjacency_to_edges(adjacency)
        expected = [
            ("alpha", "bravo"),
            ("alpha", "charlie"),
            ("bravo", "delta"),
            ("charlie", "delta"),
        ]
        assert sorted(edges) == sorted(expected)

    def test_validate_passes(self, demo_gdf):
        adjacency = AdjacencyBuilder.build(demo_gdf)
        result = AdjacencyBuilder.validate(
            adjacency,
            expected_edges=[
                ("alpha", "bravo"),
                ("alpha", "charlie"),
                ("bravo", "delta"),
                ("charlie", "delta"),
            ],
            excluded_edges=[
                ("alpha", "delta"),
                ("bravo", "charlie"),
            ],
        )
        assert result["valid"] is True
        assert result["missing"] == []
        assert result["excluded_violations"] == []

    def test_validate_detects_missing(self, demo_gdf):
        adjacency = AdjacencyBuilder.build(demo_gdf)
        result = AdjacencyBuilder.validate(
            adjacency,
            expected_edges=[
                ("alpha", "bravo"),
                ("alpha", "charlie"),
                ("bravo", "delta"),
                ("charlie", "delta"),
                ("alpha", "delta"),  # this shouldn't exist
            ],
        )
        assert result["valid"] is False
        assert ("alpha", "delta") in result["missing"]


class TestIsEdgeNeighbor:
    def test_non_intersecting_geometries(self):
        """Geometries that don't touch at all should return False."""

        a = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        b = Polygon([(5, 5), (6, 5), (6, 6), (5, 6)])
        assert is_edge_neighbor(a, b) is False

    def test_geometry_collection_with_line(self):
        """GeometryCollection containing a LineString should return True."""

        # Two polygons sharing a line segment but also touching at a corner
        # Create them via union to force a GeometryCollection
        a = Polygon([(0, 0), (2, 0), (2, 1), (0, 1)])
        b = Polygon([(2, 1), (3, 1), (3, 2), (2, 2)])  # corner only at (2,1)
        c = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])  # shares edge with a

        # a and c share an edge
        assert is_edge_neighbor(a, c) is True
        # a and b share only a corner
        assert is_edge_neighbor(a, b) is False

    def test_overlapping_polygons(self):
        """Overlapping polygons produce a Polygon intersection, not edge."""

        a = Polygon([(0, 0), (2, 0), (2, 2), (0, 2)])
        b = Polygon([(1, 1), (3, 1), (3, 3), (1, 3)])
        # Overlap → Polygon intersection → not edge neighbor
        assert is_edge_neighbor(a, b) is False

    def test_empty_intersection(self):
        """Disjoint geometries return False."""

        a = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        b = Polygon([(10, 10), (11, 10), (11, 11), (10, 11)])
        assert is_edge_neighbor(a, b) is False


# ---------------------------------------------------------------------------
# Model integration
# ---------------------------------------------------------------------------


class TestModelGeoDFIntegration:
    def test_model_accepts_gdf(self, demo_gdf):
        from strategify.sim.model import GeopolModel

        model = GeopolModel(region_gdf=demo_gdf)
        assert len(model.schedule.agents) == 4
        region_ids = {a.region_id for a in model.schedule.agents}
        assert region_ids == {"alpha", "bravo", "charlie", "delta"}

    def test_model_gdf_step_runs(self, demo_gdf):
        from strategify.sim.model import GeopolModel

        model = GeopolModel(region_gdf=demo_gdf)
        for _ in range(3):
            model.step()
        assert model.influence_map is not None

    def test_model_gdf_deterministic(self, demo_gdf):
        from strategify.sim.model import GeopolModel

        m1 = GeopolModel(region_gdf=demo_gdf)
        m2 = GeopolModel(region_gdf=demo_gdf)
        for _ in range(5):
            m1.step()
            m2.step()
        p1 = {a.region_id: a.posture for a in m1.schedule.agents}
        p2 = {a.region_id: a.posture for a in m2.schedule.agents}
        assert p1 == p2
