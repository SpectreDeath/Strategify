# Strategify Super Sprint Plan: Completed "Cognitive Core" & Next Steps

*Status: "Cognitive Core" Sprint (Phases 15-18) Completed.*

---

## ✅ COMPLETED: The "Cognitive Core" Sprint

### **Phase 15: LLM Orchestration & Symbolic Grounding**
- [x] **Epistemic Prompt Injection:** `strategify/reasoning/llm.py` now queries `StrategicBridge` for actual beliefs and knowledge before hitting the LLM.
- [x] **Clojure Counterfactual Forecaster:** Integrated `ClojureBridge.branch_timelines` to provide the LLM with simulated Lisp futures.
- [x] **The `CognitiveActorAgent`:** Created `CognitiveActorAgent` substituting Nash matrix arrays with highly contextual LLM calls.

### **Phase 16: Prolog Deep Epistemology & Deception**
- [x] **Disinformation Mechanics:** Added `believes/2` overrides in `traits.pl` for propaganda spread based on `gullible` vs `analyst` traits.
- [x] **Propagating Facts:** Integrated `StrategicBridge` inside `GeopolModel.step()` to log physical state changes (combat, posture) as Prolog beliefs (`action(region, posture)`).
- [x] **Information Warfare:** Added `disinformation_game` to `crisis_games.py` (propaganda vs censorship).

### **Phase 17: Clojure Monte Carlo Tree Search (MCTS)**
- [x] **Expand Clojure State Map:** Expanded `GameStateRecord` to include `:economic-reserve`, `:stability`, and `:un-resolutions`.
- [x] **Fast Path Combat Resolution:** Delegated kinetic combat calculations in `conflict.py` to `(resolve-combat state)` in Clojure.

### **Phase 18: The Grand Strategy Tournament**
- [x] **Tournament Runner:** Established `tournament_runner.py` comparing traditional Nash agents against `CognitiveActorAgent` across metrics like global tension and escalations.

---

## 🚀 NEW SPRINT: UI & Interactive MLOps Integration

**Objective:** Move the simulation out of headless mode by properly exposing the newly created Cognitive architectures to the React frontend. We need to allow humans to see the "thoughts" of the agents, interact with them, and expand our economic fidelity.

### **Phase 19: Full-Stack API Integration**
**Goal:** Tie the Mesa simulation backend to the React/Vite frontend.
- **Task 1: FastAPI Controller Layer:** Add a `fastapi` app running alongside or wrapping the Mesa model. Expose endpoints for `POST /api/simulation/start`, `GET /api/simulation/state`, and `POST /api/simulation/step`.
- **Task 2: Frontend Data Hookup:** Populate `frontend/src/api/` and `frontend/src/hooks/` with Axios fetchers. Replace the hardcoded `sampleRiskData` in `Dashboard.jsx` and `Simulation.jsx` with live simulation data.

### **Phase 20: Explainable AI (XAI) UI layer**
**Goal:** Visualize the "brain" of the `CognitiveActorAgent`.
- **Task 1: Epistemic Graph View:** Create a PyVis/React component showing a node-graph of what an agent "knows" vs "believes" dynamically queried from Prolog.
- **Task 2: Lisp Branching UI:** On the Simulation view, add a "Timeline Prediction" tree showing the Clojure MCTS branch projections that the LLM is currently evaluating.
- **Task 3: Live LLM Logs:** Add an inspector panel for agents revealing the raw prompt and response (XAI transparency for the user).

### **Phase 21: RL Sandbox & Human-in-the-Loop**
**Goal:** Allow users to step into the role of a faction and play against the Cognitive AI or RL Agents.
- **Task 1: Interactive Play Mode:** Modify the `PettingZoo` wrapper so that one agent can be `"human"`. 
- **Task 2: Frontend Command Terminal:** Add a UI module allowing the user to submit actions (`Escalate`, `SpreadFakeNews`, etc.) for their mapped nation during a live turn.

### **Phase 22: Deep Supply Chain Economics**
**Goal:** Increase the fidelity of the `"economic"` variable to multi-commodity supply chains.
- **Task 1: Commodity Ledger:** Update the economic models to track Oil, Semiconductors, and Food across the network graph.
- **Task 2: Vulnerability Analysis:** Implement tools to detect critical supply chain choke points using NetworkX betweenness centrality and feed these into the Prolog epistemology `potential_gain/risk_level` facts.
