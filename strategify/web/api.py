import logging
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from strategify.agents.cognitive_actor import CognitiveActorAgent
from strategify.agents.state_actor import StateActorAgent
from strategify.config.settings import REGION_COLORS
from strategify.economics.supply_chain import SupplyChainEngine
from strategify.osint.live_feed import StrategifyLiveFeed
from strategify.reasoning.swarm import StrategifySwarm
from strategify.sim.counterfactual import CounterfactualSimulator
from strategify.sim.infrastructure import CyberPhysicalResilienceEngine
from strategify.sim.model import GeopolModel
from strategify.sim.uncertainty import UncertaintyQuantificationEngine
from strategify.sim.wargame import MultiDomainWargameEngine
from strategify.theory.nash_solver import NashEquilibriumSolver
from strategify.viz.epidemic_plots import EpidemicPlotter
from strategify.viz.war_room_reporter import StrategifyWarRoomReporter

logger = logging.getLogger(__name__)

app = FastAPI(title="Strategify API", version="1.0.0", docs_url="/docs", redoc_url="/redoc")

# Allow requests from the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model_instance = None


class ScenarioConfig(BaseModel):
    scenario_id: str


class InjectActionRequest(BaseModel):
    agent_id: str
    action: str  # "Escalate" | "Deescalate" | "SpreadFakeNews" | "Negotiate" | "Invade" | "Observe"


class AnalysisRequest(BaseModel):
    type: str  # "var" | "granger" | "community" | "risk" | "forecast"
    params: dict[str, Any] = {}


@app.get("/api/status")
def get_status() -> dict[str, Any]:
    return {
        "status": "running",
        "model_initialized": model_instance is not None,
        "step": model_instance.schedule.steps if model_instance else 0,
    }


@app.post("/api/simulation/start")
def start_simulation(config: ScenarioConfig) -> dict[str, Any]:
    global model_instance
    try:
        scenario_file = config.scenario_id

        # Load a default headless instance for the backend
        model_instance = GeopolModel(
            scenario=scenario_file if scenario_file in ["ukraine", "middle_east", "south_china_sea"] else None,
            enable_governance=True,
            enable_economics=True,
            enable_temporal=True,
        )
        return {"success": True, "message": f"Simulation started with scenario {config.scenario_id}"}
    except Exception as err:
        logger.exception("Failed to start simulation")
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.post("/api/simulation/stop")
def stop_simulation() -> dict[str, Any]:
    global model_instance
    model_instance = None
    return {"success": True, "message": "Simulation stopped"}


@app.post("/api/simulation/step")
def step_simulation() -> dict[str, Any]:
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized")

    try:
        model_instance.step()
        return {"success": True, "step": model_instance.schedule.steps}
    except Exception as err:
        logger.exception("Error during simulation step")
        raise HTTPException(status_code=500, detail=str(err)) from err


@app.get("/api/simulation/state")
def get_simulation_state() -> dict[str, Any]:
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized")

    agents_state = [
        {
            "region_id": agent.region_id,
            "posture": agent.posture,
            "personality": getattr(agent, "personality", "Neutral"),
            "stability": getattr(agent, "stability", 1.0),
            "military_capability": agent.capabilities.get("military", 0.0),
            "economic_capability": agent.capabilities.get("economic", 0.0),
            "color": REGION_COLORS.get(agent.region_id, "gray"),
        }
        for agent in model_instance.schedule.agents
        if isinstance(agent, StateActorAgent)
    ]

    global_tension = getattr(model_instance, "global_tension", 0.0)

    return {
        "step": model_instance.schedule.steps,
        "global_tension": global_tension,
        "agents": agents_state,
    }


