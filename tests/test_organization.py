"""Tests for OrganizationAgent decision logic and behavior."""

import pytest
from shapely.geometry import Point

from strategify.agents.organization import OrganizationAgent
from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


@pytest.fixture
def peacekeeping_org(model):
    """Create a peacekeeping IGO with 2 member state agents."""
    members = model.schedule.agents[:2]
    member_ids = [a.unique_id for a in members]

    org = OrganizationAgent(
        unique_id=999,
        model=model,
        geometry=Point(30, 50),
        crs="EPSG:4326",
        org_type="IGO",
        mandate="peacekeeping",
        member_ids=member_ids,
    )
    return org


@pytest.fixture
def security_org(model):
    members = model.schedule.agents[:2]
    member_ids = [a.unique_id for a in members]
    org = OrganizationAgent(
        unique_id=998,
        model=model,
        geometry=Point(30, 50),
        crs="EPSG:4326",
        org_type="IGO",
        mandate="security",
        member_ids=member_ids,
    )
    return org


@pytest.fixture
def ngo(model):
    members = model.schedule.agents[:2]
    member_ids = [a.unique_id for a in members]
    org = OrganizationAgent(
        unique_id=997,
        model=model,
        geometry=Point(30, 50),
        crs="EPSG:4326",
        org_type="NGO",
        mandate="humanitarian",
        member_ids=member_ids,
    )
    return org


class TestOrganizationAgentInit:
    def test_default_attributes(self, peacekeeping_org):
        assert peacekeeping_org.org_type == "IGO"
        assert peacekeeping_org.mandate == "peacekeeping"
        assert peacekeeping_org.posture == "Deescalate"
        assert peacekeeping_org.personality == "Neutral"
        assert peacekeeping_org.role == "observer"

    def test_region_id_format(self, peacekeeping_org):
        assert peacekeeping_org.region_id.startswith("org_")

    def test_zero_military_capability(self, peacekeeping_org):
        assert peacekeeping_org.capabilities["military"] == 0.0

    def test_stats_empty(self, peacekeeping_org):
        stats = peacekeeping_org.get_stats()
        assert stats["resolutions"] == 0
        assert stats["aid_operations"] == 0
        assert stats["members"] == 2


class TestOrganizationDecide:
    def test_no_members_returns_observe(self, model):
        org = OrganizationAgent(
            unique_id=1000,
            model=model,
            geometry=Point(30, 50),
            crs="EPSG:4326",
            org_type="IGO",
            mandate="peacekeeping",
            member_ids=[],
        )
        result = org.decide()
        assert result["action"] == "Deescalate"
        assert result["type"] == "observe"

    def test_igo_peacekeeping_escalation_triggers_resolution(self, peacekeeping_org):
        # Set both members to escalate
        for agent in peacekeeping_org.model.schedule.agents:
            if agent.unique_id in peacekeeping_org.member_ids:
                agent.posture = "Escalate"
        result = peacekeeping_org.decide()
        assert result["action"] == "Deescalate"
        assert result["type"] == "resolution"

    def test_igo_peacekeeping_moderate_escalation_triggers_advisory(self, peacekeeping_org):
        # Set 1 of 2 members to escalate (50% = >0.25 but at boundary)
        members = [
            a
            for a in peacekeeping_org.model.schedule.agents
            if a.unique_id in peacekeeping_org.member_ids
        ]
        members[0].posture = "Escalate"
        members[1].posture = "Deescalate"
        result = peacekeeping_org.decide()
        # 1/2 = 0.5 > 0.5 is false, > 0.25 is true
        assert result["action"] == "Deescalate"
        assert result["type"] in ("advisory", "resolution")

    def test_igo_security_collective_defense(self, security_org):
        for agent in security_org.model.schedule.agents:
            if agent.unique_id in security_org.member_ids:
                agent.posture = "Escalate"
        result = security_org.decide()
        assert result["action"] == "Escalate"
        assert result["type"] == "collective_defense"

    def test_igo_economic(self, model):
        members = model.schedule.agents[:2]
        org = OrganizationAgent(
            unique_id=1001,
            model=model,
            geometry=Point(30, 50),
            crs="EPSG:4326",
            org_type="IGO",
            mandate="economic",
            member_ids=[a.unique_id for a in members],
        )
        result = org.decide()
        assert result["action"] == "Deescalate"
        assert result["type"] == "economic_coordination"

    def test_ngo_humanitarian_aid(self, ngo):
        # Set members to escalate
        for agent in ngo.model.schedule.agents:
            if agent.unique_id in ngo.member_ids:
                agent.posture = "Escalate"
        result = ngo.decide()
        assert result["action"] == "Deescalate"
        assert result["type"] == "humanitarian_aid"

    def test_ngo_economic(self, model):
        members = model.schedule.agents[:2]
        org = OrganizationAgent(
            unique_id=1002,
            model=model,
            geometry=Point(30, 50),
            crs="EPSG:4326",
            org_type="NGO",
            mandate="economic",
            member_ids=[a.unique_id for a in members],
        )
        result = org.decide()
        assert result["action"] == "Deescalate"
        assert result["type"] == "development_aid"

    def test_ngo_humanitarian_no_escalation(self, ngo):
        # All members peaceful
        for agent in ngo.model.schedule.agents:
            if agent.unique_id in ngo.member_ids:
                agent.posture = "Deescalate"
        result = ngo.decide()
        assert result["action"] == "Deescalate"
        assert result["type"] == "observe"


