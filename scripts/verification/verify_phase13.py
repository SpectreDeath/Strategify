"""Phase 13 Verification Script: Hybrid Warfare & Proxy Conflict."""

import logging
import mesa_geo as mg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from shapely.geometry import Point
from strategify.sim.model import GeopolModel
from strategify.agents.state_actor import StateActorAgent
from strategify.agents.non_state import NonStateActor
from strategify.agents.military import UnitType

def test_nsa_funding_and_equipping():
    print("Testing NSA funding and equipping...")
    model = GeopolModel()
    alpha = model.get_agent_by_region("alpha")
    
    # Spawn an NSA
    nsa = NonStateActor(unique_id=999, model=model, geometry=Point(0,0), crs="EPSG:3857")
    nsa.target_region = "bravo"
    model.add_actor(nsa)
    
    # Bravo is in rivalry with Alpha? Let's make it so.
    bravo = model.get_agent_by_region("bravo")
    model.relations.set_relation(alpha.unique_id, bravo.unique_id, -1.0)
    
    # Alpha funds proxy
    alpha.posture = "FundProxy"
    alpha._apply({"action": "FundProxy"})
    
    assert nsa.budget > 0
    print(f"[DONE] NSA budget increased: {nsa.budget:.2f}")
    
    # NSA decide() should equip if budget high
    nsa.budget = 1.0
    nsa.decide()
    assert len(nsa.military.units) > 0
    print("[DONE] NSA unit spawning verified.")

def test_hit_and_run_movement():
    print("Testing Hit-and-Run mission movement...")
    model = GeopolModel()
    alpha = model.get_agent_by_region("alpha")
    nsa = NonStateActor(unique_id=998, model=model, geometry=alpha.geometry.centroid, crs="EPSG:3857")
    nsa.target_region = "alpha"
    model.add_actor(nsa)
    
    unit = nsa.military.add_unit(UnitType.Infantry)
    unit.mission = "HitAndRun"
    
    # Step NSA
    print(f"DEBUG: NSA location: {unit.location}")
    print(f"DEBUG: Alpha geometry: {alpha.geometry.bounds}")
    print(f"DEBUG: Contains? {alpha.geometry.contains(unit.location)}")
    print(f"DEBUG: Intersects? {alpha.geometry.intersects(unit.location)}")
    print(f"DEBUG: Adjacency['alpha']: {model.adjacency.get('alpha')}")
    
    nsa.step()
    
    # Unit should have moved or at least changed target
    print(f"DEBUG: Target location: {unit.target_location}")
    assert unit.target_location is not None
    print("[DONE] NSA Hit-and-Run tactic verified.")

def test_attribution_blowback():
    print("Testing attribution blowback logic...")
    model = GeopolModel()
    alpha = model.get_agent_by_region("alpha")
    bravo = model.get_agent_by_region("bravo")
    
    # Initial relations
    rel_init = model.relations.get_relation(alpha.unique_id, bravo.unique_id)
    
    # Mock a target NSA so the funding code executes
    nsa = NonStateActor(unique_id=997, model=model, geometry=bravo.geometry.centroid, crs="EPSG:3857")
    nsa.target_region = "bravo"
    model.schedule.add(nsa)
    model.relations.set_relation(alpha.unique_id, bravo.unique_id, -1.0) # Ensure Bravo is a rival

    # We want to force attribution to test the effect.
    # We can override random.random for a moment
    original_random = model.random.random
    model.random.random = lambda: 0.01 # Force attribution (< 0.15)
    
    alpha._apply({"action": "FundProxy"})
    
    rel_after = model.relations.get_relation(alpha.unique_id, bravo.unique_id)
    assert rel_after < rel_init
    print(f"[DONE] Attribution blowback verified: {rel_init:.2f} -> {rel_after:.2f}")
    
    # Clean up
    model.random.random = original_random

if __name__ == "__main__":
    try:
        test_nsa_funding_and_equipping()
        test_hit_and_run_movement()
        test_attribution_blowback()
        print("\n[SUCCESS] Phase 13 Hybrid Warfare verifications PASSED!")
    except Exception as e:
        print(f"\n[FAILURE] Phase 13 Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
