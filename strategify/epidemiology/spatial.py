"""Spatial Epidemic Contagion & Inter-Region Mobility.

Models cross-border virus transmission driven by trade network connections,
spatial proximity, and population mobility across regions.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class GeoEpidemicMap:
    """Manager for inter-region spatial virus transmission across GeopolModel.

    Parameters
    ----------
    model : Any
        The GeopolModel simulation environment.
    """

    def __init__(self, model: Any) -> None:
        self.model = model

    def step_spatial_transmission(self, cross_border_mobility_rate: float = 0.01) -> dict[str, float]:
        """Transmit infections between adjacent regions based on trade and mobility.

        Parameters
        ----------
        cross_border_mobility_rate : float
            Inter-region mobility factor [0.0, 1.0].

        Returns
        -------
        dict
            Dict of exported infections per region.
        """
        if not hasattr(self.model, "adjacency") or not self.model.adjacency:
            return {}

        regional_engines = {}
        for agent in self.model.schedule.agents:
            if hasattr(agent, "seir_engine"):
                rid = getattr(agent, "region_id", str(agent.unique_id))
                regional_engines[rid] = agent.seir_engine

        exported_cases = {}

        for rid, engine in regional_engines.items():
            if engine.infectious < 1.0:
                continue

            neighbors = self.model.adjacency.get(rid, [])
            if not neighbors:
                continue

            # Infections seeded across borders
            border_leak = engine.infectious * cross_border_mobility_rate * (1.0 - getattr(agent, "biodefense", None).status.npi_level if hasattr(agent, "biodefense") else 1.0)
            seed_per_neighbor = border_leak / max(len(neighbors), 1)

            for neighbor_id in neighbors:
                neighbor_engine = regional_engines.get(neighbor_id)
                if neighbor_engine and neighbor_engine.susceptible > seed_per_neighbor:
                    neighbor_engine.susceptible -= seed_per_neighbor
                    neighbor_engine.exposed += seed_per_neighbor
                    exported_cases[neighbor_id] = exported_cases.get(neighbor_id, 0.0) + seed_per_neighbor

        if exported_cases:
            logger.info("Spatial epidemic transmission exported cases across borders: %s", exported_cases)

        return exported_cases
