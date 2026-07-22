"""Tests for Phase E: Multi-Domain Wargaming Engine, CLI commands, and REST Web API endpoints."""

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.sim.wargame import MultiDomainWargameEngine
from strategify.web.api import app

EXPECTED_DEFAULT_WARGAME_STEPS = 5
MIN_PLOT_BASE64_LENGTH = 100


def test_multi_domain_wargame_engine():
    engine = MultiDomainWargameEngine(actors=["BlueLand", "RedNation"])
    result = engine.run_wargame(total_steps=EXPECTED_DEFAULT_WARGAME_STEPS)

    assert result.total_steps == EXPECTED_DEFAULT_WARGAME_STEPS
    assert len(result.history) == EXPECTED_DEFAULT_WARGAME_STEPS
    assert result.winner in ["BlueLand", "RedNation"]
    assert "BlueLand" in result.actor_scores
    assert "RedNation" in result.actor_scores


def test_cli_wargame_command(capsys):
    main(["wargame", "3"])
    captured = capsys.readouterr()

    assert "Running Multi-Domain Wargame for 3 steps..." in captured.out
    assert "Wargame Finished! Winner:" in captured.out


def test_wargame_and_epidemiology_web_api():
    client = TestClient(app)

    res_wargame = client.post("/api/wargame/run?steps=2")
    assert res_wargame.status_code == 200
    json_wg = res_wargame.json()
    assert json_wg["status"] == "success"
    assert json_wg["total_steps"] == 2
    assert "winner" in json_wg

    res_plot = client.get("/api/epidemiology/trajectory")
    assert res_plot.status_code == 200
    json_plot = res_plot.json()
    assert json_plot["status"] == "success"
    assert len(json_plot["plot_base64"]) > MIN_PLOT_BASE64_LENGTH