@app.get("/api/agents/{agent_id}/beliefs")
def get_agent_beliefs(agent_id: str) -> dict[str, Any]:
    """Fetch agent's belief graph — live from model when running, demo fallback otherwise."""
    # Try to pull live beliefs from a running CognitiveActorAgent
    if model_instance:
        for agent in model_instance.schedule.agents:
            rid = getattr(agent, "region_id", "").lower()
            if rid == agent_id.lower() and isinstance(agent, CognitiveActorAgent):
                raw = getattr(agent, "epistemic_beliefs", {})
                beliefs = [
                    {"fact": k, "value": str(v), "source": "live"}
                    for k, v in raw.items()
                ]
                if beliefs:
                    return {"agent_id": agent_id, "beliefs": beliefs, "mode": "live"}

    # Fallback: demo / Prolog mock
    mock_beliefs: dict[str, list[dict[str, str]]] = {
        "usa": [
            {"fact": "russia_military_weak", "source": "prolog"},
            {"fact": "china_economy_strong", "source": "prolog"},
            {"fact": "ukraine_needs_aid", "source": "prolog"},
        ],
        "ukraine": [
            {"fact": "russia_aggressive", "source": "prolog"},
            {"fact": "nato_support_vital", "source": "prolog"},
        ],
        "russia": [
            {"fact": "nato_expanding", "source": "prolog"},
            {"fact": "sanctions_ineffective", "source": "prolog"},
        ],
    }
    try:
        from strategify.logic.bridge import StrategicBridge

        bridge = StrategicBridge()
        if bridge._initialized:
            query_res = [
                b for b in mock_beliefs.get(agent_id, []) if bridge.believes(agent_id, b["fact"])
            ] or mock_beliefs.get(agent_id, [])
            return {"agent_id": agent_id, "beliefs": query_res, "mode": "prolog"}
    except Exception:
        logger.info("Using demo beliefs (Prolog unavailable)")
    return {"agent_id": agent_id, "beliefs": mock_beliefs.get(agent_id, []), "mode": "demo"}


@app.get("/api/agents/{agent_id}/mcts-branches")
def get_mcts_branches(agent_id: str) -> dict[str, Any]:
    """Fetch MCTS timeline branches from Clojure."""
    mock_branches = [
        {"move": "attack", "version": 1, "state": {"p1_strength": 8, "p2_strength": 5}},
        {"move": "display", "version": 1, "state": {"p1_strength": 10, "p2_strength": 10}},
        {"move": "retreat", "version": 1, "state": {"p1_strength": 5, "p2_strength": 12}},
    ]

    try:
        from strategify.logic.clj import ClojureBridge

        bridge = ClojureBridge()
        if not bridge._available:
            return {
                "agent_id": agent_id,
                "branches": mock_branches,
                "count": len(mock_branches),
                "mode": "demo",
                "error": "Clojure unavailable",
            }

        state = {
            "version": 0,
            "players": {agent_id: {"resources": 50}},
            "board": {},
            "history": [],
            "metadata": {},
        }

        branches = bridge.branch_timelines(state, ["attack", "display", "retreat"])
        if not branches:
            return {
                "agent_id": agent_id,
                "branches": mock_branches,
                "count": len(mock_branches),
                "mode": "demo",
                "error": "Clojure returned empty",
            }
        return {
            "agent_id": agent_id,
            "branches": [
                {
                    "move": b.get("history", [{}])[-1].get("action", "unknown") if b.get("history") else "unknown",
                    "version": b.get("version", 0),
                    "state": b,
                }
                for b in branches[:10]
            ],
            "count": len(branches),
            "mode": "production",
        }
    except Exception:
        logger.info("Using demo branches (Clojure unavailable)")
        return {
            "agent_id": agent_id,
            "branches": mock_branches,
            "count": len(mock_branches),
            "mode": "demo",
            "error": "Clojure unavailable",
        }


@app.post("/api/wargame/run")
def run_wargame_api(steps: int = 5) -> dict[str, Any]:
    engine = MultiDomainWargameEngine()
    result = engine.run_wargame(total_steps=steps)
    return {
        "status": "success",
        "total_steps": result.total_steps,
        "winner": result.winner,
        "actor_scores": result.actor_scores,
    }


@app.get("/api/epidemiology/trajectory")
def get_epidemiology_trajectory_plot() -> dict[str, Any]:
    plotter = EpidemicPlotter()
    t = [float(i) for i in range(10)]
    s = [1.0 - i * 0.05 for i in t]
    i_arr = [0.01 + i * 0.02 for i in t]
    r = [0.0 + i * 0.03 for i in t]
    u_arr = [0.1 * i for i in t]
    b64 = plotter.render_trajectory_plot(t, s, i_arr, r, u_arr)
    return {"status": "success", "plot_base64": b64}


@app.post("/api/swarm/deliberate")
def run_swarm_deliberation_api(actor_id: str = "BlueLand") -> dict[str, Any]:
    engine = MultiDomainWargameEngine()
    swarm = StrategifySwarm(actor_id=actor_id)
    res = swarm.deliberate_step(engine)
    return {
        "status": "success",
        "step": res.step,
        "actor_id": res.actor_id,
        "consensus_score": res.consensus_score,
        "consensus_action_vector": res.consensus_action_vector,
        "proposals": [p.__dict__ for p in res.proposals],
    }


@app.get("/api/osint/live-feed")
def get_osint_live_feed_api() -> dict[str, Any]:
    feed = StrategifyLiveFeed()
    events = feed.fetch_live_events()
    return {
        "status": "success",
        "count": len(events),
        "events": [evt.__dict__ for evt in events],
    }


