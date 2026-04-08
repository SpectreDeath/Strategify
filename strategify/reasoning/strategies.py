"""Axelrod strategy adapter for iterated diplomatic game strategies.

Maps between our Escalate/Deescalate world and Axelrod's Cooperate/Defect world:
  Cooperate (C) = Deescalate
  Defect    (D) = Escalate
"""

from __future__ import annotations

import axelrod as axl

ESCALATE = "Escalate"
DEESCALATE = "Deescalate"

# Map Axelrod Action enums to our actions
_ACTION_MAP = {axl.Action.C: DEESCALATE, axl.Action.D: ESCALATE}
_REVERSE_MAP = {DEESCALATE: axl.Action.C, ESCALATE: axl.Action.D}

# Map personality names to Axelrod strategy constructors
PERSONALITY_STRATEGIES: dict[str, type] = {
    "Aggressor": axl.Defector,
    "Pacifist": axl.Cooperator,
    "Tit-for-Tat": axl.TitForTat,
    "Neutral": axl.GoByMajority,
    "Grudger": axl.Grudger,
}


class OpponentProxy:
    """Lightweight proxy that presents our agent data as an Axelrod Player.

    Axelrod strategies inspect the opponent's history via the Player object.
    This proxy bridges our agent posture history to that interface.
    """

    def __init__(self) -> None:
        self.history = axl.History()
        self._my_actions: list[str] = []
        self._opp_actions: list[str] = []

    def update(self, my_action: str, opponent_action: str) -> None:
        """Record both sides of the last round (mapped to C/D).

        From TitForTat's perspective, the proxy IS the opponent.
        So the proxy's history must show opponent_action as the "play"
        (what the proxy "played" from TitForTat's point of view).
        """
        axl_opp = _REVERSE_MAP[opponent_action]
        axl_my = _REVERSE_MAP[my_action]
        # Store opponent's action as "play" so opponent.history[-1] returns it
        self.history.append(axl_opp, axl_my)

    @property
    def cooperations(self):
        return self.history.cooperations

    @property
    def defections(self):
        return self.history.defections


class DiplomacyStrategy:
    """Wraps an Axelrod strategy for use in the geopolitical simulation.

    Parameters
    ----------
    personality:
        One of the keys in PERSONALITY_STRATEGIES.
    """

    def __init__(self, personality: str = "Neutral") -> None:
        strategy_cls = PERSONALITY_STRATEGIES.get(personality, axl.GoByMajority)
        self._strategy = strategy_cls()
        self._opponent = OpponentProxy()
        self._personality = personality
        self._last_action: str | None = None

    @property
    def personality(self) -> str:
        return self._personality

    def decide(self, last_opponent_action: str | None = None) -> str:
        """Choose an action based on the Axelrod strategy.

        Parameters
        ----------
        last_opponent_action:
            The opponent's last action ("Escalate" or "Deescalate"), or None.

        Returns
        -------
        str
            "Escalate" or "Deescalate"
        """
        # Record the completed round BEFORE asking for the next action
        # so the strategy sees updated histories
        if last_opponent_action is not None and self._last_action is not None:
            axl_my = _REVERSE_MAP[self._last_action]
            axl_opp = _REVERSE_MAP[last_opponent_action]
            self._opponent.update(self._last_action, last_opponent_action)
            self._strategy.history.append(axl_my, axl_opp)

        axl_action = self._strategy.strategy(self._opponent)
        chosen = _ACTION_MAP.get(axl_action, DEESCALATE)
        self._last_action = chosen
        return chosen

    def reset(self) -> None:
        """Reset the strategy state for a fresh interaction."""
        self._strategy = type(self._strategy)()
        self._opponent = OpponentProxy()
        self._last_action = None

    @staticmethod
    def available_personalities() -> list[str]:
        """Return list of supported personality names."""
        return list(PERSONALITY_STRATEGIES.keys())
