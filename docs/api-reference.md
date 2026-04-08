# strategify API Reference

Complete API reference for all modules.

## Quick Start

```python
from strategify import GeopolModel
from strategify.analysis import *
from strategify.theory import DEFAULT_REGISTRY
from strategify.geo import create_data_collector
```

---

## Core Simulation (`strategify.sim`)

### GeopolModel

```python
from strategify import GeopolModel

model = GeopolModel(n_steps=100)
for _ in range(100):
    model.step()
```

**Parameters:**
- `n_steps`: Maximum steps for headless run
- `scenario`: Scenario name or path to JSON
- `enable_economics`: Enable trade network
- `enable_escalation_ladder`: Discrete escalation levels
- `enable_health`: Pandemic spread
- `region_gdf`: Pre-loaded GeoDataFrame

---

## Analysis Suite (`strategify.analysis`)

### Time Series Analysis

```python
from strategify.analysis import (
    prepare_agent_timeseries,
    fit_var_model,
    pairwise_granger_causality,
)

ts = prepare_agent_timeseries(df)
var_result = fit_var_model(ts, maxlags=3)
granger = pairwise_granger_causality(ts)
```

### Sensitivity & Optimization

```python
from strategify.analysis import (
    run_sensitivity_analysis,
    rank_parameters,
    optimize_resources,
)

# Sobol sensitivity
results = run_sensitivity_analysis(
    model_factory, 
    param_ranges,
    n_samples=100,
)
ranked = rank_parameters(results)

# NSGA2 optimization
opt_result = optimize_resources(
    model_factory,
    n_regions=4,
    n_generations=50,
)
```

### Risk Assessment

```python
from strategify.analysis import (
    RiskLevel,
    assess_all_risks,
    compute_threat_score,
    identify_critical_regions,
)

risks = assess_all_risks(model)
critical = identify_critical_regions(risks)

# Per-region
score = compute_threat_score(model, "alpha")
level = get_risk_level(score)
```

### War Gaming

```python
from strategify.analysis import (
    run_war_game,
    predict_adversary_response,
    analyze_red_lines,
    AdversaryType,
)

# Monte Carlo adversary simulation
result = run_war_game(
    model_factory,
    initial_state={"alpha": "Deescalate"},
    my_actions=["Escalate", "Deescalate"],
    n_simulations=100,
)

# Predict specific response
response = predict_adversary_response(
    model, "bravo", "Escalate", AdversaryType.AGGRESSIVE
)
```

### Alliance Forecasting

```python
from strategify.analysis import (
    forecast_alliance_stability,
    compute_alliance_strength,
    predict_fracture_probability,
    suggest_rebalancing,
)

stability = forecast_alliance_stability(model, n_future_steps=20)
rebalance = suggest_rebalancing(model, "alpha")
```

### Strategic Recommendations

```python
from strategify.analysis import (
    generate_strategy_report,
    compute_optimal_action,
    compute_win_probability,
    recommend_preemptive_actions,
)

report = generate_strategy_report(model, "alpha")
win_prob = compute_win_probability(model, "alpha", "bravo")
actions = recommend_preemptive_actions(model, target_risk=0.5)
```

---

## Geopolitical Theories (`strategify.theory`)

```python
from strategify.theory import (
    DEFAULT_REGISTRY,
    RealpolitikTheory,
    DemocraticPeaceTheory,
    PowerTransitionTheory,
    OffensiveRealism,
    DefensiveRealism,
    LiberalInstitutionalism,
    Constructivism,
)

# Get theory-based decision
result = DEFAULT_REGISTRY.decide(agent, model, "Realpolitik")

# Analyze with all theories
results = DEFAULT_REGISTRY.analyze_with_all(agent, model)
for r in results:
    print(f"{r.theory}: {r.recommended_action} (conf={r.confidence})")
```

**Available Theories:**
| Theory | Key Principle |
|--------|------------|
| Realpolitik | Balance of power |
| Democratic Peace | Democracies don't fight |
| Power Transition | Rising powers challenge |
| Offensive Realism | Aggression pays |
| Defensive Realism | Security through balancing |
| Liberal Institutionalism | Institutions enable cooperation |
| Constructivism | Identity shapes interests |

---

## Data Collection (`strategify.geo`)

```python
from strategify.geo import (
    RealWorldDataCollector,
    create_data_collector,
    GeoJSONLoader,
    RegionSubsetConfig,
)

# Create collector
collector = create_data_collector()
collector.load_geometries()

# Custom config
config = RegionSubsetConfig(
    countries=["Ukraine", "Russia", "Poland"],
    id_map={"Ukraine": "alpha", "Russia": "bravo"},
    resolution="50m",
)
gdf = GeoJSONLoader.load(config)
```

---

## OSINT Pipeline (`strategify.osint`)

```python
from strategify.osint import FeaturePipeline
from strategify.osint.adapters import GDELTAdapter

pipeline = FeaturePipeline(
    region_keywords={
        "alpha": ["Ukraine", "Kyiv"],
        "bravo": ["Russia", "Moscow"],
    },
    adapters=[GDELTAdapter()],
    cache_ttl=3600,
)
features = pipeline.compute()
```

---

## Visualization (`strategify.viz`)

```python
from strategify.viz import create_map, create_diplomacy_network

# Interactive map with satellite imagery
create_map(model, "map.html", basemap="satellite")
create_alliance_map(model, "alliances.html", basemap="satellite")
create_diplomacy_network(model, "network.html")

# Static choropleth
from strategify.viz.choropleth import HeadlessChoropleth
renderer = HeadlessChoropleth(model)
renderer.render_step("frame.png")
```

---

## RL Environment (`strategify.rl`)

```python
from strategify.rl import GeopolEnv
from pettingzoo.test import api_test

env = GeopolEnv()
env.reset()

for agent in env.agent_iter():
    obs, rew, term, trunc, info = env.last()
    action = env.action_space(agent).sample()
    env.step(action)
```

---

## Reinforcement Learning (`strategify.rl`)

```python
from strategify.rl.evaluation import evaluate_policy
from strategify.rl.training import train_qlearning

# Training
train_qlearning(env, episodes=1000)

# Evaluation
win_rate = evaluate_policy(env, policy, n_episodes=100)
```

---

## Configuration (`strategify.config`)

```python
from strategify.config.scenarios import load_scenario
from strategify.config.settings import get_region_hex_color

# Load scenario
scenario = load_scenario("default")

# Get region colors
color = get_region_hex_color("alpha")
```

---

## CLI Usage

```bash
# Run simulation
strategify

# Run with specific scenario
strategify --scenario arms_race

# Run with real data
python scripts/init_with_real_data.py
```