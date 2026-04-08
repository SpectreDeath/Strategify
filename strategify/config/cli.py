"""Scenario CLI: create and validate scenario JSON files.

Usage::

    python -m strategify.config.cli create --name my_scenario --regions 3
    python -m strategify.config.cli validate path/to/scenario.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_PERSONALITIES = {"Aggressor", "Pacifist", "Tit-for-Tat", "Neutral", "Grudger"}
VALID_ROLES = {"row", "col"}


def create_scenario(args: argparse.Namespace) -> None:
    """Create a new scenario JSON file."""
    n = args.regions
    region_ids = [chr(ord("alpha"[0]) + i) + ("" if i == 0 else "") for i in range(n)]
    # Use simple sequential IDs: alpha, bravo, charlie, delta, echo, ...
    id_names = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel"]
    region_ids = id_names[:n]

    actors = {}
    alliances = []
    region_resources = {}

    for rid in region_ids:
        actors[rid] = {
            "name": rid.capitalize(),
            "capabilities": {"military": 0.5, "economic": 0.5},
            "role": "row",
            "personality": "Neutral",
        }
        region_resources[rid] = 1.0

    # Add a default alliance between first two regions
    if n >= 2:
        alliances.append({"source": region_ids[0], "target": region_ids[1], "weight": 0.5})

    scenario = {
        "name": args.name,
        "description": f"Auto-generated scenario with {n} regions",
        "geojson": "real_world.geojson",
        "random_seed": 42,
        "n_steps": 20,
        "actors": actors,
        "region_resources": region_resources,
        "alliances": alliances,
    }

    out_path = Path(args.output) if args.output else Path(f"{args.name}.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(scenario, f, indent=2)

    print(f"Scenario written to {out_path}")
    print(f"  {len(actors)} actors, {len(alliances)} alliances")
    print("  Edit the file to customize capabilities, personalities, and alliances.")


def validate_scenario(args: argparse.Namespace) -> None:
    """Validate a scenario JSON file."""
    path = Path(args.scenario_file)
    if not path.exists():
        print(f"ERROR: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    errors = []
    warnings = []

    # Required fields
    for field in ("name", "actors"):
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    # Validate actors
    actors = data.get("actors", {})
    if not actors:
        errors.append("No actors defined")
    for rid, cfg in actors.items():
        caps = cfg.get("capabilities", {})
        if "military" not in caps:
            errors.append(f"Actor '{rid}' missing 'military' capability")
        if "economic" not in caps:
            errors.append(f"Actor '{rid}' missing 'economic' capability")
        for cap, val in caps.items():
            if not isinstance(val, (int, float)) or not 0 <= val <= 1:
                errors.append(f"Actor '{rid}' capability '{cap}' must be in [0, 1]")
        personality = cfg.get("personality", "Neutral")
        if personality not in VALID_PERSONALITIES:
            warnings.append(
                f"Actor '{rid}' has unknown personality '{personality}'. "
                f"Valid options: {', '.join(sorted(VALID_PERSONALITIES))}"
            )
        role = cfg.get("role", "row")
        if role not in VALID_ROLES:
            errors.append(f"Actor '{rid}' has invalid role '{role}'")

    # Validate alliances
    for i, alliance in enumerate(data.get("alliances", [])):
        for key in ("source", "target", "weight"):
            if key not in alliance:
                errors.append(f"Alliance {i} missing '{key}'")
        src = alliance.get("source", "")
        tgt = alliance.get("target", "")
        if src and src not in actors:
            errors.append(f"Alliance {i}: source '{src}' not in actors")
        if tgt and tgt not in actors:
            errors.append(f"Alliance {i}: target '{tgt}' not in actors")
        w = alliance.get("weight", 0)
        if not isinstance(w, (int, float)) or not -1 <= w <= 1:
            errors.append(f"Alliance {i}: weight must be in [-1, 1]")

    # Validate region_resources
    for rid in data.get("region_resources", {}):
        if rid not in actors:
            warnings.append(f"region_resources has key '{rid}' not in actors")

    # Report
    if errors:
        print(f"INVALID: {len(errors)} error(s), {len(warnings)} warning(s)")
        for e in errors:
            print(f"  ERROR: {e}")
        for w in warnings:
            print(f"  WARN:  {w}")
        sys.exit(1)
    else:
        print(f"VALID: {len(actors)} actors, {len(data.get('alliances', []))} alliances")
        for w in warnings:
            print(f"  WARN: {w}")


def run_counterfactual(args: argparse.Namespace) -> None:
    """Run a counterfactual scenario comparison."""
    import json as _json

    from strategify.analysis.counterfactual import (
        run_baseline,
    )
    from strategify.analysis.counterfactual import (
        run_counterfactual as _run_cf,
    )
    from strategify.sim.model import GeopolModel

    scenario = args.scenario if args.scenario else None

    def factory():
        if scenario:
            return GeopolModel(scenario=scenario)
        return GeopolModel()

    n_steps = args.steps
    intervention = _json.loads(args.intervention) if args.intervention else []

    print(f"Running baseline ({n_steps} steps)...")
    baseline = run_baseline(factory, n_steps)
    print(f"  Baseline escalation count: {baseline['escalation_count']}")

    print(f"Running counterfactual ({n_steps} steps)...")
    cf = _run_cf(factory, n_steps, intervention_step=2, interventions=intervention)
    print(f"  Counterfactual escalation count: {cf['counterfactual']['escalation_count']}")

    comp = cf["comparison"]
    print("\nComparison:")
    print(f"  Posture changes: {comp.get('posture_changes', {})}")
    print(f"  Escalation delta: {comp.get('escalation_delta', 'N/A')}")


def main() -> None:
    from importlib.metadata import version

    parser = argparse.ArgumentParser(
        prog="strategify-scenario",
        description="Create and validate geopolitical simulation scenarios",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"strategify-scenario {version('strategify')}",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = sub.add_parser("create", help="Create a new scenario file")
    p_create.add_argument("--name", required=True, help="Scenario name")
    p_create.add_argument("--regions", type=int, default=3, help="Number of regions (default: 3)")
    p_create.add_argument("--output", "-o", help="Output file path")

    # validate
    p_validate = sub.add_parser("validate", help="Validate a scenario file")
    p_validate.add_argument("scenario_file", help="Path to scenario JSON")

    # counterfactual
    p_cf = sub.add_parser("counterfactual", help="Run counterfactual scenario comparison")
    p_cf.add_argument("--scenario", "-s", help="Scenario name or path")
    p_cf.add_argument("--steps", type=int, default=10, help="Steps to simulate (default: 10)")
    p_cf.add_argument(
        "--intervention",
        "-i",
        required=True,
        help=(
            "Intervention JSON, e.g. "
            '\'[{"type": "capability", "region_id": "alpha",'
            ' "field": "military", "value": 0.9}]\''
        ),
    )

    args = parser.parse_args()
    if args.command == "create":
        create_scenario(args)
    elif args.command == "validate":
        validate_scenario(args)
    elif args.command == "counterfactual":
        run_counterfactual(args)


if __name__ == "__main__":
    main()
