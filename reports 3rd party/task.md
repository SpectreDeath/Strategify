# Tasks: Geopol-Sim Advancement (Phases 11-15)

## Phase 10.5: Cleanup & Verification Fixes
- [x] Fix Phase 8 verification script failing due to `enable_non_state_actors` not being set to True.
- [x] Region references are correct — the default scenario uses abstract IDs (alpha/bravo/charlie/delta), not real-world names.

## Phase 11: Mesa 3.0 Migration & Architectural Optimization
- [ ] Modernize `GeopolModel` and `GeoSpace` to use Mesa 3.0 API.
- [ ] Implement spatial lookups: cached `region_id -> Agent` map and mesa-geo's spatial index.
- [ ] Unify step order for `Military`, `Environment`, and `Economy` components to ensure determinism.

## Phase 12: Integrated Command & Military AI
- [ ] Add "Deploy," "Withdraw," and "Invade" actions to `GAME_REGISTRY` or action space.
- [ ] Incorporate `MilitaryComponent.get_total_power()` into `InfluenceMap` calculations.
- [ ] Add autonomous "Mission" states (Patrol, Intercept, Occupy) for Units.

## Phase 13: Industrial Base & Production Chains
- [ ] Add `InfrastructureAgent` representing Ports, Factories, Refineries.
- [ ] Build production loops: consuming Resources and GDP to produce/repair Units.
- [ ] Implement strategic logistics interdiction (crippling supply hubs).

## Phase 14: Global Governance & International Law
- [ ] Formalize sovereignty and borders; implement sanctions for undeclared war.
- [ ] Refactor `MultilateralSummit` with voting weights and resolutions.

## Phase 15: MARL Policy Tournament (Full Scale)
- [ ] Extend RL state space to include Units, Resources, Factions, and Diplomacy.
- [ ] Stress-test Phase 11-14 systems using training policies.
