% ============================================================================
% Strategify Behavioral DNA - Prolog Logic for Agent Behaviors
% ============================================================================
% 
% This file encodes the "DNA" of agent behaviors as logical predicates.
% It provides:
%   - Behavioral traits ( Reciprocity, Forgiveness, Aggression )
%   - Theory of Mind ( nested beliefs )
%   - Evolutionary payoff calculations
%
% Usage: Load with ?- ['traits.pl']. or consult/1 in Python
% ============================================================================

:- use_module(library(lists)).
:- use_module(library(apply)).
:- use_module(library(random)).

% Suppress singleton variable and discontiguous predicate warnings
:- style_check(-singleton).
:- style_check(-discontiguous).

% ---------------------------------------------------------------------------
% SECTION 1: TRAIT DEFINITIONS
% ---------------------------------------------------------------------------

% Trait is a named behavior pattern
trait(reciprocity).
trait(forgiveness).
trait(aggression).
trait(tit_for_tat).
trait(grudger).
trait(pacifist).

% ---------------------------------------------------------------------------
% SECTION 2: ACTION OUTCOMMES
% ---------------------------------------------------------------------------

% Actions in the escalation game
action(escalate).
action(deescalate).

% Map action to numeric utility
action_utility(escalate, 1).
action_utility(deescalate, 0).

% ---------------------------------------------------------------------------
% SECTION 2B: HELPER PREDICATES
% ---------------------------------------------------------------------------

% count_cooperations(+History, -Count)
% Count number of deescalate actions in history
count_cooperations([], 0).
count_cooperations([H|T], Count) :-
    ( H = deescalate
    -> count_cooperations(T, C),
       Count is C + 1
    ; count_cooperations(T, Count)
    ).

% count_defections(+History, -Count)
% Count number of escalate actions in history
count_defections([], 0).
count_defections([H|T], Count) :-
    ( H = escalate
    -> count_defections(T, C),
       Count is C + 1
    ; count_defections(T, Count)
    ).

% has_defected(+History)
% True if history contains at least one escalation
has_defected([escalate|_]) :- !.
has_defected([_|T]) :- has_defected(T).

% ---------------------------------------------------------------------------
% SECTION 3: BEHAVIORAL RULES
% ---------------------------------------------------------------------------

% rule(+AgentProfile, +OpponentHistory, -Action)
% Core decision predicate that determines action based on traits
% Profile format: profile(Traits, Resources, TOMLevel)

% Rule: RECIPROCITY - "I do what you did to me"
rule(profile(Traits,_,_), History, Action) :-
    member(trait(reciprocity), Traits),
    last(History, LastAction),
    !,
    Action = LastAction.  % Mirror the opponent's last move

% Rule: TIT_FOR_TAT - Copy opponent's first move, then reciprocate
rule(profile(Traits,_,_), History, Action) :-
    member(trait(tit_for_tat), Traits),
    !,
    ( length(History, 0) 
    -> Action = deescalate  % Start cooperative
    ; last(History, LastAction), 
      Action = LastAction
    ).

% Rule: FORGIVENESS - "If you cheated once but cooperated twice, I trust you again"
rule(profile(Traits,_,_), History, Action) :-
    member(trait(forgiveness), Traits),
    !,
    ( length(History, L), L < 3
    -> Action = deescalate  % Forgive early
    ; count_cooperations(History, Coop),
      count_defections(History, Def),
      ( Def = 1, Coop >= 2 
      -> Action = deescalate  % Forgive one defection after 2 cooperations
      ; last(History, Action)
      )
    ).

% Rule: GRUDGER - "Once you defect, I never cooperate again"
rule(profile(Traits,_,_), History, Action) :-
    member(trait(grudger), Traits),
    !,
    ( has_defected(History)
    -> Action = escalate
    ; Action = deescalate
    ).

% Rule: AGGRESSION - "If I have more resources, I always compete"
rule(profile(Traits, Resources, _), _History, escalate) :-
    member(trait(aggression), Traits),
    Resources > 5.0,
    !.

% Rule: PACIFIST - Always deescalate
rule(profile(Traits,_,_), _History, deescalate) :-
    member(trait(pacifist), Traits),
    !.

% Default: If no trait matches, use Neutral behavior (majority vote)
rule(profile(_,_,_), History, Action) :-
    ( length(History, 0) 
    -> Action = deescalate
    ; count_cooperations(History, Coop),
      count_defections(History, Def),
      ( Coop >= Def -> Action = deescalate
      ; Action = escalate
      )
    ).

