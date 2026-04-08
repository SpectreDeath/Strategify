"""Tests for scenario runner (batch runs, parameter sweeps, comparisons)."""

import tempfile
from pathlib import Path

from strategify.sim.runner import run_comparison, run_parameter_sweep, run_scenario


def test_run_scenario():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_scenario("default", n_steps=5, output_dir=tmpdir)
        assert result["scenario"] == "eastern_europe_crisis"
        assert result["n_steps"] == 5
        assert result["csv_path"] is not None
        assert Path(result["csv_path"]).exists()


def test_run_scenario_with_checkpoints():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_scenario(
            "default",
            n_steps=6,
            output_dir=tmpdir,
            save_checkpoints=True,
            checkpoint_interval=3,
        )
        # 2 checkpoints (step 3, 6) + 1 final = 3
        assert len(result["checkpoint_paths"]) == 3


def test_run_scenario_detente():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_scenario("detente", n_steps=3, output_dir=tmpdir)
        assert result["scenario"] == "detente"
        assert Path(result["csv_path"]).exists()


def test_run_scenario_arms_race():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_scenario("arms_race", n_steps=3, output_dir=tmpdir)
        assert result["scenario"] == "arms_race"


def test_run_parameter_sweep():
    with tempfile.TemporaryDirectory() as tmpdir:
        param_grid = {
            "alpha_military": [0.3, 0.7],
            "bravo_military": [0.3, 0.7],
        }
        results = run_parameter_sweep(
            "default",
            param_grid,
            n_steps=3,
            output_dir=tmpdir,
        )
        assert len(results) == 4  # 2x2 combinations
        assert all("params" in r for r in results)
        assert all("agent_postures" in r for r in results)


def test_run_parameter_sweep_with_metric():
    with tempfile.TemporaryDirectory() as tmpdir:
        param_grid = {"alpha_military": [0.5, 0.9]}
        results = run_parameter_sweep(
            "default",
            param_grid,
            n_steps=3,
            output_dir=tmpdir,
            metric_fn=lambda m: sum(1 for a in m.schedule.agents if a.posture == "Escalate"),
        )
        assert len(results) == 2
        assert all(r["metric"] is not None for r in results)
        assert all(isinstance(r["metric"], (int, float)) for r in results)


def test_run_comparison():
    with tempfile.TemporaryDirectory() as tmpdir:
        comparison = run_comparison(
            ["default", "detente"],
            n_steps=5,
            output_dir=tmpdir,
        )
        assert "eastern_europe_crisis" in comparison
        assert "detente" in comparison
        for name, data in comparison.items():
            assert "final_postures" in data
            assert "escalation_count" in data
            assert data["n_steps"] == 5


def test_sweep_results_saved():
    with tempfile.TemporaryDirectory() as tmpdir:
        param_grid = {"alpha_military": [0.5]}
        run_parameter_sweep("default", param_grid, n_steps=2, output_dir=tmpdir)
        results_path = Path(tmpdir) / "sweep_results.json"
        assert results_path.exists()


def test_comparison_results_saved():
    with tempfile.TemporaryDirectory() as tmpdir:
        run_comparison(["default"], n_steps=2, output_dir=tmpdir)
        results_path = Path(tmpdir) / "comparison_results.json"
        assert results_path.exists()


def test_run_scenario_csv_reproducible():
    """Two identical runs should produce identical CSVs."""
    with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
        r1 = run_scenario("default", n_steps=5, output_dir=d1)
        r2 = run_scenario("default", n_steps=5, output_dir=d2)
        csv1 = Path(r1["csv_path"]).read_bytes()
        csv2 = Path(r2["csv_path"]).read_bytes()
        assert csv1 == csv2


def test_run_scenario_no_economics():
    """Running without economics should still work."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from strategify.sim.model import GeopolModel

        model = GeopolModel(enable_economics=False)
        for _ in range(3):
            model.step()
        assert model.trade_network is None


def test_run_scenario_no_escalation():
    """Running without escalation ladder should still work."""
    with tempfile.TemporaryDirectory() as tmpdir:
        from strategify.sim.model import GeopolModel

        model = GeopolModel(enable_escalation_ladder=False)
        for _ in range(3):
            model.step()
        assert model.escalation_ladder is None
        assert model.coalition_engine is None
