"""Run Middle East current day scenario with real Middle East regions."""

import sys
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategify import GeopolModel
from strategify.config import MIDDLE_EAST_PRESET
from strategify.viz import (
    create_map,
    create_diplomacy_network,
    export_gexf,
    export_timeline,
    export_chart_png,
)


def run_simulation():
    """Run the Middle East scenario."""
    print("\n=== Middle East Scenario: Current Day ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
    print(f"Regions: {', '.join(MIDDLE_EAST_PRESET.regions)}")
    print(f"Description: {MIDDLE_EAST_PRESET.description}")
    print()

    print("Initializing simulation model...")
    model = GeopolModel(n_steps=30, scenario="middle_east")

    print(f"Created model with {len(model.schedule.agents)} agents")

    agent_names = [getattr(a, "region_id", "?") for a in model.schedule.agents]
    print(f"Agents: {', '.join(agent_names)}")

    print(f"Running {model.n_steps} steps...")

    model_history = []
    for step in range(model.n_steps):
        model.step()
        model_history.append(model)

        if step % 10 == 0:
            escalate_count = sum(
                1
                for a in model.schedule.agents
                if getattr(a, "posture", None) and "Escalate" in str(a.posture)
            )
            print(f"  Step {step}: {escalate_count} escalated")

    print("\nSimulation complete!")
    return model, model_history


def generate_outputs(model, model_history):
    """Generate all output files."""
    print("\nGenerating outputs...")

    output_dir = Path("middle_east_output")
    output_dir.mkdir(exist_ok=True)

    print("  Creating map...")
    create_map(model, output_dir / "map.html")

    print("  Creating diplomacy network...")
    create_diplomacy_network(model, output_dir / "network.html")

    print("  Exporting to GEXF for Gephi...")
    export_gexf(model, output_dir / "diplomacy.gexf")

    print("  Creating timeline...")
    export_timeline(model_history, output_dir / "timeline.html")

    print("  Exporting charts...")
    export_chart_png(model, output_dir / "escalation.png", "escalation")
    export_chart_png(model, output_dir / "diplomacy_matrix.png", "diplomacy")

    print(f"\nOutputs saved to: {output_dir}/")
    return output_dir


def analyze_results(model):
    """Analyze and display key results."""
    print("\n=== Results ===")

    print("\nActor Status:")
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        posture = getattr(agent, "posture", None)
        if posture is not None and hasattr(posture, "value"):
            posture_str = posture.value
        else:
            posture_str = str(posture) if posture else "Unknown"
        caps = getattr(agent, "capabilities", {})
        print(
            f"  {rid:4}: {posture_str:10} | Mil: {caps.get('military', 0):.2f} | Eco: {caps.get('economic', 0):.2f}"
        )

    print("\nDiplomatic Relations:")
    agents = list(model.schedule.agents)
    for i, a in enumerate(agents):
        for j, b in enumerate(agents):
            if i < j:
                rid_a = getattr(a, "region_id", "?")
                rid_b = getattr(b, "region_id", "?")
                rel = model.relations.get_relation(a.unique_id, b.unique_id)
                if abs(rel) > 0.3:
                    rel_type = "ALLIANCE" if rel > 0 else "RIVALRY"
                    print(f"  {rid_a} <-> {rid_b}: {rel_type} ({rel:.2f})")


if __name__ == "__main__":
    model, model_history = run_simulation()
    output_dir = generate_outputs(model, model_history)
    analyze_results(model)

    print("\n=== Done! ===")
    print(f"Open {output_dir}/map.html for the interactive map")
