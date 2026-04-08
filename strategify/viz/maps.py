"""Interactive map visualization using Folium.

Generates choropleth maps of simulation state with region coloring
by escalation posture, alliances, and influence. Supports multiple
basemap styles including satellite imagery.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import folium

from strategify.config.settings import get_region_hex_color

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


ESCALATION_OPACITY = {
    "Escalate": 0.8,
    "Deescalate": 0.3,
}

# Escalation level opacity mapping
LEVEL_OPACITY = {
    "Cooperative": 0.2,
    "Diplomatic": 0.35,
    "Economic": 0.55,
    "Military": 0.85,
}

# Basemap tile providers
BASEMAP_TILES = {
    "satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    "streets": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}",
    "topo": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
    "light": "CartoDB positron",
    "dark": "CartoDB dark_matter",
    "osm": "OpenStreetMap",
}


def create_map(
    model: GeopolModel,
    output_path: str | Path = "simulation_map.html",
    basemap: str = "satellite",
) -> str:
    """Create an interactive Folium map of the simulation state.

    Parameters
    ----------
    model:
        The active GeopolModel (should have been stepped at least once).
    output_path:
        Where to save the HTML file.
    basemap:
        Basemap style: "satellite", "streets", "topo", "light", "dark", "osm".
        Default: "satellite" for realistic imagery.

    Returns
    -------
    str
        Path to the saved HTML file.
    """
    output_path = Path(output_path)

    tiles = BASEMAP_TILES.get(basemap, BASEMAP_TILES["satellite"])
    attr = None
    if basemap in ("satellite", "streets", "topo"):
        attr = "Esri"

    # Center map on Eastern Europe
    m = folium.Map(location=[50, 30], zoom_start=4, tiles=tiles, attr=attr)

    # Load GeoJSON from model's agents
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        posture = getattr(agent, "posture", "Deescalate")
        personality = getattr(agent, "personality", "Unknown")
        color = get_region_hex_color(rid)
        opacity = ESCALATION_OPACITY.get(posture, 0.3)

        # Get influence data
        net_inf = 0.0
        if model.influence_map:
            net_inf = model.influence_map.get_net_influence(rid, agent.unique_id)

        # Economic data if available
        econ_info = ""
        if hasattr(model, "trade_network") and model.trade_network is not None:
            gdp = model.trade_network.get_gdp(agent.unique_id)
            trade = model.trade_network.get_trade_balance(agent.unique_id)
            econ_info = f"GDP: {gdp:.2f}<br>Trade Bal: {trade:.2f}<br>"

        # Escalation level if available
        esc_info = ""
        if hasattr(model, "escalation_ladder") and model.escalation_ladder is not None:
            level_name = model.escalation_ladder.get_level_name(agent.unique_id)
            esc_info = f"Escalation: {level_name}<br>"

        popup_html = f"""
        <b>{rid.upper()}</b><br>
        Posture: <b>{posture}</b><br>
        Personality: {personality}<br>
        Net Influence: {net_inf:.2f}<br>
        Military: {agent.capabilities.get("military", 0):.2f}<br>
        Economic: {agent.capabilities.get("economic", 0):.2f}<br>
        {econ_info}{esc_info}
        """

        geojson = json.loads(json.dumps(agent.geometry.__geo_interface__))
        folium.GeoJson(
            geojson,
            style_function=lambda x, c=color, o=opacity: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": o,
            },
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=rid.upper(),
        ).add_to(m)

    m.save(str(output_path))
    return str(output_path)


def create_alliance_map(
    model: GeopolModel,
    output_path: str | Path = "alliance_map.html",
    basemap: str = "satellite",
) -> str:
    """Create a map showing alliance relationships as edge overlays.

    Parameters
    ----------
    model:
        The active GeopolModel.
    output_path:
        Where to save the HTML file.
    basemap:
        Basemap style: "satellite", "streets", "topo", "light", "dark", "osm".
        Default: "satellite".

    Returns
    -------
    str
        Path to the saved HTML file.
    """
    output_path = Path(output_path)
    tiles = BASEMAP_TILES.get(basemap, BASEMAP_TILES["satellite"])
    attr = None
    if basemap in ("satellite", "streets", "topo"):
        attr = "Esri"
    m = folium.Map(location=[50, 30], zoom_start=4, tiles=tiles, attr=attr)

    # Add region polygons
    centroids = {}
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        color = get_region_hex_color(rid)
        centroid = agent.geometry.centroid
        centroids[agent.unique_id] = (centroid.y, centroid.x)

        geojson = json.loads(json.dumps(agent.geometry.__geo_interface__))
        folium.GeoJson(
            geojson,
            style_function=lambda x, c=color: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": 0.3,
            },
            tooltip=rid.upper(),
        ).add_to(m)

    # Add alliance/rivalry edges
    for u, v, data in model.relations.graph.edges(data=True):
        weight = data.get("weight", 0.0)
        if u in centroids and v in centroids:
            color = "#4CAF50" if weight > 0.5 else "#F44336" if weight < -0.3 else "#9E9E9E"
            folium.PolyLine(
                [centroids[u], centroids[v]],
                color=color,
                weight=3,
                opacity=0.7,
                tooltip=f"Weight: {weight:.1f}",
            ).add_to(m)

    m.save(str(output_path))
    return str(output_path)
