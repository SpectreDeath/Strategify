"""Health engine for global pandemic and biological resilience modeling.

This module simulates the spread of pathogens via trade links and spatial
proximity, and its impact on regional productivity and stability.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)


class HealthEngine:
    """Manages global health crises and pandemic spread.

    Parameters
    ----------
    model : GeopolModel
        The parent model.
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        # infectivity[region_id] = [0.0, 1.0]
        self.infection_rates: dict[str, float] = {}
        self.hospital_capacity: dict[str, float] = {}
        self.base_recovery_rate = 0.05
        self.base_infection_gradient = 0.1

    def initialize(self) -> None:
        """Set initial health states for all regions."""
        for agent in self.model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            if rid != "unknown":
                self.infection_rates[rid] = 0.0
                self.hospital_capacity[rid] = 1.0  # Normalized [0, 1]

    def step(self) -> None:
        """Calculate step-wise contagion and mortality."""
        new_rates = self.infection_rates.copy()

        # 1. Spatial Contagion (Neighbors)
        for rid, rate in self.infection_rates.items():
            if rate > 0.01:
                # Spread to neighbors
                agent = next(
                    (a for a in self.model.schedule.agents if getattr(a, "region_id", "") == rid),
                    None,
                )
                if agent:
                    # Get neighbors from Space
                    neighbors = self.model.space.get_neighbors(agent)
                    for n in neighbors:
                        n_id = getattr(n, "region_id", "unknown")
                        if n_id in new_rates:
                            # Contagion factor
                            gradient = rate * self.base_infection_gradient
                            new_rates[n_id] = min(1.0, new_rates[n_id] + gradient)

        # 2. Trade-based Spread (Long distance)
        if self.model.trade_network:
            for rid, rate in self.infection_rates.items():
                if rate > 0.05:
                    # Potential spread to trade partners
                    for partner_id in self.model.trade_network.get_partners(rid):
                        if partner_id in new_rates:
                            new_rates[partner_id] = min(1.0, new_rates[partner_id] + (rate * 0.05))

        # 3. Recovery and Capacity Drain
        for rid in new_rates:
            # Infection reduces if capacity is high
            recovery = self.base_recovery_rate * self.hospital_capacity[rid]
            new_rates[rid] = max(0.0, new_rates[rid] - recovery)

            # Healthcare capacity drains under high load
            if new_rates[rid] > 0.3:
                self.hospital_capacity[rid] = max(0.1, self.hospital_capacity[rid] - 0.01)
            else:
                self.hospital_capacity[rid] = min(1.0, self.hospital_capacity[rid] + 0.005)

        self.infection_rates = new_rates

    def trigger_outbreak(self, region_id: str, intensity: float = 0.2) -> None:
        """Manually trigger a biological event."""
        if region_id in self.infection_rates:
            self.infection_rates[region_id] = intensity
            logger.warning("PANDEMIC OUTBREAK in %s!", region_id)

    def get_productivity_impact(self, region_id: str) -> float:
        """Return economic multiplier [0, 1] due to illness."""
        rate = self.infection_rates.get(region_id, 0.0)
        # Productivity drops exponentially after critical mass
        if rate < 0.1:
            return 1.0
        return max(0.6, 1.0 - (rate - 0.1))