@app.post("/api/counterfactual/simulate")
def run_counterfactual_simulation_api(steps: int = 5, actor_id: str = "BlueLand") -> dict[str, Any]:
    feed = StrategifyLiveFeed()
    events = feed.fetch_live_events()

    engine = MultiDomainWargameEngine()
    snap = feed.calibrate_snapshot(engine.get_state_snapshot(), events, actor_id=actor_id)

    sim = CounterfactualSimulator(actor_id=actor_id)
    branches = sim.simulate_branches(snap, steps=steps)

    return {
        "status": "success",
        "actor_id": actor_id,
        "steps": steps,
        "branches": {b_key: b_res.__dict__ for b_key, b_res in branches.items()},
    }


@app.post("/api/report/generate")
def generate_war_room_report_api(actor_id: str = "BlueLand", steps: int = 3) -> dict[str, Any]:
    reporter = StrategifyWarRoomReporter(actor_id=actor_id)
    payload = reporter.generate_report(steps=steps)
    return {
        "status": "success",
        "title": payload.title,
        "actor_id": payload.actor_id,
        "threat_level": payload.threat_level,
        "readiness_score": payload.readiness_score,
        "infection_cases": payload.infection_cases,
        "gdp_growth_pct": payload.gdp_growth_pct,
        "diplomatic_tension": payload.diplomatic_tension,
        "swarm_consensus_score": payload.swarm_consensus_score,
        "swarm_proposals": payload.swarm_proposals,
        "counterfactual_branches": payload.counterfactual_branches,
        "html_content": payload.html_content,
    }


@app.post("/api/resilience/simulate")
def run_resilience_simulation_api(
    target_node_id: str = "PWR_01",
    cyber_exploit_severity: float = 0.5,
    workforce_absenteeism_pct: float = 0.2,
) -> dict[str, Any]:
    engine = CyberPhysicalResilienceEngine()
    result = engine.inject_disruption(
        target_node_id=target_node_id,
        cyber_exploit_severity=cyber_exploit_severity,
        workforce_absenteeism_pct=workforce_absenteeism_pct,
    )
    return {
        "status": "success",
        "target_node_id": target_node_id,
        "total_nodes": result.total_nodes,
        "collapsed_nodes_count": result.collapsed_nodes_count,
        "degraded_nodes_count": result.degraded_nodes_count,
        "cascade_failure_index": result.cascade_failure_index,
        "systemic_bottleneck_nodes": result.systemic_bottleneck_nodes,
        "mean_time_to_recovery_days": result.mean_time_to_recovery_days,
        "nodes_state": result.nodes_state,
    }


@app.post("/api/uq/simulate")
def run_uncertainty_quantification_api(
    actor_id: str = "BlueLand",
    num_samples: int = 10,
    steps: int = 3,
) -> dict[str, Any]:
    engine = UncertaintyQuantificationEngine(actor_id=actor_id)
    res = engine.run_monte_carlo(num_samples=num_samples, steps=steps)
    return {
        "status": "success",
        "actor_id": actor_id,
        "num_samples": res.num_samples,
        "steps": res.steps,
        "readiness_quantiles": res.readiness_quantiles,
        "infections_quantiles": res.infections_quantiles,
        "gdp_growth_quantiles": res.gdp_growth_quantiles,
        "sensitivity_indices": res.sensitivity_indices,
    }


@app.post("/api/nash/solve")
def solve_nash_equilibrium_api(actor_a: str = "BlueLand", actor_b: str = "RedNation") -> dict[str, Any]:
    solver = NashEquilibriumSolver(actor_a=actor_a, actor_b=actor_b)
    outcome = solver.solve()
    return {
        "status": "success",
        "actor_a": actor_a,
        "actor_b": actor_b,
        "has_pure_equilibrium": outcome.has_pure_equilibrium,
        "pure_equilibria": outcome.pure_equilibria,
        "mixed_probabilities_a": outcome.mixed_probabilities_a,
        "mixed_probabilities_b": outcome.mixed_probabilities_b,
        "expected_payoff_a": outcome.expected_payoff_a,
        "expected_payoff_b": outcome.expected_payoff_b,
        "pareto_efficiency_score": outcome.pareto_efficiency_score,
        "bargaining_agreement": outcome.bargaining_agreement,
    }


