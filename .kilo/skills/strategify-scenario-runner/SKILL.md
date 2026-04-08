---
name: strategify-scenario-runner
description: Use when running strategify simulations in headless mode or creating new scenario configurations
---

# Geopol-Sim Scenario Runner Skill

## Quick Start

### Run Built-in Scenario

```bash
# Basic crisis scenario (CSV output)
python examples/basic_crisis_scenario/run.py

# With custom scenario
python -c "from strategify import GeopolModel; m = GeopolModel(scenario='default', n_steps=50)"
```

### Run Interactive Visualization

```bash
# Map-based server
strategify
# or
python -m strategify.sim.run_mesa_geo_server
```

Then open http://localhost:8521

### Run Grid Demo

```bash
python -m strategify.sim.run_mesa_server
```

## Programmatic Usage

```python
from strategify import GeopolModel
from strategify.viz import create_map, create_diplomacy_network

# Create model with options
model = GeopolModel(
    n_steps=50,
    scenario="default",
    enable_economics=True,
    enable_escalation_ladder=True,
    enable_non_state_actors=True,
    enable_health=False,
    enable_temporal=False,
    enable_propaganda=False,
)

# Run simulation
for step in range(model.n_steps):
    model.step()
    if step % 10 == 0:
        print(f"Step {step} complete")

# Export visualizations
create_map(model, "map.html")
create_diplomacy_network(model, "network.html")

# Access data
df = model.datacollector.get_agent_vars_dataframe()
```

## Scenario Configuration

### Built-in Scenarios

Located in `strategify/config/scenarios.py`:
- `"default"` - Ukraine, Russia, Belarus, Poland with default settings
- `"arms_race"` - High tension scenario
- Custom scenarios via JSON

### Custom Scenario JSON

```json
{
  "region_data": "path/to/geojson.json",
  "actors": [
    {
      "region_id": "UKR",
      "actor_name": "Ukraine",
      "initial_capabilities": 0.6,
      "strategy_type": "TitForTat",
      "ideology": "Neutral",
      "resources": {"energy": 0.5, "food": 0.8, "military": 0.6}
    }
  ],
  "alliances": [
    {"member1": "UKR", "member2": "POL", "strength": 0.7}
  ],
  "rivalries": [
    {"actor1": "RUS", "actor2": "UKR", "intensity": 0.9}
  ]
}
```

### Load Custom Scenario

```python
from strategify.config.scenarios import load_scenario

config = load_scenario("path/to/scenario.json")
model = GeopolModel(scenario=config)
```

## Engine Options

| Option | Description | Default |
|--------|-------------|---------|
| `enable_economics` | Trade network | True |
| `enable_escalation_ladder` | Discrete escalation levels | True |
| `enable_non_state_actors` | Insurgents, NGOs | True |
| `enable_health` | Pandemic spread | False |
| `enable_temporal` | Seasons, elections | False |
| `enable_propaganda` | Information warfare | False |

## Output Files

After running:
- `simulation_output.csv` - Agent state over time
- `final_state.json` - Complete final state
- `map.html` - Interactive Folium map
- `network.html` - Pyvis diplomacy network

## Analysis Integration

```python
from strategify.analysis import (
    prepare_agent_timeseries,
    fit_var_model,
    pairwise_granger_causality,
    detect_communities,
)

# Get data
df = model.datacollector.get_agent_vars_dataframe()

# Time series analysis
ts = prepare_agent_timeseries(df)
var_result = fit_var_model(ts, maxlags=3)

# Community detection
G = model.diplomacy.get_network()
communities = detect_communities(G)
```

## CLI Commands

```bash
# Scenario management
strategify-scenario list
strategify-scenario validate path/to/scenario.json

# Dashboard
strategify-dashboard
```
