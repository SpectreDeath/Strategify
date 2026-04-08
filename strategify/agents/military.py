"""Military units and logistics management.

This module defines the Unit class for physical assets and the MilitaryComponent
that attaches to agents to manage their combat capabilities and logistics.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from shapely.geometry import Point

if TYPE_CHECKING:
    from strategify.agents.state_actor import StateActorAgent

logger = logging.getLogger(__name__)


class UnitType(Enum):
    """Types of military units with different attributes."""

    Infantry = "Infantry"
    Armor = "Armor"
    Air = "Air"


class Unit:
    """A physical military asset on the map.

    Attributes
    ----------
    unit_id : str
        Unique identifier for the unit.
    owner : StateActorAgent
        The agent that owns this unit.
    unit_type : UnitType
        The type of unit.
    strength : float
        Current combat strength [0.0, 1.0].
    readiness : float
        Current combat readiness [0.0, 1.0].
    location : Point
        Current geospatial location.
    base_location : Point
        The home base or supply hub for this unit.
    """

    def __init__(
        self,
        unit_id: str,
        owner: StateActorAgent,
        unit_type: UnitType,
        location: Point,
    ) -> None:
        self.unit_id = unit_id
        self.owner = owner
        self.unit_type = unit_type
        self.location = location
        self.base_location = location

        self.strength = 1.0
        self.readiness = 1.0

        # Constants based on type
        self.max_range = self._get_max_range()
        self.combat_multiplier = self._get_combat_multiplier()

    def _get_max_range(self) -> float:
        """Return max movement/attack range in meters (CRS EPSG:3857)."""
        ranges = {
            UnitType.Infantry: 50_000.0,  # 50km
            UnitType.Armor: 150_000.0,  # 150km
            UnitType.Air: 500_000.0,  # 500km
        }
        return ranges[self.unit_type]

    def _get_combat_multiplier(self) -> float:
        """Return base combat power multiplier."""
        multipliers = {
            UnitType.Infantry: 1.0,
            UnitType.Armor: 2.5,
            UnitType.Air: 5.0,
        }
        return multipliers[self.unit_type]

    def move_to(self, new_location: Point) -> None:
        """Move the unit to a new location, consuming readiness."""
        dist = self.location.distance(new_location)
        cost = (dist / self.max_range) * 0.2  # Up to 20% readiness loss
        self.readiness = max(0.0, self.readiness - cost)
        self.location = new_location

    def __repr__(self) -> str:
        utype = self.unit_type.value
        return f"<Unit {self.unit_id} ({utype}) S:{self.strength:.2f} R:{self.readiness:.2f}>"


class LogisticsManager:
    """Manages supply lines and readiness recovery for an agent's units.

    Parameters
    ----------
    owner : StateActorAgent
        The agent that owns this manager.
    """

    def __init__(self, owner: StateActorAgent) -> None:
        self.owner = owner
        self.supply_hubs: list[Point] = [owner.geometry.centroid]
        self.efficiency: float = 1.0

    def calculate_supply_quality(self, unit: Unit) -> float:
        """Calculate supply quality [0, 1] for a unit based on hub distance."""
        min_dist = min(unit.location.distance(hub) for hub in self.supply_hubs)
        # Supply drops off after 200km
        max_supply_dist = 200_000.0
        quality = max(0.0, 1.0 - (min_dist / max_supply_dist))
        return quality * self.efficiency

    def update(self) -> None:
        """Recover readiness for all owned units based on supply quality."""
        for unit in self.owner.military.units:
            quality = self.calculate_supply_quality(unit)
            # Recover 5% readiness per step if utility is 1.0
            recovery = 0.05 * quality
            unit.readiness = min(1.0, unit.readiness + recovery)


class MilitaryComponent:
    """Attached to a StateActorAgent to manage its military capabilities.

    Parameters
    ----------
    owner : StateActorAgent
        The agent that owns this component.
    """

    def __init__(self, owner: StateActorAgent) -> None:
        self.owner = owner
        self.units: list[Unit] = []
        self.logistics = LogisticsManager(owner)

    def add_unit(self, unit_type: UnitType, location: Point | None = None) -> Unit:
        """Spawn a new unit for the agent."""
        if location is None:
            location = self.owner.geometry.centroid

        unit_id = f"{self.owner.region_id}_{len(self.units)}"
        unit = Unit(unit_id, self.owner, unit_type, location)
        self.units.append(unit)
        return unit

    def get_total_power(self) -> float:
        """Return aggregate combat power of all units."""
        return sum(u.strength * u.readiness * u.combat_multiplier for u in self.units)

    def step(self) -> None:
        """Step military component: manage logistics and unit lifecycle."""
        self.logistics.update()
