"""Strategic Cyber-Physical Digital Twin & Infrastructure Resilience Engine.

Models critical physical infrastructure networks (power grids, semiconductor fabs,
pharmaceutical manufacturing, satellite uplink stations) and simulates cascade failures
triggered by cyber exploits, EW jamming, and pandemic workforce absenteeism.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class InfrastructureNode:
    """Represents a node in critical national infrastructure network."""

    node_id: str
    name: str
    sector: str  # 'Power', 'Semiconductor', 'Pharma', 'Satellite', 'Transport'
    capacity: float = 100.0  # Operational capacity %
    status: str = "Operational"  # 'Operational', 'Degraded', 'Collapsed'
    dependencies: list[str] = field(default_factory=list)
    vulnerability_index: float = 0.3  # 0.0 to 1.0 vulnerability rating


@dataclass
class CascadeResult:
    """Outcome of a cyber-physical infrastructure cascade stress simulation."""

    total_nodes: int
    collapsed_nodes_count: int
    degraded_nodes_count: int
    cascade_failure_index: float  # Percentage of network collapsed
    systemic_bottleneck_nodes: list[str]
    mean_time_to_recovery_days: float
    nodes_state: dict[str, dict[str, Any]]


class CyberPhysicalResilienceEngine:
    """Engine simulating cyber-physical infrastructure network cascades."""

    def __init__(self, region_id: str = "BlueLand") -> None:
        self.region_id = region_id
        self.nodes: dict[str, InfrastructureNode] = self._build_default_network()

    def _build_default_network(self) -> dict[str, InfrastructureNode]:
        """Build default baseline infrastructure network."""
        return {
            "PWR_01": InfrastructureNode("PWR_01", "Primary Power Grid", "Power", dependencies=[]),
            "FAB_01": InfrastructureNode("FAB_01", "Semiconductor Fab A", "Semiconductor", dependencies=["PWR_01"]),
            "MED_01": InfrastructureNode("MED_01", "Pharma Vaccine Lab", "Pharma", dependencies=["PWR_01", "FAB_01"]),
            "SAT_01": InfrastructureNode("SAT_01", "Satellite Ground HQ", "Satellite", dependencies=["PWR_01"]),
            "TRN_01": InfrastructureNode("TRN_01", "Logistics Supply Hub", "Transport", dependencies=["PWR_01", "FAB_01"]),
        }

    def inject_disruption(
        self,
        target_node_id: str,
        cyber_exploit_severity: float = 0.5,
        workforce_absenteeism_pct: float = 0.2,
    ) -> CascadeResult:
        """Inject cyber/physical attack and simulate failure propagation cascade.

        Parameters
        ----------
        target_node_id : str
            Target node ID to attack/disrupt.
        cyber_exploit_severity : float
            Severity of cyber exploit (0.0 to 1.0).
        workforce_absenteeism_pct : float
            Pandemic workforce absenteeism percentage.

        Returns
        -------
        CascadeResult
            Cascade failure analysis result.
        """
        logger.info("Injecting cyber-physical disruption into node %s...", target_node_id)

        if target_node_id in self.nodes:
            target = self.nodes[target_node_id]
            impact = (cyber_exploit_severity + workforce_absenteeism_pct) * 100.0
            target.capacity = max(0.0, target.capacity - impact)
            if target.capacity < 20.0:
                target.status = "Collapsed"
            elif target.capacity < 70.0:
                target.status = "Degraded"

        # Propagate cascade dependencies
        changed = True
        while changed:
            changed = False
            for node in self.nodes.values():
                if node.status == "Collapsed":
                    continue

                for dep_id in node.dependencies:
                    if dep_id in self.nodes and self.nodes[dep_id].status == "Collapsed":
                        # Downstream dependency collapse
                        node.capacity = max(0.0, node.capacity - 50.0)
                        if node.capacity < 20.0:
                            node.status = "Collapsed"
                            changed = True
                        elif node.capacity < 70.0:
                            node.status = "Degraded"
                            changed = True

        collapsed = [nid for nid, n in self.nodes.items() if n.status == "Collapsed"]
        degraded = [nid for nid, n in self.nodes.items() if n.status == "Degraded"]
        total = len(self.nodes)

        cascade_index = len(collapsed) / total if total > 0 else 0.0
        mttr = len(collapsed) * 3.5 + len(degraded) * 1.2

        return CascadeResult(
            total_nodes=total,
            collapsed_nodes_count=len(collapsed),
            degraded_nodes_count=len(degraded),
            cascade_failure_index=cascade_index,
            systemic_bottleneck_nodes=collapsed,
            mean_time_to_recovery_days=mttr,
            nodes_state={nid: n.__dict__ for nid, n in self.nodes.items()},
        )
