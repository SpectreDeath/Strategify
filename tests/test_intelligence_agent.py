"""Tests for intelligence agent module."""

import time
from unittest.mock import MagicMock

from strategify.agents.intelligence import (
    CollectionStatus,
    IntelligenceComponent,
    IntelligenceNetwork,
    IntelligenceReport,
    IntelligenceSource,
    ISRTasking,
)


class TestIntelligenceReport:
    """Tests for IntelligenceReport dataclass."""

    def test_report_init(self):
        report = IntelligenceReport(
            report_id="rep_1",
            source=IntelligenceSource.HUMINT,
            target_id="region_A",
            content={"strength": 50},
            reliability=0.9,
            timestamp=time.time(),
        )
        assert report.report_id == "rep_1"
        assert report.source == IntelligenceSource.HUMINT
        assert report.reliability == 0.9
        assert report.is_stale() is False

    def test_reliability_decay(self):
        now = time.time()
        report = IntelligenceReport(
            report_id="rep_1",
            source=IntelligenceSource.SIGINT,
            target_id="region_A",
            content={},
            reliability=0.8,
            timestamp=now - 3600,  # 1 hour ago (1 half-life)
        )
        decayed = report.decay_reliability(3600.0)
        assert abs(decayed - 0.4) < 1e-4

    def test_reliability_cap(self):
        report = IntelligenceReport(
            report_id="rep_2",
            source=IntelligenceSource.IMINT,
            target_id="region_B",
            content={},
            reliability=0.99,  # Should be capped at 0.95
            timestamp=time.time(),
        )
        assert report.reliability == 0.95


class TestISRTasking:
    """Tests for ISRTasking dataclass."""

    def test_tasking_init(self):
        task = ISRTasking(
            task_id="task_1",
            target_region="region_A",
            source=IntelligenceSource.IMINT,
            priority=1,
        )
        assert task.task_id == "task_1"
        assert task.priority == 1
        assert task.status == CollectionStatus.IDLE


class TestIntelligenceComponent:
    """Tests for IntelligenceComponent class."""

    def test_component_init(self):
        mock_agent = MagicMock()
        comp = IntelligenceComponent(mock_agent)
        assert comp.owner == mock_agent
        assert len(comp.reports) == 0
        assert IntelligenceSource.HUMINT in comp.collection_capabilities

    def test_collect_intelligence(self):
        mock_owner = MagicMock()
        mock_model = MagicMock()
        mock_owner.model = mock_model
        mock_owner.unique_id = "USA"

        target_agent = MagicMock()
        target_agent.unique_id = "Russia"
        target_agent.posture = "Hostile"
        target_agent.military.get_total_power.return_value = 100.0
        target_agent.stability = 0.8
        target_agent.capabilities = {"military": 0.9}

        mock_model.get_agent_by_region.return_value = target_agent
        mock_model.relations.get_relation.return_value = -0.5

        comp = IntelligenceComponent(mock_owner)
        report = comp.collect(IntelligenceSource.SIGINT, "region_A")

        assert report is not None
        assert report.target_id == "region_A"
        assert report.content["assessed_posture"] == "Hostile"
        assert report.content["military_strength"] == 100.0
        assert len(comp.reports) == 1

    def test_analyze_and_disseminate(self):
        mock_owner = MagicMock()
        mock_model = MagicMock()
        mock_owner.model = mock_model
        mock_owner.region_id = "USA"
        comp = IntelligenceComponent(mock_owner)

        rep1 = IntelligenceReport(
            report_id="r1",
            source=IntelligenceSource.HUMINT,
            target_id="reg1",
            content={"assessed_posture": "Invade", "relation_score": -0.8},
            reliability=0.8,
            timestamp=time.time(),
        )
        comp.reports.append(rep1)

        analysis = comp.analyze(rep1)
        assert analysis["target"] == "reg1"
        assert len(analysis["warnings"]) > 0

        mock_ally = MagicMock()
        mock_ally_comp = IntelligenceComponent(mock_ally)
        mock_ally.intelligence = mock_ally_comp
        mock_model._agent_registry = {2: mock_ally}

        res = comp.disseminate(rep1, [2])
        assert res is True
        assert len(mock_ally_comp.reports) == 1


class TestIntelligenceNetwork:
    """Tests for IntelligenceNetwork class."""

    def test_network_operations(self):
        mock_owner = MagicMock()
        net = IntelligenceNetwork(mock_owner)
        assert net.owner == mock_owner

        net.update_coverage("East", IntelligenceSource.HUMINT, 0.8)
        cov = net.calculate_coverage("East")
        assert cov > 0.0
