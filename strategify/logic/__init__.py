"""Logic layer for behavioral traits and Theory of Mind.

This module provides Prolog-based reasoning for agent behaviors:
- Behavioral traits (Reciprocity, Forgiveness, Aggression)
- Behavioral profiles (Cautious, Opportunistic, Analyst, Idealist)
- Theory of Mind (nested beliefs)
- Epistemology (knows vs believes)
- Hawk-Dove game with Evolutionary Stability (ESS)
- Clojure strategy synthesis (timeline branching)
- Evolutionary payoff calculations

Usage:
    # Trait-based decisions (Axelrod-style)
    from strategify.logic import PrologEngine, Trait, AgentProfile
    engine = PrologEngine()
    profile = AgentProfile(traits=[Trait.RECIPROCITY], resources=5.0)
    action = engine.decide(profile, opponent_history)

    # Personality-based decisions (with context)
    from strategify.logic import StrategicBridge
    bridge = StrategicBridge()
    bridge.set_context(risk_level="low", potential_gain="high")
    decisions = bridge.decide("cautious")

    # Hawk-Dove ESS
    from strategify.logic import is_safe, is_ess
    if is_safe("dove"):
        print("Dove cannot be invaded")

    # Clojure strategy synthesis
    from strategify.logic.clj import ClojureBridge, run_strategy_simulation
    bridge = ClojureBridge()
    timelines = bridge.branch_timelines(state, ["attack", "display"])
"""

from strategify.logic.bridge import StrategicBridge, run_strategic_simulation
from strategify.logic.clj import (
    ClojureBridge,
    run_strategy_simulation,
)
from strategify.logic.engine import PrologEngine
from strategify.logic.hawk_dove import (
    HawkDoveGame,
    get_payoff,
)
from strategify.logic.hawk_dove import (
    is_ess as is_ess,
)
from strategify.logic.hawk_dove import (
    is_safe as hawk_dove_is_safe,
)
from strategify.logic.types import (
    AgentProfile,
    Belief,
    DecisionResult,
    Payoff,
    Personality,
    PotentialGain,
    RiskLevel,
    Trait,
)

__all__ = [
    "PrologEngine",
    "StrategicBridge",
    "run_strategic_simulation",
    "HawkDoveGame",
    "is_safe",
    "is_ess",
    "get_payoff",
    "ClojureBridge",
    "run_strategy_simulation",
    "Trait",
    "Personality",
    "RiskLevel",
    "PotentialGain",
    "AgentProfile",
    "DecisionResult",
    "Belief",
    "Payoff",
]

# Backwards compatibility: expose is_safe from hawk_dove module
is_safe = hawk_dove_is_safe
