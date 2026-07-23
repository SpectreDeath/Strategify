"""Tests for Phase I: Strategic Cyber-Physical Digital Twin & Infrastructure Resilience Engine."""

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.sim.infrastructure import CyberPhysicalResilienceEngine
from strategify.web.api import app

EXPECTED_TOTAL_NODES = 5
MIN_COLLAPSED_ON_PWR_ATTACK = 3


def test_cyber_physical_disruption_cascade():
    engine = CyberPhysicalResilienceEngine(region_id="BlueLand")
    res = engine.inject_disruption(target_node_id="PWR_01", cyber_exploit_severity=0.8, workforce_absenteeism_pct=0.3)

    assert res.total_nodes == EXPECTED_TOTAL_NODES
    assert res.collapsed_nodes_count >= MIN_COLLAPSED_ON_PWR_ATTACK
    assert res.cascade_failure_index > 0.5
    assert "PWR_01" in res.systemic_bottleneck_nodes
    assert res.mean_time_to_recovery_days > 0.0


def test_cli_resilience_command(capsys):
    main(["resilience", "PWR_01"])
    captured = capsys.readouterr()

    assert "Cyber-Physical Infrastructure Cascade Stress Test" in captured.out
    assert "Cascade Failure Index:" in captured.out
    assert "Collapsed Nodes:" in captured.out


def test_phase_i_web_api_endpoint():
    client = TestClient(app)

    response = client.post("/api/resilience/simulate?target_node_id=PWR_01&cyber_exploit_severity=0.7")
    assert response.status_code == 200
    json_resp = response.json()

    assert json_resp["status"] == "success"
    assert json_resp["target_node_id"] == "PWR_01"
    assert json_resp["total_nodes"] == EXPECTED_TOTAL_NODES
    assert json_resp["cascade_failure_index"] > 0.0
    assert "nodes_state" in json_resp
