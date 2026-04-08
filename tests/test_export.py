"""Tests for export suite — CSV, GeoJSON, LaTeX, SVG export formats."""

import json
import tempfile
from pathlib import Path

import pytest

from strategify.sim.model import GeopolModel
from strategify.viz.export import (
    export_all,
    export_chart_svg,
    export_csv,
    export_geojson,
    export_latex_table,
)


@pytest.fixture
def stepped_model():
    model = GeopolModel()
    for _ in range(3):
        model.step()
    return model


class TestExportCSV:
    def test_csv_creates_file(self, stepped_model):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            path = f.name
        try:
            result = export_csv(stepped_model, path)
            assert result.exists()
            content = result.read_text()
            assert "posture" in content
            assert "region_id" in content
        finally:
            Path(path).unlink(missing_ok=True)


class TestExportGeoJSON:
    def test_geojson_creates_file(self, stepped_model):
        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as f:
            path = f.name
        try:
            result = export_geojson(stepped_model, path)
            assert result.exists()
            data = json.loads(result.read_text())
            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) == 4
            props = data["features"][0]["properties"]
            assert "region_id" in props
            assert "posture" in props
            assert "military" in props
        finally:
            Path(path).unlink(missing_ok=True)


class TestExportLaTeX:
    def test_latex_creates_file(self, stepped_model):
        with tempfile.NamedTemporaryFile(suffix=".tex", delete=False) as f:
            path = f.name
        try:
            result = export_latex_table(stepped_model, path)
            assert result.exists()
            content = result.read_text()
            assert r"\begin{table}" in content
            assert r"\end{table}" in content
            assert "Region" in content
            assert "Posture" in content
        finally:
            Path(path).unlink(missing_ok=True)


class TestExportSVG:
    def test_svg_escalation_chart(self, stepped_model):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            path = f.name
        try:
            result = export_chart_svg(stepped_model, path, "escalation")
            assert result.exists()
            assert result.stat().st_size > 0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_svg_diplomacy_chart(self, stepped_model):
        with tempfile.NamedTemporaryFile(suffix=".svg", delete=False) as f:
            path = f.name
        try:
            result = export_chart_svg(stepped_model, path, "diplomacy")
            assert result.exists()
            assert result.stat().st_size > 0
        finally:
            Path(path).unlink(missing_ok=True)


class TestExportAll:
    def test_export_all_creates_directory(self, stepped_model):
        with tempfile.TemporaryDirectory() as tmpdir:
            results = export_all(stepped_model, tmpdir)
            assert "csv" in results
            assert "geojson" in results
            assert "latex" in results
            assert results["csv"].exists()
            assert results["geojson"].exists()
            assert results["latex"].exists()
