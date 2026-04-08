"""Tests for Phase 4: export suite, plugin system, and web components."""

import tempfile
from pathlib import Path

import pytest

from strategify.sim.model import GeopolModel


@pytest.fixture
def stepped_model():
    m = GeopolModel()
    for _ in range(5):
        m.step()
    return m


# ---------------------------------------------------------------------------
# Export Suite (4.4)
# ---------------------------------------------------------------------------


class TestExport:
    def test_export_csv(self, stepped_model):
        from strategify.viz.export import export_csv

        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_csv(stepped_model, Path(tmpdir) / "out.csv")
            assert path.exists()
            assert path.stat().st_size > 0

    def test_export_geojson(self, stepped_model):
        from strategify.viz.export import export_geojson

        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_geojson(stepped_model, Path(tmpdir) / "out.geojson")
            assert path.exists()
            import json

            with open(path) as f:
                data = json.load(f)
            assert data["type"] == "FeatureCollection"
            assert len(data["features"]) == 4

    def test_export_geojson_properties(self, stepped_model):
        from strategify.viz.export import export_geojson

        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_geojson(stepped_model, Path(tmpdir) / "out.geojson")
            import json

            with open(path) as f:
                data = json.load(f)
            props = data["features"][0]["properties"]
            assert "region_id" in props
            assert "posture" in props
            assert "military" in props

    def test_export_latex_table(self, stepped_model):
        from strategify.viz.export import export_latex_table

        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_latex_table(stepped_model, Path(tmpdir) / "out.tex")
            assert path.exists()
            content = path.read_text()
            assert "\\begin{table}" in content
            assert "\\toprule" in content

    def test_export_chart_svg(self, stepped_model):
        from strategify.viz.export import export_chart_svg

        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_chart_svg(stepped_model, Path(tmpdir) / "esc.svg", "escalation")
            assert path.exists()
            assert path.stat().st_size > 0

    def test_export_chart_svg_diplomacy(self, stepped_model):
        from strategify.viz.export import export_chart_svg

        with tempfile.TemporaryDirectory() as tmpdir:
            path = export_chart_svg(stepped_model, Path(tmpdir) / "dip.svg", "diplomacy")
            assert path.exists()

    def test_export_all(self, stepped_model):
        from strategify.viz.export import export_all

        with tempfile.TemporaryDirectory() as tmpdir:
            results = export_all(stepped_model, tmpdir)
            assert "csv" in results
            assert "geojson" in results
            assert "latex" in results
            assert results["csv"].exists()
            assert results["geojson"].exists()


# ---------------------------------------------------------------------------
# Plugin System (4.6)
# ---------------------------------------------------------------------------


class TestPlugins:
    def test_register_agent(self):
        from strategify.plugins import _agent_plugins, get_agent, register_agent

        class DummyAgent:
            pass

        register_agent("dummy", DummyAgent)
        assert get_agent("dummy") is DummyAgent
        del _agent_plugins["dummy"]

    def test_register_game(self):
        from strategify.plugins import _game_plugins, get_game_plugin, register_game

        def dummy_game():
            return "game"

        register_game("dummy_game", dummy_game)
        assert get_game_plugin("dummy_game") is dummy_game
        del _game_plugins["dummy_game"]

    def test_register_analysis(self):
        from strategify.plugins import _analysis_plugins, get_analysis, register_analysis

        def dummy_analysis(model):
            return {}

        register_analysis("dummy_analysis", dummy_analysis)
        assert get_analysis("dummy_analysis") is dummy_analysis
        del _analysis_plugins["dummy_analysis"]

    def test_register_visualization(self):
        from strategify.plugins import (
            _visualization_plugins,
            get_visualization,
            register_visualization,
        )

        def dummy_viz(model, path):
            return path

        register_visualization("dummy_viz", dummy_viz)
        assert get_visualization("dummy_viz") is dummy_viz
        del _visualization_plugins["dummy_viz"]

    def test_list_plugins(self):
        from strategify.plugins import _agent_plugins, list_plugins, register_agent

        class DummyAgent:
            pass

        register_agent("test_dummy", DummyAgent)
        plugins = list_plugins()
        assert "test_dummy" in plugins["agents"]
        del _agent_plugins["test_dummy"]

    def test_get_all_games_includes_builtins(self):
        from strategify.plugins import get_all_games

        games = get_all_games()
        assert "escalation" in games
        assert "trade" in games
        assert "sanctions" in games
        assert "alliance" in games
        assert "military" in games

    def test_get_agent_returns_none_for_unknown(self):
        from strategify.plugins import get_agent

        assert get_agent("nonexistent") is None

    def test_get_analysis_returns_none_for_unknown(self):
        from strategify.plugins import get_analysis

        assert get_analysis("nonexistent") is None


# ---------------------------------------------------------------------------
# Web Dashboard (4.1) - import test only (Streamlit may not be installed)
# ---------------------------------------------------------------------------


class TestWebDashboard:
    def test_dashboard_importable(self):
        from strategify.web import run_dashboard

        assert callable(run_dashboard)

    def test_dashboard_raises_without_streamlit(self):
        import sys

        # Temporarily block streamlit import
        original = sys.modules.get("streamlit")
        sys.modules["streamlit"] = None

        try:
            from strategify.web.dashboard import run_dashboard

            with pytest.raises(ImportError, match="Streamlit"):
                run_dashboard()
        finally:
            if original is not None:
                sys.modules["streamlit"] = original
            else:
                sys.modules.pop("streamlit", None)
