"""Tests for RL Control Benchmarking, Epidemic Plotter, and MCP Env Tools."""

import numpy as np

from strategify.plugins.mcp_bridge import EpidemiologyMCPBridge
from strategify.rl.benchmark import RLControlBenchmark
from strategify.viz.epidemic_plots import EpidemicPlotter

EXPECTED_MCP_TOOLS_COUNT = 6
MIN_BASE64_LENGTH = 100


def test_rl_control_benchmark():
    benchmark_engine = RLControlBenchmark()
    result = benchmark_engine.compare_rl_vs_pontryagin(num_episodes=2, t_horizon=10.0)

    assert result.rl_total_cost_j > 0.0
    assert result.pontryagin_optimal_cost_j > 0.0
    assert result.optimality_gap_pct >= 0.0
    assert len(result.rl_control_trajectory) > 0
    assert len(result.optimal_control_trajectory) > 0


def test_epidemic_plotter():
    plotter = EpidemicPlotter()
    t = [0, 1, 2, 3, 4]
    s = [0.99, 0.9, 0.8, 0.7, 0.6]
    i_arr = [0.01, 0.1, 0.2, 0.25, 0.2]
    r = [0.0, 0.0, 0.0, 0.05, 0.2]
    u_arr = [0.1, 0.5, 0.8, 0.6, 0.2]

    img_b64 = plotter.render_trajectory_plot(t, s, i_arr, r, u_arr, title="Test Plot")
    assert len(img_b64) > MIN_BASE64_LENGTH

    matrix = np.random.uniform(0, 1, size=(5, 3))
    heatmap_b64 = plotter.render_spatial_node_heatmap(matrix, node_names=["NodeA", "NodeB", "NodeC"])
    assert len(heatmap_b64) > MIN_BASE64_LENGTH


def test_mcp_bridge_rl_tools():
    bridge = EpidemiologyMCPBridge()
    decls = bridge.get_tool_declarations()
    assert len(decls) == EXPECTED_MCP_TOOLS_COUNT

    res_step = bridge.execute_tool("step_epidemic_env", {"action": [0.7, 0.3, 0.1]})
    assert res_step["status"] == "success"
    assert "observation" in res_step

    res_bench = bridge.execute_tool("benchmark_rl_vs_optimal", {"num_episodes": 2})
    assert res_bench["status"] == "success"
    assert "optimality_gap_pct" in res_bench