% ---------------------------------------------------------------------------
% SECTION 4: THEORY OF MIND - Nested Beliefs
% ---------------------------------------------------------------------------

% believes(+Agent, +Belief)
% Epistemology: What an agent believes about the world

% Level 0: Direct knowledge
believes(Agent,Fact) :- 
    Fact =.. [Predicate|_Args], 
    call(Predicate,_).  % Ground fact from world state

% Level 1: Agent believes another agent knows something
believes(Agent, believes(OtherAgent, Fact)) :-
    not(Agent = OtherAgent),
    % Agent reasons about OtherAgent's knowledge
    can_reason_about(Agent, OtherAgent).

% Level 2: Agent believes another agent is being deceptive
believes(Agent, deceptive(OtherAgent, Fact)) :-
    believes(Agent, believes(OtherAgent, HiddenFact)),
    HiddenFact \= Fact,
    % Agent recognizes deception
    has_theory_of_mind(Agent, 2).

% can_reason_about(+Reasoner, +Target)
% Whether Reasoner can model Target's beliefs
can_reason_about(Reasoner, Target) :-
    Reasoner \= Target,
   Reasoner^tom_level >= 1.

% has_theory_of_mind(+Agent, +Level)
% Agent has Theory of Mind at given depth
has_theory_of_mind(Agent, Level) :-
    Agent^tom_level >= Level.

% ---------------------------------------------------------------------------
% SECTION 5: EVOLUTIONARY PAYOFF MATRIX
% ---------------------------------------------------------------------------

% payoff(+MyAction, +OpponentAction, -MyPayoff, -OppPayoff)
% Standard prisoner's dilemma payoff matrix

% (Escalate, Escalate) -> Both lose, but I lose less
payoff(escalate, escalate, 0, -1).

% (Escalate, Deescalate) -> I win, you lose
payoff(escalate, deescalate, 3, -2).

% (Deescalate, Escalate) -> I lose, you win
payoff(deescalate, escalate, -2, 3).

% (Deescalate, Deescalate) -> Both cooperate
payoff(deescalate, deescalate, 1, 1).

% ---------------------------------------------------------------------------
% SECTION 6: TRAIT COMPOSITION
% ---------------------------------------------------------------------------

% combine_traits(+Traits, -CompositeRule)
% Combine multiple traits into unified behavior

combine_traits([T], T).
combine_traits([T1,T2|Rest], T1) :- 
    member(T1, [reciprocity, aggression, pacifist]),
    !,
    combine_traits(Rest, _).
combine_traits([_|Rest], Combined) :-
    combine_traits(Rest, Combined).

% ---------------------------------------------------------------------------
% SECTION 7: FITNESS CALCULATION (Evolutionary Game Theory)
% ---------------------------------------------------------------------------

% fitness(+Trait, +OpponentTraits, +Rounds, -Fitness)
% Calculate fitness of a trait against opponent's trait pool

fitness(Trait, OpponentTraits, Rounds, Fitness) :-
    simulate_rounds(Trait, OpponentTraits, Rounds, Outcomes),
    sum_payoffs(Outcomes, Fitness).

simulate_rounds(_Trait, _OpponentTraits, 0, []) :- !.
simulate_rounds(Trait, OpponentTraits, N, [Outcome|More]) :-
    N > 0,
    nth0(_, OpponentTraits, OppTrait),
    rule(trait(Trait), [], MyAction),
    rule(trait(OppTrait), [], OppAction),
    payoff(MyAction, OppAction, MyPayoff, _OppPayoff),
    Outcome = MyPayoff,
    N1 is N - 1,
    simulate_rounds(Trait, OpponentTraits, N1, More).

sum_payoffs([], 0).
sum_payoffs([P|Rest], Total) :-
    sum_payoffs(Rest, SubTotal),
    Total is P + SubTotal.

% ---------------------------------------------------------------------------
% SECTION 8: DECISION ENTRY POINT
% ---------------------------------------------------------------------------

% decide(+Profile, +History, -Decision)
% Main entry point for behavior selection

decide(Profile, History, Action) :-
    rule(Profile, History, Action).

% trace_decide(+Profile, +History, -Decision, -Trace)
% Returns decision with reasoning trace

trace_decide(Profile, History, Action, Trace) :-
    findall(RuleUsed, 
            (rule(Profile, History, Action), RuleUsed = Action), 
            Rules),
    ( Rules = [Action|_]
    -> Trace = matched(Action)
    ; Trace = default_fallback
    ).

