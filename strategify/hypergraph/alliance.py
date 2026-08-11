"""Multilateral Alliance & Geopolitical Hypergraph Tracker for Strategify."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from em_cubed.hypergraph.exporter import export_store_to_gexf
from em_cubed.hypergraph.metrics import jaccard_similarity, overlap_coefficient
from em_cubed.hypergraph.store import HypergraphStore
from em_cubed.hypergraph.types import Hyperedge


class MultilateralAllianceTracker:
    """Tracks complex multi-state alliances, treaties, and proxy defense pacts using N-ary hyperedges."""

    def __init__(self) -> None:
        self.store = HypergraphStore()

    def register_treaty(
        self,
        alliance_id: str,
        member_states: Set[str],
        commitment_level: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Hyperedge:
        """Register a multilateral defense pact or alliance hyperedge."""
        meta = metadata or {}
        meta["commitment_level"] = commitment_level

        edge = Hyperedge(
            edge_id=alliance_id,
            member_entities=member_states,
            metadata=meta,
        )
        self.store.add_edge(edge)
        return edge

    def get_shared_alliances(self, state_a: str, state_b: str) -> Set[Hyperedge]:
        """Return all hyperedges/treaties that include both state_a and state_b."""
        return self.store.query_by_intersection({state_a, state_b})

    def calculate_alliance_overlap(self, state_a: str, state_b: str) -> float:
        """Calculate Jaccard similarity of alliance portfolios between two states."""
        edges_a = {e.edge_id for e in self.store.get_edges_for_entity(state_a)}
        edges_b = {e.edge_id for e in self.store.get_edges_for_entity(state_b)}
        return jaccard_similarity(edges_a, edges_b)

    def calculate_coalition_overlap(self, state_a: str, state_b: str) -> float:
        """Calculate overlap coefficient between alliance portfolios."""
        edges_a = {e.edge_id for e in self.store.get_edges_for_entity(state_a)}
        edges_b = {e.edge_id for e in self.store.get_edges_for_entity(state_b)}
        return overlap_coefficient(edges_a, edges_b)

    def get_all_alliances(self) -> List[Hyperedge]:
        """Return list of all registered multilateral alliance hyperedges."""
        return self.store.all_edges()

    def export_gexf(self, filepath: Union[str, Path], mode: str = "bipartite") -> str:
        """Export alliance hypergraph to GEXF XML for Gephi visualization."""
        return export_store_to_gexf(self.store, filepath, mode=mode)
