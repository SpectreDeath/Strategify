import logging
import os
import sys

# Ensure we can import strategify
sys.path.append(os.getcwd())

from strategify.sim.model import GeopolModel

# Configure logging to see stability warnings
logging.basicConfig(level=logging.WARNING)

def test_stability_fluctuation():
    print("--- Testing Political Stability ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)

    # Pick an agent: alpha (Aggressor)
    alpha = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "alpha")

    # Hawks support 'Escalate', Doves support 'Deescalate'
    # Default Hawks power 0.3, Doves 0.3, Industrialists 0.4

    initial_stability = alpha.stability
    print(f"Initial Stability: {initial_stability:.2f}")

    # Force 'Escalate' (Supported by Hawks: power 0.3)
    # Total support = 0.3. Weighted average will drop stability.
    for _ in range(5):
        alpha._update_stability("Escalate")
        print(f"Stability after 'Escalate': {alpha.stability:.2f}")

    # Stability should drop because total support (0.3) < target (1.0)
    assert alpha.stability < initial_stability
    print("Stability drop verified.")

def test_stability_reform():
    print("\n--- Testing Domestic Reform Trigger ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True)
    alpha = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "alpha")

    # Force an action with NO support (e.g. 'InvalidAction')
    # Support = 0.0
    for i in range(20):
        alpha._update_stability("InvalidAction")
        if alpha.stability == 0.5: # Reform reset value
            print(f"Reform triggered at step {i}!")
            break

    assert alpha.stability >= 0.4 # Should have reset to 0.5
    print("Reform trigger verified.")

if __name__ == "__main__":
    try:
        test_stability_fluctuation()
        test_stability_reform()
        print("\nPhase 7 Verification SUCCESSFUL")
    except Exception as e:
        print(f"\nPhase 7 Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
