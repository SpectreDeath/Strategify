import logging
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from strategify.config.settings import REGION_COLORS
from strategify.sim.model import GeopolModel

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
    except Exception:
        logger.exception("Failed to start simulation")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/simulation/stop")
def stop_simulation() -> dict[str, Any]:
    global model_instance
    model_instance = None
    return {"success": True, "message": "Simulation stopped"}


@app.post("/api/simulation/step")
def step_simulation() -> dict[str, Any]:
    global model_instance
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized")

    try:
        model_instance.step()
        return {"success": True, "step": model_instance.schedule.steps}
    except Exception:
        logger.exception("Error during simulation step")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/simulation/state")
def get_simulation_state() -> dict[str, Any]:
    global model_instance
    if not model_instance:
        raise HTTPException(status_code=400, detail="Model not initialized")

    agents_state = []
    from strategify.agents.state_actor import StateActorAgent

    for agent in model_instance.schedule.agents:
        if isinstance(agent, StateActorAgent):
            agents_state.append(
                {
                    "region_id": agent.region_id,
                    "posture": agent.posture,
                    "personality": getattr(agent, "personality", "Neutral"),
                    "stability": getattr(agent, "stability", 1.0),
                    "military_capability": agent.capabilities.get("military", 0.0),
                    "economic_capability": agent.capabilities.get("economic", 0.0),
                    "color": REGION_COLORS.get(agent.region_id, "gray"),
                }
            )

    global_tension = getattr(model_instance, "global_tension", 0.0)
    if hasattr(model_instance, "governance") and model_instance.governance:
        global_tension = model_instance.governance.global_tension

    return {"step": model_instance.schedule.steps, "global_tension": global_tension, "agents": agents_state}


# =============================================================================
# Phase 20: XAI Endpoints - Beliefs and MCTS
# =============================================================================


@app.get("/api/agents/{agent_id}/beliefs")
def get_agent_beliefs(agent_id: str) -> dict[str, Any]:
    """Fetch agent's belief graph from Prolog."""
    MOCK_BELIEFS = {
        "usa": [
            {"fact": "russia_military_weak", "source": "prolog"},
            {"fact": "china_economic_growth", "source": "prolog"},
            {"fact": "ukraine_nato_expansion", "source": "prolog"},
            {"fact": "global_tension_rising", "source": "verified"},
        ],
        "russia": [
            {"fact": "ukraine_west_support", "source": "prolog"},
            {"fact": "nato_encirclement", "source": "prolog"},
            {"fact": "sanctions_effective", "source": "prolog"},
        ],
        "china": [
            {"fact": "taiwan_independence", "source": "prolog"},
            {"fact": "us_pacific_dominance", "source": "prolog"},
            {"fact": "south_china_sea_claim", "source": "verified"},
        ],
    }

    try:
        from strategify.logic.bridge import StrategicBridge

        bridge = StrategicBridge()
        if not bridge._initialized:
            beliefs = MOCK_BELIEFS.get(agent_id.lower(), [{"fact": f"demo_belief_{agent_id}", "source": "prolog"}])
            return {"agent_id": agent_id, "beliefs": beliefs, "count": len(beliefs), "mode": "demo"}

        beliefs = []
        for result in bridge._prolog.query(f"believes({agent_id}, Fact)"):
            fact_str = str(result.get("Fact", ""))
            if fact_str:
                beliefs.append({"fact": fact_str, "source": "prolog"})

        for result in bridge._prolog.query(f"knows({agent_id}, Fact)"):
            fact_str = str(result.get("Fact", ""))
            if fact_str:
                beliefs.append({"fact": fact_str, "source": "verified"})

        return {"agent_id": agent_id, "beliefs": beliefs, "count": len(beliefs), "mode": "production"}
    except Exception:
        logger.info("Using demo beliefs (Prolog unavailable)")
        beliefs = MOCK_BELIEFS.get(agent_id.lower(), [{"fact": f"demo_belief_{agent_id}", "source": "prolog"}])
        return {
            "agent_id": agent_id,
            "beliefs": beliefs,
            "count": len(beliefs),
            "mode": "demo",
            "error": "Prolog unavailable",
        }


@app.get("/api/agents/{agent_id}/mcts-branches")
def get_mcts_branches(agent_id: str) -> dict[str, Any]:
    """Fetch MCTS timeline branches from Clojure."""
    MOCK_BRANCHES = [
        {"move": "attack", "version": 1, "state": {"p1_strength": 8, "p2_strength": 5}},
        {"move": "display", "version": 1, "state": {"p1_strength": 10, "p2_strength": 10}},
        {"move": "retreat", "version": 1, "state": {"p1_strength": 10, "p2_strength": 8}},
    ]

    try:
        from strategify.logic.clj import ClojureBridge

        bridge = ClojureBridge()
        if not bridge._available:
            return {
                "agent_id": agent_id,
                "branches": MOCK_BRANCHES,
                "count": len(MOCK_BRANCHES),
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
                "branches": MOCK_BRANCHES,
                "count": len(MOCK_BRANCHES),
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
            "branches": MOCK_BRANCHES,
            "count": len(MOCK_BRANCHES),
            "mode": "demo",
            "error": "Clojure unavailable",
        }
