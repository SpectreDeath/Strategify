"""Spatial reasoning for agent decisions using terrain and location context.

Based on the Geo-Commander framework (Nature 2026) for integrating geospatial
reasoning into military AI decision-making.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class TerrainFeatures:
    """Terrain characteristics for tactical decision-making."""

    defensibility: float
    concealment: float
    mobility: float
    key_terrain: bool
    chokepoint: bool
    elevation_advantage: float


class SpatialReasoningEngine:
    """Engine for integrating spatial reasoning into agent decisions."""

    TERRAIN_CACHE: dict[str, TerrainFeatures] = {}

    @staticmethod
    def get_terrain_features(agent: Any, model: Any) -> TerrainFeatures:
        """Get terrain features for an agent's location."""
        region_id = getattr(agent, "region_id", "unknown")

        if region_id in SpatialReasoningEngine.TERRAIN_CACHE:
            return SpatialReasoningEngine.TERRAIN_CACHE[region_id]

        terrain = TerrainFeatures(
            defensibility=0.5,
            concealment=0.5,
            mobility=0.5,
            key_terrain=False,
            chokepoint=False,
            elevation_advantage=0.0,
        )

        agent_geom = getattr(agent, "geometry", None)
        if agent_geom and hasattr(model, "adjacency"):
            neighbors = model.adjacency.get(region_id, [])
            terrain.concealment = min(1.0, len(neighbors) * 0.15)
            terrain.defensibility = 0.6 if len(neighbors) < 3 else 0.4
            terrain.mobility = 0.7 if len(neighbors) > 2 else 0.3

        SpatialReasoningEngine.TERRAIN_CACHE[region_id] = terrain
        return terrain

    @staticmethod
    def calculate_tactical_advantage(
        agent: Any,
        target: Any,
        model: Any,
    ) -> dict[str, float]:
        """Calculate tactical advantage for an action against a target."""
        agent_terrain = SpatialReasoningEngine.get_terrain_features(agent, model)
        target_terrain = SpatialReasoningEngine.get_terrain_features(target, model)

        advantage = {
            "position_score": 0.5,
            "flanking_score": 0.5,
            "defensive_bonus": 0.0,
            "exposure_score": 0.5,
        }

        if agent_terrain.key_terrain:
            advantage["defensive_bonus"] += 0.2
        if agent_terrain.elevation_advantage > target_terrain.elevation_advantage:
            advantage["position_score"] += 0.15
        if agent_terrain.concealment > target_terrain.concealment:
            advantage["exposure_score"] -= 0.1
        if target_terrain.chokepoint:
            advantage["position_score"] += 0.1
            advantage["flanking_score"] = 0.7

        return advantage

    @staticmethod
    def recommend_position(
        current_position: str,
        target_position: str,
        model: Any,
    ) -> dict[str, Any]:
        """Recommend optimal position for engagement."""
        current_neighbors = model.adjacency.get(current_position, [])
        target_neighbors = model.adjacency.get(target_position, [])

        options = []

        for neighbor in current_neighbors:
            neighbor_terrain = SpatialReasoningEngine.TERRAIN_CACHE.get(
                neighbor,
                TerrainFeatures(0.5, 0.5, 0.5, False, False, 0.0),
            )
            options.append(
                {
                    "position": neighbor,
                    "defensibility": neighbor_terrain.defensibility,
                    "concealment": neighbor_terrain.concealment,
                    "score": neighbor_terrain.defensibility * 0.4 + neighbor_terrain.concealment * 0.3,
                }
            )

        if not options:
            return {"recommended": current_position, "reason": "No better options available"}

        best = max(options, key=lambda x: x["score"])
        return {"recommended": best["position"], "score": best["score"], "alternatives": options}


def integrate_spatial_reasoning(
    agent: Any,
    model: Any,
    base_decision: dict[str, Any],
) -> dict[str, Any]:
    """Integrate spatial reasoning into agent decision-making.

    This function modifies a base decision by incorporating terrain and
    positional factors based on the Geo-Commander framework.
    """
    if not hasattr(agent, "region_id"):
        return base_decision

    engine = SpatialReasoningEngine

    target_region = getattr(agent, "target_region", None)
    if target_region:
        target_agent = model.get_agent_by_region(target_region)
        if target_agent:
            tactical = engine.calculate_tactical_advantage(agent, target_agent, model)

            if tactical["position_score"] > 0.6:
                base_decision["position_bonus"] = tactical["position_score"] - 0.5

            if tactical["flanking_score"] > 0.6:
                base_decision["recommended_action"] = "flank"
                base_decision["reason"] = "Flanking opportunity detected"

            base_decision["tactical_advantage"] = tactical

    return base_decision
