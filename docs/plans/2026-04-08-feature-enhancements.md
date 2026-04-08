# Feature Enhancements Implementation Plan

> **For agentic workers:** REQUIRED: Use `subagent-driven-development` (if subagents available) or `executing-plans` to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking via your Task Tracker.

**Goal:** Implement 9 feature enhancements to strengthen OSINT integration, CI/CD, visualization, and distribution

**Architecture:** 
- OSINT: Add WikipediaEventAdapter to existing adapter framework
- CI/CD: Enable GitHub Actions with CodeCov integration  
- Visualization: Add time-series and PDF/PNG export capabilities
- Distribution: Prepare for PyPI packaging

**Tech Stack:** Python, GitHub Actions, matplotlib, folium, pyvista, twine

---

## Phase 1: OSINT Enhancements

### Task 1: Wikipedia Events API Adapter

**Files:**
- Create: `strategify/osint/adapters.py` - add WikipediaEventAdapter class
- Modify: `strategify/osint/__init__.py` - export new adapter
- Test: `tests/test_osint_modules.py` - add Wikipedia adapter tests

- [ ] **Step 1: Add WikipediaEventAdapter to adapters.py**

```python
class WikipediaEventAdapter(BaseAdapter):
    """Adapter for Wikipedia Current Events API (free, no API key).
    
    Provides historical and current geopolitical events from Wikipedia's
    Current Events portal and related pages.
    """
    
    _EVENTS_URL = "https://en.wikipedia.org/api/rest_v1/page/related/Current_Events"
    
    @property
    def name(self) -> str:
        return "wikipedia"
    
    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        # Implementation uses Wikipedia REST API
        # Returns event summaries with timestamps
```

- [ ] **Step 2: Update __init__.py exports**
- [ ] **Step 3: Write tests**
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**

---

## Phase 2: CI/CD Enhancement

### Task 2: Enable GitHub Actions CI with CodeCov

**Files:**
- Modify: `.github/workflows/ci.yml` - add coverage reporting
- Create: `codecov.yml` - CodeCov configuration
- Modify: `pyproject.toml` - add pytest-cov if needed

- [ ] **Step 1: Update CI workflow with coverage**

```yaml
- name: Run tests with coverage
  run: |
    pip install pytest pytest-cov
    pytest --cov=strategify --cov-report=xml --cov-report=term
    
- name: Upload coverage to CodeCov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
    fail_ci_if_error: true
```

- [ ] **Step 2: Create codecov.yml**

```yaml
codecov:
  require_ci_to_pass: true
comment:
  require_base: false
```

- [ ] **Step 3: Test workflow locally**
- [ ] **Step 4: Commit and push to trigger CI**
- [ ] **Step 5: Verify GitHub Actions runs**

---

## Phase 3: Visualization Enhancements

### Task 3: Time-series Animation Export

**Files:**
- Modify: `strategify/viz/export.py` - add animation export functions
- Create: `strategify/viz/animation.py` - animation generation
- Test: `tests/test_viz_modules.py` - add animation tests

- [ ] **Step 1: Add export_animation() function**

```python
def export_animation(
    model_history: list[Any],
    output_path: str | Path = "simulation_animation.gif",
    fps: int = 2,
) -> Path:
    """Export simulation as animated GIF.
    
    Parameters
    ----------
    model_history:
        List of GeopolModel states at each timestep
    output_path:
        Output file path (.gif or .mp4)
    fps:
        Frames per second
    """
```

- [ ] **Step 2: Create animation.py module**
- [ ] **Step 3: Write tests**
- [ ] **Step 4: Run tests**
- [ ] **Step 5: Commit**

### Task 4: PDF/PNG Report Export

**Files:**
- Modify: `strategify/viz/export.py` - add PDF/PNG export
- Modify: `strategify/viz/reports.py` - enhance report generation

- [ ] **Step 1: Add export_report_pdf()**

```python
def export_report_pdf(
    model: Any,
    output_path: str | Path = "simulation_report.pdf",
    include_maps: bool = True,
    include_charts: bool = True,
) -> Path:
    """Generate comprehensive PDF report with maps and charts."""
```

