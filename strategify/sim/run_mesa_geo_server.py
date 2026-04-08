"""Entry point: launch the Mesa-Geo ModularServer browser visualisation."""

from __future__ import annotations

from mesa.visualization.ModularVisualization import ModularServer
from mesa_geo.visualization import MapModule

from strategify.config.settings import MESA_SERVER_PORT, REGION_COLORS
from strategify.sim.model import GeopolModel
from strategify.viz.status import ActorStatusElement


def agent_portrayal(agent):
    """Define how agents are drawn on the map."""
    if agent is None:
        return {}

    color = REGION_COLORS.get(getattr(agent, "region_id", ""), "gray")
    opacity = 0.8 if getattr(agent, "posture", "Deescalate") == "Escalate" else 0.3

    return {
        "color": color,
        "fillOpacity": opacity,
    }


def main():
    """Launch the Mesa-Geo visualization server."""
    map_element = MapModule(agent_portrayal)
    server = ModularServer(
        GeopolModel,
        [map_element, ActorStatusElement()],
        "Geopol Sim - Real World",
        {},
    )
    server.port = MESA_SERVER_PORT
    server.launch()


if __name__ == "__main__":
    main()