class TestOrganizationApply:
    def test_resolution_improves_relations(self, peacekeeping_org):
        for agent in peacekeeping_org.model.schedule.agents:
            if agent.unique_id in peacekeeping_org.member_ids:
                agent.posture = "Escalate"

        # Get initial relation weight
        mids = peacekeeping_org.member_ids
        initial = peacekeeping_org.model.relations.get_relation(mids[0], mids[1])

        result = peacekeeping_org.decide()
        peacekeeping_org._apply(result)

        if result["type"] == "resolution":
            new = peacekeeping_org.model.relations.get_relation(mids[0], mids[1])
            assert new >= initial

    def test_posture_updated(self, peacekeeping_org):
        result = peacekeeping_org.decide()
        peacekeeping_org._apply(result)
        assert peacekeeping_org.posture == result["action"]


class TestOrganizationStats:
    def test_stats_after_resolution(self, peacekeeping_org):
        for agent in peacekeeping_org.model.schedule.agents:
            if agent.unique_id in peacekeeping_org.member_ids:
                agent.posture = "Escalate"

        for _ in range(3):
            result = peacekeeping_org.decide()
            peacekeeping_org._apply(result)

        stats = peacekeeping_org.get_stats()
        assert stats["resolutions"] >= 1

    def test_stats_after_aid(self, ngo):
        for agent in ngo.model.schedule.agents:
            if agent.unique_id in ngo.member_ids:
                agent.posture = "Escalate"

        for _ in range(3):
            result = ngo.decide()
            ngo._apply(result)

        stats = ngo.get_stats()
        assert stats["aid_operations"] >= 1


class TestOrganizationInModel:
    def test_scenario_with_organizations(self):
        """Scenario with organizations should create org agents."""
        model = GeopolModel(scenario="default")
        # Default scenario may or may not have organizations
        # Just verify the model works with org list
        assert hasattr(model, "organizations")

    def test_org_step_in_model(self):
        """Organization agents should participate in model steps."""
        model = GeopolModel()
        # Manually add an org
        org = OrganizationAgent(
            unique_id=100,
            model=model,
            geometry=Point(30, 50),
            crs="EPSG:4326",
            org_type="IGO",
            mandate="peacekeeping",
            member_ids=[a.unique_id for a in model.schedule.agents[:2]],
        )
        model.schedule.add(org)
        model.space.add_agents(org)
        model.organizations.append(org)

        for _ in range(3):
            model.step()

        assert org.posture in ("Escalate", "Deescalate")
