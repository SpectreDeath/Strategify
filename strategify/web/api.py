import logging
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from strategify.sim.model import GeopolModel
from strategify.config.settings import REGION_COLORS

logger = logging.getLogger(__name__)

app = FastAPI(title="Strategify API", version="1.0.0")

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
        "step": model_instance.schedule.steps if model_instance else 0
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
            enable_temporal=True
        )
        return {"success": True, "message": f"Simulation started with scenario {config.scenario_id}"}
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
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
    except Exception as e:
        logger.error(f"Error during simulation step: {e}")
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
            agents_state.append({
                "region_id": agent.region_id,
                "posture": agent.posture,
                "personality": getattr(agent, "personality", "Neutral"),
                "stability": getattr(agent, "stability", 1.0),
                "military_capability": agent.capabilities.get("military", 0.0),
                "economic_capability": agent.capabilities.get("economic", 0.0),
                "color": REGION_COLORS.get(agent.region_id, "gray")
            })
            
    global_tension = getattr(model_instance, "global_tension", 0.0)
    if hasattr(model_instance, "governance") and model_instance.governance:
        global_tension = model_instance.governance.global_tension
        
    return {
        "step": model_instance.schedule.steps,
        "global_tension": global_tension,
        "agents": agents_state
    }
