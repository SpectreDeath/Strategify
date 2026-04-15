import logging
from typing import Any
import numpy as np

from strategify.sim.model import GeopolModel
from strategify.agents.state_actor import StateActorAgent
from strategify.agents.cognitive_actor import CognitiveActorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_tournament(num_simulations: int = 5, steps_per_sim: int = 10):
    """Run a headless tournament comparing pure game theory against cognitive AI logic."""
    
    logger.info(f"Starting Grand Strategy Tournament ({num_simulations} matches per architecture)")
    
    results = {
        "Nash": {"tension": [], "escalations": []},
        "Cognitive": {"tension": [], "escalations": []}
    }

    from strategify.geo.loader import GeoJSONLoader
    minimal_gdf = GeoJSONLoader.load_from_geojson("minimal.geojson", target_crs="EPSG:3857")

    # Match Part A: Standard Nash Equilibrium Agents
    logger.info("=== Phase A: Nash Equilibrium (StateActorAgent) ===")
    for i in range(num_simulations):
        model = GeopolModel(
            region_gdf=minimal_gdf,
            enable_governance=True,
            enable_economics=False,
            enable_temporal=False
        )
        
        escalation_count = 0
        for step in range(steps_per_sim):
            model.step()
            for a in model.schedule.agents:
                if isinstance(a, StateActorAgent) and a.posture in ["Escalate", "Invade"]:
                    escalation_count += 1
                    
        results["Nash"]["tension"].append(model.governance.global_tension if model.governance else 0)
        results["Nash"]["escalations"].append(escalation_count)

    # Match Part B: Cognitive Agents (LLM + Prolog + Clojure)
    logger.info("=== Phase B: Cognitive AI (CognitiveActorAgent) ===")
    
    import mesa_geo as mg
    original_creator = mg.AgentCreator
    
    class CognitiveCreator(original_creator):
        def __init__(self, agent_class, model, crs):
            super().__init__(agent_class=CognitiveActorAgent, model=model, crs=crs)
            
    mg.AgentCreator = CognitiveCreator
    
    for i in range(num_simulations):
        model = GeopolModel(
            region_gdf=minimal_gdf,
            enable_governance=True,
            enable_economics=False,
            enable_temporal=False
        )
        # Give the cognitive engine a clojure bridge for fast path
        from strategify.logic.clj import ClojureBridge
        model.clj_bridge = ClojureBridge()
        
        escalation_count = 0
        for step in range(steps_per_sim):
            model.step()
            for a in model.schedule.agents:
                if getattr(a, "posture", "Observe") in ["Escalate", "Invade"]:
                    escalation_count += 1
                    
        results["Cognitive"]["tension"].append(model.governance.global_tension if model.governance else 0)
        results["Cognitive"]["escalations"].append(escalation_count)
        
    mg.AgentCreator = original_creator # Restore

    # Summarize results
    print("\n==================================")
    print("TOURNAMENT RESULTS (Lower is better)")
    print("==================================")
    
    nash_t_mean = np.mean(results["Nash"]["tension"])
    nash_e_mean = np.mean(results["Nash"]["escalations"])
    
    cog_t_mean = np.mean(results["Cognitive"]["tension"])
    cog_e_mean = np.mean(results["Cognitive"]["escalations"])
    
    print(f"Standard Nash Agents:")
    print(f"  Avg Final Global Tension: {nash_t_mean:.2f}")
    print(f"  Avg Historical Escalations: {nash_e_mean:.2f}")
    
    print(f"\nCognitive AI Agents:")
    print(f"  Avg Final Global Tension: {cog_t_mean:.2f}")
    print(f"  Avg Historical Escalations: {cog_e_mean:.2f}")
    print("==================================")

if __name__ == "__main__":
    run_tournament()
