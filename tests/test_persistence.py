"""Tests for state persistence (save/load/restore)."""

import json
import tempfile
from pathlib import Path

import pytest

from strategify.sim.model import GeopolModel
from strategify.sim.persistence import list_checkpoints, load_state, restore_state, save_state


@pytest.fixture
def stepped_model():
    model = GeopolModel()
    for _ in range(5):
        model.step()
    return model


def test_save_state_creates_file(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        result = save_state(stepped_model, path)
        assert result.exists()
        assert result.suffix == ".json"


def test_save_state_valid_json(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        assert "version" in data
        assert "agents" in data
        assert "diplomacy" in data


def test_save_state_contains_all_agents(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        assert len(data["agents"]) == 4


def test_save_state_with_metadata(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path, metadata={"experiment": "test"})
        with open(path) as f:
            data = json.load(f)
        assert data["metadata"]["experiment"] == "test"


def test_save_state_includes_economics(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        assert data["economic"] is not None
        assert "gdp" in data["economic"]


def test_save_state_includes_escalation(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        assert data["escalation"] is not None
        assert "levels" in data["escalation"]


def test_load_state(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        state = load_state(path)
        assert state["version"] == "0.3.0"
        assert len(state["agents"]) == 4


def test_load_state_not_found():
    with pytest.raises(FileNotFoundError):
        load_state("/nonexistent/path.json")


def test_restore_state(stepped_model):
    model = GeopolModel()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        state = load_state(path)

        # First agent escalated in stepped_model, save that
        stepped_agent = stepped_model.schedule.agents[0]
        stepped_agent.posture = "Escalate"
        save_state(stepped_model, path)
        state = load_state(path)

        # Restore to fresh model
        restore_state(model, state)
        fresh_agent = next(
            a for a in model.schedule.agents if a.region_id == stepped_agent.region_id
        )
        assert fresh_agent.posture == "Escalate"


def test_list_checkpoints_empty():
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoints = list_checkpoints(tmpdir)
        assert checkpoints == []


def test_list_checkpoints(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        save_state(stepped_model, Path(tmpdir) / "cp1.json")
        save_state(stepped_model, Path(tmpdir) / "cp2.json")
        checkpoints = list_checkpoints(tmpdir)
        assert len(checkpoints) == 2
        assert all("scenario" in cp for cp in checkpoints)


def test_save_state_diplomacy_edges(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        assert len(data["diplomacy"]) > 0
        for edge in data["diplomacy"]:
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge


def test_save_state_version(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        assert data["version"] == "0.3.0"
        assert data["step"] > 0


def test_save_state_agent_details(stepped_model):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        with open(path) as f:
            data = json.load(f)
        for agent_data in data["agents"]:
            assert "unique_id" in agent_data
            assert "region_id" in agent_data
            assert "posture" in agent_data
            assert "personality" in agent_data
            assert "role" in agent_data
            assert "capabilities" in agent_data
            assert isinstance(agent_data["capabilities"], dict)


def test_restore_diplomacy(stepped_model):
    """Restored model should have the same diplomacy weights."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        state = load_state(path)

        model2 = GeopolModel()
        restore_state(model2, state)

        # Compare diplomacy edges
        original_edges = {(e["source"], e["target"]): e["weight"] for e in state["diplomacy"]}
        for u, v, data in model2.relations.graph.edges(data=True):
            key = (u, v)
            if key in original_edges:
                assert data["weight"] == original_edges[key]


def test_restore_escalation_levels(stepped_model):
    """Restored model should have the same escalation levels."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(stepped_model, path)
        state = load_state(path)

        model2 = GeopolModel()
        restore_state(model2, state)

        if state.get("escalation") and model2.escalation_ladder is not None:
            for uid_str, level_int in state["escalation"]["levels"].items():
                uid = int(uid_str)
                assert int(model2.escalation_ladder.levels[uid]) == level_int


def test_save_state_without_economics():
    """Model without economics should still save correctly."""
    model = GeopolModel(enable_economics=False)
    model.step()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(model, path)
        with open(path) as f:
            data = json.load(f)
        assert data["economic"] is None


def test_save_state_without_escalation():
    """Model without escalation should still save correctly."""
    model = GeopolModel(enable_escalation_ladder=False)
    model.step()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "state.json"
        save_state(model, path)
        with open(path) as f:
            data = json.load(f)
        assert data["escalation"] is None


def test_list_checkpoints_nonexistent_dir():
    result = list_checkpoints("/nonexistent/path")
    assert result == []


def test_list_checkpoints_skips_invalid_json():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write invalid JSON file
        (Path(tmpdir) / "invalid.json").write_text("not json")
        result = list_checkpoints(tmpdir)
        assert result == []


def test_save_creates_parent_dirs():
    model = GeopolModel()
    model.step()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "nested" / "deep" / "state.json"
        result = save_state(model, path)
        assert result.exists()
