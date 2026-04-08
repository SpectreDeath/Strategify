---
name: strategify-osint-analysis
description: Use when working with OSINT data sources, sentiment analysis, or building analysis pipelines (VAR, Granger causality, community detection)
---

# Geopol-Sim OSINT & Analysis Skill

## OSINT Pipeline

### Data Sources

| Source | Adapter | Data Type |
|--------|---------|-----------|
| GDELT | `GDELTAdapter` | Conflict events, media mentions |
| ACLED | `ACLEDAdapter` | Armed conflict data |
| World Bank | `WorldBankAdapter` | Economic indicators |
| Custom | `BaseAdapter` | Plug your own |

### Usage

```python
from strategify.osint.pipeline import FeaturePipeline
from strategify.osint.adapters import GDELTAdapter, WorldBankAdapter

# Create pipeline
pipeline = FeaturePipeline(
    adapters=[
        GDELTAdapter(cache_dir=".osint_cache"),
        WorldBankAdapter(cache_dir=".osint_cache"),
    ]
)

# Fetch data for region
gdelt_data = pipeline.fetch("GDELT", region="UKR", start_date="2024-01-01")
wb_data = pipeline.fetch("WorldBank", indicators=["GDP", "Population"])

# Use in simulation
model = GeopolModel()
model.update_from_osint(gdelt_data)
```

### Sentiment Analysis

```python
from strategify.osint.features import extract_tension_features

# Extract tension features from news
features = extract_tension_features(news_articles)
# Returns: {sentiment_score, event_intensity, escalation_risk, ...}
```

## Analysis Suite

### Time Series Analysis

```python
from strategify.analysis import (
    prepare_agent_timeseries,
    fit_var_model,
    pairwise_granger_causality,
)

# Get model data
df = model.datacollector.get_agent_vars_dataframe()

# Prepare time series
ts = prepare_agent_timeseries(df)

# Fit VAR model
result = fit_var_model(ts, maxlags=3)
print(result.summary())

# Granger causality (who influences whom)
granger_matrix = pairwise_granger_causality(ts)
```

### Causal Inference

```python
from strategify.analysis import build_causal_data, pairwise_causal_effects

# Build causal dataset from simulation
causal_df = build_causal_data(model, n_steps=30)

# Estimate pairwise effects
effects = pairwise_causal_effects(causal_df)
# Returns DataFrame with: source, target, effect_size, p_value
```

### Community Detection

```python
from strategify.analysis import detect_communities
from strategify.viz import create_diplomacy_network

# Get diplomacy network
G = model.diplomacy.get_network()

# Detect communities (Louvain)
communities = detect_communities(G)
# Returns: dict {node: community_id}

# Visualize
create_diplomacy_network(model, "network.html")
```

### Sensitivity Analysis

```python
from strategify.analysis import run_sobol_sensitivity

# Run Sobol sensitivity analysis
result = run_sobol_sensitivity(
    model_class=GeopolModel,
    params={"escalation_weight": (0.1, 1.0), "alliance_strength": (0.3, 0.9)},
    n_samples=500,
    n_steps=20,
)
print(result.indices)
```

### Multi-Objective Optimization

```python
from strategify.analysis import optimize_strategy

# Find Pareto-optimal strategies
result = optimize_strategy(
    model_class=GeopolModel,
    objectives=["min_escalation", "max_stability"],
    n_generations=50,
    population_size=100,
)
print(result.best_solutions)
```

## Analysis Dashboard

```bash
# Start analysis dashboard
strategify-dashboard
```

This provides:
- Time series visualization
- Granger causality heatmap
- Community network visualization
- Sensitivity analysis results
- Strategic recommendation engine

## Common Analysis Patterns

### Debug Analysis Pipeline

```python
# Check data flow
from strategify.analysis import prepare_agent_timeseries

df = model.datacollector.get_agent_vars_dataframe()
print(df.columns)
print(df.head())
ts = prepare_agent_timeseries(df)
print(ts.shape)
```

### Missing Data Handling

```python
# Analysis functions handle NaN automatically
# For custom handling:
df = df.fillna(method='ffill')  # Forward fill
df = df.dropna()  # Or drop
```
