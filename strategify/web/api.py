import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from strategify.agents.state_actor import StateActorAgent
from strategify.config.settings import REGION_COLORS
from strategify.osint.live_feed import StrategifyLiveFeed
from strategify.reasoning.swarm import StrategifySwarm
from strategify.sim.counterfactual import CounterfactualSimulator
from strategify.sim.infrastructure import CyberPhysicalResilienceEngine
from strategify.sim.model import GeopolModel
from strategify.sim.wargame import MultiDomainWargameEngine
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
    """Fetch agent's belief graph from Prolog."""
    mock_beliefs = {
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
        if not bridge._initialized:
            return {"agent_id": agent_id, "beliefs": mock_beliefs.get(agent_id, []), "mode": "demo"}

        query_res = [b for b in mock_beliefs.get(agent_id, []) if bridge.believes(agent_id, b["fact"])] or mock_beliefs.get(agent_id, [])
        return {"agent_id": agent_id, "beliefs": query_res, "mode": "demo"}
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
