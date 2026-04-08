# strategify Algorithms

## 1. Mesa 2 ABM: Scheduling and Data Collection

### RandomActivation scheduler (`mesa.time.RandomActivation`)
Each call to `GeopolModel.step()` activates agents in a **random order** (a
new random permutation each turn). This prevents systematic first-mover
advantages that come from a fixed activation order.

```python
self.schedule = RandomActivation(self)
# ... add agents ...
self.schedule.step()  # shuffles, then calls agent.step() on each
```

### DataCollector pattern
`DataCollector` is configured with `agent_reporters` so that per-agent data
is snapshotted **before** agents act each step:

```python
self.datacollector.collect(self)  # snapshot first
self.schedule.step()               # then agents act
```

Retrieve results with `model.datacollector.get_agent_vars_dataframe()`, which
returns a multi-index DataFrame `(Step, AgentID) → {posture, region_id}`.

---

## 2. Nash Equilibrium (nashpy)

### Support enumeration
`nashpy.Game.support_enumeration()` finds all Nash equilibria of a finite
2-player normal-form game by iterating over pairs of supports (subsets of
actions with positive probability) and solving the resulting linear systems.

### Tie-breaking rule
When multiple equilibria exist, `select_equilibrium()` always picks index
`[0]` from the enumerated list. This is deterministic given a fixed nashpy
version and payoff matrices.

```python
equilibria = list(game.support_enumeration())
sigma_row, sigma_col = equilibria[0]   # deterministic pick
```

**Empty-list fallback:** if enumeration returns no equilibria (degenerate
case), both players receive a uniform mixed strategy over all their actions.

### Mixed-strategy sampling
`sample_action(strategy, actions)` wraps `random.choices()`:

```python
return random.choices(actions, weights=strategy.tolist(), k=1)[0]
```

With `random.seed(42)` set in `GeopolModel.__init__`, the action sequence is
fully reproducible.

---

## 3. Adjacency: Filtering Corner-Only Contacts

The GeoJSON grid has 4 regions that share edges cleanly. Diagonal pairs
(alpha↔delta, bravo↔charlie) touch only at a single corner point.

**Algorithm in `WorldMap.neighbors()`:**

```python
if target.touches(geom):                            # step 1: touching at all?
    intersection = target.intersection(geom)
    if intersection.geom_type in (                  # step 2: shared edge?
        "LineString", "MultiLineString"
    ):
        result.append(rid)
```

- `shapely.touches()` returns `True` for both edge-sharing and corner point
  contacts.
- The `geom_type` guard guarantees that only _line_ contacts (shared borders)
  are counted as neighbours.
- A `Point` intersection (corner only) is excluded.
