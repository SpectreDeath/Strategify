# Strategify - Agent Instructions

This file provides context for AI agents working on the Strategify project.

## Project Overview

- **Version**: Geopolitical simulation framework
- **Python**: 3.10+
- **Core**: Agent-based modeling, game theory, geospatial analysis

## Key Commands

`ash
# Core simulation
pip install -e .

# With analysis tools
pip install -e '.[analysis]'

# Run simulation headless
python -m strategify.sim.model Ukraine

# Run with visualization
python -m strategify.sim.vis Ukraine

# Run tests
pytest tests/ -v
`

## Important Notes

- Prolog logic is in strategify/logic/traits.pl
- Clojure code is in strategify-clj/
- Agent behaviors: Aggressor, Pacifist, Tit-for-Tat, Neutral, Grudger

## Code Style

- Run ruff check before committing
- Use type hints
- Keep simulation logic separate from visualization
