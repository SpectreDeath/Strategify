---
name: strategify-debugging
description: Use when tests fail, verification scripts produce errors, or simulation behavior is unexpected
---

# Geopol-Sim Debugging Skill

## Verification Scripts

The project has phase verification scripts for different features:

```bash
# Run specific verification
python verify_phase6.py   # Diplomacy phase
python verify_phase7.py  # Dynamic payoffs
python verify_phase8.py  # Influence maps
python verify_phase9.py  # RL tournament
python verify_phase10.py # Optimization
```

## Common Issues

### Issue: Tests timeout or hang

**Cause:** Heavy computation or infinite loop in model step
**Fix:** Check `model.step()` for blocking operations; add timeout to tests

### Issue: Import errors

**Cause:** Missing dependencies
**Fix:** 
```bash
pip install -e ".[analysis,rl,dev]"
```

### Issue: Coverage below 70%

**Cause:** Tests not covering viz, rl, theory modules
**Fix:** See `strategify-test-coverage` skill

### Issue: GeoJSON not loading

**Cause:** Invalid GeoJSON path
**Fix:** Verify path in `config/settings.py` or scenario config

### Issue: LLM queries fail

**Cause:** No API key or network issue
**Fix:** Set environment variable or use fallback mode

## Debug Patterns

### Check Model State

```python
from strategify import GeopolModel

model = GeopolModel(n_steps=5)
print(f"Agents: {model.schedule.agents}")
print(f"Steps: {model.steps}")
print(f"Current step: {model.current_step}")

# Check agent state
for agent in model.schedule.agents:
    print(f"{agent}: cap={agent.capabilities}, esc={agent.escalation_level}")
```

### Check Diplomacy Graph

```python
# Get alliance network
G = model.diplomacy.get_network()
print(f"Nodes: {list(G.nodes())}")
print(f"Edges: {list(G.edges(data=True))}")
```

### Enable Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

from strategify import GeopolModel
model = GeopolModel(n_steps=1)
```

## Test Debugging

### Run single test

```bash
pytest tests/test_model.py::TestGeopolModel::test_init -v
```

### Run with PDB on failure

```bash
pytest tests/test_model.py --pdb --tb=short
```

### Check fixtures

```bash
pytest tests/test_model.py --fixtures
```

## Known Issues Summary

| Issue | Phase | Solution |
|-------|-------|----------|
| Coverage < 70% | All | Write tests for viz/rl/theory modules |
| RL tests slow | 9 | Use mock environments |
| LLM API required | Audit | Skip if no API key |
| GeoJSON path | 1-4 | Verify path in settings |
