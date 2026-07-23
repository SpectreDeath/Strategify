"""Interactive Scenario REPL & Command Line Runner.

Usage:
  python -m strategify.cli run <scenario_name> [n_steps]
  python -m strategify.cli repl [scenario_name]
  python -m strategify.cli vector-map <scenario_name> [output_path]
  python -m strategify.cli wargame [steps]
  python -m strategify.cli swarm [steps] [--provider PROVIDER] [--model MODEL]
  python -m strategify.cli train-rl [episodes]
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Any

from strategify.reasoning.swarm import StrategifySwarm
from strategify.rl.training_deep import DeepRLTrainer
from strategify.sim.model import GeopolModel
from strategify.sim.wargame import MultiDomainWargameEngine
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

        print(f"Overriding region '{region_id}' posture: {target.posture} -> {posture}")
        target.posture = posture

    def export_map(self, output_path: str = "vector_map.html") -> None:
        """Export current state as vector map HTML."""
        out = Path(create_vector_map_html(self.model, output_path))
        print(f"Exported interactive vector map to: {out.resolve()}")

    def start_repl(self) -> None:
        """Start interactive command loop."""
        print("=== Strategify Interactive REPL ===")
        print("Commands: step [n], status, override <region> <posture>, map [out.html], exit")
        self.print_status()

        while True:
            try:
                line = input("strategify> ").strip()
                if not line:
                    continue

                parts = line.split()
                cmd = parts[0].lower()

                if cmd in ("exit", "quit"):
                    print("Exiting REPL.")
                    break
                elif cmd == "status":
                    self.print_status()
                elif cmd == "step":
                    steps = int(parts[1]) if len(parts) > 1 else 1
                    self.run_steps(steps)
                elif cmd == "override":
                    if len(parts) < 3:
                        print("Usage: override <region_id> <posture>")
                    else:
                        self.issue_override(parts[1], parts[2])
                elif cmd == "map":
                    out_path = parts[1] if len(parts) > 1 else "vector_map.html"
                    self.export_map(out_path)
                else:
                    print(f"Unknown command: '{cmd}'. Commands: step [n], status, override, map, exit")

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

    swarm_parser = subparsers.add_parser("swarm", help="Run autonomous LLM agent swarm wargame")
    swarm_parser.add_argument("steps", nargs="?", type=int, default=3, help="Number of steps")
    swarm_parser.add_argument("--provider", default="mock", help="LLM Provider (mock, ollama, openai, anthropic)")
    swarm_parser.add_argument("--model", default=None, help="LLM Model Name")

    train_parser = subparsers.add_parser("train-rl", help="Train Deep RL agent policy in EpidemicEnv")
    train_parser.add_argument("episodes", nargs="?", type=int, default=10, help="Number of training episodes")

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
        engine = MultiDomainWargameEngine()
        print(f"Running Multi-Domain Wargame for {parsed.steps} steps...")
        result = engine.run_wargame(total_steps=parsed.steps)
        print(f"Wargame Finished! Winner: {result.winner}")
        print(f"Final Scores: {result.actor_scores}")
    elif parsed.command == "swarm":
        engine = MultiDomainWargameEngine()
        swarm = StrategifySwarm(provider=parsed.provider, model=parsed.model)
        print(f"Starting Autonomous LLM Swarm Deliberation for {parsed.steps} steps (Provider: {parsed.provider})...")
        for step_i in range(1, parsed.steps + 1):
            res = swarm.deliberate_step(engine)
            print(f"--- Step {step_i} Consensus Score: {res.consensus_score:.2f} ---")
            for prop in res.proposals:
                print(f"  [{prop.persona_name} - {prop.domain}]: {prop.recommended_action}")
        print("Swarm deliberation completed successfully.")
    elif parsed.command == "train-rl":
        trainer = DeepRLTrainer()
        print(f"Training Deep RL Policy Agent for {parsed.episodes} episodes in EpidemicEnv...")
        res = trainer.train(episodes=parsed.episodes)
        print(f"Training Finished! Mean Reward: {res.mean_reward:.2f}")
        print(f"Optimal Control Cost Benchmark: {res.optimal_control_cost_benchmark:.2f}")
    else:
        # Default to REPL if no command specified or 'repl'
        repl = InteractiveREPL(scenario_name=scen)
        repl.start_repl()


if __name__ == "__main__":
    main()
