"""Tests for gap resolution: Adversary red-teaming, Hybrid RL AI, synthetic geo fallbacks, and CLI REPL."""

from strategify.cli import InteractiveREPL, main
from strategify.geo.real_data import generate_synthetic_region_geometry
from strategify.reasoning.adversary import (
    AdversaryDoctrine,
    apply_adversary_doctrine,
    get_doctrine_profile,
)
from strategify.rl.hybrid_ai import HierarchicalHybridAI, TacticalAction
from strategify.sim.model import GeopolModel


def test_adversary_doctrine_profiles():
    profile = get_doctrine_profile(AdversaryDoctrine.AGGRESSIVE)
    assert profile.risk_tolerance == 0.8
    assert profile.prefer_offensive is True

    biases = profile.get_action_bias(
        current_posture="Deescalate",
        military_power=2.0,
        enemy_military=1.0,
        terrain_advantage=0.5,
    )
    assert "escalate" in biases
    assert biases["escalate"] > biases["deescalate"]


def test_apply_adversary_doctrine_integration():
    model = GeopolModel(n_steps=1)
    agent = model.schedule.agents[0]
    agent.adversary_doctrine = AdversaryDoctrine.AGGRESSIVE

    res = apply_adversary_doctrine(agent, AdversaryDoctrine.AGGRESSIVE, military_power=2.0, enemy_power=1.0)
    assert isinstance(res, dict)
    assert "escalate" in res


def test_hierarchical_hybrid_ai():
    hybrid = HierarchicalHybridAI(use_rl=False)
    model = GeopolModel(n_steps=1)
    agent = model.schedule.agents[0]

    decision = hybrid.make_decision(agent, model, observation=[0.5, 0.5, 0.5])
    assert decision.strategic_action in ("Escalate", "Deescalate", "Maintain")
    assert isinstance(decision.tactical_action, TacticalAction)


def test_generate_synthetic_region_geometry():
    poly1 = generate_synthetic_region_geometry("UKR")
    poly2 = generate_synthetic_region_geometry("TWN")

    assert poly1.is_valid
    assert poly2.is_valid
    assert poly1.area > 0.0


def test_cli_interactive_repl(capsys):
    repl = InteractiveREPL(scenario_name="Ukraine")
    repl.print_status()
    captured = capsys.readouterr()
    assert "Simulation Status: Ukraine" in captured.out

    repl.run_steps(1)
    repl.issue_override("alpha", "Escalate")

    target = repl.model.get_agent_by_region("alpha")
    if target:
        assert target.posture == "Escalate"


def test_cli_main_run(capsys):
    main(["run", "Ukraine", "1"])
    captured = capsys.readouterr()
    assert "Run finished successfully." in captured.out
