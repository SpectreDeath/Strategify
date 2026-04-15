import logging
import os
import sys

# Ensure we can import strategify
sys.path.append(os.getcwd())

from strategify.rl.environment import GeopolEnv

# Configure logging
logging.basicConfig(level=logging.WARNING)


def test_rl_env_minimal():
    print("--- Testing RL Environment Minimal ---")
    env = GeopolEnv(n_steps=1)
    env.reset()

    # Run one full cycle of agents
    for agent in env.agent_iter():
        obs, reward, termination, truncation, info = env.last()

        if termination or truncation:
            action = None
        else:
            # Check observation shape and value ranges
            assert obs.shape == (8,)
            assert 0.0 <= obs[4] <= 1.0  # Stability

            action = 0  # Deescalate

        env.step(action)

    print("RL Environment cycle verified.")


if __name__ == "__main__":
    try:
        test_rl_env_minimal()
        print("\nPhase 10 Verification SUCCESSFUL")
    except Exception as e:
        print(f"\nPhase 10 Verification FAILED: {e}")
        import traceback

        traceback.print_exc()
