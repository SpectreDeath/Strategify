"""Phase 5: Decision Dashboard — Monte Carlo, briefings, and human-in-the-loop.

Provides three components for predictive analytics and decision support:

- ``MonteCarloEngine``: Run N parallel simulations with varied seeds,
  aggregate escalation probabilities into heatmap data.
- ``IntelligenceBriefing``: Generate structured text reports from
  simulation outcomes, optionally augmented by LLM reasoning.
- ``CommanderInterface``: Allow runtime overrides of agent decisions
  for human-in-the-loop what-if analysis.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Monte Carlo Engine
# ---------------------------------------------------------------------------


@dataclass
class MonteCarloResult:
    """Aggregated results from Monte Carlo branching simulations.

    Attributes
    ----------
    n_runs:
        Number of parallel simulations executed.
    n_steps:
        Steps per simulation.
    escalation_probabilities:
        ``{region_id: {step: float}}`` — probability of escalation at
        each step across all runs.
    mean_postures:
        ``{region_id: {step: float}}`` — mean escalation value (0-1).
    posture_trajectories:
        Full list of per-run posture histories for detailed analysis.
    confidence_intervals:
        ``{region_id: {step: (lower, upper)}}`` — 95% CI for each probability.
    convergence_history:
        List of (run_count, max_std_dev) tracking convergence over time.
    """

    n_runs: int
    n_steps: int
    escalation_probabilities: dict[str, dict[int, float]] = field(default_factory=dict)
    mean_postures: dict[str, dict[int, float]] = field(default_factory=dict)
    posture_trajectories: list[list[dict[str, float]]] = field(default_factory=list)
    confidence_intervals: dict[str, dict[int, tuple[float, float]]] = field(default_factory=dict)
    convergence_history: list[tuple[int, float]] = field(default_factory=list)


class MonteCarloEngine:
    """Runs N parallel simulations to produce probability heatmaps.

    Each run uses a different random seed but otherwise identical
    configuration. Results are aggregated into per-region, per-step
    escalation probabilities.

    Parameters
    ----------
    model_factory:
        Callable that returns a fresh ``GeopolModel`` instance.
        Default uses ``GeopolModel()`` with no arguments.
    """

    def __init__(
        self,
        model_factory: Callable[[], Any] | None = None,
    ) -> None:
        if model_factory is None:
            from strategify.sim.model import GeopolModel

            model_factory = GeopolModel
        self._model_factory = model_factory

    def run(
        self,
        n_runs: int = 100,
        n_steps: int = 20,
        base_seed: int = 42,
        convergence_threshold: float = 0.01,
        track_convergence: bool = True,
    ) -> MonteCarloResult:
        """Execute N simulations and aggregate results.

        Parameters
        ----------
        n_runs:
            Number of independent simulations.
        n_steps:
            Steps per simulation.
        base_seed:
            Starting seed. Each run uses ``base_seed + i``.
        convergence_threshold:
            Standard deviation below which results are considered converged.
        track_convergence:
            Whether to record convergence history during execution.

        Returns
        -------
        MonteCarloResult
            Aggregated escalation probabilities, confidence intervals, and convergence data.
        """

        all_trajectories: list[list[dict[str, float]]] = []
        convergence_history: list[tuple[int, float]] = []

        # Track cumulative statistics for convergence detection
        # (kept for future enhancement to track convergence history)

        for i in range(n_runs):
            seed = base_seed + i
            random.seed(seed)

            model = self._model_factory()
            run_trajectory = []

            for _ in range(n_steps):
                model.step()
                snapshot = {}
                for agent in model.schedule.agents:
                    rid = getattr(agent, "region_id", str(agent.unique_id))
                    snapshot[rid] = 1.0 if agent.posture == "Escalate" else 0.0
                run_trajectory.append(snapshot)

            all_trajectories.append(run_trajectory)

            # Check convergence every 10 runs
            if track_convergence and (i + 1) % 10 == 0:
                max_std = self._compute_max_std(all_trajectories, i + 1)
                convergence_history.append((i + 1, max_std))

        # Aggregate with confidence intervals
        if not all_trajectories:
            return MonteCarloResult(n_runs=0, n_steps=0)

        regions = list(all_trajectories[0][0].keys()) if all_trajectories[0] else []
        escalation_probs: dict[str, dict[int, float]] = {r: {} for r in regions}
        mean_postures: dict[str, dict[int, float]] = {r: {} for r in regions}
        confidence_intervals: dict[str, dict[int, tuple[float, float]]] = {r: {} for r in regions}

        for step in range(n_steps):
            for rid in regions:
                values = [traj[step][rid] for traj in all_trajectories if step < len(traj)]
                n = len(values)
                if values:
                    mean_val = sum(values) / n
                    escalation_probs[rid][step] = mean_val
                    mean_postures[rid][step] = mean_val

                    # 95% confidence interval using Wilson score for proportions
                    # More robust than normal approximation for small n and p near 0/1
                    if n >= 2:
                        p_hat = mean_val
                        z = 1.96  # 95% confidence
                        denominator = 1 + z**2 / n
                        center = (p_hat + z**2 / (2 * n)) / denominator
                        margin = (z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denominator
                        ci_lower = max(0.0, center - margin)
                        ci_upper = min(1.0, center + margin)
                        confidence_intervals[rid][step] = (ci_lower, ci_upper)
                    else:
                        confidence_intervals[rid][step] = (0.0, 1.0)

        return MonteCarloResult(
            n_runs=n_runs,
            n_steps=n_steps,
            escalation_probabilities=escalation_probs,
            mean_postures=mean_postures,
            posture_trajectories=all_trajectories,
            confidence_intervals=confidence_intervals,
            convergence_history=convergence_history,
        )

    def _compute_max_std(
        self,
        trajectories: list[list[dict[str, float]]],
        n_samples: int,
    ) -> float:
        """Compute maximum standard deviation across all region/step combinations."""
        if n_samples < 2:
            return 1.0

        max_std = 0.0
        if not trajectories:
            return max_std

        steps = len(trajectories[0]) if trajectories else 0
        regions = list(trajectories[0][0].keys()) if trajectories and trajectories[0] else []

        for step in range(steps):
            for rid in regions:
                values = [traj[step][rid] for traj in trajectories[:n_samples] if step < len(traj)]
                if len(values) >= 2:
                    std = np.std(values, ddof=1)
                    max_std = max(max_std, std)

        return max_std

    def run_until_converged(
        self,
        max_runs: int = 1000,
        n_steps: int = 20,
        base_seed: int = 42,
        threshold: float = 0.01,
        check_interval: int = 20,
    ) -> MonteCarloResult:
        """Run Monte Carlo until convergence or max runs reached.

        Parameters
        ----------
        max_runs:
            Maximum number of simulations to run.
        n_steps:
            Steps per simulation.
        base_seed:
            Starting seed.
        threshold:
            Convergence threshold (max std dev).
        check_interval:
            Check convergence every N runs.

        Returns
        -------
        MonteCarloResult
            Results with convergence information.
        """
        import scipy.stats

        all_trajectories: list[list[dict[str, float]]] = []
        convergence_history: list[tuple[int, float]] = []

        for i in range(max_runs):
            seed = base_seed + i
            random.seed(seed)

            model = self._model_factory()
            run_trajectory = []

            for _ in range(n_steps):
                model.step()
                snapshot = {}
                for agent in model.schedule.agents:
                    rid = getattr(agent, "region_id", str(agent.unique_id))
                    snapshot[rid] = 1.0 if agent.posture == "Escalate" else 0.0
                run_trajectory.append(snapshot)

            all_trajectories.append(run_trajectory)

            # Check convergence
            if (i + 1) >= check_interval and (i + 1) % check_interval == 0:
                max_std = self._compute_max_std(all_trajectories, i + 1)
                convergence_history.append((i + 1, max_std))

                if max_std < threshold:
                    break

        # Aggregate results
        if not all_trajectories:
            return MonteCarloResult(n_runs=0, n_steps=0)

        regions = list(all_trajectories[0][0].keys()) if all_trajectories[0] else []
        escalation_probs: dict[str, dict[int, float]] = {r: {} for r in regions}
        mean_postures: dict[str, dict[int, float]] = {r: {} for r in regions}
        confidence_intervals: dict[str, dict[int, tuple[float, float]]] = {r: {} for r in regions}

        n_final = len(all_trajectories)

        for step in range(n_steps):
            for rid in regions:
                values = [traj[step][rid] for traj in all_trajectories if step < len(traj)]
                n = len(values)
                if values:
                    mean_val = sum(values) / n
                    escalation_probs[rid][step] = mean_val
                    mean_postures[rid][step] = mean_val

                    if n >= 2:
                        std = np.std(values, ddof=1)
                        se = std / np.sqrt(n) if n > 1 else 0.1
                        ci = scipy.stats.norm.interval(0.95, loc=mean_val, scale=se)
                        confidence_intervals[rid][step] = (max(0.0, ci[0]), min(1.0, ci[1]))
                    else:
                        confidence_intervals[rid][step] = (0.0, 1.0)

        return MonteCarloResult(
            n_runs=n_final,
            n_steps=n_steps,
            escalation_probabilities=escalation_probs,
            mean_postures=mean_postures,
            posture_trajectories=all_trajectories,
            confidence_intervals=confidence_intervals,
            convergence_history=convergence_history,
        )

    def run_with_override(
        self,
        override_fn: Callable[[Any, int], None],
        n_runs: int = 100,
        n_steps: int = 20,
        base_seed: int = 42,
    ) -> MonteCarloResult:
        """Run Monte Carlo with a per-step override function.

        Parameters
        ----------
        override_fn:
            ``(model, step) -> None`` called before each step to modify
            model state (e.g., force an agent's posture).
        """

        all_trajectories: list[list[dict[str, float]]] = []

        for i in range(n_runs):
            seed = base_seed + i
            random.seed(seed)

            model = self._model_factory()
            run_trajectory = []

            for step in range(n_steps):
                override_fn(model, step)
                model.step()
                snapshot = {}
                for agent in model.schedule.agents:
                    rid = getattr(agent, "region_id", str(agent.unique_id))
                    snapshot[rid] = 1.0 if agent.posture == "Escalate" else 0.0
                run_trajectory.append(snapshot)

            all_trajectories.append(run_trajectory)

        if not all_trajectories:
            return MonteCarloResult(n_runs=0, n_steps=0)

        regions = list(all_trajectories[0][0].keys()) if all_trajectories[0] else []
        escalation_probs: dict[str, dict[int, float]] = {r: {} for r in regions}
        mean_postures: dict[str, dict[int, float]] = {r: {} for r in regions}
        confidence_intervals: dict[str, dict[int, tuple[float, float]]] = {r: {} for r in regions}

        for step in range(n_steps):
            for rid in regions:
                values = [traj[step][rid] for traj in all_trajectories if step < len(traj)]
                n = len(values)
                if values:
                    mean_val = sum(values) / n
                    escalation_probs[rid][step] = mean_val
                    mean_postures[rid][step] = mean_val

                    if n >= 2:
                        p_hat = mean_val
                        z = 1.96
                        denominator = 1 + z**2 / n
                        center = (p_hat + z**2 / (2 * n)) / denominator
                        margin = (z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2))) / denominator
                        ci_lower = float(max(0.0, center - margin))
                        ci_upper = float(min(1.0, center + margin))
                        confidence_intervals[rid][step] = (ci_lower, ci_upper)
                    else:
                        confidence_intervals[rid][step] = (0.0, 1.0)

        return MonteCarloResult(
            n_runs=n_runs,
            n_steps=n_steps,
            escalation_probabilities=escalation_probs,
            mean_postures=mean_postures,
            posture_trajectories=all_trajectories,
            confidence_intervals=confidence_intervals,
            convergence_history=[],
        )

    @staticmethod
    def to_dataframe(result: MonteCarloResult) -> pd.DataFrame:
        """Convert Monte Carlo result to a DataFrame for visualization.

        Returns a DataFrame with columns: region_id, step, escalation_prob.
        """
        records = []
        for rid, steps in result.escalation_probabilities.items():
            for step, prob in steps.items():
                records.append(
                    {
                        "region_id": rid,
                        "step": step,
                        "escalation_prob": prob,
                    }
                )
        return pd.DataFrame(records)

    @staticmethod
    def to_heatmap_data(result: MonteCarloResult) -> dict[str, Any]:
        """Convert to a format suitable for heatmap rendering.

        Returns
        -------
        dict
            ``{"regions": [...], "steps": [...], "matrix": [[...]]}``
        """
        regions = sorted(result.escalation_probabilities.keys())
        if not regions:
            return {"regions": [], "steps": [], "matrix": []}

        steps = sorted(result.escalation_probabilities[regions[0]].keys())
        matrix = [[result.escalation_probabilities[rid].get(s, 0.0) for s in steps] for rid in regions]
        return {"regions": regions, "steps": steps, "matrix": matrix}


# ---------------------------------------------------------------------------
# Intelligence Briefing
# ---------------------------------------------------------------------------


class IntelligenceBriefing:
    """Generates structured text reports from simulation data.

    Can operate in standalone mode (template-based) or LLM-augmented mode
    (uses the model's LLM engine for natural language generation).
    """

    def __init__(self, model: Any) -> None:
        self.model = model

    def generate(
        self,
        monte_carlo: MonteCarloResult | None = None,
        use_llm: bool = False,
    ) -> str:
        """Generate an intelligence briefing.

        Parameters
        ----------
        monte_carlo:
            Optional Monte Carlo results for probability-based analysis.
        use_llm:
            If True and model has an LLM engine, use it to generate
            narrative analysis. Falls back to template if unavailable.

        Returns
        -------
        str
            Formatted briefing text.
        """
        sections = []
        sections.append(self._header())
        sections.append(self._situation_overview())
        sections.append(self._actor_status())

        if monte_carlo is not None:
            sections.append(self._probability_analysis(monte_carlo))

        if hasattr(self.model, "coalition_tracker") and self.model.coalition_tracker:
            sections.append(self._coalition_analysis())

        if hasattr(self.model, "trade_network") and self.model.trade_network:
            sections.append(self._economic_analysis())

        if use_llm and hasattr(self.model, "llm_engine") and self.model.llm_engine:
            llm_section = self._llm_narrative()
            if llm_section:
                sections.append(llm_section)

        sections.append(self._recommendations())

        return "\n\n".join(sections)

    def _header(self) -> str:
        step = self.model.schedule.steps if hasattr(self.model, "schedule") else 0
        scenario = getattr(self.model, "scenario_name", "unknown")
        return f"=== INTELLIGENCE BRIEFING ===\nScenario: {scenario} | Step: {step}\n{'=' * 35}"

    def _situation_overview(self) -> str:
        agents = list(self.model.schedule.agents)
        escalating = [a for a in agents if a.posture == "Escalate"]
        deescalating = [a for a in agents if a.posture == "Deescalate"]
        return (
            f"SITUATION OVERVIEW\n"
            f"  Total actors: {len(agents)}\n"
            f"  Escalating: {len(escalating)} | Deescalating: {len(deescalating)}"
        )

    def _actor_status(self) -> str:
        lines = ["ACTOR STATUS"]
        for agent in self.model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            personality = getattr(agent, "personality", "Unknown")
            mil = agent.capabilities.get("military", 0.0)
            eco = agent.capabilities.get("economic", 0.0)
            lines.append(f"  {rid.upper()}: {agent.posture} [{personality}] mil={mil:.2f} eco={eco:.2f}")
        return "\n".join(lines)

    def _probability_analysis(self, mc: MonteCarloResult) -> str:
        lines = [f"ESCALATION PROBABILITY ANALYSIS ({mc.n_runs} simulations)"]

        has_ci = mc.confidence_intervals and any(
            mc.confidence_intervals.get(rid, {}) for rid in mc.confidence_intervals
        )

        for rid in sorted(mc.escalation_probabilities.keys()):
            probs = mc.escalation_probabilities[rid]
            if probs:
                final_prob = list(probs.values())[-1]
                max_prob = max(probs.values())

                if has_ci and rid in mc.confidence_intervals and mc.confidence_intervals[rid]:
                    final_step = max(probs.keys())
                    if final_step in mc.confidence_intervals[rid]:
                        ci_lower, ci_upper = mc.confidence_intervals[rid][final_step]
                        ci_str = f" 95% CI: [{ci_lower:.1%}, {ci_upper:.1%}]"
                    else:
                        ci_str = ""
                else:
                    ci_str = ""

                lines.append(f"  {rid.upper()}: final={final_prob:.1%} peak={max_prob:.1%}{ci_str}")

        if mc.convergence_history:
            final_runs, final_std = mc.convergence_history[-1]
            lines.append(f"  Convergence: max_std={final_std:.4f} at {final_runs} runs")

        return "\n".join(lines)

    def _coalition_analysis(self) -> str:
        tracker = self.model.coalition_tracker
        summary = tracker.summary()
        lines = [f"COALITION ANALYSIS ({summary['n_coalitions']} coalitions)"]
        for i, coalition in enumerate(summary.get("coalitions", [])):
            lines.append(f"  Coalition {i + 1}: members={coalition}")
        return "\n".join(lines)

    def _economic_analysis(self) -> str:
        tn = self.model.trade_network
        summary = tn.summary()
        lines = [
            "ECONOMIC ANALYSIS",
            f"  Total GDP: {summary['total_gdp']:.2f}",
            f"  Active sanctions: {summary['total_sanctions']}",
            f"  Avg trade volume: {summary['avg_trade_volume']:.4f}",
        ]
        return "\n".join(lines)

    def _llm_narrative(self) -> str | None:
        """Attempt LLM-generated narrative. Returns None on failure."""
        try:
            state = {
                "step": self.model.schedule.steps,
                "actors": [
                    {
                        "region_id": getattr(a, "region_id", "unknown"),
                        "posture": a.posture,
                        "personality": getattr(a, "personality", "Unknown"),
                    }
                    for a in self.model.schedule.agents
                ],
            }
            result = self.model.llm_engine.query(state)
            if result:
                return f"LLM ANALYSIS\n  {result.get('reasoning', 'No analysis available.')}"
        except Exception:
            pass
        return None

    def _recommendations(self) -> str:
        agents = list(self.model.schedule.agents)
        escalating = [a for a in agents if a.posture == "Escalate"]
        if not escalating:
            return "RECOMMENDATIONS\n  Situation stable. No immediate action required."
        rid_list = [getattr(a, "region_id", "?") for a in escalating]
        return (
            f"RECOMMENDATIONS\n"
            f"  Monitor: {', '.join(r.upper() for r in rid_list)}\n"
            f"  Risk level: {'HIGH' if len(escalating) > 2 else 'MODERATE'}"
        )


# ---------------------------------------------------------------------------
# Commander Interface
# ---------------------------------------------------------------------------


@dataclass
class DecisionOverride:
    """A human-issued override for an agent's decision."""

    agent_id: int
    region_id: str
    forced_action: str  # "Escalate" or "Deescalate"
    step_applied: int
    reason: str = ""


class CommanderInterface:
    """Human-in-the-loop decision override system.

    Allows a user to override specific agent decisions at runtime,
    enabling what-if analysis and guided scenario exploration.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self._overrides: list[DecisionOverride] = []
        self._active_overrides: dict[int, str] = {}  # agent_id → forced action

    def issue_override(
        self,
        region_id: str,
        forced_action: str,
        reason: str = "",
    ) -> DecisionOverride | None:
        """Override an agent's next decision.

        Parameters
        ----------
        region_id:
            Region ID of the agent to override.
        forced_action:
            ``"Escalate"`` or ``"Deescalate"``.
        reason:
            Optional reason for the override.

        Returns
        -------
        DecisionOverride or None
            The created override, or None if region not found.
        """
        if forced_action not in ("Escalate", "Deescalate"):
            raise ValueError(f"Invalid action: {forced_action}")

        agent = self._find_agent(region_id)
        if agent is None:
            return None

        step = self.model.schedule.steps if hasattr(self.model, "schedule") else 0
        override = DecisionOverride(
            agent_id=agent.unique_id,
            region_id=region_id,
            forced_action=forced_action,
            step_applied=step,
            reason=reason,
        )
        self._overrides.append(override)
        self._active_overrides[agent.unique_id] = forced_action
        logger.info(
            "Override issued: %s forced to %s (step %d)",
            region_id,
            forced_action,
            step,
        )
        return override

    def clear_override(self, region_id: str) -> bool:
        """Remove an active override for a region."""
        agent = self._find_agent(region_id)
        if agent and agent.unique_id in self._active_overrides:
            del self._active_overrides[agent.unique_id]
            return True
        return False

    def clear_all_overrides(self) -> None:
        """Remove all active overrides."""
        self._active_overrides.clear()

    def apply_overrides(self) -> None:
        """Apply active overrides to agent postures.

        Call this after ``model.step()`` to force specific agent states.
        """
        for agent in self.model.schedule.agents:
            if agent.unique_id in self._active_overrides:
                agent.posture = self._active_overrides[agent.unique_id]

    def get_active_overrides(self) -> dict[str, str]:
        """Return ``{region_id: forced_action}`` for all active overrides."""
        agents_by_uid = {a.unique_id: a for a in self.model.schedule.agents}
        result = {}
        for uid, action in self._active_overrides.items():
            agent = agents_by_uid.get(uid)
            if agent:
                rid = getattr(agent, "region_id", str(uid))
                result[rid] = action
        return result

    def get_override_history(self) -> list[DecisionOverride]:
        """Return all issued overrides."""
        return list(self._overrides)

    def _find_agent(self, region_id: str) -> Any | None:
        """Find agent by region_id."""
        for agent in self.model.schedule.agents:
            if getattr(agent, "region_id", "") == region_id:
                return agent
        return None

    def summary(self) -> dict[str, Any]:
        """Return commander interface summary."""
        return {
            "total_overrides_issued": len(self._overrides),
            "active_overrides": len(self._active_overrides),
            "regions_overridden": list(self.get_active_overrides().keys()),
        }
