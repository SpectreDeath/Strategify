;; ============================================================================
;; Strategify - Clojure Strategy Synthesizer
;; ============================================================================
;;
;; This module handles:
;;   - Agent state management (immutable)
;;   - Strategy execution across multiple threads
;;   - Timeline branching for counterfactual analysis
;;   - Real-time data stream processing
;;
;; Usage: lein repl (then (require '[strategify.core :as s]))
;; ============================================================================

(ns strategify.core
  (:require [clojure.core.logic :as logic]
            [clojure.core.async :as async]
            [clojure.set :as set]
            [clojure.walk :as walk])
  (:gen-class))

;; ============================================================================
;; SECTION 1: GAME STATE (Immutable)
;; ============================================================================

(defprotocol GameState
  "Immutable game state protocol"
  (apply-move [state move])
  (get-positions [state])
  (get-player [state player-id]))

;; Record for immutable game state
(defrecord GameStateRecord
     [version  ;; Version counter for immutability tracking
     players ;; Map of player-id -> player data
     board   ;; Current board/positions
     history ;; Vector of all moves
     metadata
     economic-reserve
     stability
     un-resolutions])

(extend-type GameStateRecord
  GameState
  (apply-move [state move]
    (->GameStateRecord
      (inc (:version state))
      (:players state)
      (merge (:board state) {(:position move) (:player move)})
      (conj (:history state) move)
      (:metadata state)
      (:economic-reserve state)
      (:stability state)
      (:un-resolutions state)))

  (get-positions [state]
    (:board state))

  (get-player [state player-id]
    (get-in state [:players player-id])))

  clojure.core.protocols/IKVReduce
  (kv-reduce [state f init]
    (reduce f init (:board state))))

;; ============================================================================
;; SECTION 2: STRATEGY DEFINITIONS
;; ============================================================================

(def ^:dynamic *strategies*
  "Registry of strategy functions"
  {:hawk (fn [state player]
           (let [opp (opponent player)]
             (if (dominates? state player opp)
               :attack
               :retreat)))

   :dove (fn [state player]
           (let [resources (resource-value state player)]
             (if (> resources 25)
               :display
               :retreat)))

   :tit-for-tat (fn [state player]
                  (let [last-move (last-move state (opponent player))]
                    (case last-move
                      :attack  :attack
                      :display :display
                      :retreat :retreat)))

   :grudger (fn [state player]
              (let [history (:history state)
                    attacked? (some #{:attack} history)]
                (if attacked? :retreat :display)))

   :adaptive (fn [state player]
               (let [score (calculate-fitness state player)]
                 (if (> score 25) :attack :display)))})

(defn get-strategy [strategy-name]
  "Get strategy function by name"
  (or (strategy-name *strategies*)
      (throw (ex-info (str "Unknown strategy: " strategy-name)
                     {:available (keys *strategies*)}))))

;; ============================================================================
;; SECTION 3: TIMELINE BRANCHING (Counterfactual)
;; ============================================================================

(defn branch-timeline
  "Create a new timeline branch for counterfactual analysis"
  [state move]
  "Returns a new state without modifying the original"
  (apply-move state move))

(defn branch-timelines
  "Branch multiple possible futures"
  [state possible-moves]
  (map #(apply-move state %) possible-moves))

(defn compare-timelines
  "Compare outcomes across timeline branches"
  [timelines player scorer]
  (map #(scorer % player) timelines))

;; ============================================================================
;; SECTION 4: CORE.LOGIC (miniKanren) - Prolog-style rules
;; ============================================================================

;; Define relations for strategy decisions
(logic/defrel strategy-decides ?player ?strategy ?action)
(logic/defrel dominated ?dominator ?dominated)
(logic/defrel alliance ?player1 ?player2)

;; Rules using core.logic
(logic/defrule hawk-dominates
  ([player opp]
   (hawk? player)
   (resources> player opp)))

(logic/defrule alliance-formed
  ([p1 p2]
   (alliance p1 p2)
   (diplomatic-relation p1 p2)))

;; ============================================================================
;; SECTION 5: DATA STREAMS
;; ============================================================================

(defrecord EventStream
    [channel
     subscribers
     buffer-size])

(defn create-stream
  "Create a new event stream"
  [buffer-size]
  (->EventStream
    (async/chan buffer-size)
    #{}
    buffer-size))

(defn subscribe
  "Subscribe to stream events"
  [stream handler]
  (async/>!! (:channel stream) handler)
  stream)

(defn publish
  "Publish event to stream"
  [stream event]
  (async/>!! (:channel stream) event)
  stream)

;; ============================================================================
;; SECTION 6: AGENT MANAGEMENT
;; ============================================================================

(defrecord Agent
    [id
     strategy
     resources
     history
     beliefs
     tom-level])

(defn create-agent
  "Create new agent with strategy"
  [id strategy-type resources]
  (->Agent
    id
    strategy-type
    resources
    []
    []
    0))

(defn update-belief
  "Update agent's belief system"
  [agent belief]
  (update agent :beliefs conj belief))

(defn calculate-utility
  "Calculate expected utility for agent"
  [agent game-state]
  (let [strategy-fn (get-strategy (:strategy agent))
        action (strategy-fn game-state (:id agent))]
    (get-payoff action game-state)))

;; ============================================================================
;; SECTION 7: PAYOFF MATRIX
;; ============================================================================

(def ^:private payoff-matrix
  {:hawk {:hawk -25, :dove 50, :dove -25}
   :dove {:hawk 0, :dove 25, :dove 50}
   :bourgeois {:hawk 25, :dove 50, :dove 25}
   :free-loader {:hawk 25, :dove 50, :dove 0}})

(defn get-payoff
  "Get payoff for action pair"
  [my-action opp-action]
  (get-in payoff-matrix [my-action opp-action] 0))

;; ============================================================================
;; SECTION 8: EXPORT INTERFACE
;; ============================================================================

(defn state->map
  "Convert state to map for Python interop"
  [state]
  {:version (:version state)
   :players (into {} (map (fn [[k v]] [k (into {} v)]) (:players state)))
   :board (:board state)
   :history (:history state)
   :metadata (:metadata state)
   :economic-reserve (:economic-reserve state)
   :stability (:stability state)
   :un-resolutions (:un-resolutions state)})

(defn map->state
  "Convert map back to state"
  [m]
  (->GameStateRecord
    (:version m)
    (:players m)
    (:board m)
    (:history m)
    (:metadata m)
    (get m :economic-reserve 0)
    (get m :stability 1.0)
    (get m :un-resolutions [])))

;; ============================================================================
;; SECTION 9: COMBAT FAST-PATH (Phase 17)
;; ============================================================================

(defn resolve-combat
  "Probabilistic outcome of a 1-month campaign."
  [combat-payload]
  (let [p1-strength (get combat-payload :p1-strength 10)
        p2-strength (get combat-payload :p2-strength 10)
        terrain-mod (get combat-payload :terrain-modifier 1.0)
        p1-effective (* p1-strength terrain-mod)
        ratio (if (> p2-strength 0) (/ p1-effective p2-strength) 10.0)
        p1-damage (/ 1.0 ratio)
        p2-damage ratio]
     {:p1-remaining (max 0 (- p1-strength p1-damage))
      :p2-remaining (max 0 (- p2-strength p2-damage))
      :kinetic-intensity (+ p1-damage p2-damage)}))

;; ============================================================================
;; MAIN ENTRY POINT
;; ============================================================================

(defn -main
  "Main entry point"
  [& args]
  (println "Strategify Clojure Strategy Synthesizer")
  (println "Available strategies:" (keys *strategies*))
  (println "Start REPL: lein repl"))