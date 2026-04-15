"""GeopolModel: Mesa Model orchestrating world map, agents, and data collection.

Supports arbitrary N-actor scenarios, multiple game types, economic modeling,
escalation ladder, organization actors, and state persistence.
"""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any

import geopandas as gpd
import mesa_geo as mg
from mesa import Model
from mesa.datacollection import DataCollector
from mesa.time import RandomActivation

from strategify.agents.military import UnitType
from strategify.agents.non_state import NonStateActor
from strategify.agents.state_actor import StateActorAgent
from strategify.config.scenarios import (
    DEFAULT_ACTOR_CONFIGS,
    DEFAULT_ALLIANCES,
    DEFAULT_REGION_RESOURCES,
    load_scenario,
    scenario_to_configs,
)
from strategify.config.settings import (
    RANDOM_SEED,
    REAL_WORLD_GEOJSON,
    get_region_color,
)
from strategify.geo.loader import AdjacencyBuilder, GeoJSONLoader
from strategify.logic.bridge import StrategicBridge
from strategify.reasoning.diplomacy import DiplomacyGraph
from strategify.sim.conflict import ConflictEngine
from strategify.sim.environment import EnvironmentalManager

logger = logging.getLogger(__name__)


class GeopolModel(Model):
    """Top-level Mesa Model for a geopolitical simulation.

    Actors interact via game-theoretic decisions on a real-world GeoJSON map.
    Supports N actors, multiple game types, economic modeling, and escalation
    levels.

    Parameters
    ----------
    n_steps:
        Optional maximum steps for headless runs.
    scenario:
        Optional scenario name (e.g. ``"default"``, ``"arms_race"``) or
        path to a JSON scenario file.
    enable_economics:
        Whether to enable the trade network / economic model.
    enable_escalation_ladder:
        Whether to enable the discrete escalation ladder.
    enable_non_state_actors:
        Whether to spawn non-state actors (insurgents, NGOs).
    enable_health:
        Whether to enable the HealthEngine (pandemic spread).
    enable_temporal:
        Whether to enable TemporalDynamics (seasons, elections, economic cycles).
    enable_propaganda:
        Whether to enable the PropagandaEngine (information warfare).
    active_games:
        List of game types agents play. Default: ``["escalation"]``.
    region_gdf:
        Optional pre-loaded GeoDataFrame with ``region_id`` and ``geometry``
        columns. When provided, overrides the GeoJSON file path from the
        scenario.
    """

    def __init__(
        self,
        n_steps: int | None = None,
        scenario: str | Path | None = None,
        enable_economics: bool = True,
        enable_escalation_ladder: bool = True,
        enable_non_state_actors: bool = False,
        enable_health: bool = False,
        enable_temporal: bool = True,
        enable_propaganda: bool = False,
        enable_governance: bool = True,
        active_games: list[str] | None = None,
        region_gdf: gpd.GeoDataFrame | None = None,
    ) -> None:
        # Load scenario config first (no randomness needed) to determine seed
        if scenario is not None:
            scenario_data = load_scenario(scenario)
            actor_configs, region_resources, alliances = scenario_to_configs(scenario_data)
            geojson_name = scenario_data.get("geojson", "real_world.geojson")
            geojson_path = Path(geojson_name)
            if not geojson_path.is_absolute():
                from strategify.config.settings import GEO_DIR

                geojson_path = GEO_DIR / geojson_name
            seed = scenario_data.get("random_seed", RANDOM_SEED)
            self.scenario_name = scenario_data.get("name", str(scenario))
        else:
            actor_configs = DEFAULT_ACTOR_CONFIGS
            region_resources = DEFAULT_REGION_RESOURCES
            alliances = DEFAULT_ALLIANCES
            geojson_path = REAL_WORLD_GEOJSON
            seed = RANDOM_SEED
            self.scenario_name = "default"
            scenario_data = None

        # Initialize Mesa model with determined seed (ensures model.random is deterministic)
        super().__init__(seed=seed)
        random.seed(seed)

        self.n_steps = n_steps
        self.active_games = active_games or ["escalation"]
        self.schedule = RandomActivation(self)
        # Use EPSG:3857 for high-fidelity spatial analysis (meters)
        self.crs = "EPSG:3857"
        self.space = mg.GeoSpace(crs=self.crs, warn_crs_conversion=False)
        self.relations = DiplomacyGraph(self)
        self.region_resources = dict(region_resources)
        self._agent_registry: dict[str, Any] = {}
        self.global_tension = 0.0

        # Load regions from GeoDataFrame or GeoJSON file
        if region_gdf is not None:
            if region_gdf.crs != self.crs:
                self.region_gdf = region_gdf.to_crs(self.crs)
            else:
                self.region_gdf = region_gdf
        else:
            if not geojson_path.exists():
                raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")
            self.region_gdf = GeoJSONLoader.load_from_geojson(geojson_path, target_crs=self.crs)

        # Pre-calculate adjacency (Phase 13)
        self.adjacency = AdjacencyBuilder.build(self.region_gdf)

        # Create agents from GeoDataFrame
        ac = mg.AgentCreator(agent_class=StateActorAgent, model=self, crs=self.crs)
        agents = []
        for idx, row in self.region_gdf.iterrows():
            agent = ac.create_agent(geometry=row.geometry, unique_id=idx)
            agent.region_id = row["region_id"]
            agents.append(agent)

        self.space.add_agents(agents)

        # Configure agents from scenario
        for agent in agents:
            rid = getattr(agent, "region_id", "unknown")
            cfg = actor_configs.get(rid, {})
            if not cfg:
                logger.warning("No config found for region '%s', using defaults", rid)
            agent.capabilities = dict(cfg.get("caps", {"military": 0.5, "economic": 0.5}))
            agent.role = cfg.get("role", "row")
            agent.personality = cfg.get("personality", "Neutral")
            agent.active_games = list(self.active_games)

            # Phase 8: Dynamic game eligibility
            if agent.capabilities.get("military", 0.5) > 0.7 and "cyber" not in agent.active_games:
                agent.active_games.append("cyber")

            # Phase 14: UN membership
            if rid in ["Alpha", "Bravo"]:
                agent.un_seat_type = "Permanent"
            else:
                agent.un_seat_type = "Non-Permanent"

            # Ensure color is assigned for this region
            get_region_color(rid)
            self.add_actor(agent)

            # Spawn initial military units based on capability
            mil_cap = agent.capabilities.get("military", 0.5)
            n_units = int(mil_cap * 5) + 1  # 1-6 units
            for _ in range(n_units):
                agent.military.add_unit(UnitType.Infantry)
            if mil_cap > 0.6:
                agent.military.add_unit(UnitType.Armor)
            if mil_cap > 0.8:
                agent.military.add_unit(UnitType.Air)

        # Diplomacy setup
        self.relations.update_relations()

        # Diplomacy setup
        self.relations.update_relations()

        agents_by_region = {getattr(a, "region_id", ""): a for a in agents}
        for alliance in alliances:
            region_a, region_b, weight = alliance
            agent_a = agents_by_region.get(region_a)
            agent_b = agents_by_region.get(region_b)
            if agent_a and agent_b:
                self.relations.set_relation(agent_a.unique_id, agent_b.unique_id, weight)

        # Economic model
        self.trade_network = None
        self.population_model = None
        if enable_economics:
            from strategify.reasoning.economics import PopulationModel, TradeNetwork

            self.trade_network = TradeNetwork(self)
            self.trade_network.initialize()
            self.population_model = PopulationModel(self)
            self.population_model.initialize()
            # Wire population into trade network for GDP calculation
            self.trade_network.population_model = self.population_model

        # Escalation ladder
        self.escalation_ladder = None
        if enable_escalation_ladder:
            from strategify.agents.escalation import EscalationLadder

            self.escalation_ladder = EscalationLadder(self)
            self.escalation_ladder.initialize()

        # Organization agents (loaded from scenario if present)
        self.organizations: list[Any] = []
        if scenario is not None:
            self._load_organizations(scenario_data)

        # Coalition dispatch engine (optional)
        self.region_gdf["population"] = None
        self.region_gdf["gdp"] = None
        self.region_gdf["faction_influence"] = None

        # Phase 16: Deep Epistemology Bridge
        self.prolog_bridge = StrategicBridge()
        self.prolog_bridge.assert_fact("simulation_started", verified=True)
        self.coalition_engine = None
        self.coalition_tracker = None
        self._enable_coalition = enable_escalation_ladder  # piggyback on escalation flag
        if self._enable_coalition:
            from strategify.game_theory.coalition import (
                CoalitionStateTracker,
                PairwiseGameDispatchEngine,
            )

            self.coalition_engine = PairwiseGameDispatchEngine()
            self.coalition_tracker = CoalitionStateTracker()

        # Phase 3: Strategic diplomacy components
        self.diplomatic_memory = None
        self.signaling = None
        self.summit = None
        if enable_escalation_ladder:
            from strategify.reasoning.diplomacy_phase3 import (
                DiplomaticMemory,
                MultilateralSummit,
                StrategicSignaling,
            )

            self.diplomatic_memory = DiplomaticMemory(self)
            self.diplomatic_memory.initialize()
            self.signaling = StrategicSignaling(self)
            self.signaling.initialize()
            self.summit = MultilateralSummit(self)

        # Conflict Engine (Phase 6)
        self.conflict_engine = ConflictEngine(self)
        self.environmental_manager = EnvironmentalManager(self)

        # Phase 14: Governance
        self.enable_governance = enable_governance
        if self.enable_governance:
            from strategify.reasoning.governance import GovernanceEngine

            self.governance = GovernanceEngine(self)
        else:
            self.governance = None
        self.env_manager = EnvironmentalManager(self)
        self.env_manager.initialize()

        # Health Engine (pandemic spread)
        self.health_engine = None
        if enable_health:
            from strategify.sim.health import HealthEngine

            self.health_engine = HealthEngine(self)
            self.health_engine.initialize()

        # Temporal Dynamics (seasons, elections, economic cycles)
        self.temporal = None
        if enable_temporal:
            from strategify.reasoning.temporal import TemporalDynamics

            self.temporal = TemporalDynamics(self)
            self.temporal.initialize()

        # Propaganda Engine (information warfare)
        self.propaganda = None
        if enable_propaganda:
            from strategify.reasoning.propaganda import PropagandaEngine

            self.propaganda = PropagandaEngine(self)
            self.propaganda.initialize()

        # Non-State Actors (Phase 8)
        self.non_state_actors: list[NonStateActor] = []
        if enable_non_state_actors:
            self._spawn_initial_non_state_actors()

        # OSINT feature pipeline (optional, lazy)
        self.osint_pipeline = None
        self.osint_features: dict[str, dict[str, float]] = {}
        self.osint_refresh_interval = 0  # 0 = disabled, >0 = refresh every N steps

        # LLM decision engine (optional, lazy)
        self.llm_engine = None

        # Dynamic payoff history (optional)
        self.payoff_history = None

        # Auto-briefing (optional)
        self.briefing_interval = 0  # 0 = disabled
        self.briefing_dir: Path | None = None
        self._briefings: list[str] = []

        # Data collection — agent reporters capture post-action state (after
        # schedule.step()).  This is intentional: we record what agents *did*,
        # not what they were going to do.  Pre-action model state (e.g.
        # influence map) is available via self.influence_map before schedule.step().
        agent_reporters = {
            "posture": "posture",
            "region_id": "region_id",
        }
        model_reporters = {
            "step": lambda m: m.schedule.steps,
        }
        self.datacollector = DataCollector(
            model_reporters=model_reporters,
            agent_reporters=agent_reporters,
        )
        self.influence_map = None

    def _load_organizations(self, scenario_data: dict) -> None:
        """Load organization actors from scenario data if present."""
        orgs = scenario_data.get("organizations", [])
        if not orgs:
            return

        from shapely.geometry import Point

        from strategify.agents.organization import OrganizationAgent

        for org_cfg in orgs:
            # Create a point geometry for the org (use first member's centroid or default)
            member_rids = org_cfg.get("members", [])
            member_agents = [a for a in self.schedule.agents if getattr(a, "region_id", "") in member_rids]
            member_ids = [a.unique_id for a in member_agents]

            # Place org at centroid of first member, or default location
            if member_agents:
                centroid = member_agents[0].geometry.centroid
                geometry = Point(centroid.x, centroid.y)
            else:
                geometry = Point(30, 50)  # Default: Eastern Europe

            org = OrganizationAgent(
                unique_id=self.next_id(),
                model=self,
                geometry=geometry,
                crs="EPSG:4326",
                org_type=org_cfg.get("type", "IGO"),
                mandate=org_cfg.get("mandate", "peacekeeping"),
                member_ids=member_ids,
            )
            org.region_id = org_cfg.get("name", f"org_{len(self.organizations)}")
            get_region_color(org.region_id)

            self.add_actor(org)
            self.organizations.append(org)
            self.relations.update_relations()

    def _agents_from_gdf(self, gdf: gpd.GeoDataFrame) -> list:
        """Create StateActorAgent instances from a GeoDataFrame.

        Expects columns ``region_id`` and ``geometry``. Each row becomes
        one agent whose ``unique_id`` is the row index.
        """
        agents = []
        ac = mg.AgentCreator(agent_class=StateActorAgent, model=self, crs=str(gdf.crs or "EPSG:4326"))
        for idx, row in gdf.iterrows():
            agent = ac.create_agent(geometry=row.geometry, unique_id=idx)
            agent.region_id = row["region_id"]
            agents.append(agent)
        return agents

    def step(self) -> None:
        """Advance the simulation by one turn."""
        from strategify.reasoning.influence import InfluenceMap

        self.influence_map = InfluenceMap(self)
        self.influence_map.compute()

        # Step temporal dynamics (before other systems so modifiers apply)
        if self.temporal is not None:
            self.temporal.step()

        # Step economic model
        if self.trade_network is not None:
            self.trade_network.step()
        if self.population_model is not None:
            self.population_model.step()

        # Step escalation ladder
        if self.escalation_ladder is not None:
            self.escalation_ladder.step()

        # Dispatch pairwise games and update coalitions
        if self.coalition_engine is not None:
            state_agents = [a for a in self.schedule.agents if isinstance(a, StateActorAgent)]
            if len(state_agents) >= 2:
                pair_results = self.coalition_engine.dispatch(state_agents, "escalation")
                alliance_weights = {}
                for u, v, data in self.relations.graph.edges(data=True):
                    alliance_weights[tuple(sorted((u, v)))] = data.get("weight", 0.0)
                self.coalition_tracker.update(pair_results, alliance_weights=alliance_weights)

        # Step diplomacy memory and signaling
        if self.diplomatic_memory is not None:
            self.diplomatic_memory.step()
        if self.signaling is not None:
            self.signaling.resolve_signals()

        # Step conflict engine (Phase 6)
        self.conflict_engine.step()

        # Step environmental manager (Phase 9)
        self.env_manager.step()

        # Step health engine (pandemic spread)
        if self.health_engine is not None:
            self.health_engine.step()

        self.schedule.step()

        # Step propaganda engine (information warfare — after agent actions)
        if self.propaganda is not None:
            self.propaganda.step()

        # Phase 16: Sync world events to Prolog epistemology
        self._sync_events_to_prolog()

        # Collect data AFTER agents have acted
        self.datacollector.collect(self)

        # Auto-briefing
        self._maybe_generate_briefing()

        # Auto OSINT refresh
        if (
            self.osint_pipeline is not None
            and self.osint_refresh_interval > 0
            and self.schedule.steps % self.osint_refresh_interval == 0
        ):
            self.refresh_osint()

    def enable_osint(
        self,
        region_keywords: dict[str, list[str]],
        adapters: list[Any] | None = None,
        cache_ttl: int = 3600,
        refresh_interval: int = 0,
    ) -> None:
        """Enable the OSINT feature pipeline.

        Parameters
        ----------
        region_keywords:
            ``{region_id: [keyword, ...]}`` for adapter queries.
        adapters:
            List of OSINT adapter instances. Defaults to ``[GDELTAdapter()]``.
        cache_ttl:
            Cache time-to-live in seconds.
        refresh_interval:
            Auto-refresh OSINT features every N steps. 0 = manual only.
        """
        from strategify.osint.pipeline import FeaturePipeline

        self.osint_pipeline = FeaturePipeline(
            region_keywords=region_keywords,
            adapters=adapters,
            cache_ttl=cache_ttl,
        )
        self.osint_refresh_interval = max(0, refresh_interval)

    def refresh_osint(self, force: bool = False) -> None:
        """Refresh OSINT features from the pipeline.

        Parameters
        ----------
        force:
            If True, bypass cache and fetch fresh data.
        """
        if self.osint_pipeline is not None:
            self.osint_features = self.osint_pipeline.compute(force_refresh=force)

    def enable_llm(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
    ) -> None:
        """Enable the LLM decision engine for agent decisions.

        Parameters
        ----------
        provider:
            LLM provider (``"openai"``, ``"anthropic"``, ``"local"``).
        model:
            Model identifier.
        api_key:
            API key. If None, reads from environment variable.
        """
        from strategify.reasoning.llm import LLMDecisionEngine

        self.llm_engine = LLMDecisionEngine(provider=provider, model=model, api_key=api_key)

    def enable_payoff_history(self) -> None:
        """Enable logging of per-step payoff matrices."""
        from strategify.game_theory.dynamic import PayoffHistory

        self.payoff_history = PayoffHistory()

    def enable_briefing(
        self,
        interval: int = 5,
        output_dir: str | Path | None = None,
    ) -> None:
        """Enable auto-generated intelligence briefings every N steps.

        Parameters
        ----------
        interval:
            Generate a briefing every N steps. 0 = disabled.
        output_dir:
            Directory for briefing files. Defaults to ``reports/``.
        """
        self.briefing_interval = max(0, interval)
        self.briefing_dir = Path(output_dir) if output_dir else Path("reports")
        self.briefing_dir.mkdir(parents=True, exist_ok=True)

    def _maybe_generate_briefing(self) -> None:
        """Generate a briefing if interval is met."""
        if self.briefing_interval <= 0:
            return
        if self.schedule.steps % self.briefing_interval != 0:
            return
        try:
            from strategify.analysis.dashboard import IntelligenceBriefing

            briefing = IntelligenceBriefing(self).generate()
            self._briefings.append(briefing)
            if self.briefing_dir:
                path = self.briefing_dir / f"briefing_step_{self.schedule.steps}.txt"
                path.write_text(briefing)
                logger.info("Generated briefing: %s", path)
        except Exception as exc:
            logger.warning("Briefing generation failed: %s", exc)

    def enable_multiscale(
        self,
        regional_model_factories: dict[str, Any] | None = None,
    ) -> Any:
        """Create a MultiScaleModel using this model as the global scale.

        Parameters
        ----------
        regional_model_factories:
            ``{region_id: factory_fn}`` where each factory returns a
            GeopolModel for a regional sub-simulation.

        Returns
        -------
        MultiScaleModel
            The multi-scale orchestrator.
        """
        from strategify.reasoning.multiscale import MultiScaleModel

        def _global_factory() -> GeopolModel:
            return self

        msm = MultiScaleModel(
            global_model_factory=_global_factory,
            regional_model_factories=regional_model_factories,
        )
        self.multiscale = msm
        return msm

    @property
    def n_agents(self) -> int:
        """Return number of state actor agents (excluding organizations)."""
        return len([a for a in self.schedule.agents if isinstance(a, StateActorAgent)])

    @property
    def n_total_agents(self) -> int:
        """Return total number of agents including organizations."""
        return len(self.schedule.agents)

    def get_agent_by_region(self, region_id: str) -> Any | None:
        """Return the StateActorAgent for a given region_id in O(1).

        Falls back to a linear scan if the registry is missing (should not
        happen after init).
        """
        agent = self._agent_registry.get(region_id)
        if agent is not None:
            return agent
        # Fallback linear scan (shouldn't happen)
        for a in self.schedule.agents:
            if getattr(a, "region_id", "") == region_id:
                return a
        return None

    def _spawn_initial_non_state_actors(self) -> None:
        """Spawn initial insurgent/NGO groups in regions with low stability or high tension."""
        from shapely.geometry import Point

        # Spawn one 'Insurgent' group in 'bravo' (lower caps)
        bravo = next((a for a in self.schedule.agents if getattr(a, "region_id", "") == "bravo"), None)
        if bravo:
            # Place it slightly offset from centroid
            loc = Point(bravo.geometry.centroid.x + 1000, bravo.geometry.centroid.y + 1000)
            insurgent = NonStateActor(self.next_id(), self, loc, self.crs, "Insurgent")
            insurgent.target_region = "bravo"
            self.add_actor(insurgent)
            self.non_state_actors.append(insurgent)
            logger.info("Spawned Insurgent group in region 'bravo'.")

    def add_actor(self, agent: Any) -> None:
        """Add an agent to the model, schedule, and registry."""
        self.schedule.add(agent)
        if not hasattr(agent, "geometry"):
            # For organization or non-state actors that might not be mg.GeoAgent
            # (though they usually are in this project)
            pass
        else:
            try:
                self.space.add_agents([agent])
            except Exception:
                # Already in space
                pass

        rid = getattr(agent, "region_id", None)
        if rid:
            self._agent_registry[rid] = agent

    def remove_actor(self, agent: Any) -> None:
        """Remove an agent from the model, schedule, and registry."""
        self.schedule.remove(agent)
        try:
            self.space.remove_agent(agent)
        except Exception:
            pass

        rid = getattr(agent, "region_id", None)
        if rid in self._agent_registry:
            del self._agent_registry[rid]

    # ---------------------------------------------------------------------------
    # Phase 16: Prolog Epistemology Integration
    # ---------------------------------------------------------------------------

    def _sync_events_to_prolog(self) -> None:
        """Translate major world events to Prolog facts for epistemology.

        This bridges the Python simulation to the Prolog knowledge base,
        enabling agents to reason about what they know vs believe.
        """
        if not hasattr(self, "prolog_bridge") or self.prolog_bridge is None:
            return

        if not getattr(self.prolog_bridge, "_initialized", False):
            return

        try:
            # Track step as a time fact
            self.prolog_bridge._prolog.assertz(f"step({self.schedule.steps})")

            # Track major posture changes as events
            for agent in self.schedule.agents:
                if isinstance(agent, StateActorAgent):
                    region = getattr(agent, "region_id", None)
                    posture = getattr(agent, "posture", None)
                    if region and posture:
                        # Assert posture change event
                        self.prolog_bridge._prolog.assertz(f"action({region}, {posture})")

            # Track conflict events
            if hasattr(self, "conflict_engine"):
                recent_conflicts = getattr(self.conflict_engine, "_recent_combat", [])
                for conflict in recent_conflicts[-3:]:  # Last 3 conflicts
                    if conflict:
                        atkr = conflict.get("attacker")
                        defdr = conflict.get("defender")
                        if atkr and defdr:
                            self.prolog_bridge._prolog.assertz(f"event(combat, {atkr}, {defdr})")

        except Exception as e:
            logger.debug(f"Prolog event sync skipped: {e}")
