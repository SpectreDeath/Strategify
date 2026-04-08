"""Tests for scenario comparison and trajectory analysis."""

import pytest

from strategify.analysis.comparison import (
    collect_trajectories,
    compare_trajectories,
    extract_trajectory,
    multi_scenario_comparison,
    trajectory_to_dataframe,
)
from strategify.sim.model import GeopolModel


@pytest.fixture
def model():
    return GeopolModel()


# ---------------------------------------------------------------------------
# extract_trajectory
# ---------------------------------------------------------------------------


class TestExtractTrajectory:
    def test_returns_expected_keys(self, model):
        model.step()
        traj = extract_trajectory(model)
        assert "postures" in traj
        assert "resources" in traj
        assert "diplomacy_weights" in traj
        assert "escalation_levels" in traj

    def test_postures_all_agents(self, model):
        model.step()
        traj = extract_trajectory(model)
        assert len(traj["postures"]) == 4
        for rid, val in traj["postures"].items():
            assert val in (0.0, 1.0)

    def test_resources_populated(self, model):
        model.step()
        traj = extract_trajectory(model)
        assert len(traj["resources"]) == 4

    def test_diplomacy_weights_has_edges(self, model):
        model.step()
        traj = extract_trajectory(model)
        assert len(traj["diplomacy_weights"]) > 0
        for edge in traj["diplomacy_weights"]:
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge

    def test_escalation_levels_populated(self, model):
        model.step()
        traj = extract_trajectory(model)
        # Escalation ladder is enabled by default
        assert isinstance(traj["escalation_levels"], dict)


# ---------------------------------------------------------------------------
# collect_trajectories
# ---------------------------------------------------------------------------


class TestCollectTrajectories:
    def test_returns_correct_length(self, model):
        trajs = collect_trajectories(model, n_steps=5)
        assert len(trajs) == 5

    def test_step_increments(self, model):
        trajs = collect_trajectories(model, n_steps=3)
        assert [t["step"] for t in trajs] == [0, 1, 2]

    def test_each_snapshot_has_postures(self, model):
        trajs = collect_trajectories(model, n_steps=3)
        for t in trajs:
            assert len(t["postures"]) == 4


# ---------------------------------------------------------------------------
# compare_trajectories
# ---------------------------------------------------------------------------


class TestCompareTrajectories:
    def test_comparison_structure(self, model):
        trajs_a = collect_trajectories(model, n_steps=5)
        trajs_b = collect_trajectories(GeopolModel(), n_steps=5)
        result = compare_trajectories(trajs_a, trajs_b)
        assert "escalation_divergence" in result
        assert "max_escalation_diff" in result
        assert "diplomacy_drift" in result
        assert "names" in result
        assert result["steps_compared"] == 5

    def test_identical_trajectories(self):
        import random

        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()
        trajs_a = collect_trajectories(m1, n_steps=5)
        trajs_b = collect_trajectories(m2, n_steps=5)
        result = compare_trajectories(trajs_a, trajs_b)
        assert result["escalation_divergence"] == pytest.approx(0.0, abs=1e-10)

    def test_empty_trajectories(self):
        result = compare_trajectories([], [])
        assert "error" in result

    def test_custom_names(self, model):
        trajs = collect_trajectories(model, n_steps=3)
        result = compare_trajectories(trajs, trajs, names=("ScenarioA", "ScenarioB"))
        assert result["names"] == ("ScenarioA", "ScenarioB")


# ---------------------------------------------------------------------------
# multi_scenario_comparison
# ---------------------------------------------------------------------------


class TestMultiScenarioComparison:
    def test_pairwise_comparison(self, model):
        import random

        random.seed(42)
        m1 = GeopolModel()
        random.seed(42)
        m2 = GeopolModel()
        trajs1 = collect_trajectories(m1, n_steps=3)
        trajs2 = collect_trajectories(m2, n_steps=3)

        result = multi_scenario_comparison(
            {
                "default_a": trajs1,
                "default_b": trajs2,
            }
        )
        assert ("default_a", "default_b") in result

    def test_three_scenarios(self):
        import random

        scenarios = {}
        for name in ("a", "b", "c"):
            random.seed(42)
            scenarios[name] = collect_trajectories(GeopolModel(), n_steps=3)

        result = multi_scenario_comparison(scenarios)
        assert len(result) == 3  # 3 choose 2


# ---------------------------------------------------------------------------
# trajectory_to_dataframe
# ---------------------------------------------------------------------------


class TestTrajectoryToDataFrame:
    def test_dataframe_structure(self, model):
        trajs = collect_trajectories(model, n_steps=3)
        df = trajectory_to_dataframe(trajs)
        assert len(df) == 3
        assert "step" in df.columns
        # Should have escalation and resource columns per region
        escalation_cols = [c for c in df.columns if c.endswith("_escalation")]
        assert len(escalation_cols) == 4

    def test_dataframe_values(self, model):
        trajs = collect_trajectories(model, n_steps=3)
        df = trajectory_to_dataframe(trajs)
        assert df["step"].tolist() == [0, 1, 2]
