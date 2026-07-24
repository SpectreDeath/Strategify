"""Tests for Phase K: Universal Multi-Agent Game-Theoretic Equilibrium & Nash Bargaining Solver."""

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.theory.nash_solver import NashEquilibriumSolver
from strategify.web.api import app


def test_nash_equilibrium_solving():
    solver = NashEquilibriumSolver(actor_a="BlueLand", actor_b="RedNation")
    outcome = solver.solve()

    assert isinstance(outcome.has_pure_equilibrium, bool)
    assert "Escalate" in outcome.mixed_probabilities_a
    assert "Deescalate" in outcome.mixed_probabilities_b
    assert outcome.pareto_efficiency_score > 0.0
    assert len(outcome.bargaining_agreement) == 2


def test_cli_nash_command(capsys):
    main(["nash"])
    captured = capsys.readouterr()

    assert "Game-Theoretic Nash Equilibrium Analysis" in captured.out
    assert "Mixed Probabilities" in captured.out
    assert "Bargaining Agreement Solution:" in captured.out


def test_phase_k_web_api_endpoint():
    client = TestClient(app)

    response = client.post("/api/nash/solve?actor_a=BlueLand&actor_b=RedNation")
    assert response.status_code == 200
    json_resp = response.json()

    assert json_resp["status"] == "success"
    assert json_resp["actor_a"] == "BlueLand"
    assert json_resp["actor_b"] == "RedNation"
    assert "mixed_probabilities_a" in json_resp
    assert "bargaining_agreement" in json_resp
