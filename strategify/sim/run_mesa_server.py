"""Entry point: launch the Mesa 2 ModularServer with a simple grid demo.

This is a lightweight demo mode using a 2x2 CanvasGrid. For real-world
GeoJSON visualization (Ukraine/Russia/Belarus/Poland), use
``run_mesa_geo_server.py`` instead, or run ``strategify`` from the CLI.
"""

from __future__ import annotations

from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid

from strategify.config.settings import MESA_SERVER_PORT, REGION_COLORS
from strategify.sim.model import GeopolModel
from strategify.viz.status import ActorStatusElement


def actor_portrayal(agent):
    """Define how agents are drawn on the grid."""
    if agent is None:
        return None

    portrayal = {
        "Shape": "circle" if agent.posture == "Deescalate" else "rect",
        "Filled": "true",
        "Layer": 1,
        "r": 0.5,
        "w": 0.5,
        "h": 0.5,
    }

    portrayal["Color"] = REGION_COLORS.get(getattr(agent, "region_id", ""), "gray")

    return portrayal


def main():
    """Launch the Mesa visualization server (demo grid mode).

    Note: This uses a CanvasGrid which maps agents to a 2x2 layout.
    For geospatial visualization, use ``run_mesa_geo_server.py``.
    """
    grid = CanvasGrid(actor_portrayal, 2, 2, 500, 500)
    server = ModularServer(
        GeopolModel,
        [grid, ActorStatusElement()],
        "Geopol Sim (Grid Demo)",
        {},
    )
    server.port = MESA_SERVER_PORT
    server.launch()


if __name__ == "__main__":
    main()
