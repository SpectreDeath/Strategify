"""Plugin system: extensibility via entry points and custom modules.

Allows external packages to register custom agent types, game types,
analysis functions, and visualization components.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from importlib.metadata import entry_points
from typing import Any

logger = logging.getLogger(__name__)

# Plugin registries
_agent_plugins: dict[str, type] = {}
_game_plugins: dict[str, Callable[[], Any]] = {}
_analysis_plugins: dict[str, Callable] = {}
_visualization_plugins: dict[str, Callable] = {}


def register_agent(name: str, agent_class: type) -> None:
    """Register a custom agent type.

    Parameters
    ----------
    name:
        Agent type name (used in scenario configs).
    agent_class:
        The agent class (must subclass BaseActorAgent).
    """
    _agent_plugins[name] = agent_class
    logger.info("Registered agent plugin: %s", name)


def register_game(name: str, game_factory: Callable[[], Any]) -> None:
    """Register a custom game type.

    Parameters
    ----------
    name:
        Game name (used in scenario configs).
    game_factory:
        Callable returning a NormalFormGame instance.
    """
    _game_plugins[name] = game_factory
    logger.info("Registered game plugin: %s", name)


def register_analysis(name: str, func: Callable) -> None:
    """Register a custom analysis function.

    Parameters
    ----------
    name:
        Analysis name.
    func:
        Callable(model) -> dict.
    """
    _analysis_plugins[name] = func
    logger.info("Registered analysis plugin: %s", name)


def register_visualization(name: str, func: Callable) -> None:
    """Register a custom visualization function.

    Parameters
    ----------
    name:
        Visualization name.
    func:
        Callable(model, output_path) -> str.
    """
    _visualization_plugins[name] = func
    logger.info("Registered visualization plugin: %s", name)


def get_agent(name: str) -> type | None:
    """Get a registered agent class by name."""
    return _agent_plugins.get(name)


def get_game_plugin(name: str) -> Callable | None:
    """Get a registered game factory by name."""
    return _game_plugins.get(name)


def get_analysis(name: str) -> Callable | None:
    """Get a registered analysis function by name."""
    return _analysis_plugins.get(name)


def get_visualization(name: str) -> Callable | None:
    """Get a registered visualization function by name."""
    return _visualization_plugins.get(name)


def list_plugins() -> dict[str, list[str]]:
    """List all registered plugins by category."""
    return {
        "agents": list(_agent_plugins.keys()),
        "games": list(_game_plugins.keys()),
        "analysis": list(_analysis_plugins.keys()),
        "visualizations": list(_visualization_plugins.keys()),
    }


def discover_entry_point_plugins() -> None:
    """Discover and load plugins from installed packages.

    Looks for packages that define entry points under:
    - ``strategify.agents``
    - ``strategify.games``
    - ``strategify.analysis``
    - ``strategify.visualizations``
    """
    try:
        eps = entry_points()
    except TypeError:
        # Python 3.11 compatibility
        eps = entry_points().get("strategify.plugins", [])

    for ep in eps if hasattr(eps, "select") else eps:
        try:
            plugin_func = ep.load()
            if callable(plugin_func):
                plugin_func()
                logger.info("Loaded plugin: %s", ep.name)
        except Exception as exc:
            logger.warning("Failed to load plugin %s: %s", ep.name, exc)


def get_all_games() -> dict[str, Callable]:
    """Return all games (built-in + plugins).

    Returns
    -------
    dict
        ``{game_name: factory_callable}``
    """
    from strategify.game_theory.crisis_games import GAME_REGISTRY

    all_games = dict(GAME_REGISTRY)
    all_games.update(_game_plugins)
    return all_games
