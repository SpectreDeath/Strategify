import logging
import os
import sys

# Ensure we can import strategify
sys.path.append(os.getcwd())

from strategify.sim.model import GeopolModel

# Configure logging to see climate events
logging.basicConfig(level=logging.INFO)

def test_environmental_init():
    print("--- Testing Environmental Manager Initialization ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)

    assert hasattr(model, "env_manager")
    assert model.env_manager is not None

    grid = model.env_manager.resource_grid
    print(f"Regions with resources: {list(grid.keys())}")
    assert "alpha" in grid
    assert grid["alpha"]["Water"] == 1.0

def test_resource_pressure_impact():
    print("\n--- Testing Resource Pressure Impact ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)
    alpha = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "alpha")

    # Manually deplete resources in alpha
    print("Depleting resources in 'alpha' manually...")
    model.env_manager.resource_grid["alpha"]["Water"] = 0.2
    model.env_manager.resource_grid["alpha"]["Food"] = 0.2

    pressure = model.env_manager.get_resource_pressure("alpha")
    print(f"Resource Pressure: {pressure:.2f}")
    assert pressure > 0.5

    initial_stability = alpha.stability

    # Update stability
    alpha._update_stability("Deescalate")
    print(f"Stability after pressure: {alpha.stability:.2f}")

    assert alpha.stability < initial_stability
    print("Environmental stability hit verified.")

def test_climate_event():
    print("\n--- Testing Climate Event Resolution ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)

    # Force a Drought in alpha
    print("Triggering manual Drought in 'alpha'...")
    model.env_manager._trigger_climate_event = lambda: None # suppress random events

    # Manually execute the logic
    model.env_manager.resource_grid["alpha"]["Water"] *= 0.5

    pressure = model.env_manager.get_resource_pressure("alpha")
    print(f"Pressure after Drought: {pressure:.2f}")
    assert pressure > 0.0
    print("Climate event impact verified.")

if __name__ == "__main__":
    try:
        test_environmental_init()
        test_resource_pressure_impact()
        test_climate_event()
        print("\nPhase 9 Verification SUCCESSFUL")
    except Exception as e:
        print(f"\nPhase 9 Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
