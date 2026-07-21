"""Tests for military AI modules (autonomous systems, electronic warfare, occupations, operations research)."""

from unittest.mock import MagicMock

from shapely.geometry import Point

from strategify.military.autonomous_systems import (
    AutonomousSystem,
    AutonomyLevel,
    DroneType,
    ISRPlatform,
    MissionStatus,
    UAVSwarm,
    Waypoint,
)
from strategify.military.electronic_warfare import (
    ElectromagneticEffect,
    ElectronicWarfareSystem,
    EMSpectrumManager,
    JammingTechnique,
    OperationStatus,
)
from strategify.military.occupations import (
    MilitaryOccupation,
    OccupationCategory,
    PersonnelManagement,
    PersonnelRecord,
    SkillRequirement,
)
from strategify.military.operations_research import (
    AllocationScenario,
    ConflictPredictor,
    ForceAllocationOptimizer,
    WarGamingEngine,
)


class TestAutonomousSystems:
    """Tests for autonomous systems module."""

    def test_autonomous_system_init(self):
        system = AutonomousSystem(
            system_id="drone_1",
            drone_type=DroneType.ISR,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            location=Point(0, 0),
        )
        assert system.system_id == "drone_1"
        assert system.drone_type == DroneType.ISR
        assert system.autonomy_level == AutonomyLevel.AUTONOMOUS
        assert system.battery == 1.0
        assert system.mission_status == MissionStatus.PENDING

    def test_plan_patrol_route(self):
        system = AutonomousSystem(
            system_id="drone_1",
            drone_type=DroneType.ISR,
            autonomy_level=AutonomyLevel.SUPERVISED,
            location=Point(0, 0),
        )
        mock_model = MagicMock()
        mock_agent = MagicMock()
        mock_agent.geometry.centroid = Point(10, 10)
        mock_model.get_agent_by_region.return_value = mock_agent

        route = system.plan_patrol_route(["region_1"], mock_model)
        assert len(route) == 1
        assert route[0].location == Point(10, 10)
        assert route[0].action == "patrol"

    def test_execute_mission(self):
        system = AutonomousSystem(
            system_id="drone_1",
            drone_type=DroneType.ISR,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            location=Point(0, 0),
            mission_waypoints=[Waypoint(location=Point(100, 0))],
        )
        result = system.execute_mission(dt=60.0)
        assert result["status"] == MissionStatus.PENDING.value
        assert system.mission_status == MissionStatus.ACTIVE

    def test_scan_area(self):
        system = AutonomousSystem(
            system_id="drone_1",
            drone_type=DroneType.ISR,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            location=Point(0, 0),
            sensor_range=50000.0,
        )
        mock_model = MagicMock()
        mock_region_agent = MagicMock()
        mock_region_agent.geometry.centroid = Point(100, 100)
        mock_model.get_agent_by_region.return_value = mock_region_agent

        mock_military_agent = MagicMock()
        mock_unit = MagicMock()
        mock_unit.unit_id = "u1"
        mock_unit.unit_type.value = "Infantry"
        mock_unit.location = Point(200, 200)
        mock_military_agent.military.units = [mock_unit]
        mock_model.schedule.agents = [mock_military_agent]

        scan_res = system.scan_area("region_1", mock_model)
        assert scan_res["target_region"] == "region_1"
        assert len(scan_res["detections"]) == 1
        assert scan_res["detections"][0]["unit_id"] == "u1"

    def test_isr_platform(self):
        system = AutonomousSystem(
            system_id="drone_1",
            drone_type=DroneType.ISR,
            autonomy_level=AutonomyLevel.AUTONOMOUS,
            location=Point(0, 0),
        )
        isr = ISRPlatform(system)
        mock_model = MagicMock()
        mock_model.schedule.steps = 5
        mock_agent = MagicMock()
        mock_agent.geometry.centroid = Point(10, 10)
        mock_agent.geometry.bounds = (0, 0, 20, 20)
        mock_model.get_agent_by_region.return_value = mock_agent
        mock_model.schedule.agents = []

        intel = isr.perform_reconnaissance("region_1", mock_model)
        assert intel["region"] == "region_1"
        assert intel["timestamp"] == 5

        waypoints = isr.optimize_patrol_pattern(["region_1"], mock_model, pattern_type="lawnmower")
        assert len(waypoints) > 0

    def test_uav_swarm(self):
        drone1 = AutonomousSystem("d1", DroneType.ISR, AutonomyLevel.AUTONOMOUS, Point(0, 0))
        drone2 = AutonomousSystem("d2", DroneType.COMBAT, AutonomyLevel.AUTONOMOUS, Point(10, 10))
        swarm = UAVSwarm("swarm_1")
        swarm.add_platform(drone1)
        swarm.add_platform(drone2)

        assert len(swarm.platforms) == 2
        formation = swarm.form_formation("line")
        assert formation["formation"] == "line"

        health = swarm.network_health()
        assert health["platforms"] == 2


