"""Tests for Phase J: Global Strategic Sensitivity & Monte Carlo Uncertainty Quantification Engine."""

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.sim.uncertainty import UncertaintyQuantificationEngine
from strategify.web.api import app

EXPECTED_SAMPLES = 5


def test_monte_carlo_uncertainty_quantification():
    engine = UncertaintyQuantificationEngine(actor_id="BlueLand")
    res = engine.run_monte_carlo(num_samples=EXPECTED_SAMPLES, steps=2)

    assert res.num_samples == EXPECTED_SAMPLES
    assert res.actor_id == "BlueLand"
    assert "p5" in res.readiness_quantiles
    assert "p50" in res.readiness_quantiles
    assert "p95" in res.readiness_quantiles
    assert "infection_rate" in res.sensitivity_indices


def test_cli_uq_command(capsys):
    main(["uq", "5"])
    captured = capsys.readouterr()

    assert "Monte Carlo Uncertainty Quantification Results" in captured.out
    assert "Readiness Quantiles" in captured.out
    assert "Parameter Sensitivity Rankings:" in captured.out


def test_phase_j_web_api_endpoint():
    client = TestClient(app)

    response = client.post("/api/uq/simulate?actor_id=BlueLand&num_samples=5&steps=2")
    assert response.status_code == 200
    json_resp = response.json()

    assert json_resp["status"] == "success"
    assert json_resp["num_samples"] == EXPECTED_SAMPLES
    assert json_resp["actor_id"] == "BlueLand"
    assert "readiness_quantiles" in json_resp
    assert "sensitivity_indices" in json_resp
