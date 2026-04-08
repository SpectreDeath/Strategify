---
name: strategify-data-collection
description: Use when initializing simulation with real-world data, fetching GDELT/ACLED/WorldBank, or loading GeoJSON
---

# Geopol-Sim Data Collection Skill

## Data Sources

| Source | Data Type | Module |
|--------|-----------|--------|
| Natural Earth | Geographic boundaries | `geo/loader.py` |
| GDELT | News, events, sentiment | `osint/sources.py` |
| ACLED | Conflict events, fatalities | `osint/adapters.py` |
| World Bank | GDP, population, military | `osint/adapters.py` |

## Loading GeoJSON

### Load Real-World Map

```python
from strategify.geo.loader import GeoJSONLoader

loader = GeoJSONLoader("path/to/regions.geojson")
regions = loader.load()
print(f"Loaded {len(regions)} regions")

# Filter to specific countries
ukraine = loader.filter(regions, ["UKR", "RUS", "BLR", "POL"])
```

### Built-in Data

```python
from strategify.config.settings import REAL_WORLD_GEOJSON

# Default is data/uae_belarus_poland.geojson
print(f"GeoJSON: {REAL_WORLD_GEOJSON}")
```

## Real-World Data Collector

### Basic Usage

```python
from strategify.geo.real_data import RealWorldDataCollector, RegionData

collector = RealWorldDataCollector()

# Get initial state for all regions
initial_state = collector.get_initial_state()
# Returns: dict[region_id] -> RegionData

# Get specific region
ukraine_data = collector.get_region("UKR")
print(f"GDP: ${ukraine_data.gdp_usd:,.0f}")
print(f"Population: {ukraine_data.population:,}")
print(f"Military capability: {ukraine_data.military_capability}")
```

### Real-Time Updates

```python
# Get current metrics from APIs
metrics = collector.get_current_metrics()
# Updates GDELT tone, ACLED fatalities
```

## OSINT Pipeline

### Fetch External Data

```python
from strategify.osint.pipeline import FeaturePipeline
from strategify.osint.adapters import GDELTAdapter, ACLEDAdapter, WorldBankAdapter

pipeline = FeaturePipeline(
    adapters=[
        GDELTAdapter(cache_dir=".osint_cache"),
        ACLEDAdapter(cache_dir=".osint_cache"),
        WorldBankAdapter(cache_dir=".osint_cache"),
    ],
    cache_ttl_hours=6,
)

# Fetch for region
gdelt_data = pipeline.fetch("GDELT", region="UKR", start_date="2024-01-01")
acled_data = pipeline.fetch("ACLED", region="UKR", start_date="2024-01-01")

# Fetch economic indicators
wb_data = pipeline.fetch("WorldBank", indicators=["NY.GDP.MKTP.CD", "SP.POP.TOTL", "MS.MIL.XPND.GD.ZS"])
```

### Custom Adapter

```python
from strategify.osint.adapters import BaseAdapter

class MyAdapter(BaseAdapter):
    name = "my_source"
    
    def fetch(self, **kwargs):
        # Custom fetch logic
        return pd.DataFrame(...)
    
    def transform(self, raw_data):
        # Transform to standard format
        return {"region": ..., "metric": ...}

pipeline.add_adapter(MyAdapter())
```

## Initialize Model with Real Data

```python
from strategify import GeopolModel
from strategify.geo.real_data import RealWorldDataCollector

# Collect real data
collector = RealWorldDataCollector()
initial = collector.get_initial_state()

# Create model with real data
model = GeopolModel(n_steps=50)

# Update agents with real data
for agent in model.schedule.agents:
    if agent.region_id in initial:
        data = initial[agent.region_id]
        agent.capabilities = data.military_capability
        agent.resources = {"economic": data.economic_capability}
```

## Caching

```python
# OSINT data is cached automatically
pipeline = FeaturePipeline(cache_dir=".osint_cache", cache_ttl_hours=24)

# Force refresh
pipeline.fetch("GDELT", region="UKR", force_refresh=True)

# Clear cache
pipeline.clear_cache()
```

## Common Issues

### Issue: GeoJSON not found

**Fix:** Check `REAL_WORLD_GEOJSON` path in settings

### Issue: API rate limits

**Fix:** Use caching, reduce fetch frequency

### Issue: Missing data for region

**Fix:** Fallback to defaults in `RegionData`

## Data Scripts

```bash
# Fetch real data
python scripts/fetch_real_world.py

# Initialize with real data
python scripts/init_with_real_data.py
```