@app.get("/api/agents/{agent_id}/logs")
def get_agent_decision_logs(agent_id: str) -> dict[str, Any]:
    """Fetch decision audit trace log — live from CognitiveActorAgent when running."""
    if model_instance:
        for agent in model_instance.schedule.agents:
            rid = getattr(agent, "region_id", "").lower()
            if rid == agent_id.lower() and isinstance(agent, CognitiveActorAgent):
                log = getattr(agent, "decision_log", [])
                return {"agent_id": agent_id, "logs": log, "mode": "live"}

    # Demo fallback
    return {
        "agent_id": agent_id,
        "mode": "demo",
        "logs": [
            {
                "step": 1,
                "timestamp": "2026-08-08T05:00:00Z",
                "action": "Escalate posture to Defensive",
                "reasoning": "Detected military buildup and hostile propaganda belief score > 0.75",
                "prompt_snippet": "State: High tension. Epistemic belief: russia_aggressive=True. Recommend posture.",
            },
            {
                "step": 2,
                "timestamp": "2026-08-08T05:05:00Z",
                "action": "Offer Economic Pact",
                "reasoning": "MCTS projected 82% survival probability on trade expansion path",
                "prompt_snippet": "State: Economic strain. Clojure MCTS timeline: display posture gives highest stability.",
            },
        ],
    }


@app.post("/api/analysis/run")
def run_analysis(request: AnalysisRequest) -> dict[str, Any]:
    """Run a live analysis against the active simulation model."""
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized — start a simulation first")

    analysis_type = request.type
    params = request.params

    try:
        if analysis_type == "var":
            from strategify.analysis.timeseries import fit_var_model, prepare_agent_timeseries

            df = model_instance.datacollector.get_agent_vars_dataframe()
            ts = prepare_agent_timeseries(df)
            result = fit_var_model(ts, maxlags=params.get("maxlags", 3))
            # forecast is ndarray — convert to list for JSON
            forecast = result.get("forecast")
            return {
                "type": "var",
                "optimal_lags": result.get("optimal_lags", 0),
                "regions": result.get("regions", []),
                "forecast": forecast.tolist() if hasattr(forecast, "tolist") else [],
                "summary_snippet": str(result.get("model_summary", ""))[:500],
            }

        elif analysis_type == "granger":
            from strategify.analysis.timeseries import pairwise_granger_causality, prepare_agent_timeseries

            df = model_instance.datacollector.get_agent_vars_dataframe()
            ts = prepare_agent_timeseries(df)
            raw = pairwise_granger_causality(ts, maxlag=params.get("maxlag", 3))
            # Convert tuple keys to strings
            pairs = [
                {"cause": k[0], "effect": k[1], **v}
                for k, v in raw.items()
            ]
            causal_pairs = [p for p in pairs if p.get("causes")]
            return {
                "type": "granger",
                "total_pairs": len(pairs),
                "causal_pairs": causal_pairs,
                "all_pairs": pairs,
            }

        elif analysis_type == "community":
            from strategify.analysis.communities import detect_communities

            result = detect_communities(model_instance)
            # Map agent IDs back to region names
            id_to_region = {
                agent.unique_id: getattr(agent, "region_id", str(agent.unique_id))
                for agent in model_instance.schedule.agents
            }
            named_communities = [
                [id_to_region.get(aid, str(aid)) for aid in community]
                for community in result.get("communities", [])
            ]
            return {
                "type": "community",
                "num_communities": result.get("num_communities", 0),
                "modularity": result.get("modularity", 0.0),
                "communities": named_communities,
            }

        elif analysis_type == "risk":
            from strategify.analysis.strategic_risk import assess_all_risks

            risks = assess_all_risks(model_instance)
            return {
                "type": "risk",
                "risks": [
                    {
                        "region": r.region_id,
                        "threat_score": r.threat_score,
                        "risk_level": r.risk_level.value if hasattr(r.risk_level, "value") else str(r.risk_level),
                        "volatility": r.volatility,
                    }
                    for r in risks
                ],
            }

        elif analysis_type == "forecast":
            from strategify.analysis.forecasting import forecast_all_regions

            df = model_instance.datacollector.get_agent_vars_dataframe()
            forecasts = forecast_all_regions(df, steps=params.get("steps", 5))
            return {
                "type": "forecast",
                "forecasts": {
                    region: {"forecast": vals.tolist() if hasattr(vals, "tolist") else list(vals)}
                    for region, vals in forecasts.items()
                },
            }

        else:
            # Raise before entering the catch-all except to satisfy TRY301
            pass

    except HTTPException:
        raise
    except Exception as err:
        logger.exception("Analysis run failed")
        raise HTTPException(status_code=500, detail=str(err)) from err

    raise HTTPException(status_code=400, detail=f"Unknown analysis type: {analysis_type}")


