"""DiplomacyGraph: Models international relations using NetworkX."""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class DiplomacyGraph:
    """Graph-based representation of diplomatic relations.

    Nodes: Agent Unique IDs
    Edges: Weight in [-1.0, 1.0] where -1 is war/rivalry and 1 is total alliance.
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        self.graph = nx.Graph()

    def update_relations(self) -> None:
        """Initialize or update nodes from the model's agents."""
        for agent in self.model.schedule.agents:
            if agent.unique_id not in self.graph:
                self.graph.add_node(agent.unique_id, name=f"Actor {agent.unique_id}")

    def set_relation(self, id1: int, id2: int, weight: float) -> None:
        """Set relationship weight between two actors."""
        self.graph.add_edge(id1, id2, weight=max(-1.0, min(1.0, weight)))

    def get_relation(self, id1: int, id2: int) -> float:
        """Get relationship weight (defaults to 0.0 if no edge)."""
        if self.graph.has_edge(id1, id2):
            return self.graph[id1][id2]["weight"]
        return 0.0

    def get_allies(self, agent_id: int, threshold: float = 0.5) -> list[int]:
        """Return IDs of agents with relationship >= threshold."""
        allies = []
        for neighbor in self.graph.neighbors(agent_id):
            if self.graph[agent_id][neighbor]["weight"] >= threshold:
                allies.append(neighbor)
        return allies

    def get_rivals(self, agent_id: int, threshold: float = -0.3) -> list[int]:
        """Return IDs of agents with relationship <= threshold (negative)."""
        rivals = []
        for neighbor in self.graph.neighbors(agent_id):
            if self.graph[agent_id][neighbor]["weight"] <= threshold:
                rivals.append(neighbor)
        return rivals

    def get_aggregate_allied_strength(self, agent_id: int, capability: str = "military") -> float:
        """Sum the capabilities of all allies (including self)."""
        allies = self.get_allies(agent_id)
        total = 0.0
        # Include self
        for agent in self.model.schedule.agents:
            if agent.unique_id == agent_id or agent.unique_id in allies:
                total += agent.capabilities.get(capability, 0.5)
        return total
