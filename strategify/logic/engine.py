"""Python-Prolog bridge for behavioral decision making.

Provides Prolog-based reasoning for agent behaviors with fallback
to pure Python when SWI-Prolog is not available.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from strategify.logic.types import AgentProfile, DecisionResult, Trait

logger = logging.getLogger(__name__)

# Try to import pyswip, provide fallback if not available
try:
    from pyswip import Prolog

    PYSWIP_AVAILABLE = True
except ImportError:
    PYSWIP_AVAILABLE = False
    Prolog = None


@dataclass
class PrologEngine:
    """Bridge between Python agents and Prolog behavioral logic.

    Parameters
    ----------
    prolog_file:
        Path to the Prolog knowledge base. Defaults to traits.pl in this package.
    strict:
        If True, raises exception when Prolog is unavailable.
        If False, falls back to Python implementation.

    Usage
    -----
    >>> engine = PrologEngine()
    >>> profile = AgentProfile(traits=[Trait.RECIPROCITY], resources=5.0)
    >>> result = engine.decide(profile, ["escalate", "deescalate"])
    >>> print(result.action)  # 'deescalate' or 'escalate'
    """

    prolog_file: Path | None = None
    strict: bool = False
    _prolog: Prolog | None = field(default=None, init=False, repr=False)
    _loaded: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.prolog_file is None:
            self.prolog_file = Path(__file__).parent / "traits.pl"
        self._init_prolog()

    def _init_prolog(self) -> None:
        """Initialize Prolog engine or set up fallback."""
        if not PYSWIP_AVAILABLE:
            if self.strict:
                raise ImportError(
                    "pyswip is required for Prolog integration. Install with: pip install strategify[prolog]"
                )
            logger.warning("pyswip not available, using pure Python fallback for logic layer")
            return

        try:
            self._prolog = Prolog()
            # Consult the Prolog file
            self._prolog.consult(str(self.prolog_file))
            self._loaded = True
            logger.info(f"Loaded Prolog knowledge base: {self.prolog_file}")
        except Exception as e:
            logger.warning(f"Failed to load Prolog: {e}, using Python fallback")
            self._loaded = False

    def decide(
        self,
        profile: AgentProfile,
        opponent_history: list[str],
    ) -> DecisionResult:
        """Make a decision based on agent profile and opponent history.

        Parameters
        ----------
        profile:
            The agent's behavioral profile including traits and resources.
        opponent_history:
            List of opponent's past actions ("escalate" or "deescalate").

        Returns
        -------
        DecisionResult
            The chosen action and reasoning trace.
        """
        # Convert history to Prolog format
        prolog_history = self._to_prolog_history(opponent_history)

        if self._loaded and self._prolog is not None:
            return self._prolog_decide(profile, prolog_history)
        else:
            return self._python_fallback_decide(profile, opponent_history)

    def _to_prolog_history(self, history: list[str]) -> list[str]:
        """Convert Python history to Prolog format."""
        prolog_actions = []
        for action in history:
            prolog_actions.append(action.lower())
        return prolog_actions

    def _prolog_decide(
        self,
        profile: AgentProfile,
        history: list[str],
    ) -> DecisionResult:
        """Use Prolog for decision making."""
        # Build Prolog query
        query = f"decide(profile(traits,{profile.resources},{profile.tom_level}), {history}, Action)"

        try:
            result = list(self._prolog.query(query))
            if result:
                action = result[0].get("Action", "deescalate")
                return DecisionResult(
                    action=action,
                    trace=f"prolog:{action}",
                    confidence=1.0,
                )
        except Exception as e:
            logger.warning(f"Prolog query failed: {e}")

        # Fallback on query failure
        return self._python_fallback_decide(profile, history)

    def _python_fallback_decide(
        self,
        profile: AgentProfile,
        history: list[str],
    ) -> DecisionResult:
        """Pure Python fallback when Prolog is unavailable."""
        action = self._apply_traits(profile, history)
        return DecisionResult(
            action=action,
            trace="python_fallback",
            confidence=0.8,
        )

    def _apply_traits(self, profile: AgentProfile, history: list[str]) -> str:
        """Apply behavioral traits in pure Python."""
        traits = profile.traits

        # RECIPROCITY - mirror last move
        if Trait.RECIPROCITY in traits and history:
            return history[-1]

        # TIT_FOR_TAT - copy first move, then reciprocate
        if Trait.TIT_FOR_TAT in traits:
            if not history:
                return "deescalate"
            return history[-1]

        # FORGIVENESS - forgive one defection after 2 cooperations
        if Trait.FORGIVENESS in traits:
            if len(history) < 3:
                return "deescalate"
            defects = sum(1 for a in history if a == "escalate")
            coops = sum(1 for a in history if a == "deescalate")
            if defects == 1 and coops >= 2:
                return "deescalate"
            return history[-1] if history else "deescalate"

        # GRUDGER - never forgive
        if Trait.GRUDGER in traits:
            if "escalate" in history:
                return "escalate"
            return "deescalate"

        # AGGRESSION - attack if resources > 5.0
        if Trait.AGGRESSION in traits:
            if profile.resources > 5.0:
                return "escalate"
            return "deescalate"

        # PACIFIST - always deescalate
        if Trait.PACIFIST in traits:
            return "deescalate"

        # Default: majority vote
        if history:
            coops = sum(1 for a in history if a == "deescalate")
            defects = sum(1 for a in history if a == "escalate")
            if coops >= defects:
                return "deescalate"
            return "escalate"

        return "deescalate"

    def calculate_payoff(
        self,
        my_action: str,
        opponent_action: str,
    ) -> tuple[int, int]:
        """Calculate payoff for action pair.

        Uses the prisoner's dilemma matrix:
        (E, E) -> (0, -1)
        (E, D) -> (3, -2)
        (D, E) -> (-2, 3)
        (D, D) -> (1, 1)
        """
        payoff_matrix = {
            ("escalate", "escalate"): (0, -1),
            ("escalate", "deescalate"): (3, -2),
            ("deescalate", "escalate"): (-2, 3),
            ("deescalate", "deescalate"): (1, 1),
        }
        return payoff_matrix.get(
            (my_action, opponent_action),
            (0, 0),
        )

    def evaluate_fitness(
        self,
        my_traits: list[Trait],
        opponent_traits: list[Trait],
        rounds: int = 100,
    ) -> float:
        """Calculate evolutionary fitness between two trait sets."""
        my_score = 0
        opp_score = 0

        for _ in range(rounds):
            # Simulate round
            my_action = self._apply_traits(
                AgentProfile(traits=my_traits, resources=5.0),
                [],
            )
            opp_action = self._apply_traits(
                AgentProfile(traits=opponent_traits, resources=5.0),
                [],
            )

            m, o = self.calculate_payoff(my_action, opp_action)
            my_score += m
            opp_score += o

        return my_score / rounds

    def trace_decide(
        self,
        profile: AgentProfile,
        opponent_history: list[str],
    ) -> tuple[DecisionResult, str]:
        """Get decision with full reasoning trace."""
        result = self.decide(profile, opponent_history)

        # Build trace
        trace_parts = [
            f"traits:{[t.value for t in profile.traits]}",
            f"history:{opponent_history[-3:] if opponent_history else []}",
            f"decision:{result.action}",
        ]
        trace = " | ".join(trace_parts)

        return result, trace

    def set_context(
        self,
        risk_level: str = "unknown",
        potential_gain: str = "unknown",
    ) -> None:
        """Set decision context (world state) for Prolog queries.

        Parameters
        ----------
        risk_level:
            One of: "low", "medium", "high", "unknown"
        potential_gain:
            One of: "none", "low", "medium", "high", "unknown"
        """
        if not self._loaded or self._prolog is None:
            logger.warning("Prolog not loaded, cannot set context")
            return

        try:
            # Retract existing facts to prevent memory leak
            for level in ["low", "medium", "high", "unknown"]:
                try:
                    self._prolog.retractall(f"risk_level({level})")
                except Exception:
                    pass
            for gain in ["none", "low", "medium", "high", "unknown"]:
                try:
                    self._prolog.retractall(f"potential_gain({gain})")
                except Exception:
                    pass

            # Assert new facts
            self._prolog.assertz(f"risk_level({risk_level})")
            self._prolog.assertz(f"potential_gain({potential_gain})")
            logger.debug(f"Context set: risk={risk_level}, gain={potential_gain}")
        except Exception as e:
            logger.error(f"Failed to set context: {e}")

    def decide_personality(
        self,
        personality: str,
    ) -> DecisionResult:
        """Make decision based on personality type (uses context).

        Parameters
        ----------
        personality:
            One of: "cautious", "opportunistic", "analyst", "idealist"

        Returns
        -------
        DecisionResult
            The chosen action.
        """
        if not self._loaded or self._prolog is None:
            return DecisionResult(
                action="deescalate",
                trace="python_fallback",
                confidence=0.8,
            )

        try:
            query = f"decide({personality}, _Profile, Action)"
            result = list(self._prolog.query(query))
            if result:
                action = result[0].get("Action", "deescalate")
                return DecisionResult(
                    action=action,
                    trace=f"prolog:{personality}:{action}",
                    confidence=1.0,
                )
        except Exception as e:
            logger.warning(f"Personality decision failed: {e}")

        return DecisionResult(
            action="deescalate",
            trace="default_fallback",
            confidence=0.5,
        )


def create_engine(strict: bool = False) -> PrologEngine:
    """Factory function to create a Prolog engine."""
    return PrologEngine(strict=strict)
