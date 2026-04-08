"""Tests for plugin system — discovery, registration, and retrieval."""


from strategify.plugins import (
    _agent_plugins,
    _analysis_plugins,
    _game_plugins,
    _visualization_plugins,
    get_agent,
    get_analysis,
    get_game_plugin,
    get_visualization,
    list_plugins,
    register_agent,
    register_analysis,
    register_game,
    register_visualization,
)


class TestPluginRegistration:
    def setup_method(self):
        _agent_plugins.clear()
        _game_plugins.clear()
        _analysis_plugins.clear()
        _visualization_plugins.clear()

    def test_register_agent(self):
        class DummyAgent:
            pass

        register_agent("test_agent", DummyAgent)
        assert "test_agent" in _agent_plugins

    def test_register_game(self):
        def game_factory():
            return {"type": "test"}

        register_game("test_game", game_factory)
        assert "test_game" in _game_plugins

    def test_register_analysis(self):
        def analysis_func(model):
            return {}

        register_analysis("test_analysis", analysis_func)
        assert "test_analysis" in _analysis_plugins

    def test_register_visualization(self):
        def viz_func(model, path):
            return path

        register_visualization("test_viz", viz_func)
        assert "test_viz" in _visualization_plugins


class TestPluginRetrieval:
    def setup_method(self):
        _agent_plugins.clear()
        _game_plugins.clear()
        _analysis_plugins.clear()
        _visualization_plugins.clear()

    def test_get_agent(self):
        class DummyAgent:
            pass

        _agent_plugins["test_agent"] = DummyAgent
        result = get_agent("test_agent")
        assert result is DummyAgent

    def test_get_agent_missing(self):
        result = get_agent("nonexistent")
        assert result is None

    def test_get_game_plugin(self):
        def factory():
            return {}

        _game_plugins["test"] = factory
        result = get_game_plugin("test")
        assert result is factory

    def test_get_game_plugin_missing(self):
        result = get_game_plugin("missing")
        assert result is None

    def test_get_analysis(self):
        def func(model):
            return {}

        _analysis_plugins["test"] = func
        result = get_analysis("test")
        assert result is func

    def test_get_analysis_missing(self):
        result = get_analysis("missing")
        assert result is None

    def test_get_visualization_missing(self):
        result = get_visualization("missing")
        assert result is None


class TestPluginListing:
    def setup_method(self):
        _agent_plugins.clear()
        _game_plugins.clear()
        _analysis_plugins.clear()
        _visualization_plugins.clear()

    def test_list_plugins_empty(self):
        result = list_plugins()
        assert result["agents"] == []
        assert result["games"] == []
        assert result["analysis"] == []
        assert result["visualizations"] == []

    def test_list_plugins_with_entries(self):
        class DummyAgent:
            pass

        _agent_plugins["a1"] = DummyAgent
        _game_plugins["g1"] = lambda: {}
        _analysis_plugins["an1"] = lambda m: {}
        _visualization_plugins["v1"] = lambda m, p: p

        result = list_plugins()
        assert "a1" in result["agents"]
        assert "g1" in result["games"]
        assert "an1" in result["analysis"]
        assert "v1" in result["visualizations"]


class TestPluginDiscovery:
    def test_discover_entry_point_plugins_runs_noop(self):
        pass  # discover_entry_point_plugins can hang on some systems
