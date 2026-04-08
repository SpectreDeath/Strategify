"""InfluenceMap: spatial reasoning based on agent strength and distance."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from strategify.config.settings import DISTANCE_DECAY_OFFSET
from strategify.geo.adjacency import is_edge_neighbor

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)


class InfluenceMap:
    """Calculates spatial influence across the world map.

    Influence at a region decays with distance from the agent's location.
    Neighbors are filtered to exclude corner-contacts (only shared borders
    via LineString/MultiLineString intersections count as adjacent).
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        self.influence_data: dict[str, dict[int, float]] = {}
        self.contagion_data: dict[str, float] = {}

    def _get_valid_neighbors_with_weights(self, agent) -> list[tuple[Any, float]]:
        """Return neighbors with shared boundary length, excluding corner-contacts."""
        try:
            raw_neighbors = self.model.space.get_neighbors(agent)
        except Exception:
            return []

        weighted_neighbors = []
        for n in raw_neighbors:
            length = is_edge_neighbor(agent.geometry, n.geometry, return_length=True)
            if length > 0:
                weighted_neighbors.append((n, length))
        return weighted_neighbors

    def compute(self) -> None:
        """Calculate influence and contagion with shared-boundary weighting."""
        region_ids = {getattr(a, "region_id", "unknown") for a in self.model.schedule.agents}
        self.influence_data = {rid: {} for rid in region_ids}
        self.contagion_data = {rid: 0.0 for rid in region_ids}

        # 1. Influence from military strength
        # Each agent projects force that decays with BFS distance,
        # but is also enhanced by the 'connectivity' (shared boundary) of the path.
        # For prototype simplicity in Phase 1, we use direct neighbor weights for contagion
        # and standard BFS for distant influence, but we store the weights for future iterations.
        for agent in self.model.schedule.agents:
            uid = agent.unique_id
            strength = agent.capabilities.get("military", 0.5)
            origin = getattr(agent, "region_id", "unknown")

            distances = self._calculate_distances(origin)

            for rid, dist in distances.items():
                decayed = strength / (dist + DISTANCE_DECAY_OFFSET)
                if uid not in self.influence_data[rid]:
                    self.influence_data[rid][uid] = 0.0
                self.influence_data[rid][uid] += decayed

        # 2. Contagion from 'Escalate' postures
        for agent in self.model.schedule.agents:
            if getattr(agent, "posture", "Deescalate") == "Escalate":
                rid = getattr(agent, "region_id", "unknown")
                if rid in self.contagion_data:
                    self.contagion_data[rid] += 1.0

    def get_contagion_level(self, region_id: str) -> float:
        """Return contagion weighted by shared boundary length."""
        agent = next(
            (a for a in self.model.schedule.agents if getattr(a, "region_id", "") == region_id),
            None,
        )
        if not agent:
            return 0.0
        try:
            neighbors = self._get_valid_neighbors_with_weights(agent)
        except Exception:
            logger.debug("Failed to get neighbors for region %s", region_id)
            return 0.0

        # Weighted sum: normalized shared length * neighbor contagion
        total_length = sum(w for _, w in neighbors)
        if total_length == 0:
            return 0.0

        contagion = 0.0
        for n, weight in neighbors:
            n_id = getattr(n, "region_id", "")
            # Shared boundary length in EPSG:3857 (meters) divided by total perimeter
            # provides a realistic 'exposure' metric.
            influence_coeff = weight / total_length
            contagion += self.contagion_data.get(n_id, 0.0) * influence_coeff

        return contagion

    def get_net_influence(self, region_id: str, agent_id: int) -> float:
        """Return net influence for an agent's alliance vs rivals."""
        data = self.influence_data.get(region_id, {})
        allied_ids = set(self.model.relations.get_allies(agent_id))
        allied_ids.add(agent_id)

        allied_inf = sum(data.get(uid, 0.0) for uid in allied_ids)
        total_inf = sum(data.values())
        rival_inf = total_inf - allied_inf

        return allied_inf - rival_inf

    def _calculate_distances(self, origin: str) -> dict[str, int]:
        """BFS to find distance from origin to all reachable regions."""
        agent = next(
            (a for a in self.model.schedule.agents if getattr(a, "region_id", "") == origin),
            None,
        )
        if not agent:
            return {}

        distances = {origin: 0}
        queue = [agent]
        while queue:
            current = queue.pop(0)
            d = distances[getattr(current, "region_id", "")]
            # Neighbors are now tuples of (neighbor_obj, length)
            for neighbor, _ in self._get_valid_neighbors_with_weights(current):
                n_id = getattr(neighbor, "region_id", "")
                if n_id and n_id not in distances:
                    distances[n_id] = d + 1
                    queue.append(neighbor)
        return distances

    def get_spatial_autocorrelation(self) -> dict[str, float]:
        """Compute Moran's I for escalation values across regions.

        Uses libpysal spatial weights and esda.Moran to measure whether
        escalation patterns cluster geographically or disperse.

        Returns
        -------
        dict
            {"I": float, "p_value": float, "z_score": float}
            Returns empty dict if fewer than 3 regions.
        """
        import geopandas as gpd
        import numpy as np
        from esda import Moran
        from libpysal import weights

        # Collect escalation values per region
        region_order = []
        escalation_values = []
        for agent in self.model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            region_order.append(rid)
            escalation_values.append(
                1.0 if getattr(agent, "posture", "Deescalate") == "Escalate" else 0.0
            )

        if len(region_order) < 3:
            return {}

        # Build spatial weights from GeoJSON geometry
        try:
            features = []
            for agent in self.model.schedule.agents:
                rid = getattr(agent, "region_id", "unknown")
                features.append({"region_id": rid, "geometry": agent.geometry})
            gdf = gpd.GeoDataFrame(features)
            w = weights.Queen.from_dataframe(gdf, ids=gdf["region_id"].tolist())
            y = np.array(escalation_values)
            mi = Moran(y, w, two_tailed=False)
            # Moran's I is NaN when all values are identical (zero variance)
            import math

            moran_i = mi.I if not math.isnan(mi.I) else 0.0
            z = mi.z_sim if not math.isnan(mi.z_sim) else 0.0
            return {"I": moran_i, "p_value": mi.p_sim, "z_score": z}
        except (ValueError, TypeError, AttributeError, ImportError):
            return {}
