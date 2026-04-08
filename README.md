# strategify

[![PyPI](https://img.shields.io/pypi/v/strategify)](https://pypi.org/project/strategify/)
[![Python](https://img.shields.io/pypi/pyversions/strategify)](https://pypi.org/project/strategify/)
[![License](https://img.shields.io/pypi/l/strategify)](https://opensource.org/licenses/MIT)
[![CodeCov](https://codecov.io/gh/SpectreDeath/Strategify/branch/master/graph/badge.svg)](https://codecov.io/gh/SpectreDeath/Strategify)

A Python framework for geopolitical simulations using agent-based modeling (ABM),
game-theoretic decision modules, and geospatial data.

## Features

- **Agent-Based Simulation** — Mesa 2 model with `StateActorAgent` actors on a real-world GeoJSON map (Ukraine, Russia, Belarus, Poland)
- **Game Theory** — Nash equilibrium via nashpy; Chicken/brinkmanship crisis game with dynamic payoff adjustment
- **Diplomacy Graph** — NetworkX alliance/rivalry network with weighted edges
- **Influence Maps** — BFS-based spatial reasoning, escalation contagion, Moran's I spatial autocorrelation
- **Axelrod Strategies** — 5 personality types (Aggressor, Pacifist, Tit-for-Tat, Neutral, Grudger) via the Axelrod library
- **Analysis Suite** — VAR models, Granger causality, OLS causal inference, Louvain community detection, Sobol sensitivity analysis, NSGA2 multi-objective optimization, strategic risk assessment, war gaming, alliance forecasting
- **Real-World Data** — Natural Earth geographic data, OSINT integration (GDELT, ReliefWeb, Wikipedia), real-time tension updates
- **Geopolitical Theories** — Realpolitik, Democratic Peace, Power Transition, Offensive/Defensive Realism, Liberal Institutionalism, Constructivism
- **OSINT Pipeline** — VADER sentiment analysis, GDELT/ACLED/WorldBank/ReliefWeb/Wikipedia adapters with SQLite caching, RSS feed ingestion
- **RL Environment** — PettingZoo AEC multi-agent environment for training policies
- **Visualization** — Interactive Folium maps, Pyvis networks, Matplotlib choropleths, GEXF for Gephi, animated GIFs, PDF reports, interactive timeline
- **Scenario Presets** — Pre-configured scenarios for Ukraine Crisis, Middle East, and South China Sea
- **Early Warning Dashboard** — Real-time risk assessment combining OSINT sentiment with strategic analysis

## Installation

```bash
# Core (simulation + game theory + maps)
pip install -e .

# With analysis tools (VAR, sensitivity, optimization, communities)
pip install -e ".[analysis]"

# With reinforcement learning (PettingZoo, Gymnasium)
pip install -e ".[rl]"

# Development (pytest, coverage)
pip install -e ".[dev]"

# Everything
pip install -e ".[analysis,rl,dev]"
```

## Quick Start

### Headless run (CSV output)

```bash
python examples/basic_crisis_scenario/run.py
```

### Interactive map visualization

```bash
strategify
# or: python -m strategify.sim.run_mesa_geo_server
```

Then open http://localhost:8521 in your browser.

### Grid demo mode

```bash
python -m strategify.sim.run_mesa_server
```

## Programmatic Usage

```python
from strategify import GeopolModel, escalation_game, NormalFormGame
from strategify.viz import create_map, create_diplomacy_network

# Run simulation
model = GeopolModel()
for _ in range(20):
    model.step()

# Export visualizations
create_map(model, "map.html")
create_diplomacy_network(model, "network.html")

# Access data
df = model.datacollector.get_agent_vars_dataframe()
```

### Analysis

```python
from strategify.analysis import (
    prepare_agent_timeseries,
    fit_var_model,
    pairwise_granger_causality,
    build_causal_data,
    pairwise_causal_effects,
    detect_communities,
)

# Time series analysis
ts = prepare_agent_timeseries(df)
var_result = fit_var_model(ts, maxlags=3)
granger = pairwise_granger_causality(ts)

# Causal inference
causal_df = build_causal_data(model, n_steps=30)
effects = pairwise_causal_effects(causal_df)

# Community detection
communities = detect_communities(model)
```

### OSINT sentiment

```python
from strategify.osint import analyze_sentiment, analyze_texts_sentiment

score = analyze_sentiment("Military tensions escalate at the border")
batch = analyze_texts_sentiment(["headline 1", "headline 2"])
print(batch["tension_score"])  # 0.0 (calm) to 1.0 (high tension)
```

### RL environment

```python
from strategify.rl import GeopolEnv

env = GeopolEnv()
env.reset()
for agent in env.agent_iter():
    obs, rew, term, trunc, info = env.last()
    action = env.action_space(agent).sample()
    env.step(action)
```

### OSINT Data Collection

```python
from strategify.osint import (
    FeaturePipeline,
    GDELTAdapter,
    ACLEDAdapter,
    ReliefWebAdapter,
    WorldBankAdapter,
    analyze_sentiment,
)

# Initialize pipeline with caching
pipeline = FeaturePipeline(
    adapters=[
        GDELTAdapter(cache_dir=".osint_cache"),
        ACLEDAdapter(cache_dir=".osint_cache"),
        ReliefWebAdapter(cache_dir=".osint_cache"),
        WorldBankAdapter(cache_dir=".osint_cache"),
    ],
    cache_ttl_hours=6,
)

# Fetch current events for scenario regions
region_keywords = {
    "UKR": ["Ukraine", "Russia", "war", "military"],
    "RUS": ["Russia", "Putin", "sanctions"],
    "POL": ["Poland", "NATO", "border"],
}

events = pipeline.fetch("GDELT", region_keywords=region_keywords)

# Analyze sentiment
for event in events[:5]:
    score = analyze_sentiment(event["text"])
    print(f"{event['text'][:50]}: {score:.2f}")
```

### RSS News Feeds

```python
from strategify.osint import fetch_rss_feed

bbc = fetch_rss_feed("https://feeds.bbci.co.uk/news/world/rss.xml")
reuters = fetch_rss_feed("https://www.reutersagency.com/feed/?best-topics=politics")
```

### Gephi Network Export

```python
from strategify.viz import export_gexf, export_diplomacy_snapshot

# Export for Gephi analysis
export_gexf(model, "diplomacy_network.gexf")

# Time-series snapshots for temporal analysis
for step in range(20):
    model.step()
    export_diplomacy_snapshot(model, "gephi_snapshots")

# Then open .gexf files in Gephi for:
# - ForceAtlas2 layout
# - Community detection
# - Centrality metrics (betweenness, degree, PageRank)
# - Export to PDF/SVG/PNG
```

### Initialize Model with Real-World Data

```python
from strategify.geo.real_data import RealWorldDataCollector
from strategify import GeopolModel

# Get real-world data for initialization
collector = RealWorldDataCollector()
initial_state = collector.get_initial_state()

# Create model with real capabilities
model = GeopolModel()
for agent in model.schedule.agents:
    rid = getattr(agent, "region_id", None)
    if rid and rid in initial_state:
        data = initial_state[rid]
        agent.capabilities["military"] = data.military_capability
        agent.capabilities["economic"] = data.gdp_usd
        agent.capabilities["diplomatic"] = data.diplomatic_score
```

### Scenario Presets

```python
from strategify.config import get_preset, list_presets

# List available presets
print(list_presets())  # ['ukraine', 'middle_east', 'south_china_sea']

# Load a preset
preset = get_preset("ukraine")
print(preset.name)        # Ukraine Crisis
print(preset.regions)     # ['UKR', 'RUS', 'BLR', 'POL', ...]
print(preset.keywords)    # OSINT keywords per region
```

### Animation & Timeline Export

```python
from strategify.viz import export_animation, export_timeline

# Run simulation and capture history
model_history = []
model = GeopolModel()
for _ in range(20):
    model.step()
    model_history.append(model)

# Export animated GIF
export_animation(model_history, "simulation.gif")

# Export interactive HTML timeline
export_timeline(model_history, "timeline.html")
```

### PDF Report Generation

```python
from strategify.viz import export_report_pdf

# Generate comprehensive PDF report
export_report_pdf(model, "report.pdf", include_maps=True, include_charts=True)
```

### Early Warning Dashboard

```python
from strategify.viz import create_early_warning_dashboard

# Create dashboard with OSINT data
osint_data = {"UKR": events_ukr, "RUS": events_rus}
create_early_warning_dashboard(model, osint_data, "dashboard.html")
# Opens as interactive HTML with:
# - Actor status (posture, capabilities)
# - Risk assessment (threat scores)
# - OSINT sentiment (tension bars)
```

## Project Structure

```
strategify/
  config/        — settings, constants, scenario definitions
  geo/           — GeoJSON data (real-world regions, demo grid)
  game_theory/   — NormalFormGame wrapper, payoff matrices
  agents/        — BaseActorAgent, StateActorAgent
  reasoning/     — DiplomacyGraph, InfluenceMap, Axelrod strategies
  sim/           — GeopolModel, Mesa browser servers
  analysis/      — VAR, Granger causality, causal inference, communities, sensitivity, optimization
  osint/         — VADER sentiment pipeline
  rl/            — PettingZoo AEC environment
  viz/           — Folium maps, Pyvis networks, Mesa status element
examples/
  basic_crisis_scenario/  — headless 20-step run with CSV output
scripts/
  fetch_real_world.py     — download Natural Earth GeoJSON
tests/
  15 test files covering all modules
docs/
  architecture.md         — module overview, data flow
  algorithms.md           — Mesa scheduling, Nash equilibrium, adjacency
```

## Running Tests

```bash
pytest                           # all tests with coverage
pytest -v                        # verbose
pytest -m "not slow"             # skip slow sensitivity tests
pytest --cov=strategify --cov-report=html  # HTML coverage report
```

## Reproducibility

`GeopolModel` seeds `random` with `42` in `__init__`. Nash equilibrium
tie-breaking always selects index 0 from `support_enumeration()`.

## Requirements

- Python >= 3.11
- Mesa 2.3.4 (pinned — do **not** upgrade to Mesa 3)
