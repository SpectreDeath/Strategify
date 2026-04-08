# Geopol-Sim Skills Index

Skills for AI agents working with the strategify project.

## Available Skills

| Skill | Description |
|-------|-------------|
| [strategify-test-coverage](strategify-test-coverage/) | Writing tests to reach 70% coverage |
| [strategify-scenario-runner](strategify-scenario-runner/) | Running simulations, CLI usage |
| [strategify-debugging](strategify-debugging/) | Debugging test failures, verification |
| [strategify-osint-analysis](strategify-osint-analysis/) | OSINT pipeline, VAR, causal inference |
| [strategify-rl-development](strategify-rl-development/) | RL environments, training, evaluation |
| [strategify-visualization](strategify-visualization/) | Maps, networks, dashboard, plugins |
| [strategify-game-theory](strategify-game-theory/) | Nash equilibria, crisis games, coalitions |
| [context-offloading](context-offloading/) | Save/retrieve agent context across sessions |
| [skill-analyzer](skill-analyzer/) | Analyze existing skills to understand capabilities |

## Context-Aware Workflow

This project supports cross-session memory for agents using the Context-Aware Workflow:

- **context-offloading**: Use for saving agent context across sessions, tracking decisions, and maintaining project memory.
  - Triggers: "save context", "remember", "memory", "prior context", "load history", "session memory"

- **skill-analyzer**: Use for analyzing existing skills to understand capabilities and triggers.
  - Triggers: "analyze skill", "what does this skill do", "skill review", "evaluate skill"

### Context Storage

This project uses `.context/` directory for persistent agent memory:
- `.context/identity.md` - Project purpose, stack, conventions
- `.context/decisions.md` - Architecture decisions
- `.context/session-logs/` - Session notes

## Loading Skills

In Kilo/Claude, load skills by name:

```
Use the strategify-test-coverage skill when...
Use the strategify-scenario-runner skill when...
```

## Quick Start

1. Run simulation: `python examples/basic_crisis_scenario/run.py`
2. Interactive map: `strategify` (opens localhost:8521)
3. Run tests: `pytest tests/`

## Project Status

- Coverage: ~24% (target: 70%)
- Tests: 696 collected
- Core modules: Working (model, game_theory, analysis, viz)
