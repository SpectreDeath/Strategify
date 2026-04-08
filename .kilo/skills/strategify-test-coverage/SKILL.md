---
name: strategify-test-coverage
description: Use when test coverage is below 70% and you need to systematically write tests for uncovered modules
---

# Geopol-Sim Test Coverage Skill

## Context

The strategify project requires 70% test coverage (set in pyproject.toml). Current coverage is ~26%. You need to write tests to close this gap.

## Uncovered Modules (Priority Order)

These modules have 0% or very low coverage and need tests:

1. **viz/** - All visualization modules (maps, networks, choropleth, export, reports, status)
2. **rl/** - Reinforcement learning (environment, training, tournament, evaluation)
3. **theory/** - Geopolitical theories
4. **sim/health.py** - Pandemic/health engine
5. **game_theory/coalition.py** - Coalition formation

## Coverage Target by Module

| Module | Current | Target | Gap |
|--------|---------|--------|-----|
| viz/* | 0% | 50% | Write render/export tests with mocks |
| rl/* | 0% | 50% | Write env tests with mock agents |
| theory/* | 0% | 30% | Write theory application tests |
| sim/health.py | 0% | 70% | Write engine tests |
| game_theory/coalition.py | 0% | 70% | Write coalition tests |

## Workflow

### Phase 1: Identify What to Test

1. Read the module to understand its public API
2. Identify pure functions and classes that can be tested without full model
3. Mark any dependencies that need mocking

### Phase 2: Write Tests

Follow the pattern in existing tests:

```python
# tests/test_viz_<module>.py
import pytest
from unittest.mock import patch, MagicMock

class TestVizModule:
    """Tests for viz module."""
    
    @pytest.fixture
    def mock_model(self):
        """Create a minimal mock model."""
        mock = MagicMock()
        mock.datacollector.get_agent_vars_dataframe.return_value = ...
        return mock
    
    def test_render_function(self, mock_model):
        """Test render produces output."""
        result = render_function(mock_model)
        assert result is not None
    
    def test_export_function(self, tmp_path, mock_model):
        """Test export writes file."""
        output = tmp_path / "output.html"
        export_function(mock_model, str(output))
        assert output.exists()
```

### Phase 3: Mock External Dependencies

For viz/rl modules that require heavy dependencies:

```python
@pytest.fixture
def mock_folium():
    with patch('strategify.viz.maps.folium') as mock:
        mock.Map.return_value = MagicMock()
        mock.FeatureGroup.return_value = MagicMock()
        yield mock

@pytest.fixture  
def mock_pettingzoo():
    with patch('strategify.rl.environment.pettingzoo') as mock:
        yield mock
```

### Phase 4: Run and Verify

```bash
# Run specific test file
pytest tests/test_viz_maps.py -v --cov=strategify.viz.maps --cov-report=term

# Run with coverage
pytest --cov=strategify --cov-report=term-missing --cov-fail-under=70
```

## Testing Strategy by Module Type

### Visualization Modules (viz/)

**Pattern:** Test that render functions:
1. Accept model/datacollector input
2. Return expected output type (folium.Map, HTML string, etc.)
3. Handle edge cases (empty model, missing data)

**Mock:** Folium, matplotlib, pyvis imports

### RL Modules (rl/)

**Pattern:** Test that environment:
1. Initializes with correct observation/action spaces
2. Step function returns valid format
3. Reset returns initial state

**Mock:** PettingZoo, Gymnasium imports

### Theory Modules (theory/)

**Pattern:** Test that theories:
1. Apply correctly to agent state
2. Return valid decision recommendations
3. Handle edge cases

**Mock:** None needed - these are usually pure functions

### Health Engine

**Pattern:** Test that health engine:
1. Spreads disease correctly
2. Applies interventions
3. Reports statistics

**Mock:** Random/seeded random for reproducibility

## Common Issues and Solutions

### Issue: Module imports fail during test collection

**Solution:** Use `@pytest.mark.importorskip('module_name')` or mock at import time

### Issue: Coverage not counting

**Solution:** Ensure `--cov=strategify` points to source, not test dir

### Issue: Tests too slow

**Solution:** Use `@pytest.mark.fast` for quick tests, mock heavy computations

## Verification

After writing tests, run:

```bash
# Check specific module coverage
pytest tests/test_viz_*.py --cov=strategify.viz --cov-report=term

# Full coverage check
pytest --cov=strategify --cov-report=term-missing --cov-fail-under=70
```

Target: Each uncovered module should have at least basic tests to reach 50%+ coverage. Critical modules (model, crisis_games, diplomacy) already have coverage - focus on the gaps.
