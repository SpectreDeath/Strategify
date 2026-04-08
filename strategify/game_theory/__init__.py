"""Game-theory sub-package: normal-form games and crisis payoff matrices."""

from strategify.game_theory.coalition import (
    CoalitionStateTracker,
    MultiActorPayoffComputer,
    PairResult,
    PairwiseGameDispatchEngine,
)
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
from strategify.game_theory.dynamic import PayoffComputer, PayoffHistory
from strategify.game_theory.normal_form import NormalFormGame

__all__ = [
    "NormalFormGame",
    "escalation_game",
    "trade_game",
    "sanctions_game",
    "alliance_formation_game",
    "military_confrontation_game",
    "get_game",
    "get_game_actions",
    "GAME_REGISTRY",
    "GAME_ACTIONS",
    "PairwiseGameDispatchEngine",
    "PairResult",
    "CoalitionStateTracker",
    "MultiActorPayoffComputer",
    "PayoffComputer",
    "PayoffHistory",
]
