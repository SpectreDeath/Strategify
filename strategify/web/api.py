import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from strategify.agents.state_actor import StateActorAgent
from strategify.config.settings import REGION_COLORS
from strategify.sim.model import GeopolModel
from strategify.sim.wargame import MultiDomainWargameEngine
from strategify.viz.epidemic_plots import EpidemicPlotter

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

        query_res = bridge.query_facts("agent_belief", agent_id)
        if not query_res:
            return {"agent_id": agent_id, "beliefs": mock_beliefs.get(agent_id, []), "mode": "demo"}

        return {"agent_id": agent_id, "beliefs": query_res, "mode": "production"}
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
    u_arr = [float(0.1 * i) for i in t]
    b64 = plotter.render_trajectory_plot(t, s, i_arr, r, u_arr)
    return {"status": "success", "plot_base64": b64}
