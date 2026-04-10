"""State persistence: save and load simulation state.

Supports serializing the full simulation state to JSON for reproducible
experiments, checkpointing, and post-hoc analysis.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_state(model: Any, path: str | Path, metadata: dict | None = None) -> Path:
    """Save simulation state to a JSON file.

    Parameters
    ----------
    model:
        A GeopolModel instance (stepped at least once).
    path:
        Output file path.
    metadata:
        Optional metadata dict (experiment name, parameters, etc.).

    Returns
    -------
    Path
        The path the state was saved to.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Collect agent states
    agents_data = []
    for agent in model.schedule.agents:
        agent_state = {
            "unique_id": agent.unique_id,
            "region_id": getattr(agent, "region_id", "unknown"),
            "posture": getattr(agent, "posture", "Deescalate"),
            "personality": getattr(agent, "personality", "Neutral"),
            "role": getattr(agent, "role", "row"),
            "capabilities": getattr(agent, "capabilities", {}),
        }
        agents_data.append(agent_state)

    # Collect diplomacy state
    diplomacy_edges = []
    if hasattr(model, "relations"):
        for u, v, data in model.relations.graph.edges(data=True):
            diplomacy_edges.append(
                {
                    "source": u,
                    "target": v,
                    "weight": data.get("weight", 0.0),
                }
            )

    # Collect economic state if available
    economic_data = None
    if hasattr(model, "trade_network") and model.trade_network is not None:
        economic_data = {
            "gdp": dict(model.trade_network.gdp),
            "trade_balance": dict(model.trade_network.trade_balance),
        }

    # Collect escalation state if available
    escalation_data = None
    if hasattr(model, "escalation_ladder") and model.escalation_ladder is not None:
        escalation_data = {
            "levels": {str(uid): int(level) for uid, level in model.escalation_ladder.levels.items()},
            "costs": dict(model.escalation_ladder.transition_costs),
        }

    # Collect data collector output
    dc_data = None
    if hasattr(model, "datacollector"):
        try:
            agent_df = model.datacollector.get_agent_vars_dataframe()
            agent_df = agent_df.sort_index()
            dc_data = agent_df.reset_index().to_dict(orient="records")
        except Exception:
            pass

    state = {
        "version": "0.3.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "scenario": getattr(model, "scenario_name", "default"),
        "step": model.schedule.steps if hasattr(model, "schedule") else 0,
        "metadata": metadata or {},
        "agents": agents_data,
        "diplomacy": diplomacy_edges,
        "region_resources": dict(getattr(model, "region_resources", {})),
        "economic": economic_data,
        "escalation": escalation_data,
        "datacollector": dc_data,
    }

    with open(path, "w") as f:
        json.dump(state, f, indent=2, default=str)

    logger.info("Saved simulation state to %s", path)
    return path


def load_state(path: str | Path) -> dict[str, Any]:
    """Load simulation state from a JSON file.

    Parameters
    ----------
    path:
        Path to a saved state JSON file.

    Returns
    -------
    dict
        The full state dictionary.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"State file not found: {path}")

    with open(path) as f:
        state = json.load(f)

    logger.info("Loaded simulation state from %s (version %s)", path, state.get("version"))
    return state


def restore_state(model: Any, state: dict[str, Any]) -> None:
    """Restore simulation state from a loaded state dict.

    Modifies the model in-place to match the saved state.

    Parameters
    ----------
    model:
        A GeopolModel instance (must have same agents as saved state).
    state:
        State dict from ``load_state()``.
    """
    # Restore agent postures
    agents_by_rid = {getattr(a, "region_id", ""): a for a in model.schedule.agents}
    for agent_data in state.get("agents", []):
        rid = agent_data.get("region_id", "")
        agent = agents_by_rid.get(rid)
        if agent is not None:
            agent.posture = agent_data.get("posture", "Deescalate")

    # Restore diplomacy
    if "diplomacy" in state and hasattr(model, "relations"):
        agents_by_uid = {a.unique_id: a for a in model.schedule.agents}
        for edge in state["diplomacy"]:
            src = edge["source"]
            tgt = edge["target"]
            if src in agents_by_uid and tgt in agents_by_uid:
                model.relations.set_relation(src, tgt, edge["weight"])

    # Restore resources
    if "region_resources" in state:
        model.region_resources.update(state["region_resources"])

    # Restore escalation state
    if "escalation" in state and hasattr(model, "escalation_ladder"):
        esc = state["escalation"]
        if model.escalation_ladder is not None:
            for uid_str, level_int in esc.get("levels", {}).items():
                uid = int(uid_str)
                from strategify.agents.escalation import EscalationLevel

                model.escalation_ladder.levels[uid] = EscalationLevel(level_int)

    logger.info(
        "Restored simulation state (scenario: %s, step: %s)",
        state.get("scenario"),
        state.get("step"),
    )


def list_checkpoints(directory: str | Path) -> list[dict[str, Any]]:
    """List all checkpoint files in a directory.

    Returns
    -------
    list[dict]
        List of dicts with ``path``, ``scenario``, ``step``, ``timestamp``.
    """
    directory = Path(directory)
    if not directory.exists():
        return []

    checkpoints = []
    for p in sorted(directory.glob("*.json")):
        try:
            with open(p) as f:
                data = json.load(f)
            checkpoints.append(
                {
                    "path": str(p),
                    "scenario": data.get("scenario", "unknown"),
                    "step": data.get("step", 0),
                    "timestamp": data.get("timestamp", ""),
                }
            )
        except (json.JSONDecodeError, KeyError):
            continue

    return checkpoints
