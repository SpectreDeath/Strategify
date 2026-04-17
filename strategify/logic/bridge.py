"""Bridge script to drive Prolog logic from Python.

This script provides a robust way to run Prolog-based strategic decisions
by asserting world state and querying the engine.

Usage:
    >>> from strategify.logic.bridge import StrategicBridge
    >>> bridge = StrategicBridge()
    >>> bridge.set_context(risk_level="low", potential_gain="high")
    >>> decisions = bridge.decide("cautious")
    >>> for d in decisions:
    ...     print(f"{d['agent']} decided to {d['action']}")
"""

from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

from strategify.logic.engine import PYSWIP_AVAILABLE

logger = logging.getLogger(__name__)

try:
    from pyswip import Prolog
except ImportError:
    Prolog = None


class StrategicBridge:
    """Bridge between Python simulation and Prolog strategic logic.

    Provides:
    - World state assertion (risk_level, potential_gain)
    - Strategic decision queries
    - Fact verification for epistemology

    Parameters
    ----------
    prolog_file:
        Path to the Prolog knowledge base.

    Example
    -------
    >>> bridge = StrategicBridge()
    >>> bridge.set_context(risk_level="low", potential_gain="high")
    >>> decisions = bridge.decide("cautious")
    """

    def __init__(self, prolog_file: Path | None = None):
        if prolog_file is None:
            prolog_file = Path(__file__).parent / "traits.pl"
        self.prolog_file = prolog_file
        self._prolog: Prolog | None = None
        self._initialized = False
        self._init()

    def _init(self) -> None:
        """Initialize Prolog engine."""
        if not PYSWIP_AVAILABLE:
            logger.warning("pyswip not available, strategic bridge unavailable")
            return

        try:
            self._prolog = Prolog()
            self._prolog.consult(str(self.prolog_file))
            self._initialized = True
            logger.info(f"Strategic bridge initialized: {self.prolog_file}")
        except Exception:
            logger.exception("Failed to initialize bridge")

    def set_context(
        self,
        risk_level: str = "unknown",
        potential_gain: str = "unknown",
        clear: bool = True,
    ) -> None:
        """Assert world state into the Prolog engine.

        Parameters
        ----------
        risk_level:
            One of: "low", "medium", "high", "unknown"
        potential_gain:
            One of: "none", "low", "medium", "high", "unknown"
        clear:
            If True, clear previous assertions first.
        """
        if not self._initialized or self._prolog is None:
            logger.warning("Bridge not initialized")
            return

        try:
            if clear:
                self._clear_context()

            self._prolog.assertz(f"risk_level({risk_level})")
            self._prolog.assertz(f"potential_gain({potential_gain})")
            logger.debug(f"Context set: risk={risk_level}, gain={potential_gain}")
        except Exception:
            logger.exception("Failed to set context")

    def _clear_context(self) -> None:
        """Clear previous world state assertions."""
        if self._prolog is None:
            return

        for level in ["low", "medium", "high", "unknown"]:
            try:
                self._prolog.retract(f"risk_level({level})")
            except Exception:
                pass
        for gain in ["none", "low", "medium", "high", "unknown"]:
            try:
                self._prolog.retract(f"potential_gain({gain})")
            except Exception:
                pass

    def assert_fact(self, fact: str, verified: bool = False) -> None:
        """Assert a fact into the knowledge base.

        Parameters
        ----------
        fact:
            The fact predicate (e.g., "situation_safe").
        verified:
            If True, mark as verified (for epistemology).
        """
        if not self._initialized or self._prolog is None:
            return

        try:
            self._prolog.assertz(f"is_fact({fact})")
            if verified:
                self._prolog.assertz(f"source_verified({fact})")
            logger.debug(f"Fact asserted: {fact} (verified={verified})")
        except Exception:
            logger.exception("Failed to assert fact")

    def decide(
        self,
        personality: str,
    ) -> Generator[dict[str, str], None, None]:
        """Query strategic decision from the engine.

        Parameters
        ----------
        personality:
            One of: "cautious", "opportunistic", "analyst", "idealist"

        Yields
        ------
        dict
            Dict with 'agent' and 'action' keys.
        """
        if not self._initialized or self._prolog is None:
            logger.warning("Bridge not initialized")
            return

        try:
            query = f"decide({personality}, _Profile, Action)"
            for result in self._prolog.query(query):
                yield {"agent": personality, "action": result.get("Action", "unknown")}
        except Exception:
            logger.exception("Decision query failed")

    def knows(self, fact: str) -> bool:
        """Check if agent knows a fact (requires verification).

        Parameters
        ----------
        fact:
            The fact to check.

        Returns
        -------
        bool
            True if fact is known (verified).
        """
        if not self._initialized or self._prolog is None:
            return False

        try:
            result = list(self._prolog.query(f"knows(_Agent, {fact})"))
            return bool(result)
        except Exception:
            return False

    def believes(self, agent: str, fact: str) -> bool:
        """Check if agent believes a fact.

        Parameters
        ----------
        agent:
            The agent ID.
        fact:
            The fact to check.

        Returns
        -------
        bool
            True if agent believes the fact.
        """
        if not self._initialized or self._prolog is None:
            return False

        try:
            result = list(self._prolog.query(f"believes({agent}, {fact})"))
            return bool(result)
        except Exception:
            return False

    def expected_value(self, profile: str) -> float | None:
        """Calculate expected value for a profile.

        Parameters
        ----------
        profile:
            The agent profile.

        Returns
        -------
        float | None
            Expected value or None if calculation fails.
        """
        if not self._initialized or self._prolog is None:
            return None

        try:
            result = list(self._prolog.query(f"expected_value({profile}, Value)"))
            if result:
                return float(result[0].get("Value", 0))
        except Exception:
            logger.exception("Expected value failed")
        return None

    def fitness(
        self,
        my_trait: str,
        opponent_trait: str,
        rounds: int = 100,
    ) -> float | None:
        """Calculate evolutionary fitness between traits.

        Parameters
        ----------
        my_trait:
            My trait (e.g., "tit_for_tat").
        opponent_trait:
            Opponent's trait.
        rounds:
            Number of rounds to simulate.

        Returns
        -------
        float | None
            Average fitness per round.
        """
        if not self._initialized or self._prolog is None:
            return None

        try:
            result = list(self._prolog.query(f"fitness({my_trait}, [{opponent_trait}], {rounds}, Fitness)"))
            if result:
                return float(result[0].get("Fitness", 0))
        except Exception:
            logger.exception("Fitness calculation failed")
        return None


def run_strategic_simulation(
    risk_level: str = "low",
    potential_gain: str = "high",
) -> dict[str, str]:
    """Run a strategic simulation and return all decisions.

    Parameters
    ----------
    risk_level:
        Current risk level.
    potential_gain:
        Current potential gain.

    Returns
    -------
    dict
        Map of personality to action.
    """
    bridge = StrategicBridge()
    bridge.set_context(risk_level=risk_level, potential_gain=potential_gain)

    results = {}
    for personality in ["cautious", "opportunistic", "analyst", "idealist"]:
        for decision in bridge.decide(personality):
            results[personality] = decision["action"]

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Strategic Bridge Demo ===\n")

    print("Scenario: High risk, high potential gain")
    results = run_strategic_simulation(risk_level="high", potential_gain="high")
    for p, a in results.items():
        print(f"  {p}: {a}")

    print("\nScenario: Low risk, high potential gain")
    results = run_strategic_simulation(risk_level="low", potential_gain="high")
    for p, a in results.items():
        print(f"  {p}: {a}")
