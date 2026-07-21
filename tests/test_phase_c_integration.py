"""Integration tests for Phase C: Advanced Geospatial & Multi-Domain Simulation."""

from unittest.mock import MagicMock

from shapely.geometry import Point

from strategify.agents.non_state import NonStateActor
from strategify.military.autonomous_systems import (
    AutonomousSystem,
    AutonomyLevel,
    DroneType,
)
from strategify.military.electronic_warfare import (
    EMSpectrumManager,
    calculate_path_loss,
)
from strategify.sim.model import GeopolModel


def test_free_space_path_loss_calculation():
    loss_near = calculate_path_loss(distance_km=1.0, frequency_mhz=300.0)
    loss_far = calculate_path_loss(distance_km=10.0, frequency_mhz=300.0)
    assert loss_far > loss_near
    assert abs(loss_far - loss_near - 20.0) < 1e-3


def test_em_spectrum_manager_signal_attenuation():
    manager = EMSpectrumManager(owner_id="USA")
    sig_close = manager.detect_signal("radar_1", 300.0, 1.0, distance_km=1.0)
    sig_far = manager.detect_signal("radar_2", 300.0, 1.0, distance_km=50.0)

    assert sig_far["strength"] < sig_close["strength"]
    assert sig_far["path_loss_db"] > sig_close["path_loss_db"]


def test_autonomous_scan_area_terrain_concealment():
    drone = AutonomousSystem("d1", DroneType.ISR, AutonomyLevel.AUTONOMOUS, Point(0, 0))
    mock_model = MagicMock()
    mock_region_agent = MagicMock()
    mock_region_agent.region_id = "alpha"
    mock_region_agent.geometry.centroid = Point(10, 10)
    mock_model.get_agent_by_region.return_value = mock_region_agent
    mock_model.adjacency = {"alpha": ["bravo"]}

    mock_military_agent = MagicMock()
    mock_unit = MagicMock()
    mock_unit.unit_id = "u1"
    mock_unit.unit_type.value = "Infantry"
    mock_unit.location = Point(10, 10)
    mock_military_agent.military.units = [mock_unit]
    mock_model.schedule.agents = [mock_military_agent]

    scan_res = drone.scan_area("alpha", mock_model)
    assert scan_res["target_region"] == "alpha"
    assert len(scan_res["detections"]) == 1
    assert "confidence" in scan_res["detections"][0]


def test_non_state_actor_seek_sanctuary():
    model = GeopolModel(enable_non_state_actors=True)
    nsa = NonStateActor(unique_id=999, model=model, geometry=Point(0, 0), crs="EPSG:3857")
    nsa.target_region = "alpha"

    # Set up mock adjacency and target region agent posture
    model.adjacency = {"alpha": ["bravo", "charlie"]}
    state_b = model.get_agent_by_region("bravo")
    if state_b:
        state_b.capabilities["military"] = 0.1

    relocated = nsa.seek_sanctuary()
    assert relocated is True
    assert nsa.target_region in ["bravo", "charlie"]
