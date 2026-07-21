"""Autonomous systems and drone/ISR asset management.

This module provides:
- AutonomousSystem: Drone management with autonomy levels
- ISRPlatform: Intelligence, Surveillance, Reconnaissance platforms
- UAVSwarm: Coordinated drone operations

SOC Codes: 55-3010 (Unmanned Aircraft Systems), 55-2030 (ISR)
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from shapely.geometry import Point

if TYPE_CHECKING:
    from typing import Any

logger = logging.getLogger(__name__)


class DroneType(Enum):
    """Types of autonomous platforms."""

    ISR = "ISR"  # Intelligence, Surveillance, Reconnaissance
    COMBAT = "Combat"  # Armed drone
    LOGISTICS = "Logistics"  # Supply/transport


class AutonomyLevel(Enum):
    """Level of autonomous operation."""

    MANUAL = "manual"  # Human-controlled
    SUPERVISED = "supervised"  # Human in the loop
    AUTONOMOUS = "autonomous"  # Fully autonomous


class MissionStatus(Enum):
    """Status of autonomous mission."""

    PENDING = "pending"
    ACTIVE = "active"
    RETURNING = "returning"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class Waypoint:
    """A mission waypoint."""

    location: Point
    dwell_time: float = 0.0
    action: str = "transit"


@dataclass
class AutonomousSystem:
    """A drone or autonomous platform.

    Attributes
    ----------
    system_id : str
        Unique identifier.
    drone_type : DroneType
        Type of drone.
    autonomy_level : AutonomyLevel
        Level of autonomous operation.
    location : Point
        Current location.
    endurance : float
        Flight endurance in hours.
    max_speed : float
        Maximum speed in m/s.
    sensor_range : float
        Sensor detection range in meters.
    mission_status : MissionStatus
        Current mission status.
    mission_waypoints : list[Waypoint]
        Planned waypoints.
    """

    system_id: str
    drone_type: DroneType
    autonomy_level: AutonomyLevel
    location: Point
    endurance: float = 4.0
    max_speed: float = 25.0
    sensor_range: float = 50_000.0
    mission_status: MissionStatus = MissionStatus.PENDING
    mission_waypoints: list[Waypoint] | None = None

    def __post_init__(self) -> None:
        self.battery: float = 1.0
        self.current_waypoint_index: int = 0

    def plan_patrol_route(
        self,
        target_regions: list[str],
        model: Any,
    ) -> list[Waypoint]:
        """Plan a patrol route through target regions.

        Parameters
        ----------
        target_regions : list[str]
            Regions to patrol.
        model : Any
            Simulation model for spatial queries.

        Returns
        -------
        list[Waypoint]
            Planned route.
        """
        waypoints: list[Waypoint] = []

        for region_id in target_regions:
            region_agent = model.get_agent_by_region(region_id)
            if region_agent:
                waypoint = Waypoint(
                    location=region_agent.geometry.centroid,
                    dwell_time=random.uniform(10.0, 30.0),
                    action="patrol",
                )
                waypoints.append(waypoint)

        self.mission_waypoints = waypoints
        return waypoints

    def execute_mission(self, dt: float) -> dict[str, Any]:
        """Execute mission for time step.

        Parameters
        ----------
        dt : float
            Time step in seconds.

        Returns
        -------
        dict
            Mission status and sensor readings.
        """
        result = {
            "status": self.mission_status.value,
            "sensors": [],
            "battery": self.battery,
        }

        if self.mission_status == MissionStatus.PENDING:
            if self.mission_waypoints:
                self.mission_status = MissionStatus.ACTIVE

        elif self.mission_status == MissionStatus.ACTIVE:
            self._move_toward_waypoint(dt)

            if self.current_waypoint_index >= len(self.mission_waypoints or []):
                self.mission_status = MissionStatus.RETURNING

        elif self.mission_status == MissionStatus.RETURNING:
            self.battery -= dt / 3600.0
            if self.battery <= 0.1:
                self.mission_status = MissionStatus.COMPLETE

        elif self.mission_status == MissionStatus.COMPLETE:
            result["status"] = "complete"

        self.battery -= dt / 3600.0 / self.endurance

        return result

    def _move_toward_waypoint(self, dt: float) -> None:
        """Move toward current waypoint."""
        if not self.mission_waypoints:
            return

        if self.current_waypoint_index >= len(self.mission_waypoints):
            return

        target = self.mission_waypoints[self.current_waypoint_index].location
        distance = self.location.distance(target)

        if distance < 1000.0:
            self.current_waypoint_index += 1
            return

        speed = self.max_speed * 0.7
        move_dist = speed * dt

        if move_dist >= distance:
            self.location = target
            self.current_waypoint_index += 1
        else:
            direction = np.array(
                [
                    target.x - self.location.x,
                    target.y - self.location.y,
                ]
            )
            direction = direction / np.linalg.norm(direction)

            new_x = self.location.x + direction[0] * move_dist
            new_y = self.location.y + direction[1] * move_dist
            self.location = Point(new_x, new_y)

    def scan_area(self, target_region_id: str, model: Any) -> dict[str, Any]:
        """Scan an area and return sensor data.

        Parameters
        ----------
        target_region_id : str
            Region to scan.
        model : Any
            Simulation model.

        Returns
        -------
        dict
            Sensor readings.
        """
        region_agent = model.get_agent_by_region(target_region_id)
        if not region_agent:
            return {"detections": [], "coverage": 0.0}

        region_centroid = region_agent.geometry.centroid
        distance_to_target = self.location.distance(region_centroid)

        if distance_to_target > self.sensor_range:
            return {"detections": [], "coverage": 0.1}

        detections: list[dict] = []

        for agent in model.schedule.agents:
            if not hasattr(agent, "military"):
                continue

            for unit in agent.military.units:
                if unit.location.distance(self.location) < self.sensor_range:
                    detection = {
                        "type": "military_unit",
                        "unit_id": unit.unit_id,
                        "unit_type": unit.unit_type.value,
                        "location": (unit.location.x, unit.location.y),
                        "confidence": 0.8 - (distance_to_target / self.sensor_range) * 0.3,
                    }
                    detections.append(detection)

        coverage = min(1.0, 1.0 - (distance_to_target / self.sensor_range))

        return {
            "detections": detections,
            "coverage": coverage,
            "target_region": target_region_id,
        }


class ISRPlatform:
    """Intelligence, Surveillance, Reconnaissance platform.

    Extended capabilities for ISR missions.
    """

    def __init__(self, system: AutonomousSystem) -> None:
        self.system = system
        self.sensor_type: str = "EO/IR"
        self.synthetic_aperture: bool = False
        self.signals_capable: bool = False
        self.collected_intel: list[dict] = []

    def perform_reconnaissance(self, target_region: str, model: Any) -> dict[str, Any]:
        """Perform ISR on a target region.

        Parameters
        ----------
        target_region : str
            Region to recon.
        model : Any
            Simulation model.

        Returns
        -------
        dict
            ISR report.
        """
        scan_result = self.system.scan_area(target_region, model)

        intel = {
            "region": target_region,
            "timestamp": model.schedule.steps,
            "coverage": scan_result["coverage"],
            "detections": scan_result["detections"],
            "platform_id": self.system.system_id,
        }

        self.collected_intel.append(intel)

        return intel

    def optimize_patrol_pattern(
        self,
        regions: list[str],
        model: Any,
        pattern_type: str = "lawnmower",
    ) -> list[Waypoint]:
        """Optimize patrol pattern for coverage.

        Parameters
        ----------
        regions : list[str]
            Target regions.
        model : Any
            Simulation model.
        pattern_type : str
            Pattern type (lawnmower, racetrack, star).

        Returns
        -------
        list[Waypoint]
            Optimized waypoints.
        """
        waypoints: list[Waypoint] = []

        for region_id in regions:
            region_agent = model.get_agent_by_region(region_id)
            if not region_agent:
                continue

            bounds = region_agent.geometry.bounds

            if pattern_type == "lawnmower":
                num_swaths = 3
                for i in range(num_swaths + 1):
                    y = bounds[1] + (bounds[3] - bounds[1]) * i / num_swaths
                    x = bounds[0] if i % 2 == 0 else bounds[2]
                    waypoints.append(Waypoint(location=Point(x, y), action="scan"))

            elif pattern_type == "racetrack":
                waypoints.append(Waypoint(location=Point(bounds[0], bounds[1]), action="loiter"))
                waypoints.append(Waypoint(location=Point(bounds[2], bounds[1]), action="loiter"))
                waypoints.append(Waypoint(location=Point(bounds[2], bounds[3]), action="loiter"))
                waypoints.append(Waypoint(location=Point(bounds[0], bounds[3]), action="loiter"))

            else:
                waypoints.append(Waypoint(location=region_agent.geometry.centroid, action="scan"))

        return waypoints


class UAVSwarm:
    """Coordinated UAV swarm operations.

    Attributes
    ----------
    swarm_id : str
        Unique identifier.
    platforms : list[AutonomousSystem]
        UAVs in the swarm.
    swarm_leader : AutonomousSystem
        Lead platform.
    network_id : str
        Network identifier for coordination.
    """

    def __init__(self, swarm_id: str) -> None:
        self.swarm_id = swarm_id
        self.platforms: list[AutonomousSystem] = []
        self.swarm_leader: AutonomousSystem | None = None
        self.network_id: str = f"net_{swarm_id}"

    def add_platform(self, system: AutonomousSystem) -> None:
        """Add a platform to the swarm.

        Parameters
        ----------
        system : AutonomousSystem
            Platform to add.
        """
        self.platforms.append(system)

        if self.swarm_leader is None:
            self.swarm_leader = system

    def form_formation(self, formation_type: str = "line") -> dict[str, Any]:
        """Form a specific swarm formation.

        Parameters
        ----------
        formation_type : str
            Formation type (line, wedge, circle).

        Returns
        -------
        dict
            Formation parameters.
        """
        if not self.swarm_leader or not self.platforms:
            return {"formation": "none", "positions": []}

        leader_pos = self.swarm_leader.location

        positions = []

        if formation_type == "line":
            for i, _platform in enumerate(self.platforms):
                offset = (i - len(self.platforms) / 2) * 5000
                pos = Point(leader_pos.x, leader_pos.y + offset)
                positions.append(pos)

        elif formation_type == "wedge":
            for i, _platform in enumerate(self.platforms):
                offset = i * 5000
                angle = -45 + (90 * i / max(len(self.platforms) - 1, 1))
                pos = Point(
                    leader_pos.x + offset * np.cos(np.radians(angle)),
                    leader_pos.y + offset * np.sin(np.radians(angle)),
                )
                positions.append(pos)

        else:
            radius = 10_000.0
            for i, _platform in enumerate(self.platforms):
                angle = 2 * np.pi * i / len(self.platforms)
                pos = Point(
                    leader_pos.x + radius * np.cos(angle),
                    leader_pos.y + radius * np.sin(angle),
                )
                positions.append(pos)

        for i, platform in enumerate(self.platforms):
            if i < len(positions):
                platform.location = positions[i]

        return {"formation": formation_type, "positions": positions}

    def coordinated_search(
        self,
        search_area: Any,
        model: Any,
    ) -> list[dict[str, Any]]:
        """Perform coordinated search across area.

        Parameters
        ----------
        search_area : Any
            Polygon or region to search.
        model : Any
            Simulation model.

        Returns
        -------
        list[dict]
            Combined sensor results.
        """
        results: list[dict] = []

        for platform in self.platforms:
            if platform.mission_status == MissionStatus.ACTIVE:
                continue

            search_results = platform.scan_area(search_area, model)
            results.append(search_results)

        return results

    def network_health(self) -> dict[str, Any]:
        """Check swarm network health.

        Returns
        -------
        dict
            Network status.
        """
        if not self.platforms:
            return {"status": "disconnected", "platforms": 0}

        active_count = sum(
            1 for p in self.platforms if p.mission_status in (MissionStatus.ACTIVE, MissionStatus.RETURNING)
        )

        battery_levels = [p.battery for p in self.platforms]
        avg_battery = np.mean(battery_levels)

        return {
            "status": "connected" if active_count > len(self.platforms) / 2 else "degraded",
            "platforms": len(self.platforms),
            "active": active_count,
            "avg_battery": avg_battery,
        }
