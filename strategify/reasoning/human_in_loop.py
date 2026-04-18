"""Human-in-loop mode for human override of agent decisions.

Enables human operators to review and override AI agent decisions during
simulation, providing command oversight similar to military C2 systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ReviewStatus(Enum):
    """Status of decision review."""

    PENDING = "pending"
    APPROVED = "approved"
    OVERRIDDEN = "overridden"
    ESCALATED = "escalated"


@dataclass
class HumanDecisionOverride:
    """Record of human decision override."""

    agent_id: int
    original_decision: dict[str, Any]
    override_decision: dict[str, Any] | None
    reviewer_id: str
    status: ReviewStatus
    timestamp: float
    rationale: str


@dataclass
class HumanInLoopConfig:
    """Configuration for human-in-loop mode."""

    enable_overrides: bool = True
    auto_approve_safe: bool = True
    escalation_threshold: float = 0.8
    require_rationale: bool = True
    review_callback: Callable | None = None


class HumanInLoopManager:
    """Manager for human-in-loop decision oversight."""

    def __init__(self, config: HumanInLoopConfig | None = None):
        self.config = config or HumanInLoopConfig()
        self.pending_decisions: dict[int, dict[str, Any]] = {}
        self.override_history: list[HumanDecisionOverride] = []
        self.review_queue: list[int] = []

    def request_decision_review(
        self,
        agent_id: int,
        agent_region: str,
        proposed_decision: dict[str, Any],
        confidence: float,
    ) -> tuple[dict[str, Any], bool]:
        """Request review of agent decision.

        Returns the (potentially modified) decision and whether human approval is needed.
        """
        if self.config.auto_approve_safe and confidence >= (1.0 - self.config.escalation_threshold):
            return proposed_decision, False

        self.pending_decisions[agent_id] = {
            "region": agent_region,
            "proposed": proposed_decision,
            "confidence": confidence,
            "timestamp": self._get_timestamp(),
        }

        if confidence < (1.0 - self.config.escalation_threshold) * 0.5:
            self.review_queue.append(agent_id)
            return proposed_decision, True

        return proposed_decision, False

    def approve_decision(
        self,
        agent_id: int,
        reviewer_id: str = "human_operator",
    ) -> bool:
        """Approve a pending decision."""
        if agent_id not in self.pending_decisions:
            return False

        decision = self.pending_decisions[agent_id]
        override = HumanDecisionOverride(
            agent_id=agent_id,
            original_decision=decision["proposed"],
            override_decision=None,
            reviewer_id=reviewer_id,
            status=ReviewStatus.APPROVED,
            timestamp=self._get_timestamp(),
            rationale="Approved by human",
        )
        self.override_history.append(override)
        del self.pending_decisions[agent_id]

        if agent_id in self.review_queue:
            self.review_queue.remove(agent_id)

        return True

    def override_decision(
        self,
        agent_id: int,
        new_decision: dict[str, Any],
        reviewer_id: str = "human_operator",
        rationale: str = "",
    ) -> bool:
        """Override agent decision with new decision."""
        if agent_id not in self.pending_decisions:
            if agent_id in self.review_queue:
                self.review_queue.remove(agent_id)
            return False

        original = self.pending_decisions[agent_id]["proposed"]

        override = HumanDecisionOverride(
            agent_id=agent_id,
            original_decision=original,
            override_decision=new_decision,
            reviewer_id=reviewer_id,
            status=ReviewStatus.OVERRIDDEN,
            timestamp=self._get_timestamp(),
            rationale=rationale or "Human override",
        )
        self.override_history.append(override)
        del self.pending_decisions[agent_id]

        if agent_id in self.review_queue:
            self.review_queue.remove(agent_id)

        return True

    def get_pending_count(self) -> int:
        """Get number of pending decisions."""
        return len(self.pending_decisions)

    def get_review_queue(self) -> list[int]:
        """Get agents awaiting review."""
        return list(self.review_queue)

    def get_override_stats(self) -> dict[str, int]:
        """Get override statistics."""
        stats = {"approved": 0, "overridden": 0, "escalated": 0}
        for override in self.override_history:
            if override.status == ReviewStatus.APPROVED:
                stats["approved"] += 1
            elif override.status == ReviewStatus.OVERRIDDEN:
                stats["overridden"] += 1
            elif override.status == ReviewStatus.ESCALATED:
                stats["escalated"] += 1
        return stats

    @staticmethod
    def _get_timestamp() -> float:
        """Get current timestamp."""
        import time

        return time.time()


def create_human_in_loop_manager(
    enable_overrides: bool = True,
    auto_approve_safe: bool = True,
    escalation_threshold: float = 0.8,
) -> HumanInLoopManager:
    """Create a human-in-loop manager with specified configuration."""
    config = HumanInLoopConfig(
        enable_overrides=enable_overrides,
        auto_approve_safe=auto_approve_safe,
        escalation_threshold=escalation_threshold,
    )
    return HumanInLoopManager(config)
