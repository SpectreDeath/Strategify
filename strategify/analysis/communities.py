"""Alliance and community detection using CDlib.

Detects emergent coalition blocs in the DiplomacyGraph using
Louvain community detection. Tracks community evolution over time.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cdlib import algorithms as cd_algorithms

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


def detect_communities(model: GeopolModel) -> dict:
    """Run Louvain community detection on the diplomacy graph.

    Only positive edges (alliances) are used for community detection.
    Negative edges (rivalries) are excluded since Louvain requires
    non-negative weights.

    Parameters
    ----------
    model:
        The active GeopolModel with a DiplomacyGraph.

    Returns
    -------
    dict
        {"communities": list[list[int]], "num_communities": int, "modularity": float}
    """
    import networkx as nx

    graph = model.relations.graph
    if graph.number_of_nodes() < 2:
        return {"communities": [], "num_communities": 0, "modularity": 0.0}

    # Create a subgraph with only positive edges (alliances)
    positive_graph = nx.Graph()
    for node in graph.nodes():
        positive_graph.add_node(node, **graph.nodes[node])
    for u, v, data in graph.edges(data=True):
        weight = data.get("weight", 0.0)
        if weight > 0:
            positive_graph.add_edge(u, v, weight=weight)

    # If no positive edges, each node is its own community
    if positive_graph.number_of_edges() == 0:
        communities = [[n] for n in graph.nodes()]
        return {
            "communities": communities,
            "num_communities": len(communities),
            "modularity": 0.0,
        }

    communities = cd_algorithms.louvain(positive_graph)
    return {
        "communities": [list(c) for c in communities.communities],
        "num_communities": len(communities.communities),
        "modularity": communities.newman_girvan_modularity().score,
    }


def detect_communities_over_time(model: GeopolModel, n_steps: int = 20) -> list[dict]:
    """Track community detection results over simulation steps.

    Parameters
    ----------
    model:
        The active GeopolModel.
    n_steps:
        Number of steps to simulate.

    Returns
    -------
    list[dict]
        List of community detection results, one per step.
    """
    history = []
    for _ in range(n_steps):
        model.step()
        result = detect_communities(model)
        result["step"] = len(history)
        history.append(result)
    return history


def find_agent_community(agent_id: int, communities: list[list[int]]) -> int | None:
    """Find which community an agent belongs to.

    Returns the community index, or None if not found.
    """
    for i, community in enumerate(communities):
        if agent_id in community:
            return i
    return None
