# strategify Architecture

## 1. Module Overview

| Package | Role |
|---|---|
| `strategify.config` | Global constants, paths, defaults, scenario configurations |
| `strategify.geo` | GeoJSON loader, adjacency builder, Natural Earth support, real-world data collector |
| `strategify.game_theory` | `NormalFormGame` wrapper, crisis games, coalition dispatch, dynamic payoffs |
| `strategify.agents` | `BaseActorAgent` (abstract), `StateActorAgent`, `MilitaryComponent`, `NonStateActor`, `OrganizationAgent`, `EscalationLadder`, `InternalFaction` |
| `strategify.reasoning` | `DiplomacyGraph`, `DiplomaticMemory`, `StrategicSignaling`, `MultilateralSummit`, `InfluenceMap`, `DiplomacyStrategy` (Axelrod), `TradeNetwork`, `PopulationModel`, `TemporalDynamics`, `PropagandaEngine`, `MultiScaleModel`, `LLMDecisionEngine` |
| `strategify.sim` | `GeopolModel` (Mesa Model), `ConflictEngine`, `EnvironmentalManager`, `HealthEngine`, persistence, runner, browser server entry points |
| `strategify.analysis` | VAR/Granger, OLS causal, Louvain communities, Sobol sensitivity, NSGA2 optimization, ARIMA forecasting, counterfactuals, early warning, calibration, Monte Carlo dashboard, strategic risk, war gaming, alliance forecasting, strategy recommendations |
| `strategify.osint` | GDELT/ACLED/WorldBank adapters, VADER sentiment, SQLite cache, feature pipeline |
| `strategify.viz` | Folium choropleth maps (satellite/streets/topo), Pyvis network graphs, Matplotlib static maps, HTML reports, Mesa status element, export (CSV/GeoJSON/LaTeX/SVG) |
| `strategify.rl` | PettingZoo AEC multi-agent RL environment, Q-learning, tournament |
| `strategify.theory` | Geopolitical theories: Realpolitik, Democratic Peace, Power Transition, Offensive/Defensive Realism, Liberal Institutionalism, Constructivism |
| `strategify.web` | Streamlit dashboard with 6 tabs |
| `strategify.plugins` | Plugin registration API + entry point discovery |
| `strategify.dynamics` | Internal dynamics: factional politics, ideology, public opinion, leadership cycles |

## 2. Data Flow

```
OSINT / adapters.py          Scenario JSON
       │  (region features)         │
       ▼                            ▼
GeoJSONLoader ──regions──► GeopolModel.__init__()
       │                        │
       │                   agents, diplomacy, economics,
       │                   escalation, military, health,
       │                   temporal, propaganda
       │                        │
       ▼                        ▼
GeopolModel.step() ──────────────────────────────
  │  1. InfluenceMap.compute()
  │  2. TemporalDynamics.step()        (seasons, elections, cycles)
  │  3. TradeNetwork.step() + PopulationModel.step()
  │  4. EscalationLadder.step()
  │  5. Coalition dispatch (pairwise games)
  │  6. DiplomaticMemory.step() + StrategicSignaling.resolve()
  │  7. ConflictEngine.step()          (kinetic combat)
  │  8. EnvironmentalManager.step()    (resources, climate)
  │  9. HealthEngine.step()            (pandemic spread)
  │  10. schedule.step()               (agents act)
  │  11. PropagandaEngine.step()       (information warfare)
  │  12. DataCollector.collect()
       │
       ▼
  get_agent_vars_dataframe() → CSV / analysis / viz
```

## 3. Key Design Decisions

### Mesa 2 pinned at 2.3.4
Mesa 3.x removed `ModularServer`, `RandomActivation`, and
`SimultaneousActivation`. This project explicitly targets the Mesa 2 API. Do
not upgrade without a full API migration.

### Deterministic equilibrium selection
`NormalFormGame.select_equilibrium()` always picks index `[0]` from
`nashpy`'s `support_enumeration()` output. The uniform-strategy fallback is
used only when the list is empty. Combined with `random.seed(42)` in
`GeopolModel.__init__`, this ensures fully reproducible runs.

### GeoJSON grid layout
`regions_demo.geojson` uses a strict 2×2 coordinate grid with exact shared
edges. This guarantees that `shapely.touches()` + intersection type check
produces the correct 4 adjacency pairs (alpha↔bravo, alpha↔charlie,
bravo↔delta, charlie↔delta) and zero false positives from diagonal corners.

### DataCollector timing
Agent reporters capture **post-action** state (after `schedule.step()`).
This is intentional: we record what agents *did*, not what they were going to do.
Model-level reporters capture `step` count. Pre-action state (e.g. influence map)
is available via `self.influence_map` before `schedule.step()`.

### Optional subsystems
TemporalDynamics is enabled by default (`enable_temporal=True`). HealthEngine,
PropagandaEngine, NonStateActors, OSINT, and LLM are opt-in via constructor
flags. This keeps the base model lightweight while allowing full-featured runs.

### Reproducibility
All subsystems use `model.random` (Mesa's seeded RNG) instead of stdlib
`random` to ensure deterministic runs across all features.
