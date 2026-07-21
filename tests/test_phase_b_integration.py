"""Integration tests for Phase B: Deep AI Integration & Game Theory Bridge."""

from strategify.sim.model import GeopolModel


def test_geopol_model_phase_b_engines_initialized():
    model = GeopolModel(n_steps=2)
    assert hasattr(model, "prolog_bridge")
    assert model.prolog_bridge is not None
    assert hasattr(model, "treaty_checker")
    assert model.treaty_checker is not None


def test_geopol_model_step_runs_crisis_game_equilibria():
    model = GeopolModel(n_steps=2)
    agents = [a for a in model.schedule.agents if hasattr(a, "posture")]
    if len(agents) >= 2:
        agents[0].posture = "Invade"
        agents[1].posture = "Escalate"

    initial_tension = model.global_tension
    model.step()
    assert model.global_tension >= initial_tension
    assert model.schedule.steps == 1


def test_treaty_checker_integration():
    model = GeopolModel(n_steps=1)
    checker = model.treaty_checker
    report = checker.check_action(
        actor="Alpha",
        action="military_invasion",
        target="Bravo",
    )
    assert hasattr(report, "overall_status")
    assert hasattr(report, "findings")
