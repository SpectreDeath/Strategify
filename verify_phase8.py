import logging
import os
import sys

# Ensure we can import strategify
sys.path.append(os.getcwd())

from strategify.agents.non_state import NonStateActor
from strategify.sim.model import GeopolModel

# Configure logging to see non-state and cyber events
logging.basicConfig(level=logging.INFO)

def test_non_state_spawn():
    print("--- Testing Non-State Actor Spawn ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True, enable_non_state_actors=True)

    non_state = [a for a in model.schedule.agents if isinstance(a, NonStateActor)]
    print(f"Total Non-State Actors: {len(non_state)}")
    assert len(non_state) > 0

    insurgent = non_state[0]
    print(f"Insurgent operating in: {insurgent.target_region}")
    assert insurgent.target_region == "bravo"

def test_asymmetric_effects():
    print("\n--- Testing Asymmetric Effects ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True, enable_non_state_actors=True)

    bravo = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "bravo")
    insurgent = next(a for a in model.schedule.agents if isinstance(a, NonStateActor))

    # Force insurgent to Sabotage
    insurgent.influence = 0.8
    initial_stability = bravo.stability
    print(f"Initial Bravo Stability: {initial_stability:.2f}")

    # Run step
    model.step()

    print(f"Post-Step Bravo Stability: {bravo.stability:.2f}")
    assert bravo.stability < initial_stability
    print("Asymmetric subversion verified.")

def test_cyber_warfare():
    print("\n--- Testing Cyber Warfare ---")
    model = GeopolModel(enable_economics=False, enable_escalation_ladder=True, enable_non_state_actors=True)

    # Agent alpha has 'cyber' in active_games (mil_cap 0.8)
    alpha = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "alpha")
    delta = next(a for a in model.schedule.agents if getattr(a, "region_id", "") == "delta")

    print(f"Alpha active games: {alpha.active_games}")
    assert "cyber" in alpha.active_games

    # Force alpha as rival by influence or just step the model
    from strategify.reasoning.influence import InfluenceMap
    model.influence_map = InfluenceMap(model)
    model.influence_map.compute()

    # Force CyberAttack in the score dict manually to trigger effect in _apply
    action = {"action": "Escalate", "game_scores": {"cyber_choice": 1.0}}

    rival_id = alpha._find_primary_rival(model.influence_map)
    print(f"Alpha's detected rival ID: {rival_id}")
    assert rival_id is not None

    rival_agent = next(a for a in model.schedule.agents if a.unique_id == rival_id)
    initial_stability = rival_agent.stability

    alpha._apply(action)
    print(f"Rival {rival_agent.region_id} stability after Alpha CyberAttack: {rival_agent.stability:.2f}")
    assert rival_agent.stability < initial_stability
    print("Cyber Warfare effect verified.")

if __name__ == "__main__":
    try:
        test_non_state_spawn()
        test_asymmetric_effects()
        test_cyber_warfare()
        print("\nPhase 8 Verification SUCCESSFUL")
    except Exception as e:
        print(f"\nPhase 8 Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