class TestElectronicWarfare:
    """Tests for electronic warfare module."""

    def test_ew_system_init(self):
        system = ElectronicWarfareSystem(owner_id="USA")
        assert system.owner_id == "USA"
        assert system.jamming_capability == 0.5
        assert system.emission_control is False

    def test_perform_jamming(self):
        system = ElectronicWarfareSystem(owner_id="USA")
        effect = system.perform_jamming(
            target_id="Russia",
            technique=JammingTechnique.NOISE,
            target_frequency=300.0,
            duration=300.0,
        )
        assert isinstance(effect, ElectromagneticEffect)
        assert effect.target_id == "Russia"
        assert effect.frequency_mhz == 300.0
        assert effect.status in [OperationStatus.ACTIVE, OperationStatus.SUCCESS, OperationStatus.PLANNING]

    def test_activate_ecm_and_pulse(self):
        system = ElectronicWarfareSystem(owner_id="USA")
        ecm = system.activate_ecm("radar")
        assert ecm["ecm_activated"] is True

        pulse = system.emit_pulse(power=1000.0, frequency=400.0)
        assert pulse["success"] is True

        system.step(dt=10.0)

    def test_em_spectrum_manager(self):
        manager = EMSpectrumManager(owner_id="USA")
        alloc = manager.allocate_frequency("radar_1", 400.0, 10.0)
        assert alloc["allocated"] is True

        signal = manager.detect_signal("unknown_source", 250.0, 0.8)
        assert signal["source_id"] == "unknown_source"


class TestMilitaryOccupations:
    """Tests for military occupations module."""

    def test_military_occupation_init(self):
        skill = SkillRequirement("cyber_defense", 0.8, 100)
        occ = MilitaryOccupation(
            occupation_id="occ_cyber",
            name="Cyber Specialist",
            soc_code="55-4010",
            category=OccupationCategory.CYBER,
            skills=[skill],
            training_duration_months=6,
            clearance_level=3,
        )
        assert occ.soc_code == "55-4010"
        assert "cyber_defense" in occ.get_skill_names()

    def test_personnel_management(self):
        pm = PersonnelManagement(unit_id="USA_UNIT")
        rec = PersonnelRecord(
            personnel_id="p1",
            name="John Doe",
            rank="Captain",
            branch="Army",
            occupation=None,
            skills={"analysis": 0.9, "research": 0.8, "reporting": 0.7, "language": 0.6},
            clearance_level=4,
        )
        pm.add_personnel(rec)
        assert len(pm.personnel) == 1

        assigned = pm.assign_occupation("p1", "55-2030")
        assert assigned is True

        avail = pm.get_available_for_assignment("55-2030")
        assert len(avail) >= 0


class TestOperationsResearch:
    """Tests for operations research module."""

    def test_force_allocation_optimizer(self):
        optimizer = ForceAllocationOptimizer(num_theaters=2)
        threat_levels = {"region_east": 0.8, "region_west": 0.3}
        target_regions = ["region_east", "region_west"]

        scenarios = optimizer.optimize(threat_levels, target_regions, max_iterations=5)
        assert len(scenarios) > 0
        assert isinstance(scenarios[0], AllocationScenario)

    def test_conflict_predictor(self):
        predictor = ConflictPredictor()
        prediction = predictor.predict(
            attacker_power=80.0,
            defender_power=50.0,
            attacker_posture="Invade",
            defender_posture="Neutral",
            relation_score=-0.6,
        )
        assert "likelihood" in prediction
        assert 0.0 <= prediction["likelihood"] <= 1.0

    def test_war_gaming_engine(self):
        engine = WarGamingEngine(num_simulations=5)
        res = engine.simulate_campaign(attacker_power=80.0, defender_power=50.0)
        assert "attacker_win_rate" in res