@app.post("/api/simulation/inject-action")
def inject_human_action(request: InjectActionRequest) -> dict[str, Any]:
    """Human-in-the-Loop: override a state actor's posture/action for the next step."""
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized")

    posture_map = {
        "Escalate": "Escalate",
        "Deescalate": "Deescalate",
        "Observe": "Observe",
        "Invade": "Invade",
        "Negotiate": "Deescalate",  # maps negotiate intent to deescalate posture
        "SpreadFakeNews": "Observe",  # deceptive posture
    }

    target_posture = posture_map.get(request.action)
    if not target_posture:
        raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}. Valid: {list(posture_map)!r}")

    matched = False
    for agent in model_instance.schedule.agents:
        rid = getattr(agent, "region_id", "").lower()
        if rid == request.agent_id.lower() and isinstance(agent, StateActorAgent):
            agent.posture = target_posture
            # If the action is SpreadFakeNews, flag deception
            if request.action == "SpreadFakeNews":
                agent.propaganda_active = True  # type: ignore[attr-defined]
            matched = True
            break

    if not matched:
        raise HTTPException(status_code=404, detail=f"Agent '{request.agent_id}' not found in active simulation")

    return {
        "success": True,
        "agent_id": request.agent_id,
        "action": request.action,
        "new_posture": target_posture,
        "step": model_instance.schedule.steps,
    }


@app.get("/api/map/geojson")
def get_live_map_geojson() -> dict[str, Any]:
    """Return a GeoJSON FeatureCollection with live simulation state per region."""
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized")

    # Build a posture → risk colour mapping for choropleth
    posture_colors: dict[str, str] = {
        "Invade": "#e94560",
        "Escalate": "#ff7043",
        "Deploy": "#ffa726",
        "Observe": "#66bb6a",
        "Deescalate": "#29b6f6",
        "Withdraw": "#ab47bc",
    }

    features = []
    for agent in model_instance.schedule.agents:
        if not isinstance(agent, StateActorAgent):
            continue
        rid = getattr(agent, "region_id", "UNKNOWN")
        posture = getattr(agent, "posture", "Observe")
        stability = getattr(agent, "stability", 1.0)
        military = agent.capabilities.get("military", 0.0)
        economic = agent.capabilities.get("economic", 0.0)
        tension = round((military + (1.0 - stability)) * 50, 1)

        # Pull geometry if the agent has a shape (mesa-geo)
        shape = getattr(agent, "shape", None)
        geometry = None
        if shape is not None:
            try:
                import json

                from shapely.geometry import mapping
                geometry = json.loads(json.dumps(mapping(shape)))
            except Exception:
                geometry = None

        features.append({
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "region_id": rid,
                "posture": posture,
                "tension": tension,
                "stability": round(stability, 3),
                "military": round(military, 3),
                "economic": round(economic, 3),
                "color": posture_colors.get(posture, REGION_COLORS.get(rid, "#888888")),
            },
        })

    return {
        "type": "FeatureCollection",
        "step": model_instance.schedule.steps,
        "global_tension": getattr(model_instance, "global_tension", 0.0),
        "features": features,
    }


@app.get("/api/economics/chokepoints")
def get_supply_chain_chokepoints() -> dict[str, Any]:
    """Calculate strategic trade network chokepoints across commodities."""
    engine = SupplyChainEngine()
    engine.add_route("USA", "Ukraine", "semiconductors", capacity=120.0, flow=85.0, chokepoint_name="Bosphorus")
    engine.add_route("Ukraine", "Poland", "grain", capacity=200.0, flow=150.0, chokepoint_name="BlackSea")
    engine.add_route("MiddleEast", "USA", "oil", capacity=500.0, flow=420.0, chokepoint_name="Hormuz")
    engine.add_route("China", "Russia", "semiconductors", capacity=300.0, flow=210.0, chokepoint_name="Malacca")

    chokepoints = engine.compute_chokepoints()
    prolog_facts = engine.export_prolog_facts()

    return {
        "status": "success",
        "chokepoints": {node: assessment.__dict__ for node, assessment in chokepoints.items()},
        "prolog_facts": prolog_facts,
    }


connected_websockets: list[WebSocket] = []


@app.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket) -> None:
    """Real-time simulation state streaming over WebSocket."""
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "step" and model_instance:
                model_instance.step()
                state = get_simulation_state()
                await websocket.send_json(state)
            elif data == "state" and model_instance:
                state = get_simulation_state()
                await websocket.send_json(state)
            else:
                await websocket.send_json(
                    {"status": "connected", "step": model_instance.schedule.steps if model_instance else 0}
                )
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)
    except Exception as err:
        logger.warning(f"WebSocket error: {err}")
        if websocket in connected_websockets:
            connected_websockets.remove(websocket)
