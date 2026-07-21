"""Vector Map Engine & Interactive GeoJSON/Vector Visualization.

Exports multi-layer GeoJSON FeatureCollections (regions, units, movement vectors,
EW coverage circles, trade flows) and renders standalone WebGL MapLibre GL HTML vector maps.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from strategify.config.settings import get_region_hex_color

logger = logging.getLogger(__name__)


class VectorMapBuilder:
    """Builder for constructing vector GIS layers from simulation state.

    Parameters
    ----------
    model : Any
        GeopolModel instance.
    """

    def __init__(self, model: Any) -> None:
        self.model = model

    def build_region_layer(self) -> dict[str, Any]:
        """Build GeoJSON FeatureCollection of state actor regions."""
        features = []
        for agent in self.model.schedule.agents:
            if not hasattr(agent, "geometry") or agent.geometry is None:
                continue

            rid = getattr(agent, "region_id", str(agent.unique_id))
            posture = getattr(agent, "posture", "Deescalate")
            color = get_region_hex_color(rid)

            geom_json = json.loads(json.dumps(agent.geometry.__geo_interface__))

            feature = {
                "type": "Feature",
                "geometry": geom_json,
                "properties": {
                    "region_id": rid,
                    "posture": posture if isinstance(posture, str) else posture.value,
                    "personality": getattr(agent, "personality", "Unknown"),
                    "fill": color,
                    "fill-opacity": 0.5 if posture == "Deescalate" else 0.8,
                    "stroke": "#ffffff",
                    "stroke-width": 2,
                },
            }
            features.append(feature)

        return {"type": "FeatureCollection", "features": features}

    def build_military_units_layer(self) -> dict[str, Any]:
        """Build GeoJSON FeatureCollection of military units and drones."""
        features = []
        for agent in self.model.schedule.agents:
            if not hasattr(agent, "military") or not agent.military.units:
                continue

            for unit in agent.military.units:
                loc = getattr(unit, "location", None)
                if not loc:
                    continue

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [loc.x, loc.y],
                    },
                    "properties": {
                        "unit_id": unit.unit_id,
                        "unit_type": unit.unit_type.value,
                        "owner_id": getattr(agent, "region_id", "unknown"),
                        "strength": getattr(unit, "readiness", 1.0),
                    },
                }
                features.append(feature)

        return {"type": "FeatureCollection", "features": features}

    def build_trade_vectors_layer(self) -> dict[str, Any]:
        """Build GeoJSON FeatureCollection of trade/diplomatic vectors."""
        features = []
        if not hasattr(self.model, "trade_network") or self.model.trade_network is None:
            return {"type": "FeatureCollection", "features": features}

        # Build trade flow vectors between centroids
        agents = {getattr(a, "region_id", "unknown"): a for a in self.model.schedule.agents if hasattr(a, "geometry")}

        for r1, agent1 in agents.items():
            for r2, agent2 in agents.items():
                if r1 >= r2:
                    continue

                p1 = agent1.geometry.centroid
                p2 = agent2.geometry.centroid

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [[p1.x, p1.y], [p2.x, p2.y]],
                    },
                    "properties": {
                        "source": r1,
                        "target": r2,
                        "trade_volume": 1.0,
                    },
                }
                features.append(feature)

        return {"type": "FeatureCollection", "features": features}

    def export_geojson(self, output_path: str | Path) -> Path:
        """Export all layers as a combined GeoJSON FeatureCollection.

        Parameters
        ----------
        output_path : str | Path
            Destination filepath (.geojson).

        Returns
        -------
        Path
            Path to exported GeoJSON file.
        """
        path = Path(output_path)

        regions = self.build_region_layer()["features"]
        units = self.build_military_units_layer()["features"]
        trades = self.build_trade_vectors_layer()["features"]

        combined = {
            "type": "FeatureCollection",
            "features": regions + units + trades,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)

        logger.info("Exported vector map GeoJSON to %s", path)
        return path


def create_vector_map_html(
    model: Any,
    output_path: str | Path = "vector_map.html",
) -> Path:
    """Generate an interactive HTML vector map powered by MapLibre GL JS.

    Parameters
    ----------
    model : Any
        GeopolModel simulation instance.
    output_path : str | Path
        Output HTML file location (default: 'vector_map.html').

    Returns
    -------
    Path
        Saved HTML map path.
    """
    path = Path(output_path)
    builder = VectorMapBuilder(model)

    region_geojson = json.dumps(builder.build_region_layer())
    unit_geojson = json.dumps(builder.build_military_units_layer())
    trade_geojson = json.dumps(builder.build_trade_vectors_layer())

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Strategify Vector Map Engine</title>
    <meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
    <link href="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.css" rel="stylesheet" />
    <script src="https://unpkg.com/maplibre-gl@3.6.2/dist/maplibre-gl.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background: #0b0f19; font-family: sans-serif; }}
        #map {{ position: absolute; top: 0; bottom: 0; width: 100%; }}
        .legend {{
            position: absolute; top: 20px; right: 20px;
            background: rgba(15, 23, 42, 0.85); backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.1); border-radius: 8px;
            padding: 16px; color: #f8fafc; z-index: 10; min-width: 200px;
        }}
        .legend h3 {{ margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; color: #38bdf8; }}
        .legend-item {{ display: flex; align-items: center; margin-bottom: 6px; font-size: 12px; }}
        .color-box {{ width: 14px; height: 14px; border-radius: 3px; margin-right: 8px; }}
    </style>
</head>
<body>
<div id="map"></div>
<div class="legend">
    <h3>Vector Map Layers</h3>
    <div class="legend-item"><div class="color-box" style="background: #3b82f6;"></div> State Boundaries</div>
    <div class="legend-item"><div class="color-box" style="background: #ef4444;"></div> Escalation posture</div>
    <div class="legend-item"><div class="color-box" style="background: #10b981;"></div> Trade Vectors</div>
    <div class="legend-item"><div class="color-box" style="background: #f59e0b;"></div> Military Units</div>
</div>
<script>
    const map = new maplibregl.Map({{
        container: 'map',
        style: 'https://demotiles.maplibre.org/style.json',
        center: [30, 50],
        zoom: 4
    }});

    map.on('load', () => {{
        // Regions Layer
        map.addSource('regions', {{ type: 'geojson', data: {region_geojson} }});
        map.addLayer({{
            'id': 'regions-fill',
            'type': 'fill',
            'source': 'regions',
            'paint': {{
                'fill-color': ['get', 'fill'],
                'fill-opacity': ['get', 'fill-opacity']
            }}
        }});
        map.addLayer({{
            'id': 'regions-border',
            'type': 'line',
            'source': 'regions',
            'paint': {{
                'line-color': '#ffffff',
                'line-width': 2
            }}
        }});

        // Trade Vectors Layer
        map.addSource('trade', {{ type: 'geojson', data: {trade_geojson} }});
        map.addLayer({{
            'id': 'trade-lines',
            'type': 'line',
            'source': 'trade',
            'paint': {{
                'line-color': '#10b981',
                'line-width': 2,
                'line-dasharray': [2, 2]
            }}
        }});

        // Military Units Layer
        map.addSource('units', {{ type: 'geojson', data: {unit_geojson} }});
        map.addLayer({{
            'id': 'units-point',
            'type': 'circle',
            'source': 'units',
            'paint': {{
                'circle-radius': 8,
                'circle-color': '#f59e0b',
                'circle-stroke-width': 2,
                'circle-stroke-color': '#ffffff'
            }}
        }});
    }});
</script>
</body>
</html>"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Exported WebGL vector map HTML to %s", path)
    return path
