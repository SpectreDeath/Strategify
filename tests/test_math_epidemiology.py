"""Tests for Advanced Mathematical & Evolutionary Game Epidemiology Modules."""

from strategify.epidemiology.math_engine import NextGenMatrixOperator
from strategify.epidemiology.public_goods import PublicGoodsGame
from strategify.epidemiology.replicator import ReplicatorDynamicsODE


def test_next_gen_matrix_operator_sir():
    operator = NextGenMatrixOperator()
    r0 = operator.compute_sir_r0(beta=0.5, gamma=0.1)
    assert abs(r0 - 5.0) < 1e-4

    f_matrix = [[0.5, 0.2], [0.0, 0.3]]
    v_matrix = [[0.2, 0.0], [0.0, 0.1]]

    result = operator.compute_r0(f_matrix, v_matrix)
    assert result.r0 > 1.0
    assert result.is_stable_disease_free is False


def test_replicator_dynamics_ode_solver():
    ode_solver = ReplicatorDynamicsODE(
        beta_baseline=0.5,
        beta_mitigated=0.1,
        gamma=0.1,
        cost_of_disease=1.0,
        cost_of_mitigation=0.2,
    )

    solution = ode_solver.solve(
        initial_state=(0.99, 0.01, 0.0, 0.5),
        t_span=(0.0, 20.0),
        n_eval_points=50,
    )

    assert len(solution.t) == 50
    assert len(solution.susceptible) == 50
    assert len(solution.cooperation_fraction) == 50
    assert 0.0 <= solution.cooperation_fraction[-1] <= 1.0


def test_public_goods_game_payoffs_and_thresholds():
    pgg = PublicGoodsGame(
        group_size_n=10,
        synergy_factor_r=3.0,
        cost_of_contribution_c=1.0,
        defection_threshold=0.4,
    )

    # All contribute (10/10)
    c_payoff, d_payoff = pgg.calculate_payoffs(num_contributors=10)
    assert c_payoff > 0.0
    assert d_payoff > c_payoff

    # Simulate group round with 50% contributors
    result = pgg.simulate_group_round(contributor_fraction=0.5)
    assert result.num_contributors == 5
    assert result.num_defectors == 5
    assert result.defection_threshold_crossed is True
