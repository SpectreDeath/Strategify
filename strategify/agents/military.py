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

        # Phase 12: Missions
        self.mission: str = "Patrol"
        self.target_region: str | None = None
        self.target_location: Point | None = None

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
        if dist < 1.0:  # Already there
            return
        cost = (dist / self.max_range) * 0.2  # Up to 20% readiness loss
        self.readiness = max(0.0, self.readiness - cost)
        self.location = new_location

    def step_mission(self) -> None:
        """Progress the unit's current mission (Movement towards target)."""
        if self.mission == "HitAndRun":
            # Dynamic target generation
            self._execute_hit_and_run_logic()

        if self.mission == "Withdraw":
            target = self.base_location
        elif self.mission == "Peacekeeping":
            # Move towards the target region's centroid
            if self.target_region:
                target_agent = self.owner.model.get_agent_by_region(self.target_region)
                if target_agent:
                    target = target_agent.geometry.centroid
                else:
                    return
            elif self.target_location:
                target = self.target_location
            else:
                return
        elif self.target_location:
            target = self.target_location
        else:
            return

        dist = self.location.distance(target)
        if dist <= 1000.0:  # Close enough
            if self.mission == "Withdraw":
                self.mission = "Patrol"
            return
        
    def _execute_hit_and_run_logic(self) -> None:
        """Find a neighbor region and set it as target for escape."""
        try:
            # Find current region ID
            current_rid = "unknown"
            from strategify.agents.state_actor import StateActorAgent
            if isinstance(self.owner, StateActorAgent):
                current_rid = self.owner.region_id
            else:
                # Find region this unit is currently in
                for agent in self.owner.model.schedule.agents:
                    if isinstance(agent, StateActorAgent) and agent.geometry.intersects(self.location):
                        current_rid = agent.region_id
                        break
                
                # Fallback if spatial lookup fails but target_region is set
                if current_rid == "unknown" and hasattr(self.owner, "target_region"):
                    current_rid = getattr(self.owner, "target_region")
            
            # Use pre-calculated adjacency
            neighbor_rids = self.owner.model.adjacency.get(current_rid, [])
            if neighbor_rids:
                target_rid = self.owner.model.random.choice(neighbor_rids)
                target_agent = self.owner.model.get_agent_by_region(target_rid)
                if target_agent:
                    self.target_location = target_agent.geometry.centroid
                    if hasattr(self.owner, "target_region"):
                        self.owner.target_region = target_rid
                else:
                    logger.error("DEBUG: Neighbor %s not found in registry.", target_rid)
        except Exception as e:
            logger.error("Error in HitAndRun move: %s", e)
            pass

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

    def get_total_power(self, region_id: str | None = None) -> float:
        """Return aggregate combat power of all units, optionally filtered by region."""
        power = 0.0
        for u in self.units:
            if region_id is not None:
                # Approximate check: is unit within the region geometry?
                # (O(N) geom check, use sparingly)
                agent = self.owner.model.get_agent_by_region(region_id)
                if agent and not agent.geometry.contains(u.location):
                    continue
            power += u.strength * u.readiness * u.combat_multiplier
        return power

    def step(self) -> None:
        """Step military component: manage logistics and unit lifecycle."""
        self.logistics.update()
        for unit in self.units:
            unit.step_mission()

    def get_peacekeeping_strength(self, region_id: str) -> float:
        """Return total strength of units on peacekeeping missions in a region."""
        strength = 0.0
        for u in self.units:
            if u.mission == "Peacekeeping":
                # Check if unit is actually in the region
                agent = self.owner.model.get_agent_by_region(region_id)
                if agent and agent.geometry.contains(u.location):
                    strength += u.strength * u.readiness
        return strength