% ============================================================================
% SECTION 9: BEHAVIORAL PROFILES (Extended)
% ============================================================================

% --- PERSONALITY TYPES ---
% Defines how an agent "thinks" - higher-order behavioral patterns
personality(cautious).
personality(opportunistic).
personality(analyst).
personality(idealist).
personality(gullible).

% --- STATE VARIABLES FOR DECISION CONTEXT ---
% These are typically set dynamically by the Python side
:- dynamic risk_level/1.
:- dynamic potential_gain/1.
:- dynamic source_verified/1.
:- dynamic is_fact/1.
:- dynamic is_propaganda/1.

% Default state assertions
risk_level(unknown).
potential_gain(unknown).

% --- PERSONALITY-BASED DECISION RULES ---
% Cautious agents only escalate if risk is low
decide(Agent, Profile, escalate) :-
    personality(Agent, cautious),
    risk_level(low).

% Cautious agents deescalate by default unless proven safe
decide(Agent, Profile, deescalate) :-
    personality(Agent, cautious),
    \+ risk_level(low).

% Opportunistic agents escalate if there is any potential gain
decide(Agent, Profile, escalate) :-
    personality(Agent, opportunistic),
    potential_gain(high).

% Opportunistic agents also escalate on medium gain
decide(Agent, Profile, escalate) :-
    personality(Agent, opportunistic),
    potential_gain(medium).

% Opportunistic agents deescalate only when no gain possible
decide(Agent, Profile, deescalate) :-
    personality(Agent, opportunistic),
    potential_gain(none).

% Analyst agents calculate expected value before committing
decide(Agent, Profile, escalate) :-
    personality(Agent, analyst),
    expected_value(Profile, Value),
    Value > 0.

% Idealist agents prioritize mutual cooperation
decide(Agent, Profile, deescalate) :-
    personality(Agent, idealist).

% --- EXPECTED VALUE CALCULATION ---
% expected_value(+Profile, -Value)
% Calculates expected value of escalation action
expected_value(Profile, Value) :-
    potential_gain(Gain),
    risk_penalty(Risk, Penalty),
    Value is Gain - Penalty.

risk_penalty(low, 1).
risk_penalty(medium, 2).
risk_penalty(high, 4).

% ============================================================================
% SECTION 10: EPISTEMOLOGY (Knowledge vs Belief)
% ============================================================================

% knows(+Agent, +Fact)
% An agent 'knows' a fact only if it's verified by the system.
% This is stronger than believes/2 - requires verification.
knows(Agent, Fact) :-
    is_fact(Fact),
    source_verified(Fact).

% knows(+Agent, +Fact)
% An agent knows a compound fact if all components are verified
knows(Agent, and(Fact1, Fact2)) :-
    knows(Agent, Fact1),
    knows(Agent, Fact2).

% knows(+Agent, +Fact)
% An agent knows a negated fact if the opposite is falsified
knows(Agent, not(Fact)) :-
    \+ is_fact(Fact).

% believes(+Agent, +Fact)
% Weaker than knows/2 - doesn't require verification
% Already defined in Section 4, extended here

%believes(Agent, Fact) :-
%    is_fact(Fact).  % Fallback: if it's a fact, we believe it

% --- BELIEF UPDATE ---
% update_belief(+Agent, +Fact, +Source)
% Used to track where beliefs came from (for opacity)
update_belief(Agent, Fact, osint) :-
    is_fact(Fact).
update_belief(Agent, Fact, intelligence) :-
    source_verified(Fact).
update_belief(Agent, Fact, observation) :-
    is_fact(Fact).

% --- DECISION WITH EPISTEMOLOGY ---
% decide_knowledgeable(+Agent, +Profile, -Action)
% Only decide based on what agent knows (not just believes)
decide_knowledgeable(Agent, Profile, Action) :-
    knows(Agent, situation_safe),
    decide(Agent, Profile, Action).
decide_knowledgeable(Agent, Profile, deescalate) :-
    \+ knows(Agent, situation_safe),
    % Default to caution when uncertain
    decide(Agent, Profile, deescalate).

% --- DISINFORMATION MECHANICS (Phase 16) ---
% A gullible agent believes propaganda
believes(Agent, Fact) :-
    is_propaganda(Fact),
    personality(Agent, gullible).

% Analyst only believes propaganda if cleverly verified (mock)
believes(Agent, Fact) :-
    is_propaganda(Fact),
    personality(Agent, analyst),
    source_verified(Fact).