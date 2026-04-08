"""Economic model: trade flows, GDP growth, population, sanctions, and resources.

Provides a TradeNetwork that tracks bilateral trade via a NetworkX directed
graph, computes GDP with time-series growth from resource production and
trade balance, models sanctions as trade node blockers, and exposes economic
features for agent decision-making.

Also provides PopulationModel for tracking per-region population dynamics
with resource-dependent growth rates.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import networkx as nx

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)

# GDP growth rates by economic capability tier
_GROWTH_RATES = {
    "high": 0.03,  # 3% per step
    "medium": 0.02,  # 2% per step
    "low": 0.01,  # 1% per step
}

# Population growth rates (per step, applied to population base)
_POP_GROWTH = {
    "high": 0.015,  # 1.5% per step
    "medium": 0.01,  # 1.0% per step
    "low": 0.005,  # 0.5% per step
}

# Base population per unit of region resources
_POP_BASE_FACTOR = 1_000_000  # 1M per resource unit


def _growth_tier(capability: float) -> str:
    """Map economic capability to growth tier."""
    if capability >= 0.7:
        return "high"
    elif capability >= 0.4:
        return "medium"
    return "low"


class PopulationModel:
    """Tracks per-region population with resource-dependent growth.

    Population grows based on economic capability tier and is influenced
    by available resources. Larger populations contribute to GDP through
    a labor force multiplier.

    Parameters
    ----------
    model:
        The parent GeopolModel.
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        # population[uid] = current population (float, can be large)
        self.population: dict[int, float] = {}
        # population_history[uid] = list of population values per step
        self.population_history: dict[int, list[float]] = {}
        # growth_rate[uid] = per-step growth rate
        self.growth_rate: dict[int, float] = {}

    def initialize(self) -> None:
        """Set initial population from region resources and capabilities."""
        for agent in self.model.schedule.agents:
            uid = agent.unique_id
            resources = self.model.region_resources.get(agent.region_id, 1.0)
            base_pop = resources * _POP_BASE_FACTOR
            self.population[uid] = base_pop
            self.population_history[uid] = [base_pop]

            eco_cap = agent.capabilities.get("economic", 0.5)
            tier = _growth_tier(eco_cap)
            self.growth_rate[uid] = _POP_GROWTH[tier]

    def step(self) -> None:
        """Advance population by one step with compound growth."""
        for agent in self.model.schedule.agents:
            uid = agent.unique_id
            if uid not in self.population:
                continue

            rate = self.growth_rate.get(uid, 0.01)
            resources = self.model.region_resources.get(agent.region_id, 1.0)

            # Resource constraint: growth slows if resources are scarce
            resource_factor = min(
                1.0, resources / max(self.population[uid] / _POP_BASE_FACTOR, 0.1)
            )

            # Escalation penalty: conflict reduces population growth
            escalation_penalty = 0.0
            if agent.posture == "Escalate":
                escalation_penalty = 0.005  # -0.5% during conflict

            effective_rate = rate * resource_factor - escalation_penalty
            self.population[uid] *= 1.0 + effective_rate
            self.population[uid] = max(0.0, self.population[uid])

            self.population_history.setdefault(uid, []).append(self.population[uid])

    def get_population(self, unique_id: int) -> float:
        """Return current population for an agent."""
        return self.population.get(unique_id, 0.0)

    def get_growth_rate(self, unique_id: int) -> float:
        """Return per-step growth rate for an agent."""
        return self.growth_rate.get(unique_id, 0.01)

    def get_labor_multiplier(self, unique_id: int) -> float:
        """Return a GDP multiplier based on population size.

        Larger populations provide more labor, boosting economic output.
        Returns a value in [0.5, 2.0].
        """
        pop = self.population.get(unique_id, 0.0)
        if pop <= 0:
            return 0.5
        # Log scale: 1M = 1.0x, 10M = 1.5x, 100M = 2.0x
        import math

        log_pop = math.log10(max(pop, 1.0))
        return max(0.5, min(2.0, 0.5 + 0.3 * log_pop))

    def summary(self) -> dict[str, Any]:
        """Return population model summary."""
        total_pop = sum(self.population.values())
        return {
            "total_population": total_pop,
            "regions_tracked": len(self.population),
            "avg_growth_rate": (sum(self.growth_rate.values()) / max(1, len(self.growth_rate))),
        }


