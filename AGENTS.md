# Strategify - Agent Instructions

This file provides context for AI agents working on the Strategify project.

## Project Overview

- **Version**: 0.5.0 — Geopolitical simulation framework
- **Python**: 3.11+ (CI runs 3.11, 3.12, 3.13)
- **Core**: Agent-based modeling (Mesa 2.3.4), game theory, geospatial analysis, LLM-grounded cognitive agents

## Key Commands

```bash
# Install all extras (recommended for development)
pip install -e ".[dev,analysis,rl,web]"

# Run backend API server (FastAPI on port 8000)
uvicorn strategify.web.api:app --reload --port 8000

# Run interactive map visualization (Mesa)
python -m strategify.sim.run_mesa_geo_server
# or: strategify

# Run headless simulation
python examples/basic_crisis_scenario/run.py

# Run tests (with coverage)
pytest

# Run specific test
pytest tests/test_web_api.py -v

# Linting
ruff check .
ruff format --check .
```

## Frontend

```bash
cd frontend
npm install
npm run dev   # Vite dev server on http://localhost:5173
```

## Architecture Notes

- Prolog logic: `strategify/logic/traits.pl`, `strategify/logic/bridge.py`
- Clojure MCTS: `strategify-clj/` + `strategify/logic/clj.py`
- Agent behaviours: Aggressor, Pacifist, Tit-for-Tat, Neutral, Grudger
- Cognitive agent (LLM + XAI): `strategify/agents/cognitive_actor.py`
- FastAPI routes: `strategify/web/api.py`
- Frontend pages: `frontend/src/pages/` (Dashboard, Simulation, Map, Analysis, XAI, HumanPlay, Economics)

## Code Style

- Run `ruff check .` before committing
- Use type hints on all function signatures
- Keep simulation logic separate from visualization
- Do NOT upgrade Mesa beyond 2.3.4
