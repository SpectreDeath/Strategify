"""Python-Clojure bridge for strategy synthesis.

This module provides a bridge to the Clojure Strategify module:
- Subprocess-based execution (lein exec)
- Timeline branching for counterfactual analysis
- Event stream processing
- Agent state management

Usage:
    from strategify.logic.clj import ClojureBridge, run_strategy_simulation

    bridge = ClojureBridge()
    result = bridge.execute_strategy("hawk", state_map)

    # Timeline branching
    timelines = bridge.branch_timelines(state, moves_list)
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Try to find Clojure project
CLOJURE_PROJECT_DIR = Path(__file__).parent.parent.parent / "strategify-clj"


class ClojureBridge:
    """Bridge to Clojure Strategify module.

    Provides:
    - Strategy execution
    - Timeline branching
    - Agent management
    - Event stream processing

    Parameters
    ----------
    project_dir:
        Path to Clojure project. Auto-detected if not provided.
    timeout:
        Timeout for Clojure execution in seconds.
    """

    def __init__(
        self,
        project_dir: Path | None = None,
        timeout: int = 30,
    ):
        self.project_dir = project_dir or CLOJURE_PROJECT_DIR
        self.timeout = timeout
        self._available = self._check_lein()

    def _check_lein(self) -> bool:
        """Check if Leiningen is available."""
        try:
            result = subprocess.run(
                ["lein", "version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def execute(
        self,
        code: str,
    ) -> dict | None:
        """Execute Clojure code and return result.

        Parameters
        ----------
        code:
            Clojure code to execute.

        Returns
        -------
        dict | None
            Parsed JSON result or None on failure.
        """
        if not self._available:
            logger.warning("Leiningen not available")
            return None

        cmd = ["lein", "exec", "-"]

        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                cwd=str(self.project_dir),
            )

            if result.returncode == 0:
                # Try to parse JSON output
                for line in result.stdout.strip().split("\n"):
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
            else:
                logger.error(f"Clojure error: {result.stderr}")

        except subprocess.TimeoutExpired:
            logger.error(f"Clojure execution timed out after {self.timeout}s")
        except Exception as e:
            logger.error(f"Clojure execution failed: {e}")

        return None

    def execute_strategy(
        self,
        strategy_name: str,
        state: dict,
    ) -> dict | None:
        """Execute a strategy on given state.

        Parameters
        ----------
        strategy_name:
            One of: hawk, dove, tit-for-tat, grudger, adaptive
        state:
            Game state as dict.

        Returns
        -------
        dict
            Result with action and payoff.
        """
        code = f"""
(do
  (require '[strategify.core :as s])
  (let [state# (s/map->state '{json.dumps(state)})
        strategy# (s/get-strategy '{strategy_name})]
    {{:strategy '{strategy_name}
     :action (strategy# state# :player)
     :payoff (s/get-payoff strategy# :dove)}})
"""
        return self.execute(code)

    def branch_timelines(
        self,
        state: dict,
        moves: list[str],
    ) -> list[dict]:
        """Branch multiple possible timelines.

        Parameters
        ----------
        state:
            Current game state.
        moves:
            List of possible moves to branch.

        Returns
        -------
        list[dict]
            List of new states (one per move).
        """
        result_moves = "[" + ", ".join(f"'({m})" for m in moves) + "]"

        code = f"""
(do
  (require '[strategify.core :as s])
  (let [state# (s/map->state '{json.dumps(state)})
        moves# {result_moves}
        timelines# (s/branch-timelines state# moves#)]
    (map s/state->map timelines#)))
"""
        result = self.execute(code)
        if result:
            return result if isinstance(result, list) else [result]
        return []

    def calculate_utility(
        self,
        agent_id: str,
        state: dict,
    ) -> float | None:
        """Calculate expected utility for agent.

        Parameters
        ----------
        agent_id:
            Agent ID.
        state:
            Game state.

        Returns
        -------
        float | None
            Expected utility.
        """
        code = f"""
(do
  (require '[strategify.core :as s])
  (let [agent# (s/create-agent '{agent_id} :hawk 50)
        state# (s/map->state '{json.dumps(state)})]
    (s/calculate-utility agent# state#)))
"""
        result = self.execute(code)
        if result:
            return float(result) if isinstance(result, (int, float)) else None
        return None

    def create_agent(
        self,
        agent_id: str,
        strategy: str,
        resources: float,
    ) -> dict | None:
        """Create a new agent.

        Parameters
        ----------
        agent_id:
            Unique agent ID.
        strategy:
            Strategy type.
        resources:
            Resource level.

        Returns
        -------
        dict
            Agent state.
        """
        code = f"""
(require '[strategify.core :as s])
(s/state->map (s/create-agent '{agent_id} '{strategy} {resources}))
"""
        return self.execute(code)


def run_strategy_simulation(
    strategies: list[str],
    initial_state: dict,
    rounds: int = 100,
) -> dict[str, float]:
    """Run strategy simulation comparing multiple strategies.

    Parameters
    ----------
    strategies:
        List of strategy names to compare.
    initial_state:
        Starting state.
    rounds:
        Number of rounds.

    Returns
    -------
    dict
        Map of strategy to average utility.
    """
    bridge = ClojureBridge()
    results = {}

    for strategy in strategies:
        total = 0
        for _ in range(rounds):
            utility = bridge.calculate_utility(strategy, initial_state)
            if utility is not None:
                total += utility

        results[strategy] = total / rounds if rounds > 0 else 0

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Clojure Bridge Demo ===\n")

    # Test availability
    bridge = ClojureBridge()
    if bridge._available:
        print("Leiningen: available")

        # Demo state
        state = {
            "version": 0,
            "players": {"player1": {"resources": 50}},
            "board": {},
            "history": [],
            "metadata": {},
        }

        # Branch timelines
        timelines = bridge.branch_timelines(state, ["attack", "display"])
        print(f"Branched timelines: {len(timelines)}")
    else:
        print("Leiningen: NOT available")
        print("Install: winget install -e --id Technomancy.Leiningen")