class TradeNetwork:
    """Tracks bilateral trade relationships and economic state.

    Uses a NetworkX directed graph for bilateral flows, supports GDP
    growth modeling, and provides sanctions logic for blocking trade
    between specific actors.

    Parameters
    ----------
    model:
        The parent GeopolModel.
    """

    def __init__(self, model: GeopolModel) -> None:
        self.model = model
        # trade_flows[(id_a, id_b)] = volume (legacy dict, synced with graph)
        self.trade_flows: dict[tuple[int, int], float] = {}
        # flows_graph: directed NetworkX graph of bilateral trade
        self.flows_graph: nx.DiGraph = nx.DiGraph()
        # gdp[unique_id] = current GDP
        self.gdp: dict[int, float] = {}
        # gdp_history[unique_id] = list of GDP values per step
        self.gdp_history: dict[int, list[float]] = {}
        # trade_balance[unique_id] = net exports
        self.trade_balance: dict[int, float] = {}
        # sanctions[source_uid] = set of target_uids being sanctioned
        self.sanctions: dict[int, set[int]] = {}
        # growth_rate[unique_id] = per-step GDP growth rate
        self.growth_rate: dict[int, float] = {}
        # population_model reference (set after initialization)
        self.population_model: PopulationModel | None = None

    def initialize(self) -> None:
        """Set up initial trade flows from agent capabilities and alliances."""
        agents = list(self.model.schedule.agents)
        self.trade_flows = {}
        self.gdp = {}
        self.gdp_history = {}
        self.trade_balance = {}
        self.sanctions = {}
        self.growth_rate = {}
        self.flows_graph = nx.DiGraph()

        for agent in agents:
            base_gdp = agent.capabilities.get("economic", 0.5) * self.model.region_resources.get(
                agent.region_id, 1.0
            )
            uid = agent.unique_id
            self.gdp[uid] = base_gdp
            self.gdp_history[uid] = [base_gdp]
            self.trade_balance[uid] = 0.0
            self.sanctions[uid] = set()
            tier = _growth_tier(agent.capabilities.get("economic", 0.5))
            self.growth_rate[uid] = _GROWTH_RATES[tier]
            self.flows_graph.add_node(uid)

        # Initialize bilateral trade from alliance weights
        for i, a in enumerate(agents):
            for j in range(i + 1, len(agents)):
                b = agents[j]
                weight = self.model.relations.get_relation(a.unique_id, b.unique_id)
                # Allies trade more; rivals trade less
                base_flow = 0.1 * (1.0 + weight)
                volume = max(0.0, base_flow)
                self.trade_flows[(a.unique_id, b.unique_id)] = volume
                self.trade_flows[(b.unique_id, a.unique_id)] = volume
                self.flows_graph.add_edge(a.unique_id, b.unique_id, volume=volume)
                self.flows_graph.add_edge(b.unique_id, a.unique_id, volume=volume)

    def step(self) -> None:
        """Update trade flows, GDP growth, and sanctions for one step."""
        agents = list(self.model.schedule.agents)

        # Apply sanctions: zero out blocked flows
        self._apply_sanctions()

        # Update trade flows based on current relations
        for (uid_a, uid_b), volume in list(self.trade_flows.items()):
            if uid_a > uid_b:
                continue  # process each pair once
            weight = self.model.relations.get_relation(uid_a, uid_b)
            # Escalation reduces trade
            agent_a = next((a for a in agents if a.unique_id == uid_a), None)
            agent_b = next((a for a in agents if a.unique_id == uid_b), None)
            escalation_penalty = 0.0
            if agent_a and agent_a.posture == "Escalate":
                escalation_penalty += 0.3
            if agent_b and agent_b.posture == "Escalate":
                escalation_penalty += 0.3

            # Sanctions penalty
            san_penalty = 0.0
            if uid_b in self.sanctions.get(uid_a, set()):
                san_penalty += 0.5
            if uid_a in self.sanctions.get(uid_b, set()):
                san_penalty += 0.5

            new_volume = max(0.0, volume * (1.0 + 0.1 * weight - escalation_penalty - san_penalty))
            # Smooth transition
            smoothed = 0.7 * volume + 0.3 * new_volume
            self.trade_flows[(uid_a, uid_b)] = smoothed
            self.trade_flows[(uid_b, uid_a)] = smoothed

            # Sync with graph
            if self.flows_graph.has_edge(uid_a, uid_b):
                self.flows_graph[uid_a][uid_b]["volume"] = smoothed
            if self.flows_graph.has_edge(uid_b, uid_a):
                self.flows_graph[uid_b][uid_a]["volume"] = smoothed

        # Recompute GDP with growth
        for agent in agents:
            uid = agent.unique_id
            base_production = agent.capabilities.get(
                "economic", 0.5
            ) * self.model.region_resources.get(agent.region_id, 1.0)

            # Sum trade flows
            exports = 0.0
            imports = 0.0
            for (uid_a, uid_b), volume in self.trade_flows.items():
                if uid_a == uid:
                    exports += volume
                elif uid_b == uid:
                    imports += volume

            self.trade_balance[uid] = exports - imports

            # GDP = production * labor_multiplier + trade balance, with compound growth
            labor_mult = 1.0
            if self.population_model is not None:
                labor_mult = self.population_model.get_labor_multiplier(uid)
            growth_factor = 1.0 + self.growth_rate.get(uid, 0.02)
            raw_gdp = (base_production * labor_mult + self.trade_balance[uid]) * growth_factor
            self.gdp[uid] = max(0.0, raw_gdp)

            # Track history
            self.gdp_history.setdefault(uid, []).append(self.gdp[uid])

    # ------------------------------------------------------------------
    # Sanctions API
    # ------------------------------------------------------------------

    def get_partners(self, region_id: str) -> list[int]:
        """Return list of trade partner unique_ids for a given region_id.

        Partners are agents that have a non-zero trade flow with the given
        region in the flows graph.
        """
        # Find unique_id for this region_id
        uid = None
        for agent in self.model.schedule.agents:
            if getattr(agent, "region_id", "") == region_id:
                uid = agent.unique_id
                break
        if uid is None:
            return []
        if uid not in self.flows_graph:
            return []
        return [
            n
            for n in self.flows_graph.neighbors(uid)
            if self.flows_graph[uid][n].get("volume", 0) > 0
        ]

    def impose_sanction(self, source_uid: int, target_uid: int) -> None:
        """Impose a trade sanction from source on target.

        Reduces bilateral trade volume and marks the relationship.
        """
        self.sanctions.setdefault(source_uid, set()).add(target_uid)
        logger.info("Sanction imposed: agent %d → agent %d", source_uid, target_uid)

    def lift_sanction(self, source_uid: int, target_uid: int) -> None:
        """Remove a previously imposed sanction."""
        if source_uid in self.sanctions:
            self.sanctions[source_uid].discard(target_uid)

    def is_sanctioned(self, source_uid: int, target_uid: int) -> bool:
        """Check if source has an active sanction against target."""
        return target_uid in self.sanctions.get(source_uid, set())

    def _apply_sanctions(self) -> None:
        """Zero out trade flows blocked by sanctions."""
        for source_uid, targets in self.sanctions.items():
            for target_uid in targets:
                pair = (source_uid, target_uid)
                if pair in self.trade_flows:
                    self.trade_flows[pair] = 0.0
                if self.flows_graph.has_edge(source_uid, target_uid):
                    self.flows_graph[source_uid][target_uid]["volume"] = 0.0

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_gdp(self, unique_id: int) -> float:
        """Return current GDP for an agent."""
        return self.gdp.get(unique_id, 0.0)

    def get_gdp_growth(self, unique_id: int) -> float:
        """Return GDP growth rate for an agent."""
        return self.growth_rate.get(unique_id, 0.02)

    def get_gdp_history(self, unique_id: int) -> list[float]:
        """Return GDP history for an agent."""
        return self.gdp_history.get(unique_id, [])

    def get_trade_balance(self, unique_id: int) -> float:
        """Return net trade balance for an agent."""
        return self.trade_balance.get(unique_id, 0.0)

    def get_bilateral_trade(self, id_a: int, id_b: int) -> float:
        """Return trade volume between two agents."""
        return self.trade_flows.get((id_a, id_b), 0.0)

    def get_total_trade(self, unique_id: int) -> float:
        """Return total trade volume (exports + imports) for an agent."""
        total = 0.0
        for (uid_a, uid_b), volume in self.trade_flows.items():
            if uid_a == unique_id or uid_b == unique_id:
                total += volume
        return total

    def get_sanction_targets(self, source_uid: int) -> set[int]:
        """Return set of agents being sanctioned by source."""
        return set(self.sanctions.get(source_uid, set()))

    def get_economic_features(self, unique_id: int) -> dict[str, float]:
        """Return economic feature dict for use in agent decisions."""
        n_sanctions_imposed = len(self.sanctions.get(unique_id, set()))
        n_sanctions_received = sum(1 for targets in self.sanctions.values() if unique_id in targets)
        return {
            "gdp": self.get_gdp(unique_id),
            "gdp_growth": self.get_gdp_growth(unique_id),
            "trade_balance": self.get_trade_balance(unique_id),
            "total_trade": self.get_total_trade(unique_id),
            "sanctions_imposed": float(n_sanctions_imposed),
            "sanctions_received": float(n_sanctions_received),
        }

    def summary(self) -> dict[str, Any]:
        """Return network-level summary."""
        return {
            "n_nodes": self.flows_graph.number_of_nodes(),
            "n_edges": self.flows_graph.number_of_edges(),
            "total_gdp": sum(self.gdp.values()),
            "total_sanctions": sum(len(s) for s in self.sanctions.values()),
            "avg_trade_volume": (sum(self.trade_flows.values()) / max(1, len(self.trade_flows))),
        }
