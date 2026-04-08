"""Example: Using geopolitical theories in simulation.

This script demonstrates theory-based decision making
using classical geopolitical frameworks.

Usage:
    python scripts/geopolitical_theories.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategify.sim.model import GeopolModel
from strategify.theory import DEFAULT_REGISTRY


def run_theory_analysis():
    """Run simulation with theory-based analysis."""
    print("=" * 60)
    print("Geopolitical Theories Analysis")
    print("=" * 60)

    # Create model
    model = GeopolModel(n_steps=10)
    model.step()  # Initialize

    # Analyze each agent with all theories
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        if rid == "unknown":
            continue

        print(f"\n{'-' * 40}")
        print(f"Region: {rid.upper()} ({getattr(agent, 'personality', 'Neutral')})")
        print(f"{'-' * 40}")

        # Get analysis from all theories
        results = DEFAULT_REGISTRY.analyze_with_all(agent, model)

        # Aggregate recommendations
        actions = {}
        for result in results:
            action = result.recommended_action
            if action not in actions:
                actions[action] = []
            actions[action].append((result.theory, result.confidence))

        # Print theory results
        print("\nTheory Recommendations:")
        for result in results:
            print(
                f"  {result.theory:20s}: {result.recommended_action:12s} "
                f"(conf={result.confidence:.2f}) - {result.rationale}"
            )

        # Print aggregated recommendation
        print("\nAggregated Recommendation:")
        for action, theories in actions.items():
            avg_conf = sum(c for _, c in theories) / len(theories)
            print(f"  {action:12s}: {len(theories)} theories, avg confidence: {avg_conf:.2f}")


def compare_theories():
    """Compare theory predictions."""
    model = GeopolModel()
    model.step()

    print("\n" + "=" * 60)
    print("Theory Comparison")
    print("=" * 60)

    # Get Realpolitik and Democratic Peace for comparison
    rp = DEFAULT_REGISTRY.get("Realpolitik")
    dpt = DEFAULT_REGISTRY.get("Democratic Peace")

    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "")
        if not rid:
            continue

        print(f"\nRegion: {rid}")

        # Realpolitik
        rp_result = rp.evaluate(agent, model)
        print(f"  Realpolitik: {rp_result.recommended_action} - {rp_result.rationale}")

        # Democratic Peace
        dpt_result = dpt.evaluate(agent, model)
        print(f"  Democratic Peace: {dpt_result.recommended_action} - {dpt_result.rationale}")

        # Power calculation comparison
        rp_power = rp.calculate_power(agent, model)
        dpt_power = dpt.calculate_power(agent, model)
        print(f"  Power (Realpolitik): {rp_power:.3f}")
        print(f"  Power (Dem. Peace): {dpt_power:.3f}")


def main():
    """Main entry point."""
    import logging

    logging.basicConfig(level=logging.WARNING)

    run_theory_analysis()
    compare_theories()

    print("\n" + "=" * 60)
    print("Analysis Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
