"""Interactive diplomacy graph visualization using pyvis.

Generates standalone HTML files with physics-based network visualization
of alliance and rivalry relationships.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pyvis.network import Network

from strategify.config.settings import get_region_hex_color

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


def create_diplomacy_network(
    model: GeopolModel,
    output_path: str | Path = "diplomacy_network.html",
) -> str:
    """Create an interactive network visualization of diplomatic relations.

    Parameters
    ----------
    model:
        The active GeopolModel.
    output_path:
        Where to save the HTML file.

    Returns
    -------
    str
        Path to the saved HTML file.
    """
    output_path = Path(output_path)
    net = Network(height="600px", width="100%", directed=False, bgcolor="#ffffff")

    # Add nodes
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        posture = getattr(agent, "posture", "Deescalate")
        personality = getattr(agent, "personality", "Unknown")
        military = agent.capabilities.get("military", 0.5)
        color = get_region_hex_color(rid)
        size = 20 + military * 30

        label = f"{rid.upper()}"
        title = f"Region: {rid.upper()}\nPosture: {posture}\nPersonality: {personality}\nMilitary: {military:.2f}"

        net.add_node(
            agent.unique_id,
            label=label,
            title=title,
            color=color,
            size=size,
        )

    # Add edges
    for u, v, data in model.relations.graph.edges(data=True):
        weight = data.get("weight", 0.0)
        if weight > 0.5:
            color = "#4CAF50"
            title = f"Alliance (weight: {weight:.1f})"
            width = 3
        elif weight < -0.3:
            color = "#F44336"
            title = f"Rivalry (weight: {weight:.1f})"
            width = 2
        else:
            color = "#9E9E9E"
            title = f"Neutral (weight: {weight:.1f})"
            width = 1

        net.add_edge(u, v, color=color, width=width, title=title)

    net.save_graph(str(output_path))
    return str(output_path)
