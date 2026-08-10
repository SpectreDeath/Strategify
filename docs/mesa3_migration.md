# Mesa 3 Migration Plan

> Status: **Tracking** | Target: After Mesa 3 stable LTS | Priority: Low (non-urgent)

---

## Background

Strategify currently pins `mesa==2.3.4` with a hard constraint in `pyproject.toml`.
Mesa 3.0 was released as a significant breaking change — it rewrites the scheduling, agent, and model APIs.

The README explicitly warns: *"do NOT upgrade to Mesa 3"*. This document tracks the migration path.

---

## Currently Used Mesa 2 APIs

The following Mesa 2 APIs are used across `strategify/`:

| Module | Mesa API | Location |
|---|---|---|
| `sim/model.py` | `mesa.Model`, `model.schedule` | `GeopolModel.__init__` |
| `sim/model.py` | `RandomActivation` scheduler | `strategify/sim/model.py` |
| `sim/model.py` | `DataCollector` | `model.datacollector` |
| `agents/state_actor.py` | `mesa.Agent` | `StateActorAgent` base class |
| `sim/run_mesa_server.py` | `mesa.visualization.ModularServer` | Browser viz |
| `sim/run_mesa_geo_server.py` | `mesa_geo.GeoSpace`, `GeoAgent` | GeoJSON map agents |

---

## Mesa 3 API Surface Changes

| Mesa 2 | Mesa 3 Equivalent | Notes |
|---|---|---|
| `mesa.Model` | `mesa.Model` | Mostly compatible; `self.schedule` removed |
| `RandomActivation` | `mesa.AgentSet.shuffle_do("step")` | Major change — schedulers are replaced by `AgentSet` |
| `DataCollector` | `mesa.DataCollector` | Compatible with minor changes |
| `mesa.Agent` | `mesa.Agent` | `self.unique_id` renamed to `self.agent_id` in some versions |
| `ModularServer` | `SolaraViz` (Solara-based) | Complete visualization rewrite |
| `mesa_geo.GeoSpace` | `mesa_geo.GeoSpace` | Depends on mesa-geo compatibility release |

---

## Migration Checklist

- [ ] Pin test to Mesa 2.3.4 in a `mesa2` tox/CI environment as a regression baseline
- [ ] Create a `mesa3` feature branch
- [ ] Replace all `RandomActivation` usages with `AgentSet.shuffle_do("step")`
- [ ] Remove `self.schedule` references; use `self.agents` (Mesa 3 `AgentSet`) instead
- [ ] Update `unique_id` → `agent_id` if required by installed Mesa 3 version
- [ ] Port `ModularServer`-based visualization to `SolaraViz` or remove in favor of Folium
- [ ] Verify `mesa_geo` compatibility with Mesa 3 (track: [mesa-geo GitHub](https://github.com/projectmesa/mesa-geo))
- [ ] Run full test suite and fix regressions
- [ ] Update `pyproject.toml` constraint: `mesa==2.3.4` → `mesa>=3.0,<4.0`
- [ ] Update README migration note

---

## Timeline

| Milestone | Trigger |
|---|---|
| Start migration | `mesa-geo` releases a Mesa 3-compatible version |
| Complete migration | Mesa 2 reaches end-of-maintenance |
| Target branch | `feat/mesa3-migration` |

---

## References

- [Mesa 3.0 Migration Guide](https://mesa.readthedocs.io/en/stable/migration_guide.html)
- [mesa-geo GitHub](https://github.com/projectmesa/mesa-geo) — track for Mesa 3 support issue
- [Strategify sim module](file:///d:/GitHub/projects/Strategify/strategify/sim/)
