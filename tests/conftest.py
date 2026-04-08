"""Shared pytest fixtures for strategify tests."""

import pytest


@pytest.fixture
def model():
    """A fresh GeopolModel instance."""
    from strategify.sim.model import GeopolModel

    return GeopolModel()


@pytest.fixture
def chicken_game():
    """The standard escalation (Chicken) game."""
    from strategify.game_theory.crisis_games import escalation_game

    return escalation_game()
