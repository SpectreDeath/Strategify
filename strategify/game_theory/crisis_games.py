"""Crisis game definitions: pre-built payoff matrices for common scenarios.

Each function returns a NormalFormGame with payoff matrices for two players.
Games are parameterised by action labels so the caller knows which row/column
maps to which action.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np

from strategify.game_theory.normal_form import NormalFormGame


def escalation_game() -> NormalFormGame:
    """Chicken / brinkmanship payoff structure.

    Actions: ["Escalate", "Deescalate"]

    Payoff intuition::

      Both Deescalate  -> modest mutual gain  (3, 3)
      One Escalates, one Deescalates          (5, 1) or (1, 5)
      Both Escalate    -> mutual loss         (-2, -2)
    """
    A = np.array([[-2, 5], [1, 3]], dtype=float)
    B = np.array([[-2, 1], [5, 3]], dtype=float)
    return NormalFormGame(A, B)


def trade_game() -> NormalFormGame:
    """Trade cooperation vs protectionism game.

    Actions: ["Open", "Protect"]

    Payoff intuition::

      Both Open       -> mutual gain via free trade  (4, 4)
      One Protects     -> mercantilist advantage      (5, 1) or (1, 5)
      Both Protect    -> trade war loss              (-1, -1)
    """
    A = np.array([[-1, 5], [1, 4]], dtype=float)
    B = np.array([[-1, 1], [5, 4]], dtype=float)
    return NormalFormGame(A, B)


def sanctions_game() -> NormalFormGame:
    """Sanctions imposition vs compliance game.

    Actions: ["Impose", "Comply"]

    Payoff intuition::

      Both Comply      -> stable relations           (3, 3)
      Impose/Comply    -> coercive gain vs cost      (4, 0) or (0, 4)
      Both Impose      -> mutual economic damage     (-2, -2)
    """
    A = np.array([[-2, 4], [0, 3]], dtype=float)
    B = np.array([[-2, 0], [4, 3]], dtype=float)
    return NormalFormGame(A, B)


def alliance_formation_game() -> NormalFormGame:
    """Alliance commitment vs defection game (Stag Hunt variant).

    Actions: ["Commit", "Defect"]

    Payoff intuition::

      Both Commit     -> strong alliance benefit      (5, 5)
      One Defects      -> free-rider advantage         (6, 2) or (2, 6)
      Both Defect     -> no alliance, moderate gain   (3, 3)
    """
    A = np.array([[3, 6], [2, 5]], dtype=float)
    B = np.array([[3, 2], [6, 5]], dtype=float)
    return NormalFormGame(A, B)


def military_confrontation_game() -> NormalFormGame:
    """Military action vs restraint game (Hawk-Dove variant)."""
    A = np.array([[-3, 6], [0, 3]], dtype=float)
    B = np.array([[-3, 0], [6, 3]], dtype=float)
    return NormalFormGame(A, B)


def cyber_game() -> NormalFormGame:
    """Cyber offensive vs defensive game.

    Actions: ["CyberAttack", "Defend"]

    Payoff intuition::

      Both Defend      -> no impact                  (3, 3)
      Attack/Defend    -> disruption vs frustration  (5, 1) or (1, 5)
      Both Attack      -> mutual infrastructure loss (-1, -1)
    """
    A = np.array([[-1, 5], [1, 3]], dtype=float)
    B = np.array([[-1, 1], [5, 3]], dtype=float)
    return NormalFormGame(A, B)


def maneuver_game() -> NormalFormGame:
    """Military maneuvering: deployment vs interdiction.

    Actions: ["Infiltrate", "Defend"]

    Payoff intuition::

      Both Defend      -> status quo                 (3, 3)
      Infiltrate/Defend -> limited gain vs resistance  (4, 2) or (2, 4)
      Both Infiltrate  -> local skirmish damage      (-1, -1)
    """
    A = np.array([[-1, 4], [2, 3]], dtype=float)
    B = np.array([[-1, 2], [4, 3]], dtype=float)
    return NormalFormGame(A, B)


def hybrid_game() -> NormalFormGame:
    """Asymmetric proxy warfare: funding vs containment.

    Actions: ["FundProxy", "CounterInsurgency"]

    Payoff intuition::

      Both Counter      -> status quo                 (3, 3)
      Fund/Counter     -> friction vs frustration    (4, 2) or (1, 4)
      Both Fund        -> maximum instability        (-2, -2)
    """
    A = np.array([[-2, 4], [1, 3]], dtype=float)
    B = np.array([[-2, 1], [4, 3]], dtype=float)
    return NormalFormGame(A, B)


def governance_game() -> NormalFormGame:
    """Resolution compliance game: Comply vs Defy.

    Actions: ["Comply", "Defy"]

    Payoff intuition:
      Both Comply -> high global stability (4, 4)
      One Defies  -> short-term gain for defier (5), cost for other (0)
      Both Defy   -> resolution collapse, high tension (-2, -2)
    """
    A = np.array([[-2, 5], [0, 4]], dtype=float)
    B = np.array([[-2, 0], [5, 4]], dtype=float)
    return NormalFormGame(A, B)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

GAME_REGISTRY: dict[str, Callable[[], NormalFormGame]] = {
    "escalation": escalation_game,
    "trade": trade_game,
    "sanctions": sanctions_game,
    "alliance": alliance_formation_game,
    "military": military_confrontation_game,
    "cyber": cyber_game,
    "maneuver": maneuver_game,
    "hybrid": hybrid_game,
    "governance": governance_game,
}

GAME_ACTIONS: dict[str, list[str]] = {
    "escalation": ["Escalate", "Deescalate"],
    "trade": ["Open", "Protect"],
    "sanctions": ["Impose", "Comply"],
    "alliance": ["Commit", "Defect"],
    "military": ["Act", "Restrain"],
    "cyber": ["CyberAttack", "Defend"],
    "maneuver": ["Infiltrate", "Defend"],
    "hybrid": ["FundProxy", "CounterInsurgency"],
    "governance": ["Comply", "Defy"],
}


def get_game(name: str) -> NormalFormGame:
    """Return a fresh instance of the named game.

    Parameters
    ----------
    name:
        One of the keys in GAME_REGISTRY.

    Raises
    ------
    KeyError
        If the game name is not registered.
    """
    factory = GAME_REGISTRY.get(name)
    if factory is None:
        raise KeyError(f"Unknown game '{name}'. Available: {list(GAME_REGISTRY.keys())}")
    return factory()


def get_game_actions(name: str) -> list[str]:
    """Return the action labels for the named game."""
    actions = GAME_ACTIONS.get(name)
    if actions is None:
        raise KeyError(f"Unknown game '{name}'. Available: {list(GAME_ACTIONS.keys())}")
    return actions
