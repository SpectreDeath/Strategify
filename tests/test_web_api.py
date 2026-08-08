"""Tests for FastAPI web endpoints."""

from fastapi.testclient import TestClient

from strategify.web.api import app

client = TestClient(app)


def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "model_initialized" in data


def test_agent_beliefs_endpoint():
    response = client.get("/api/agents/usa/beliefs")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "usa"
    assert "beliefs" in data


def test_agent_mcts_branches_endpoint():
    response = client.get("/api/agents/usa/mcts-branches")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "usa"
    assert "branches" in data


def test_uninitialized_model_errors():
    # Attempt to step or get state before initialization
    resp_step = client.post("/api/simulation/step")
    assert resp_step.status_code == 400

    resp_state = client.get("/api/simulation/state")
    assert resp_state.status_code == 400


def test_simulation_lifecycle_endpoints():
    # Start simulation
    resp_start = client.post("/api/simulation/start", json={"scenario_id": "default"})
    assert resp_start.status_code in [200, 500]

    # Get state when initialized
    resp_state = client.get("/api/simulation/state")
    assert resp_state.status_code in [200, 400]

    # Step simulation when initialized
    resp_step = client.post("/api/simulation/step")
    assert resp_step.status_code in [200, 400]

    # Stop simulation
    resp_stop = client.post("/api/simulation/stop")
    assert resp_stop.status_code == 200


def test_agent_logs_endpoint():
    response = client.get("/api/agents/usa/logs")
    assert response.status_code == 200
    data = response.json()
    assert data["agent_id"] == "usa"
    assert "logs" in data
    assert len(data["logs"]) > 0


def test_economics_chokepoints_endpoint():
    response = client.get("/api/economics/chokepoints")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "chokepoints" in data
    assert "prolog_facts" in data

