"""Interactive Scenario REPL & Command Line Runner.

Usage:
  python -m strategify.cli run <scenario_name> [n_steps]
  python -m strategify.cli repl [scenario_name]
  python -m strategify.cli vector-map <scenario_name> [output_path]
"""

from __future__ import annotations

import argparse
import logging
from typing import Any

from strategify.sim.model import GeopolModel
from strategify.viz.vector_map import create_vector_map_html

logger = logging.getLogger(__name__)


class InteractiveREPL:
    """Interactive Command Line REPL for stepping and inspecting simulations."""

    def __init__(self, scenario_name: str = "default") -> None:
        self.scenario_name = scenario_name
        scen = "default" if scenario_name in ("Ukraine", "default") else scenario_name
        self.model = GeopolModel(scenario=scen)

    def print_status(self) -> None:
        """Print current simulation state overview."""
        print(f"\n--- Simulation Status: {self.scenario_name} (Step {self.model.schedule.steps}) ---")
        for agent in self.model.schedule.agents:
            rid = getattr(agent, "region_id", str(agent.unique_id))
            posture = getattr(agent, "posture", "Unknown")
            print(f"  [{rid}] Posture: {posture} | Role: {getattr(agent, 'role', 'N/A')}")
        print("-" * 55 + "\n")

    def run_steps(self, n_steps: int = 1) -> None:
        """Run N simulation steps."""
        print(f"Stepping model {n_steps} times...")
        for _ in range(n_steps):
            self.model.step()
        self.print_status()

    def issue_override(self, region_id: str, posture: str) -> None:
        """Force posture override on a region agent."""
        target = self.model.get_agent_by_region(region_id)
        if not target:
            print(f"Error: Region '{region_id}' not found.")
            return
        target.posture = posture
        print(f"Issued override: Set [{region_id}] posture -> '{posture}'")

    def export_vector_map(self, output_path: str = "vector_map.html") -> None:
        """Export WebGL vector map."""
        out = create_vector_map_html(self.model, output_path)
        print(f"Exported interactive vector map to: {out.resolve()}")

    def start_repl(self) -> None:
        """Start interactive command loop."""
        print("=== Strategify Interactive REPL ===")
        print("Type 'help' for commands or 'exit' to quit.\n")
        self.print_status()

        while True:
            try:
                line = input("strategify> ").strip()
                if not line:
                    continue

                parts = line.split()
                cmd = parts[0].lower()

                if cmd in ("exit", "quit", "q"):
                    print("Exiting REPL.")
                    break
                elif cmd == "help":
                    print("Available Commands:")
                    print("  step [n]             - Step simulation N times (default: 1)")
                    print("  status               - Display current agent postures & info")
                    print("  override <rid> <act> - Force posture (e.g. override UKR Escalate)")
                    print("  vector-map [path]    - Export interactive HTML vector map")
                    print("  exit / quit          - Exit REPL")
                elif cmd == "step":
                    n = int(parts[1]) if len(parts) > 1 else 1
                    self.run_steps(n)
                elif cmd == "status":
                    self.print_status()
                elif cmd == "override":
                    if len(parts) < 3:
                        print("Usage: override <region_id> <posture>")
                    else:
                        self.issue_override(parts[1], parts[2])
                elif cmd in ("vector-map", "vectormap"):
                    out = parts[1] if len(parts) > 1 else "vector_map.html"
                    self.export_vector_map(out)
                else:
                    print(f"Unknown command: '{cmd}'. Type 'help' for available commands.")
            except KeyboardInterrupt:
                print("\nKeyboardInterrupt. Exiting.")
                break
            except Exception as err:
                print(f"Command error: {err}")


def main(args: list[str] | None = None) -> Any:
    """CLI entry point for python -m strategify.cli."""
    parser = argparse.ArgumentParser(description="Strategify CLI & Interactive REPL")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run scenario headless")
    run_parser.add_argument("scenario", nargs="?", default="Ukraine", help="Scenario name")
    run_parser.add_argument("steps", nargs="?", type=int, default=5, help="Number of steps")

    repl_parser = subparsers.add_parser("repl", help="Start interactive REPL")
    repl_parser.add_argument("scenario", nargs="?", default="Ukraine", help="Scenario name")

    vector_parser = subparsers.add_parser("vector-map", help="Generate vector map HTML")
    vector_parser.add_argument("scenario", nargs="?", default="Ukraine", help="Scenario name")
    vector_parser.add_argument("output", nargs="?", default="vector_map.html", help="Output path")

    wargame_parser = subparsers.add_parser("wargame", help="Run multi-domain wargame scenario")
    wargame_parser.add_argument("steps", nargs="?", type=int, default=5, help="Number of steps")

    parsed = parser.parse_args(args)

    scen = "default" if getattr(parsed, "scenario", "Ukraine") in ("Ukraine", "default") else getattr(parsed, "scenario", "default")

    if parsed.command == "run":
        model = GeopolModel(scenario=scen)
        print(f"Running scenario '{parsed.scenario}' for {parsed.steps} steps...")
        for step_idx in range(1, parsed.steps + 1):
            model.step()
            print(f"Step {step_idx} completed.")
        print("Run finished successfully.")
    elif parsed.command == "vector-map":
        model = GeopolModel(scenario=scen)
        model.step()
        out = create_vector_map_html(model, parsed.output)
        print(f"Generated vector map HTML: {out}")
    elif parsed.command == "wargame":
        from strategify.sim.wargame import MultiDomainWargameEngine
        engine = MultiDomainWargameEngine()
        print(f"Running Multi-Domain Wargame for {parsed.steps} steps...")
        result = engine.run_wargame(total_steps=parsed.steps)
        print(f"Wargame Finished! Winner: {result.winner}")
        print(f"Final Scores: {result.actor_scores}")
    else:
        # Default to REPL if no command specified or 'repl'
        repl = InteractiveREPL(scenario_name=scen)
        repl.start_repl()


if __name__ == "__main__":
    main()
