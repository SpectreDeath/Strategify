"""Multi-commodity supply chain trade network and vulnerability analysis engine."""

import logging
from dataclasses import dataclass

import networkx as nx

logger = logging.getLogger(__name__)


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


DEGREE_THRESHOLD = 2


class SupplyChainEngine:
    """Multi-commodity supply chain vulnerability and strategic chokepoint analyzer."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()
        self.routes: list[TradeRoute] = []

    def add_route(  # noqa: PLR0913
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

    def compute_chokepoints(self) -> dict[str, ChokepointAssessment]:
        """Calculate NetworkX betweenness centrality and vulnerability per region node."""
        if len(self.graph.nodes) == 0:
            return {}

        centrality = nx.betweenness_centrality(self.graph)
        results: dict[str, ChokepointAssessment] = {}

        for node, c_score in centrality.items():
            connected_edges = list(self.graph.in_edges(node, data=True)) + list(self.graph.out_edges(node, data=True))
            commodities = list({d.get("commodity", "general") for _, _, d in connected_edges})

            # Vulnerability calculation based on centrality and node degree
            degree = self.graph.degree(node)
            vulnerability = min(1.0, float(c_score) * 1.5 + (0.1 if degree > DEGREE_THRESHOLD else 0.0))

            results[node] = ChokepointAssessment(
                node_id=str(node),
                centrality=round(float(c_score), 4),
                vulnerability_score=round(vulnerability, 4),
                critical_commodities=commodities,
            )

        return results

    def export_prolog_facts(self) -> list[str]:
        """Export computed vulnerability scores into Prolog fact strings."""
        assessments = self.compute_chokepoints()
        facts = []
        for node, assessment in assessments.items():
            node_clean = str(node).lower().replace(" ", "_")
            facts.append(f"chokepoint_risk({node_clean}, {assessment.vulnerability_score}).")
        return facts
