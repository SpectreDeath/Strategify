"""Tests for Phase G: Real-Time OSINT Intelligence Feed & Counterfactual Crisis Simulator."""

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.osint.live_feed import StrategifyLiveFeed
from strategify.sim.counterfactual import CounterfactualSimulator
from strategify.sim.wargame import MultiDomainWargameEngine
from strategify.web.api import app

EXPECTED_BRANCHES_COUNT = 3
EXPECTED_EVENTS_COUNT = 3


def test_live_feed_ingestion_and_calibration():
    feed = StrategifyLiveFeed()
    events = feed.fetch_live_events()
    assert len(events) == EXPECTED_EVENTS_COUNT

    engine = MultiDomainWargameEngine()
    snap = engine.get_state_snapshot()

    calibrated = feed.calibrate_snapshot(snap, events, actor_id="BlueLand")
    assert calibrated.military_readiness["BlueLand"] < 100.0
    assert calibrated.epidemic_infections["BlueLand"] > 0.0


def test_counterfactual_branch_simulation():
    engine = MultiDomainWargameEngine()
    snap = engine.get_state_snapshot()

    sim = CounterfactualSimulator(actor_id="BlueLand")
    branches = sim.simulate_branches(snap, steps=2)

    assert len(branches) == EXPECTED_BRANCHES_COUNT
    assert "baseline" in branches
    assert "escalation" in branches
    assert "mitigation" in branches

    assert branches["mitigation"].final_infections < branches["escalation"].final_infections


def test_cli_live_feed_command(capsys):
    main(["live-feed", "2"])
    captured = capsys.readouterr()

    assert "Ingested 3 Live OSINT Events:" in captured.out
    assert "Parallel Counterfactual Crisis Simulation Results" in captured.out
    assert "Live OSINT feed & counterfactual simulation finished." in captured.out


def test_phase_g_web_api_endpoints():
    client = TestClient(app)

    feed_res = client.get("/api/osint/live-feed")
    assert feed_res.status_code == 200
    feed_json = feed_res.json()
    assert feed_json["status"] == "success"
    assert feed_json["count"] == EXPECTED_EVENTS_COUNT

    sim_res = client.post("/api/counterfactual/simulate?steps=2&actor_id=BlueLand")
    assert sim_res.status_code == 200
    sim_json = sim_res.json()
    assert sim_json["status"] == "success"
    assert "baseline" in sim_json["branches"]
    assert "mitigation" in sim_json["branches"]
