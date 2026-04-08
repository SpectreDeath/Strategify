---
name: strategify-visualization
description: Use when creating visualizations from simulation output, building custom map overlays, or extending with plugins
---

# Geopol-Sim Visualization & Extension Skill

## Visualization Modules

### Maps (Folium)

```python
from strategify.viz import create_map

# Create interactive map
create_map(model, "map.html")
# Opens in browser or saves to file
```

**Map Options:**
```python
create_map(
    model,
    "map.html",
    basemap="satellite",  # "satellite", "streets", "topo"
    show_alliances=True,
    show_rivalries=True,
    color_by="capabilities",  # or "escalation", "ideology"
)
```

### Diplomacy Network (Pyvis)

```python
from strategify.viz import create_diplomacy_network

create_diplomacy_network(model, "network.html")
```

### Choropleth

```python
from strategify.viz import create_choropleth

create_choropleth(
    model,
    "choropleth.png",
    metric="escalation",  # or "capabilities", "resources"
    colormap="RdYlBu_r",
)
```

### Custom Visualization

```python
from strategify.viz.maps import MapRenderer

renderer = MapRenderer(model)
overlay = renderer.add_choropleth(
    data=agent_capabilities,
    colormap="viridis",
)
renderer.save("custom_map.html")
```

## Plugin System

### Creating a Plugin

```python
# my_plugin.py
from strategify.plugins import AgentPlugin, register_plugin

@AgentPlugin
class MediaInfluencePlugin:
    """Extends agent behavior with media influence."""
    
    name = "media_influence"
    
    def on_step(self, agent, model):
        # Modify agent behavior each step
        agent.media_coverage *= 1.05
    
    def on_escalation(self, agent, model, level):
        # Handle escalation events
        if level > 3:
            agent.legitimacy -= 0.1

# Register plugin
register_plugin(MediaInfluencePlugin)
```

### Using Plugins

```python
from strategify import GeopolModel

# Plugins loaded via entry point or explicit registration
model = GeopolModel(
    n_steps=50,
    plugins=["media_influence", "economic_sanctions"],
)
```

### Plugin Entry Points

In `pyproject.toml`:
```toml
[project.entry-points."strategify.plugins"]
media = "my_package.plugins:MediaInfluencePlugin"
```

## Custom Agent Types

### Extend StateActorAgent

```python
from strategify.agents.state_actor import StateActorAgent

class CustomAgent(StateActorAgent):
    def __init__(self, *args, custom_param=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_param = custom_param
    
    def decide(self, model):
        # Custom decision logic
        if self.custom_param:
            return self.custom_strategy()
        return super().decide(model)
```

### Add to Model

```python
from strategify import GeopolModel

model = GeopolModel(n_steps=50)

# Add custom agent
custom = CustomAgent(
    model.next_id(),
    "CustomRegion",
    model,
    custom_param=0.5,
)
model.schedule.add(custom)
```

## Dashboard

```bash
# Start dashboard
strategify-dashboard
# or
python -m strategify.web.dashboard
```

Then open http://localhost:8501

### Dashboard Features

- Time series plots
- Agent state tables
- Network visualization
- Escalation heatmaps
- Strategy comparison

## Export Options

### CSV

```python
from strategify.viz.export import export_csv

df = model.datacollector.get_agent_vars_dataframe()
export_csv(df, "output.csv")
```

### JSON

```python
from strategify.viz.export import export_json

export_json(model, "state.json")
```

### Geopackage

```python
from strategify.viz.export import export_geopackage

export_geopackage(model, "output.gpkg")
```

## Common Visualization Issues

### Issue: Map not showing data

**Fix:** Ensure model has run at least one step

### Issue: Network too large

**Fix:** Use `filter_threshold` parameter

### Issue: Folium not installed

**Fix:** `pip install folium pyvis`
