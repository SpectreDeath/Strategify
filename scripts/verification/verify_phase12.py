"""Phase 12 Verification Script: Missions, Power Projection, and Occupation."""

import mesa_geo as mg
from shapely.geometry import Point
from strategify.sim.model import GeopolModel
from strategify.agents.state_actor import StateActorAgent
from strategify.agents.military import UnitType

def test_unit_missions_and_movement():
    print("Testing unit missions and movement...")
    model = GeopolModel()
    alpha = model.get_agent_by_region("alpha")
    
    # Spawn a unit
    unit = alpha.military.add_unit(UnitType.Armor)
    start_loc = unit.location
    
    # Set a target and mission
    target_loc = Point(start_loc.x + 100000, start_loc.y + 100000)
    unit.mission = "Patrol"
    unit.target_location = target_loc
    
    # Step units
    alpha.military.step()
    
    assert unit.location.x != start_loc.x
    assert unit.location.y != start_loc.y
    print("[DONE] Unit movement verified.")

def test_occupation_stability_impact():
    print("Testing occupation stability impact...")
    model = GeopolModel()
    alpha = model.get_agent_by_region("alpha")
    bravo = model.get_agent_by_region("bravo")
    
    # Set them as rivals
    model.relations.set_relation(alpha.unique_id, bravo.unique_id, -1.0)
    
    # Initial stability
    initial_stability = bravo.stability
    
    # Move alpha's unit into bravo
    unit = alpha.military.add_unit(UnitType.Armor, location=bravo.geometry.centroid)
    unit.mission = "Occupy"
    unit.target_region = "bravo"
    
    # Update bravo stability
    bravo._update_stability("Deescalate")
    
    assert bravo.stability < initial_stability
    print(f"[DONE] Occupation drain verified: {initial_stability:.2f} -> {bravo.stability:.2f}")

def test_influence_map_power():
    print("Testing influence map power integration...")
    model = GeopolModel()
    alpha = model.get_agent_by_region("alpha")
    
    # Initialize influence map explicitly
    from strategify.reasoning.influence import InfluenceMap
    model.influence_map = InfluenceMap(model)
    
    # Initial influence
    model.influence_map.compute()
    init_inf = model.influence_map.get_net_influence("alpha", alpha.unique_id)
    
    # Add several heavy units to alpha in its own region
    for _ in range(5):
        alpha.military.add_unit(UnitType.Armor)
    
    # Recompute influence
    model.influence_map.compute()
    new_inf = model.influence_map.get_net_influence("alpha", alpha.unique_id)
    
    assert new_inf > init_inf
    print(f"[DONE] Influence power integration verified: {init_inf:.2f} -> {new_inf:.2f}")

if __name__ == "__main__":
    try:
        test_unit_missions_and_movement()
        test_occupation_stability_impact()
        test_influence_map_power()
        print("\n[SUCCESS] All Phase 12 verifications PASSED!")
    except Exception as e:
        print(f"\n[FAILURE] Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
