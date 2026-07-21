"""Tests for Vector Map Engine & GeoJSON/Vector Map generation."""


from strategify.sim.model import GeopolModel
from strategify.viz.vector_map import VectorMapBuilder, create_vector_map_html


def test_vector_map_builder_regions():
    model = GeopolModel(n_steps=1)
    model.step()

    builder = VectorMapBuilder(model)
    region_fc = builder.build_region_layer()

    assert region_fc["type"] == "FeatureCollection"
    assert len(region_fc["features"]) > 0
    first_feat = region_fc["features"][0]
    assert "region_id" in first_feat["properties"]
    assert "fill" in first_feat["properties"]


def test_vector_map_builder_military_units():
    model = GeopolModel(n_steps=1)
    model.step()

    builder = VectorMapBuilder(model)
    units_fc = builder.build_military_units_layer()

    assert units_fc["type"] == "FeatureCollection"
    assert isinstance(units_fc["features"], list)


def test_vector_map_builder_export_geojson(tmp_path):
    model = GeopolModel(n_steps=1)
    model.step()

    builder = VectorMapBuilder(model)
    out_file = tmp_path / "test_map.geojson"
    result_path = builder.export_geojson(out_file)

    assert result_path.exists()
    assert result_path.stat().st_size > 100


def test_create_vector_map_html(tmp_path):
    model = GeopolModel(n_steps=1)
    model.step()

    out_file = tmp_path / "vector_map.html"
    result_path = create_vector_map_html(model, out_file)

    assert result_path.exists()
    html_text = result_path.read_text(encoding="utf-8")
    assert "maplibregl.Map" in html_text
    assert "Vector Map Layers" in html_text
