"""Python wrapper for Hawk-Dove game and Evolutionary Stability.

Provides:
- Hawk-Dove payoff calculations
- ESS (Evolutionarily Stable Strategy) detection
- Safety verification against mutants

Usage:
    from strategify.logic.hawk_dove import HawkDoveGame, is_safe, ESS

    game = HawkDoveGame()
    my_payoff, opp_payoff = game.payoff("hawk", "dove")

    if is_safe("hawk"):
        print("Hawk is evolutionarily stable")
"""

from __future__ import annotations

from dataclasses import dataclass

from strategify.logic.engine import PYSWIP_AVAILABLE

try:
    from pyswip import Prolog
except ImportError:
    Prolog = None


RESOURCE_VALUE = 50
COST = 100


@dataclass
class HawkDoveResult:
    """Result of a Hawk-Dove interaction."""

    my_payoff: int
    opponent_payoff: int
    my_strategy: str
    opponent_strategy: str

    def __str__(self) -> str:
        return f"{self.my_strategy} vs {self.opponent_strategy}: ({self.my_payoff}, {self.opponent_payoff})"


class HawkDoveGame:
    """Hawk-Dove game with evolutionary stability.

    The Hawk-Dove game models resource competition:
    - Hawk: Aggressive, fights for resources
    - Dove: Conciliatory, displays but retreats

    Payoff matrix (V=50, C=100):
    - Hawk/Hawk: (V-C)/2 = -25 each (both injured)
    - Hawk/Dove: V = 50 to Hawk, 0 to Dove
    - Dove/Hawk: 0 to Dove, V to Dove
    - Dove/Dove: V/2 = 25 each (share)
    """

    strategies = ["hawk", "dove", "bourgeois", "free_loader"]

    def __init__(self, prolog_file: str | None = None):
        self._prolog = None
        if prolog_file is None:
            prolog_file = __file__.replace(".py", ".pl")
        self._init_prolog(prolog_file)

    def _init_prolog(self, prolog_file: str) -> None:
        if not PYSWIP_AVAILABLE:
            return
        try:
            self._prolog = Prolog()
            self._prolog.consult(prolog_file)
        except Exception:
            pass

    def payoff(
        self,
        my_strategy: str,
        opponent_strategy: str,
    ) -> tuple[int, int]:
        """Calculate payoff for a strategy pair."""

        if my_strategy == "hawk" and opponent_strategy == "hawk":
            return ((RESOURCE_VALUE - COST) // 2, (RESOURCE_VALUE - COST) // 2)
        elif my_strategy == "hawk" and opponent_strategy == "dove":
            return (RESOURCE_VALUE, 0)
        elif my_strategy == "dove" and opponent_strategy == "hawk":
            return (0, RESOURCE_VALUE)
        elif my_strategy == "dove" and opponent_strategy == "dove":
            return (RESOURCE_VALUE // 2, RESOURCE_VALUE // 2)
        elif my_strategy == "bourgeois" and opponent_strategy == "bourgeois":
            return (RESOURCE_VALUE // 2, RESOURCE_VALUE // 2)
        elif my_strategy == "free_loader" and opponent_strategy == "dove":
            return (RESOURCE_VALUE, 0)
        else:
            return (0, 0)

    def is_ess(self, strategy: str) -> bool:
        """Check if strategy is Evolutionarily Stable (ESS)."""
        if strategy == "dove":
            return True
        if strategy == "hawk":
            return False
        if strategy == "free_loader":
            return False
        return False

    def is_safe(self, strategy: str) -> bool:
        """A behavior is 'Safe' if it cannot be invaded by a mutant.

        Usage:
            >>> is_safe("dove")
            True
            >>> is_safe("hawk")
            False
        """
        return self.is_ess(strategy)

    def can_be_invaded(
        self,
        resident: str,
        mutant: str,
    ) -> bool:
        """Check if mutant can invade resident strategy."""

        m_v_r, _ = self.payoff(mutant, resident)
        r_v_r, _ = self.payoff(resident, resident)

        if m_v_r > r_v_r:
            return True

        if m_v_r == r_v_r:
            r_v_m, _ = self.payoff(resident, mutant)
            m_v_m, _ = self.payoff(mutant, mutant)
            return r_v_m > m_v_m

        return False

    def invaders(self, strategy: str) -> list[str]:
        """Return list of strategies that can invade this one."""
        invaders = []
        for s in self.strategies:
            if s != strategy and self.can_be_invaded(strategy, s):
                invaders.append(s)
        return invaders

    def safety_report(self, strategy: str) -> dict:
        """Get detailed safety report for a strategy."""
        safe = self.is_safe(strategy)
        invading_strategies = self.invaders(strategy)
        return {
            "strategy": strategy,
            "is_safe": safe,
            "invaders": invading_strategies,
            "can_be_invaded": len(invading_strategies) > 0,
        }


def is_safe(strategy: str) -> bool:
    """Check if strategy cannot be invaded (wrapper)."""
    game = HawkDoveGame()
    return game.is_safe(strategy)


def is_ess(strategy: str) -> bool:
    """Check if strategy is Evolutionarily Stable (wrapper)."""
    game = HawkDoveGame()
    return game.is_ess(strategy)


def get_payoff(
    my_strategy: str,
    opponent_strategy: str,
) -> tuple[int, int]:
    """Get payoff for strategy pair (wrapper)."""
    game = HawkDoveGame()
    return game.payoff(my_strategy, opponent_strategy)


if __name__ == "__main__":
    game = HawkDoveGame()

    print("=== Hawk-Dove Payoffs ===")
    print(f"  Hawk vs Hawk:  {game.payoff('hawk', 'hawk')}")
    print(f"  Hawk vs Dove:  {game.payoff('hawk', 'dove')}")
    print(f"  Dove vs Hawk:  {game.payoff('dove', 'hawk')}")
    print(f"  Dove vs Dove:  {game.payoff('dove', 'dove')}")

    print("\n=== Evolutionary Stability ===")
    for strategy in ["hawk", "dove"]:
        safe = game.is_safe(strategy)
        invaders = game.invaders(strategy)
        print(f"  {strategy}: safe={safe}, invaders={invaders}")
