# Research Library Integration Implementation Plan

> **For agentic workers:** REQUIRED: Use `subagent-driven-development` (if subagents available) or `executing-plans` to implement this plan. Steps use checkbox (`- [x]`) syntax for tracking via your Task Tracker.

**Goal:** Integrate three libraries from gathered research (Axelrod, PySAL/esda, VADER Sentiment) to enhance agent decision-making, spatial reasoning, and OSINT capabilities.

**Architecture:** Three independent subsystems — each produces working software on its own. (1) Axelrod wraps iterated game strategies into a `DiplomacyStrategy` adapter that replaces the hardcoded personality bias in agent decisions. (2) PySAL/esda computes spatial autocorrelation (Moran's I) to measure instability clustering, replacing crude BFS distance decay with rigorous statistical spillover detection. (3) VADER sentiment analysis powers the OSINT stub to score geopolitical tension from text.

**Tech Stack:** axelrod, libpysal, esda, vaderSentiment, existing nashpy/mesa stack

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `requirements.txt` | Modify | Add new deps |
| `pyproject.toml` | Modify | Add new deps |
| `strategify/reasoning/strategies.py` | Create | Axelrod strategy adapter |
| `strategify/reasoning/influence.py` | Modify | Add PySAL spatial autocorrelation |
| `strategify/osint/features.py` | Modify | Wire VADER sentiment pipeline |
| `tests/test_strategies.py` | Create | Unit tests for Axelrod adapter |
| `tests/test_spatial_autocorrelation.py` | Create | Tests for PySAL integration |
| `tests/test_osint.py` | Create | Tests for VADER pipeline |

---

## Task 1: Add dependencies

- [x] Step 1: Add `axelrod`, `libpysal`, `esda`, `vaderSentiment` to `pyproject.toml` and `requirements.txt`
- [x] Step 2: Verify imports work

## Task 2: Axelrod strategy adapter (`reasoning/strategies.py`)

- [x] Step 1: Create `strategify/reasoning/strategies.py`
- [x] Step 2: Write tests in `tests/test_strategies.py`
- [x] Step 3: Run tests, verify
- [x] Step 4: Integrate into `state_actor.py` decide()

## Task 3: PySAL spatial autocorrelation (`reasoning/influence.py`)

- [x] Step 1: Add spatial autocorrelation method to InfluenceMap
- [x] Step 2: Write tests in `tests/test_spatial_autocorrelation.py`
- [x] Step 3: Run tests, verify

## Task 4: VADER OSINT pipeline (`osint/features.py`)

- [x] Step 1: Implement sentiment analysis in osint/features.py
- [x] Step 2: Write tests in `tests/test_osint.py`
- [x] Step 3: Run tests, verify

## Task 5: Full test suite verification

- [x] Step 1: Run `pytest tests/ -v` — all tests pass

---
