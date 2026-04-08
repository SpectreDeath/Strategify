"""Tests for multi-game crisis ladder and game registry."""

import pytest

from strategify.game_theory.crisis_games import (
    GAME_ACTIONS,
    GAME_REGISTRY,
    alliance_formation_game,
    escalation_game,
    get_game,
    get_game_actions,
    military_confrontation_game,
    sanctions_game,
    trade_game,
)
from strategify.game_theory.normal_form import NormalFormGame

# ---------------------------------------------------------------------------
# Original escalation game tests
# ---------------------------------------------------------------------------


def test_escalation_game_returns_normal_form():
    game = escalation_game()
    assert isinstance(game, NormalFormGame)


def test_escalation_game_payoff_shape():
    game = escalation_game()
    assert game.A.shape == (2, 2)
    assert game.B.shape == (2, 2)


def test_escalation_game_payoffs():
    game = escalation_game()
    assert game.A[1, 1] == 3.0
    assert game.B[1, 1] == 3.0
    assert game.A[0, 0] == -2.0
    assert game.B[0, 0] == -2.0
    assert game.A[0, 1] == 5.0
    assert game.B[0, 1] == 1.0
    assert game.A[1, 0] == 1.0
    assert game.B[1, 0] == 5.0


def test_escalation_game_has_nash_equilibria():
    game = escalation_game()
    eq = game.get_nash_equilibria()
    assert len(eq) > 0


def test_escalation_game_is_symmetric_structure():
    """Chicken game has symmetric structure: A[i,j] == B[j,i]."""
    game = escalation_game()
    assert game.A[0, 1] == game.B[1, 0]
    assert game.A[1, 0] == game.B[0, 1]


# ---------------------------------------------------------------------------
# All game types
# ---------------------------------------------------------------------------


class TestAllGames:
    """Test that all game types create valid NormalFormGames."""

    @pytest.mark.parametrize("game_name", list(GAME_REGISTRY.keys()))
    def test_game_factory_returns_normal_form(self, game_name):
        game = GAME_REGISTRY[game_name]()
        assert isinstance(game, NormalFormGame)

    @pytest.mark.parametrize("game_name", list(GAME_REGISTRY.keys()))
    def test_game_has_2x2_payoffs(self, game_name):
        game = GAME_REGISTRY[game_name]()
        assert game.A.shape == (2, 2)
        assert game.B.shape == (2, 2)

    @pytest.mark.parametrize("game_name", list(GAME_REGISTRY.keys()))
    def test_game_has_nash_equilibria(self, game_name):
        game = GAME_REGISTRY[game_name]()
        equilibria = game.get_nash_equilibria()
        assert len(equilibria) > 0

    @pytest.mark.parametrize("game_name", list(GAME_REGISTRY.keys()))
    def test_get_game_factory(self, game_name):
        game = get_game(game_name)
        assert isinstance(game, NormalFormGame)

    def test_get_game_invalid(self):
        with pytest.raises(KeyError, match="Unknown game"):
            get_game("nonexistent")

    @pytest.mark.parametrize("game_name", list(GAME_REGISTRY.keys()))
    def test_get_game_actions(self, game_name):
        actions = get_game_actions(game_name)
        assert len(actions) == 2
        assert all(isinstance(a, str) for a in actions)

    def test_get_game_actions_invalid(self):
        with pytest.raises(KeyError, match="Unknown game"):
            get_game_actions("nonexistent")


# ---------------------------------------------------------------------------
# Game-specific tests
# ---------------------------------------------------------------------------


class TestTradeGame:
    def test_trade_actions(self):
        assert get_game_actions("trade") == ["Open", "Protect"]

    def test_both_open_positive(self):
        game = trade_game()
        assert game.A[1, 1] == 4.0
        assert game.B[1, 1] == 4.0

    def test_both_protect_negative(self):
        game = trade_game()
        assert game.A[0, 0] == -1.0
        assert game.B[0, 0] == -1.0


class TestSanctionsGame:
    def test_sanctions_actions(self):
        assert get_game_actions("sanctions") == ["Impose", "Comply"]

    def test_mutual_impose_hurts(self):
        game = sanctions_game()
        assert game.A[0, 0] == -2.0
        assert game.B[0, 0] == -2.0


class TestAllianceGame:
    def test_alliance_actions(self):
        assert get_game_actions("alliance") == ["Commit", "Defect"]

    def test_both_commit_best(self):
        game = alliance_formation_game()
        assert game.A[1, 1] == 5.0
        assert game.B[1, 1] == 5.0


class TestMilitaryGame:
    def test_military_actions(self):
        assert get_game_actions("military") == ["Act", "Restrain"]

    def test_both_act_worst(self):
        game = military_confrontation_game()
        assert game.A[0, 0] == -3.0
        assert game.B[0, 0] == -3.0


class TestGameRegistry:
    def test_all_games_have_actions(self):
        for name in GAME_REGISTRY:
            assert name in GAME_ACTIONS

    def test_registry_has_core_games(self):
        assert len(GAME_REGISTRY) >= 5
        assert len(GAME_ACTIONS) >= 5
