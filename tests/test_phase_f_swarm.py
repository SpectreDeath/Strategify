"""Tests for Phase F: Autonomous LLM Agent Swarm Orchestrator."""

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.reasoning.swarm import StrategifySwarm
from strategify.sim.wargame import MultiDomainWargameEngine
from strategify.web.api import app

EXPECTED_PERSONAS_COUNT = 4


def test_strategify_swarm_orchestration():
    engine = MultiDomainWargameEngine()
    swarm = StrategifySwarm(actor_id="BlueLand")

    result = swarm.deliberate_step(engine)

    assert result.actor_id == "BlueLand"
    assert len(result.proposals) == EXPECTED_PERSONAS_COUNT
    assert result.consensus_score > 0.0
    assert "Defense" in result.consensus_action_vector
    assert "Epidemiology" in result.consensus_action_vector
    assert "Finance" in result.consensus_action_vector
    assert "Diplomacy" in result.consensus_action_vector


def test_cli_swarm_command(capsys):
    main(["swarm", "2"])
    captured = capsys.readouterr()

    assert "Starting Autonomous LLM Swarm Deliberation for 2 steps..." in captured.out
    assert "Consensus Score:" in captured.out
    assert "Swarm deliberation completed successfully." in captured.out


def test_swarm_web_api_endpoint():
    client = TestClient(app)

    response = client.post("/api/swarm/deliberate?actor_id=BlueLand")
    assert response.status_code == 200
    json_resp = response.json()

    assert json_resp["status"] == "success"
    assert json_resp["actor_id"] == "BlueLand"
    assert len(json_resp["proposals"]) == EXPECTED_PERSONAS_COUNT
    assert "consensus_action_vector" in json_resp
