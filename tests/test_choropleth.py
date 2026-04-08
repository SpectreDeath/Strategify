"""Tests for headless choropleth renderer."""

import tempfile
from pathlib import Path

import pytest

from strategify.sim.model import GeopolModel
from strategify.viz.choropleth import HeadlessChoropleth


@pytest.fixture
def model():
    return GeopolModel()


class TestHeadlessChoropleth:
    def test_render_step_creates_png(self, model):
        renderer = HeadlessChoropleth(model)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = renderer.render_step(Path(tmpdir) / "test.png")
            assert path.exists()
            assert path.stat().st_size > 0

    def test_render_step_with_step_number(self, model):
        model.step()
        renderer = HeadlessChoropleth(model)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = renderer.render_step(Path(tmpdir) / "test.png", step=1, title="Test")
            assert path.exists()

    def test_render_all_creates_frames(self, model):
        renderer = HeadlessChoropleth(model)
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = renderer.render_all(tmpdir, steps=3, dpi=72)
            assert len(paths) == 3
            for p in paths:
                assert p.exists()

    def test_color_mode_posture(self, model):
        model.step()
        renderer = HeadlessChoropleth(model, color_mode="posture")
        gdf = renderer._build_gdf()
        colors = renderer._get_colors(gdf)
        assert len(colors) == 4
        assert all(c.startswith("#") for c in colors)

    def test_color_mode_escalation_level(self, model):
        model.step()
        renderer = HeadlessChoropleth(model, color_mode="escalation_level")
        gdf = renderer._build_gdf()
        colors = renderer._get_colors(gdf)
        assert len(colors) == 4

    def test_color_mode_region(self, model):
        model.step()
        renderer = HeadlessChoropleth(model, color_mode="region")
        gdf = renderer._build_gdf()
        colors = renderer._get_colors(gdf)
        assert len(colors) == 4

    def test_color_mode_influence(self, model):
        model.step()
        renderer = HeadlessChoropleth(model, color_mode="influence")
        gdf = renderer._build_gdf()
        colors = renderer._get_colors(gdf)
        assert len(colors) == 4

    def test_build_gdf_columns(self, model):
        model.step()
        renderer = HeadlessChoropleth(model)
        gdf = renderer._build_gdf()
        assert "region_id" in gdf.columns
        assert "posture" in gdf.columns
        assert "geometry" in gdf.columns
        assert "net_influence" in gdf.columns
        assert len(gdf) == 4

    def test_render_from_csv(self, model):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Run model and save CSV
            for _ in range(3):
                model.step()
            df = model.datacollector.get_agent_vars_dataframe().sort_index()
            csv_path = tmpdir / "output.csv"
            df.to_csv(csv_path)

            # Save GeoJSON from model
            import geopandas as gpd

            records = []
            for agent in model.schedule.agents:
                records.append(
                    {
                        "region_id": agent.region_id,
                        "geometry": agent.geometry,
                    }
                )
            gdf = gpd.GeoDataFrame(records, crs="EPSG:4326")
            geojson_path = tmpdir / "regions.geojson"
            gdf.to_file(geojson_path, driver="GeoJSON")

            # Render from CSV
            out_dir = tmpdir / "frames"
            paths = HeadlessChoropleth.render_from_csv(csv_path, geojson_path, out_dir, dpi=72)
            assert len(paths) == 3  # steps 0, 1, 2
            for p in paths:
                assert p.exists()
