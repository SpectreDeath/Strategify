"""Tests for Phase H: Automated Strategic War-Room Report Generator."""

from pathlib import Path

from fastapi.testclient import TestClient

from strategify.cli import main
from strategify.viz.war_room_reporter import StrategifyWarRoomReporter
from strategify.web.api import app

EXPECTED_BRANCHES_COUNT = 3
EXPECTED_PROPOSALS_COUNT = 4


def test_war_room_reporter_generation():
    reporter = StrategifyWarRoomReporter(actor_id="BlueLand")
    payload = reporter.generate_report(steps=2)

    assert payload.actor_id == "BlueLand"
    assert payload.threat_level in ("CRITICAL", "ELEVATED")
    assert len(payload.swarm_proposals) == EXPECTED_PROPOSALS_COUNT
    assert len(payload.counterfactual_branches) == EXPECTED_BRANCHES_COUNT
    assert "<!DOCTYPE html>" in payload.html_content


def test_war_room_reporter_file_export(tmp_path):
    reporter = StrategifyWarRoomReporter(actor_id="BlueLand")
    out_file = tmp_path / "test_report.html"

    result_path = reporter.export_html(output_path=str(out_file), steps=2)

    assert Path(result_path).exists()
    content = Path(result_path).read_text(encoding="utf-8")
    assert "STRATEGIFY EXECUTIVE WAR-ROOM BRIEFING" in content


def test_cli_report_command(tmp_path, capsys):
    out_file = tmp_path / "cli_brief.html"
    main(["report", str(out_file)])
    captured = capsys.readouterr()

    assert "Executive War-Room Briefing HTML exported to:" in captured.out
    assert Path(out_file).exists()


def test_phase_h_web_api_endpoint():
    client = TestClient(app)

    response = client.post("/api/report/generate?actor_id=BlueLand&steps=2")
    assert response.status_code == 200
    json_resp = response.json()

    assert json_resp["status"] == "success"
    assert json_resp["actor_id"] == "BlueLand"
    assert "html_content" in json_resp
    assert "<!DOCTYPE html>" in json_resp["html_content"]
