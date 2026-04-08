import os
import sys

# Ensure we can import strategify
sys.path.append(os.getcwd())


from strategify.agents.state_actor import StateActorAgent
from strategify.sim.model import GeopolModel


def test_military_init():
    print("--- Testing Military Initialization ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)

    total_units = 0
    for agent in model.schedule.agents:
        if isinstance(agent, StateActorAgent):
            units = agent.military.units
            print(f"Region {agent.region_id} has {len(units)} units.")
            total_units += len(units)
            for u in units:
                assert u.strength == 1.0
                assert u.readiness == 1.0

    assert total_units > 0
    print(f"Total units spawned: {total_units}")

def test_kinetic_combat():
    print("\n--- Testing Kinetic Combat ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)

    # Pick two non-allied regions (alpha and delta are enemies: weight -0.5)
    alpha = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "alpha")
    delta = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "delta")

    # Move one unit from each to the same point (alpha centroid)
    p_unit = alpha.military.units[0]
    r_unit = delta.military.units[0]

    target_pos = alpha.geometry.centroid
    p_unit.location = target_pos
    r_unit.location = target_pos

    print(f"Initial Strength: alpha={p_unit.strength:.2f}, delta={r_unit.strength:.2f}")

    # Run a step
    model.step()

    # Check if combat happened
    print(f"Post-Step Strength: alpha={p_unit.strength:.2f}, delta={r_unit.strength:.2f}")

    # Both should have lost strength because they were at the same point
    assert p_unit.strength < 1.0
    assert r_unit.strength < 1.0
    print("Combat verified: Strength reduced.")

if __name__ == "__main__":
    try:
        test_military_init()
        test_kinetic_combat()
        print("\nPhase 6 Verification SUCCESSFUL")
    except Exception as e:
        print(f"\nPhase 6 Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