- [ ] **Step 2: Add export_chart_png()**
- [ ] **Step 3: Run linting**
- [ ] **Step 4: Commit**

### Task 5: Conflict Timeline Export

**Files:**
- Create: `strategify/viz/timeline.py` - temporal visualization
- Modify: `strategify/viz/__init__.py` - export new functions

- [ ] **Step 1: Create timeline.py with export_timeline()**

```python
def export_timeline(
    model_history: list[Any],
    output_path: str | Path = "conflict_timeline.html",
) -> Path:
    """Export interactive timeline of conflicts and events."""
```

- [ ] **Step 2: Add to __init__.py**
- [ ] **Step 3: Commit**

---

## Phase 4: Scenario & Dashboard

### Task 6: Scenario Presets

**Files:**
- Create: `strategify/config/presets.py` - pre-configured scenarios
- Modify: `strategify/config/__init__.py` - export presets
- Create: `examples/ukraine_scenario.py`
- Create: `examples/middle_east_scenario.py`
- Create: `examples/south_china_sea_scenario.py`

- [ ] **Step 1: Create presets.py**

```python
class ScenarioPreset:
    """Pre-configured simulation scenario."""
    
    def __init__(
        self,
        name: str,
        regions: list[str],
        initial_relations: dict,
        keywords: dict[str, list[str]],
        duration: int = 50,
    ):
        self.name = name
        self.regions = regions
        self.initial_relations = initial_relations
        self.keywords = keywords
        self.duration = duration

UKRAINE_PRESET = ScenarioPreset(
    name="Ukraine Crisis",
    regions=["UKR", "RUS", "BLR", "POL", "MDA", "ROU", "HUN", "SVK"],
    initial_relations={...},
    keywords={...},
)

MIDDLE_EAST_PRESET = ScenarioPreset(...)
SOUTH_CHINA_SEA_PRESET = ScenarioPreset(...)
```

- [ ] **Step 2: Create example scripts**
- [ ] **Step 3: Commit**

### Task 7: Early Warning Dashboard

**Files:**
- Create: `strategify/viz/dashboard.py` - early warning UI
- Modify: `strategify/viz/__init__.py` - export dashboard

- [ ] **Step 1: Create dashboard.py**

```python
def create_early_warning_dashboard(
    model: Any,
    osint_data: dict[str, list],
    output_path: str | Path = "early_warning.html",
) -> Path:
    """Generate early warning dashboard combining:
    - Current sentiment scores
    - Risk assessment metrics
    - Escalation probability
    - Historical trend charts
    """
```

- [ ] **Step 2: Add to exports**
- [ ] **Step 3: Commit**

---

## Phase 5: PyPI Distribution

### Task 8: PyPI Package Preparation

**Files:**
- Modify: `pyproject.toml` - add PyPI metadata
- Create: `MANIFEST.in` - include data files
- Create: `docs/changelog.md` - version history
- Modify: `README.md` - add pip install badge

- [ ] **Step 1: Update pyproject.toml**

```toml
[project]
name = "strategify"
version = "0.1.0"
description = "Geopolitical simulation framework"
readme = "README.md"
license = {text = "MIT"}
authors = [{name = "Your Name", email = "you@example.com"}]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Science/Research",
    "Programming Language :: Python :: 3.11",
]

[project.urls]
Homepage = "https://github.com/SpectreDeath/Strategify"
```

- [ ] **Step 2: Create MANIFEST.in**
- [ ] **Step 3: Test local build**
- [ ] **Step 4: Commit**

---

## Execution Order

1. Task 1 (Wikipedia) - 30 min - OSINT enhancement
2. Task 2 (CI/CodeCov) - 20 min - Quality gates
3. Task 3-5 (Visualization) - 1 hr - Enhanced exports
4. Task 6-7 (Dashboard/Scenarios) - 1 hr - Usability
5. Task 8 (PyPI) - 30 min - Distribution

**Total estimated time:** ~4 hours

---

## Review Points

- After Task 1: Verify adapter integrates with FeaturePipeline
- After Task 2: Confirm CI triggers on push
- After Phase 3: Test all visualization exports work
- After Phase 4: Verify scenarios load correctly
- Before Task 8: Ensure all tests pass