"""Deception & Counter-Intelligence Engine.

Enables state actors to conduct covert operations, maskirovka signaling,
and inject deceptive intelligence reports into rival intelligence networks.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any

from strategify.agents.intelligence import IntelligenceReport, IntelligenceSource

logger = logging.getLogger(__name__)


@dataclass
class DeceptiveSignal:
    """A deceptive posture or military signal sent to mislead rivals."""

    source_agent_id: str
    target_agent_id: str
    purported_posture: str
    true_posture: str
    credibility: float = 0.8
    active: bool = True


class DeceptionEngine:
    """Engine for executing strategic deception and intelligence manipulation.

    Parameters
    ----------
    agent : Any
        StateActorAgent owning this deception engine.
    """

    def __init__(self, agent: Any) -> None:
        self.agent = agent
        self.active_deceptions: list[DeceptiveSignal] = []

    def create_feint(self, target_id: str, purported_posture: str) -> DeceptiveSignal:
        """Create a feint military signal (maskirovka) to mislead target.

        Parameters
        ----------
        target_id : str
            Rival agent identifier.
        purported_posture : str
            False posture (e.g. 'Invade', 'Deescalate') to signal.

        Returns
        -------
        DeceptiveSignal
            Deceptive signal object.
        """
        signal = DeceptiveSignal(
            source_agent_id=self.agent.region_id,
            target_agent_id=target_id,
            purported_posture=purported_posture,
            true_posture=self.agent.posture,
            credibility=min(1.0, self.agent.capabilities.get("intelligence", 0.5) + 0.3),
        )
        self.active_deceptions.append(signal)
        logger.info(
            "Agent %s created feint posture '%s' targeting %s (true posture: %s)",
            self.agent.region_id,
            purported_posture,
            target_id,
            self.agent.posture,
        )
        return signal

    def inject_deceptive_intelligence(self, target_agent: Any) -> bool:
        """Inject false intelligence report into target agent's intelligence component.

        Parameters
        ----------
        target_agent : Any
            The rival state actor agent.

        Returns
        -------
        bool
            True if injection succeeded.
        """
        if not hasattr(target_agent, "intelligence"):
            return False

        # Attempt intelligence spoofing based on intelligence capability comparison
        my_intel = self.agent.capabilities.get("intelligence", 0.5)
        their_intel = target_agent.capabilities.get("intelligence", 0.5)

        success_prob = max(0.2, min(0.9, 0.5 + (my_intel - their_intel)))
        if random.random() < success_prob:
            report = IntelligenceReport(
                report_id=f"deceptive_intel_{self.agent.unique_id}_{random.randint(1000, 9999)}",
                source=IntelligenceSource.HUMINT,
                target_id=self.agent.region_id,
                content={
                    "assessed_posture": "Deescalate" if self.agent.posture in ("Invade", "Escalate") else "Invade",
                    "military_strength": 10.0,
                    "is_deceptive": True,
                },
                reliability=0.85,
                timestamp=time.time(),
            )
            target_agent.intelligence.reports.append(report)
            logger.info("Agent %s successfully injected deceptive intel into %s", self.agent.region_id, target_agent.region_id)
            return True

        logger.info("Agent %s failed deceptive intel injection against %s", self.agent.region_id, target_agent.region_id)
        return False
