"""Intelligence collection and analysis capabilities.

This module provides intelligence gathering, analysis, and dissemination
following the pattern of MilitaryComponent in military.py.

Classes:
- IntelligenceSource: Enum for intelligence collection methods
- IntelligenceReport: Dataclass for intelligence products
- IntelligenceComponent: Agent attachment for intelligence capabilities
- IntelligenceNetwork: Multi-source intelligence coordination
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from strategify.agents.state_actor import StateActorAgent

logger = logging.getLogger(__name__)


class IntelligenceSource(Enum):
    """Types of intelligence collection methods."""

    HUMINT = "humint"  # Human intelligence
    SIGINT = "sigint"  # Signals intelligence
    IMINT = "imint"  # Imagery intelligence
    OSINT = "osint"  # Open source intelligence


class CollectionStatus(Enum):
    """Status of intelligence collection operations."""

    IDLE = "idle"
    COLLECTING = "collecting"
    PROCESSING = "processing"
    DISSEMINATING = "disseminating"
    COMPLETE = "complete"


@dataclass
class IntelligenceReport:
    """An intelligence report product.

    Attributes
    ----------
    report_id : str
        Unique identifier for this report.
    source : IntelligenceSource
        Method of collection.
    target_id : str
        Region or agent ID this intel targets.
    content : dict
        Intelligence findings.
    reliability : float
        Reliability score [0.0, 1.0]. Never 1.0 (military intel is probabilistic).
    timestamp : float
        Unix timestamp when collected.
    collection_time : float
        Time spent collecting (seconds).
    """

    report_id: str
    source: IntelligenceSource
    target_id: str
    content: dict[str, Any]
    reliability: float
    timestamp: float
    collection_time: float = 0.0

    def __post_init__(self) -> None:
        self.reliability = min(self.reliability, 0.95)  # Cap at 95%
        self.reliability = max(self.reliability, 0.0)

    def decay_reliability(self, age_seconds: float) -> float:
        """Apply time-based reliability decay.

        Intelligence becomes less reliable as it ages.
        Half-life: 1 hour (3600 seconds)
        """
        half_life = 3600.0
        decay_factor = 0.5 ** (age_seconds / half_life)
        return self.reliability * decay_factor

    def is_stale(self, staleness_threshold: float = 7200.0) -> bool:
        """Check if report is stale (>2 hours by default)."""
        age = time.time() - self.timestamp
        return age > staleness_threshold


@dataclass
class ISRTasking:
    """Intelligence, Surveillance, Reconnaissance tasking order.

    Attributes
    ----------
    task_id : str
        Unique identifier.
    target_region : str
        Region to target.
    source : IntelligenceSource
        Collection method.
    priority : int
        Priority (1=highest).
    status : CollectionStatus
        Current status.
    assigned_platform : str | None
        Platform assigned to this task.
    """

    task_id: str
    target_region: str
    source: IntelligenceSource
    priority: int = 3
    status: CollectionStatus = CollectionStatus.IDLE
    assigned_platform: str | None = None
    created_at: float = field(default_factory=time.time)


class IntelligenceComponent:
    """Attached to StateActorAgent for intelligence capabilities.

    Parameters
    ----------
    owner : StateActorAgent
        The agent that owns this component.
    """

    def __init__(self, owner: StateActorAgent) -> None:
        self.owner = owner
        self.reports: list[IntelligenceReport] = []
        self.pending_tasks: list[ISRTasking] = []
        self.collection_capabilities: dict[IntelligenceSource, float] = {
            IntelligenceSource.HUMINT: 0.3,
            IntelligenceSource.SIGINT: 0.3,
            IntelligenceSource.IMINT: 0.3,
            IntelligenceSource.OSINT: 0.4,
        }
        self.intelligence_network: IntelligenceNetwork | None = None
        self.counter_intel_coverage: float = 0.2

    def collect(
        self,
        source: IntelligenceSource,
        target_region: str,
    ) -> IntelligenceReport | None:
        """Gather intelligence on a target region.

        Parameters
        ----------
        source : IntelligenceSource
            Collection method to use.
        target_region : str
            Region to target.

        Returns
        -------
        IntelligenceReport | None
            Collected report or None if collection failed.
        """
        capability = self.collection_capabilities.get(source, 0.1)
        base_reliability = capability * 0.8

        model = self.owner.model
        target_agent = model.get_agent_by_region(target_region)

        content: dict[str, Any] = {
            "target": target_region,
            "assessed_posture": "unknown",
            "military_activity": "unknown",
            "economic_indicators": {},
        }

        if target_agent:
            if hasattr(target_agent, "posture"):
                content["assessed_posture"] = target_agent.posture
            if hasattr(target_agent, "military"):
                power = target_agent.military.get_total_power()
                content["military_strength"] = power
            if hasattr(target_agent, "stability"):
                content["stability_score"] = target_agent.stability

            relation = model.relations.get_relation(self.owner.unique_id, target_agent.unique_id)
            content["relation_score"] = relation

            if hasattr(target_agent, "capabilities"):
                content["capabilities"] = target_agent.capabilities

        collection_time = np.random.exponential(10.0)
        time.sleep(min(collection_time / 100, 0.01))

        noise = np.random.normal(0, 0.1)
        reliability = max(0.1, min(0.9, base_reliability + noise))

        report = IntelligenceReport(
            report_id=f"{self.owner.region_id}_{source.value}_{int(time.time())}",
            source=source,
            target_id=target_region,
            content=content,
            reliability=reliability,
            timestamp=time.time(),
            collection_time=collection_time,
        )

        self.reports.append(report)
        logger.debug(
            "Agent %s collected %s intel on %s (reliability: %.2f)",
            self.owner.region_id,
            source.value,
            target_region,
            reliability,
        )

        return report

    def analyze(self, report: IntelligenceReport) -> dict[str, Any]:
        """Analyze a raw intelligence report into actionable intelligence.

        Parameters
        ----------
        report : IntelligenceReport
            Raw report to analyze.

        Returns
        -------
        dict
            Analyzed intelligence with assessments.
        """
        age = time.time() - report.timestamp
        current_reliability = report.decay_reliability(age)

        assessment: dict[str, Any] = {
            "report_id": report.report_id,
            "source": report.source.value,
            "target": report.target_id,
            "current_reliability": current_reliability,
            "assessments": {},
            "warnings": [],
            "recommended_actions": [],
        }

        content = report.content

        if "assessed_posture" in content:
            posture = content["assessed_posture"]
            if posture in ("Escalate", "Invade"):
                assessment["warnings"].append(f"Target shows aggressive posture: {posture}")
                assessment["recommended_actions"].append("Increase surveillance")
                assessment["recommended_actions"].append("Alert potential targets")

        if "relation_score" in content:
            relation = content["relation_score"]
            if relation < -0.3:
                assessment["warnings"].append(f"Hostile relations detected: {relation:.2f}")
                assessment["recommended_actions"].append("Pre-position defensive assets")

        if "military_strength" in content:
            strength = content["military_strength"]
            assessment["assessments"]["military_power"] = strength
            if strength > 5.0:
                assessment["warnings"].append(f"Target has significant military power: {strength:.1f}")

        return assessment

    def disseminate(
        self,
        report: IntelligenceReport,
        recipients: list[int],
    ) -> bool:
        """Share intelligence report with allies.

        Parameters
        ----------
        report : IntelligenceReport
            Report to share.
        recipients : list[int]
            Agent IDs to receive the report.

        Returns
        -------
        bool
            True if dissemination successful.
        """
        model = self.owner.model

        for recipient_id in recipients:
            recipient = model._agent_registry.get(recipient_id)
            if recipient is None:
                continue

            if not hasattr(recipient, "intelligence"):
                continue

            reliability_loss = 0.1
            shared_report = IntelligenceReport(
                report_id=f"{report.report_id}_shared_{recipient_id}",
                source=report.source,
                target_id=report.target_id,
                content=report.content.copy(),
                reliability=report.reliability - reliability_loss,
                timestamp=report.timestamp,
                collection_time=report.collection_time,
            )

            recipient.intelligence.reports.append(shared_report)
            logger.debug(
                "Agent %s shared intel with agent %d",
                self.owner.region_id,
                recipient_id,
            )

        return True

    def counter_intelligence(self, target_region: str) -> float:
        """Detect potential espionage activities.

        Parameters
        ----------
        target_region : str
            Region to check.

        Returns
        -------
        float
            Threat score [0.0, 1.0].
        """
        threat_score = 0.0

        model = self.owner.model

        for agent in model.schedule.agents:
            if agent.unique_id == self.owner.unique_id:
                continue

            relation = model.relations.get_relation(self.owner.unique_id, agent.unique_id)

            if relation < -0.2:
                threat_score += (1.0 - relation) * self.counter_intel_coverage

                if hasattr(agent, "intelligence"):
                    agent_capability = sum(agent.intelligence.collection_capabilities.values()) / len(
                        agent.intelligence.collection_capabilities
                    )
                    if agent_capability > 0.5:
                        threat_score += 0.2

        return min(1.0, threat_score)

    def add_task(self, target_region: str, source: IntelligenceSource, priority: int = 3) -> ISRTasking:
        """Create a new ISR tasking order.

        Parameters
        ----------
        target_region : str
            Region to target.
        source : IntelligenceSource
            Collection method.
        priority : int
            Priority (1=highest, 3=lowest).

        Returns
        -------
        ISRTasking
            Created task.
        """
        task = ISRTasking(
            task_id=f"{self.owner.region_id}_task_{len(self.pending_tasks)}",
            target_region=target_region,
            source=source,
            priority=priority,
            status=CollectionStatus.IDLE,
        )
        self.pending_tasks.append(task)
        return task

    def step(self) -> None:
        """Process pending ISR tasks."""
        if not self.pending_tasks:
            return

        self.pending_tasks.sort(key=lambda t: t.priority)

        for task in self.pending_tasks[:2]:
            if task.status == CollectionStatus.IDLE:
                task.status = CollectionStatus.COLLECTING
                self.collect(task.source, task.target_region)
                task.status = CollectionStatus.COMPLETE

        self.pending_tasks = [t for t in self.pending_tasks if t.status != CollectionStatus.COMPLETE]


class IntelligenceNetwork:
    """Manages multiple intelligence sources and tracks collection coverage.

    Parameters
    ----------
    owner : StateActorAgent
        The agent that owns this network.
    """

    def __init__(self, owner: StateActorAgent) -> None:
        self.owner = owner
        self.coverage_map: dict[str, dict[IntelligenceSource, float]] = {}
        self.adversary_capabilities: dict[int, dict[IntelligenceSource, float]] = {}
        self.collection_priority_regions: list[tuple[str, int]] = []

    def calculate_coverage(self, region_id: str) -> float:
        """Calculate intelligence coverage score for a region.

        Parameters
        ----------
        region_id : str
            Region to evaluate.

        Returns
        -------
        float
            Coverage score [0.0, 1.0].
        """
        if region_id not in self.coverage_map:
            return 0.0

        source_scores = self.coverage_map[region_id]
        if not source_scores:
            return 0.0

        weights = {
            IntelligenceSource.HUMINT: 0.3,
            IntelligenceSource.SIGINT: 0.3,
            IntelligenceSource.IMINT: 0.25,
            IntelligenceSource.OSINT: 0.15,
        }

        coverage = sum(score * weights.get(source, 0.1) for source, score in source_scores.items())

        return min(1.0, coverage)

    def update_coverage(
        self,
        region_id: str,
        source: IntelligenceSource,
        quality: float,
    ) -> None:
        """Update coverage map after collection.

        Parameters
        ----------
        region_id : str
            Region that was collected.
        source : IntelligenceSource
            Source used.
        quality : float
            Quality of collection [0.0, 1.0].
        """
        if region_id not in self.coverage_map:
            self.coverage_map[region_id] = {}

        current = self.coverage_map[region_id].get(source, 0.0)
        self.coverage_map[region_id][source] = min(1.0, current + quality * 0.2)

    def track_adversary(
        self,
        adversary_id: int,
        capabilities: dict[IntelligenceSource, float],
    ) -> None:
        """Track an adversary's intelligence capabilities.

        Parameters
        ----------
        adversary_id : int
            Agent ID of adversary.
        capabilities : dict
            Their intelligence capabilities.
        """
        self.adversary_capabilities[adversary_id] = capabilities

    def get_collection_gaps(self, regions: list[str]) -> list[tuple[str, IntelligenceSource]]:
        """Identify gaps in intelligence coverage.

        Parameters
        ----------
        regions : list[str]
            Regions to check.

        Returns
        -------
        list[tuple[str, IntelligenceSource]]
            Gaps as (region, needed_source) tuples.
        """
        gaps: list[tuple[str, IntelligenceSource]] = []

        for region in regions:
            coverage = self.calculate_coverage(region)
            if coverage < 0.5:
                needed_sources = [
                    source for source in IntelligenceSource if self.coverage_map.get(region, {}).get(source, 0.0) < 0.3
                ]
                if needed_sources:
                    gaps.append((region, needed_sources[0]))

        gaps.sort(key=lambda g: self.calculate_coverage(g[0]))
        return gaps[:5]

    def register_with_component(self, component: IntelligenceComponent) -> None:
        """Register this network with an intelligence component.

        Parameters
        ----------
        component : IntelligenceComponent
            Component to register with.
        """
        component.intelligence_network = self
