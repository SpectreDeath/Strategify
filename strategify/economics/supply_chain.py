"""Multi-commodity supply chain trade network and vulnerability analysis engine.

Tracks commodity flows (oil, semiconductors, grain, gas, rare-earths) across
a directed trade graph, computes chokepoint risk via betweenness centrality,
and supports shock injection (embargo, port closure, sanctions) that propagates
as economic_penalty modifiers on affected StateActorAgents.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import networkx as nx

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class TradeRoute:
    source: str
    target: str
    commodity: str
    capacity: float
    flow: float
    chokepoint_name: str | None = None


@dataclass
class ChokepointAssessment:
    node_id: str
    centrality: float
    vulnerability_score: float
    critical_commodities: list[str]
    # Extended fields for live API serialisation
    bottleneck_score: float = 0.0
    commodity: str = "mixed"
    flow: float = 0.0
    capacity: float = 0.0
    utilization: float = 0.0
    route_count: int = 0
    risk_score: float = 0.0


@dataclass
class CommodityLedger:
    """Per-commodity global supply/demand ledger updated each simulation step."""

    commodity: str
    total_supply: float = 0.0
    total_demand: float = 0.0
    disruption_pct: float = 0.0   # 0-1: fraction of capacity offline from shocks

    @property
    def stress(self) -> float:
        """Supply stress ratio — >1.0 means demand exceeds supply."""
        if self.total_supply <= 0:
            return 1.0
        return max(0.0, self.total_demand / self.total_supply + self.disruption_pct)


@dataclass
class ShockEvent:
    """A supply-chain shock: embargo, port closure, or sanctions."""

    shock_type: str          # "embargo" | "port_closure" | "sanctions"
    source: str              # originating region
    target: str              # affected region / chokepoint / commodity
    commodity: str | None    # None = all commodities
    severity: float          # 0.0–1.0
    duration_steps: int      # -1 = permanent
    step_applied: int = 0
    active: bool = True


DEGREE_THRESHOLD = 2

# Default commodity topology: list of (source, target, commodity, capacity, flow, chokepoint)
DEFAULT_ROUTES: list[tuple[str, str, str, float, float, str | None]] = [
    # Oil/gas flows
    ("RUS", "EUR", "oil",            120.0, 80.0,  "Bosphorus"),
    ("IRN", "CHN", "oil",            100.0, 70.0,  "Hormuz"),
    ("SAU", "ASI", "oil",            150.0, 110.0, "Hormuz"),
    ("USA", "EUR", "oil",             60.0, 40.0,  None),
    ("RUS", "CHN", "gas",            100.0, 65.0,  None),
    ("NOR", "EUR", "gas",             80.0, 60.0,  None),
    # Semiconductors
    ("TWN", "USA", "semiconductors",  90.0, 70.0,  "Malacca"),
    ("KOR", "USA", "semiconductors",  60.0, 45.0,  "Malacca"),
    ("CHN", "EUR", "semiconductors",  50.0, 35.0,  "Suez"),
    # Grain
    ("UKR", "MNA", "grain",           80.0, 55.0,  "Bosphorus"),
    ("RUS", "MNA", "grain",           70.0, 50.0,  "Bosphorus"),
    ("USA", "AFR", "grain",           60.0, 40.0,  None),
    # Rare earths
    ("CHN", "USA", "rare_earths",     50.0, 38.0,  "Malacca"),
    ("CHN", "EUR", "rare_earths",     40.0, 30.0,  "Suez"),
]


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class SupplyChainEngine:
    """Multi-commodity supply chain vulnerability and strategic chokepoint analyzer.

    Parameters
    ----------
    model:
        The active GeopolModel. If provided, shock penalties are applied to
        ``StateActorAgent.capabilities["economic"]`` each step.
    """

    def __init__(self, model: GeopolModel | None = None) -> None:
        self.model = model
        self.graph = nx.DiGraph()
        self.routes: list[TradeRoute] = []
        self.ledgers: dict[str, CommodityLedger] = {}
        self.shocks: list[ShockEvent] = []
        self._step: int = 0
        self._initialized = False

    # ------------------------------------------------------------------
    # Public: setup
    # ------------------------------------------------------------------

    def initialize_default_routes(self) -> None:
        """Populate the graph with the built-in geopolitical commodity topology."""
        for src, tgt, commodity, cap, flow, choke in DEFAULT_ROUTES:
            self.add_route(src, tgt, commodity, cap, flow, choke)
        self._initialized = True
        logger.info("SupplyChainEngine: %d routes loaded", len(self.routes))

    def add_route(
        self,
        source: str,
        target: str,
        commodity: str,
        capacity: float = 100.0,
        flow: float = 50.0,
        chokepoint_name: str | None = None,
    ) -> None:
        """Add a strategic trade route to the network graph."""
        route = TradeRoute(
            source=source,
            target=target,
            commodity=commodity,
            capacity=capacity,
            flow=flow,
            chokepoint_name=chokepoint_name,
        )
        self.routes.append(route)
        self.graph.add_edge(
            source,
            target,
            commodity=commodity,
            capacity=capacity,
            flow=flow,
            chokepoint=chokepoint_name,
        )
        # Update commodity ledger
        if commodity not in self.ledgers:
            self.ledgers[commodity] = CommodityLedger(commodity=commodity)
        self.ledgers[commodity].total_supply += capacity
        self.ledgers[commodity].total_demand += flow

    # ------------------------------------------------------------------
    # Public: shock injection (Phase 22)
    # ------------------------------------------------------------------

    def inject_shock(
        self,
        shock_type: str,
        source: str,
        target: str,
        commodity: str | None = None,
        severity: float = 0.5,
        duration_steps: int = 10,
    ) -> ShockEvent:
        """Inject a supply chain disruption event.

        Parameters
        ----------
        shock_type:
            "embargo", "port_closure", or "sanctions"
        source:
            Region imposing the disruption.
        target:
            Region / chokepoint / commodity affected.
        commodity:
            Specific commodity disrupted, or None for all.
        severity:
            0.0–1.0 disruption fraction.
        duration_steps:
            Number of simulation steps the shock lasts. -1 = permanent.
        """
        shock = ShockEvent(
            shock_type=shock_type,
            source=source,
            target=target,
            commodity=commodity,
            severity=severity,
            duration_steps=duration_steps,
            step_applied=self._step,
        )
        self.shocks.append(shock)
        logger.info(
            "ShockEvent injected: %s by %s on %s (commodity=%s, severity=%.2f, duration=%d)",
            shock_type, source, target, commodity, severity, duration_steps,
        )
        return shock

    # ------------------------------------------------------------------
    # Public: simulation step (called by GeopolModel.step)
    # ------------------------------------------------------------------

    def step(self) -> None:
        """Advance the supply chain by one simulation step.

        1. Expire time-limited shocks.
        2. Recalculate commodity stress ratios.
        3. Apply economic penalty modifiers to affected StateActorAgents.
        """
        self._step += 1
        self._expire_shocks()
        self._update_ledgers()
        self._apply_economic_penalties()

    # ------------------------------------------------------------------
    # Public: analysis queries
    # ------------------------------------------------------------------

    def compute_chokepoints(self) -> dict[str, ChokepointAssessment]:
        """Calculate NetworkX betweenness centrality and vulnerability per node.

        Returns a dict keyed by node_id with full ChokepointAssessment objects
        suitable for direct JSON serialisation by the API.
        """
        if len(self.graph.nodes) == 0:
            return {}

        centrality = nx.betweenness_centrality(self.graph)
        results: dict[str, ChokepointAssessment] = {}

        for node, c_score in centrality.items():
            in_edges = list(self.graph.in_edges(node, data=True))
            out_edges = list(self.graph.out_edges(node, data=True))
            connected_edges = in_edges + out_edges

            commodities = list({d.get("commodity", "general") for _, _, d in connected_edges})
            total_cap = sum(d.get("capacity", 0) for _, _, d in connected_edges)
            total_flow = sum(d.get("flow", 0) for _, _, d in connected_edges)
            utilization = (total_flow / total_cap) if total_cap > 0 else 0.0

            degree = self.graph.degree(node)
            vulnerability = min(1.0, float(c_score) * 1.5 + (0.1 if degree > DEGREE_THRESHOLD else 0.0))

            # Active shocks targeting this node boost the vulnerability
            shock_boost = sum(
                s.severity for s in self.shocks
                if s.active and (s.target == node or s.source == node)
            )
            bottleneck_score = min(1.0, vulnerability + shock_boost * 0.15)

            dominant_commodity = commodities[0] if commodities else "mixed"

            results[node] = ChokepointAssessment(
                node_id=str(node),
                centrality=round(float(c_score), 4),
                vulnerability_score=round(vulnerability, 4),
                critical_commodities=commodities,
                bottleneck_score=round(bottleneck_score, 4),
                commodity=dominant_commodity,
                flow=round(total_flow, 2),
                capacity=round(total_cap, 2),
                utilization=round(utilization, 4),
                route_count=len(connected_edges),
                risk_score=round(bottleneck_score, 4),
            )

        return results

    def get_commodity_status(self) -> dict[str, dict[str, Any]]:
        """Return current ledger status for all commodities."""
        return {
            c: {
                "total_supply": round(ledger.total_supply, 2),
                "total_demand": round(ledger.total_demand, 2),
                "disruption_pct": round(ledger.disruption_pct, 3),
                "stress": round(ledger.stress, 3),
            }
            for c, ledger in self.ledgers.items()
        }

    def get_active_shocks(self) -> list[dict[str, Any]]:
        """Return all currently active shocks as dicts."""
        return [
            {
                "shock_type": s.shock_type,
                "source": s.source,
                "target": s.target,
                "commodity": s.commodity,
                "severity": s.severity,
                "remaining_steps": (
                    s.duration_steps - (self._step - s.step_applied)
                    if s.duration_steps >= 0 else -1
                ),
            }
            for s in self.shocks
            if s.active
        ]

    def export_prolog_facts(self) -> list[str]:
        """Export vulnerability scores and shock events as Prolog fact strings."""
        assessments = self.compute_chokepoints()
        facts = []
        for node, assessment in assessments.items():
            node_clean = str(node).lower().replace(" ", "_")
            facts.append(f"chokepoint_risk({node_clean}, {assessment.vulnerability_score}).")
        for s in self.shocks:
            if s.active:
                src = s.source.lower()
                tgt = s.target.lower()
                facts.append(f"supply_shock({src}, {tgt}, {s.shock_type}, {s.severity}).")
        return facts

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _expire_shocks(self) -> None:
        """Deactivate shocks that have exceeded their duration."""
        for shock in self.shocks:
            if not shock.active:
                continue
            if shock.duration_steps >= 0:
                elapsed = self._step - shock.step_applied
                if elapsed >= shock.duration_steps:
                    shock.active = False
                    logger.info("ShockEvent expired: %s on %s", shock.shock_type, shock.target)

    def _update_ledgers(self) -> None:
        """Recalculate disruption_pct in each commodity ledger from active shocks."""
        # Reset disruptions
        for ledger in self.ledgers.values():
            ledger.disruption_pct = 0.0

        for shock in self.shocks:
            if not shock.active:
                continue
            targets = (
                [shock.commodity] if shock.commodity and shock.commodity in self.ledgers
                else list(self.ledgers.keys())
            )
            for commodity in targets:
                if commodity in self.ledgers:
                    self.ledgers[commodity].disruption_pct = min(
                        1.0,
                        self.ledgers[commodity].disruption_pct + shock.severity * 0.3,
                    )

    def _apply_economic_penalties(self) -> None:
        """Propagate commodity stress onto agent economic capabilities.

        Each active shock targeting a specific region reduces the matching
        StateActorAgent's ``capabilities["economic"]`` by severity * 0.05
        (capped at -0.3 cumulative). The penalty recovers at +0.01/step
        when no active shocks target that region.
        """
        if self.model is None:
            return

        from strategify.agents.state_actor import StateActorAgent

        # Build per-region shock severity totals
        region_penalties: dict[str, float] = {}
        for shock in self.shocks:
            if not shock.active:
                continue
            for agent in self.model.schedule.agents:
                if not isinstance(agent, StateActorAgent):
                    continue
                rid = getattr(agent, "region_id", "")
                if rid and (rid == shock.target or rid == shock.source):
                    region_penalties[rid] = min(
                        0.3, region_penalties.get(rid, 0.0) + shock.severity * 0.05
                    )

        # Apply or recover
        for agent in self.model.schedule.agents:
            if not isinstance(agent, StateActorAgent):
                continue
            rid = getattr(agent, "region_id", "")
            current_eco = agent.capabilities.get("economic", 0.5)
            penalty = region_penalties.get(rid, 0.0)

            if penalty > 0:
                agent.capabilities["economic"] = max(0.05, current_eco - penalty)
            else:
                # Gradual recovery
                agent.capabilities["economic"] = min(1.0, current_eco + 0.01)
