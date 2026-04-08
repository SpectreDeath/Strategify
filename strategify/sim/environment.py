"""Environmental manager for resource grids and climate events.

This module tracks Water, Food, and Energy resources per region,
handles depletion/regeneration, and simulates extreme weather events.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)


class EnvironmentalManager:
    """Manages resource abundance and climate shocks.

    Parameters
    ----------
    model : GeopolModel
        The parent model.
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        # resource_grid[region_id] = {"Water": 1.0, "Food": 1.0, "Energy": 1.0}
        self.resource_grid: dict[str, dict[str, float]] = {}
        self.climate_hazard_level: float = 0.05  # Probability of event per step

    def initialize(self) -> None:
        """Initialize resource levels for all regions."""
        for agent in self.model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            if rid != "unknown":
                self.resource_grid[rid] = {
                    "Water": 1.0,
                    "Food": 1.0,
                    "Energy": 1.0,
                }

    def get_climate_event_probability(self) -> float:
        """Get the probability of a climate event in the next step."""
        return self.climate_hazard_level

    def get_expected_impact(self, region_id: str) -> dict[str, float]:
        """Get expected resource impact from climate events for a region.

        Returns
        -------
        dict
            Expected percentage loss per resource type.
        """
        event_probs = {
            "Drought": 1 / 3,
            "Storm": 1 / 3,
            "Heatwave": 1 / 3,
        }
        expected_impact = {"Water": 0.0, "Food": 0.0, "Energy": 0.0}

        for event_type, prob in event_probs.items():
            event_loss_prob = self.climate_hazard_level * prob
            if event_type == "Drought":
                expected_impact["Water"] += event_loss_prob * 0.3  # 30% loss
                expected_impact["Food"] += event_loss_prob * 0.2
            elif event_type == "Storm":
                expected_impact["Energy"] += event_loss_prob * 0.3
            elif event_type == "Heatwave":
                expected_impact["Water"] += event_loss_prob * 0.1
                expected_impact["Energy"] += event_loss_prob * 0.2

        return expected_impact

    def step(self) -> None:
        """Update resource levels and trigger random climate events."""
        for rid, resources in self.resource_grid.items():
            # 1. Natural Regeneration (1% per step)
            for res_type in resources:
                resources[res_type] = min(1.0, resources[res_type] * 1.01)

            # 2. Consumption based on population (if exists)
            if self.model.population_model:
                pop_scale = self.model.population_model.get_population(rid) / 10_000_000.0
                consumption = 0.02 * pop_scale
                resources["Water"] = max(0.0, resources["Water"] - consumption)
                resources["Food"] = max(0.0, resources["Food"] - consumption)

        # 3. Random Climate Events
        if self.model.random.random() < self.climate_hazard_level:
            self._trigger_climate_event()

    def _trigger_climate_event(self) -> None:
        """Trigger a major climate event in a random region."""
        region_ids = list(self.resource_grid.keys())
        if not region_ids:
            return

        target_rid = self.model.random.choice(region_ids)
        event_type = self.model.random.choice(["Drought", "Storm", "Heatwave"])

        logger.warning("CLIMATE EVENT: %s in %s!", event_type, target_rid)

        # Immediate resource hit
        if event_type == "Drought":
            self.resource_grid[target_rid]["Water"] *= 0.7
            self.resource_grid[target_rid]["Food"] *= 0.8
        elif event_type == "Storm":
            self.resource_grid[target_rid]["Energy"] *= 0.7
        elif event_type == "Heatwave":
            self.resource_grid[target_rid]["Water"] *= 0.9
            self.resource_grid[target_rid]["Energy"] *= 0.8

    def get_resource_pressure(self, region_id: str) -> float:
        """Return aggregate resource scarcity [0, 1] for a region."""
        resources = self.resource_grid.get(region_id)
        if not resources:
            return 0.0

        avg_level = sum(resources.values()) / len(resources)
        # Pressure is inverse of abundance
        return max(0.0, 1.0 - avg_level)
