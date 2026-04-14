% ============================================================================
% Hawk-Dove Game and Evolutionary Stability
% ============================================================================
%
% This module defines:
%   - Hawk-Dove payoff matrix
%   - ESS (Evolutionarily Stable Strategy) rules
%   - Mutant invasion detection
%   - Safety verification
%
% Background:
%   The Hawk-Dove game models aggression vs conciliation in resource
%   competition. An ESS is a strategy that cannot be invaded by mutant
%   strategies that do better.
%
% Usage: ?- ['hawk_dove.pl'].
% ============================================================================

:- use_module(library(lists)).
:- use_module(library(format)).

% ---------------------------------------------------------------------------
% SECTION 1: STRATEGY DEFINITIONS
% ---------------------------------------------------------------------------

% Strategies in Hawk-Dove
strategy(hawk).
strategy(dove).
strategy(bourgeois).   % Defends if owns, retreats if doesn't
strategy(free_loader). % Copies Dove but exploits when possible

% Aliases for clarity
hawk_strategy(hawk).
dove_strategy(dove).

% ---------------------------------------------------------------------------
% SECTION 2: RESOURCE VALUE AND COST
% ---------------------------------------------------------------------------

% V = Value of resource
resource_value(V) :- V = 50.

% C = Cost of fighting (injury, etc)
cost(C) :- C = 100.

% ---------------------------------------------------------------------------
% SECTION 3: HAWK-DOVE PAYOFF MATRIX
% ---------------------------------------------------------------------------

% payoff(+MyStrategy, +OppStrategy, -MyPayoff, -OppPayoff)
%
% Payoff matrix for Hawk-Dove:
%   Hawk vs Hawk: (V-C)/2 each (both injured in fight)
%   Hawk vs Dove: V to Hawk, 0 to Dove (Hawk takes all)
%   Dove vs Hawk: 0 to Dove, V to Dove (Dove retreats)
%   Dove vs Dove: V/2 each (cooperate, share)

% Hawk vs Hawk
payoff(hawk, hawk, MyPayoff, OppPayoff) :-
    resource_value(V),
    cost(C),
    MyPayoff is (V - C) / 2,
    OppPayoff is (V - C) / 2.

% Hawk vs Dove
payoff(hawk, dove, V, 0) :- resource_value(V).

% Dove vs Hawk
payoff(dove, hawk, 0, V) :- resource_value(V).

% Dove vs Dove
payoff(dove, dove, MyPayoff, OppPayoff) :-
    resource_value(V),
    MyPayoff is V / 2,
    OppPayoff is V / 2.

% ---------------------------------------------------------------------------
% SECTION 4: EVOLUTIONARILY STABLE STRATEGY (ESS)
% ---------------------------------------------------------------------------

% An Evolutionarily Stable Strategy satisfies:
%   1. E(S,S) >= E(M,S)   (does at least as well as mutant against S)
%   2. If E(S,S) = E(M,S), then E(S,M) > E(M,M)  (does better if equal)

% ess(+Strategy)
% True if Strategy is Evolutionarily Stable
ess(Strategy) :-
    strategy(Strategy),
    \+ can_be_invaded(Strategy).

% can_be_invaded(+Strategy)
% True if Strategy can be invaded by some mutant
can_be_invaded(Strategy) :-
    strategy(Mutant),
    Mutant \= Strategy,
    % Check if mutant can invade
    invasion_profitable(Strategy, Mutant).

% invasion_profitable(+Resident, +Mutant)
% True if Mutant can invade Resident
invasion_profitable(Resident, Mutant) :-
    % Condition 1: E(Mutant, Resident) > E(Resident, Resident)
    payoff(Mutant, Resident, MutantVsResident, _),
    payoff(Resident, Resident, ResidentVsResident, _),
    MutantVsResident > ResidentVsResident.
invasion_profitable(Resident, Mutant) :-
    % Condition 2: E(Mutant, Resident) = E(Resident, Resident)
    %           AND E(Resident, Mutant) > E(Mutant, Mutant)
    payoff(Mutant, Resident, MutantVsResident, _),
    payoff(Resident, Resident, ResidentVsResident, _),
    MutantVsResident =:= ResidentVsResident,
    payoff(Resident, Mutant, ResidentVsMutant, _),
    payoff(Mutant, Mutant, MutantVsMutant, _),
    ResidentVsMutant > MutantVsMutant.

% ---------------------------------------------------------------------------
% SECTION 5: SAFETY VERIFICATION
% ---------------------------------------------------------------------------

% is_safe(+Strategy)
% A behavior is "Safe" if it cannot be invaded by any mutant.
% This is the core rule the user requested.

is_safe(Strategy) :-
    strategy(Strategy),
    ess(Strategy).

% is_safe(+Strategy, -Reason)
% Returns explanation of why strategy is safe/is not safe
is_safe(Strategy, safe) :-
    is_safe(Strategy).
is_safe(Strategy, not_safe(Invader)) :-
    strategy(Strategy),
    strategy(Invader),
    Invader \= Strategy,
    invasion_profitable(Strategy, Invader).

% check_safety(+Strategy, +OpponentStrategies)
% Check if Strategy is safe against a POPULATION of opponents
check_safety(Strategy, OppStrategies) :-
    forall(
        member(Opp, OppStrategies),
        payoff(Strategy, Opp, MyPayoff, _),
        payoff(Opp, Opp, OppPayoff, _),
        MyPayoff >= OppPayoff
    ).

% ---------------------------------------------------------------------------
% SECTION 6: SIMULATION HELPERS
% ---------------------------------------------------------------------------

% simulate(+Strategies, +Rounds, -Results)
% Run simulation for multiple rounds
simulate(Strategies, Rounds, Results) :-
    simulate_round(Strategies, Rounds, [], Results).

simulate_round(_, 0, Acc, Acc) :- !.
simulate_round(Strategies, N, Acc, Results) :-
    N > 0,
    length(Strategies, PopSize),
    random_select(MyStrat, Strategies, Others),
    random_select(OppStrat, Others, _),
    payoff(MyStrat, OppStrat, MyPayoff, _),
    NewAcc = [score(MyStrat, MyPayoff)|Acc],
    N1 is N - 1,
    simulate_round(Strategies, N1, NewAcc, Results).

% calculate_fitness(+Strategy, +Population, -Fitness)
% Calculate average fitness against a population
calculate_fitness(Strategy, Population, Fitness) :-
    findall(Payoff,
            (member(Opp, Population),
             payoff(Strategy, Opp, Payoff, _)),
            Payoffs),
    ( Payoffs = []
    -> Fitness = 0
    ; sum_list(Payoffs, Sum),
      length(Payoffs, Count),
      Fitness is Sum / Count
    ).

% ---------------------------------------------------------------------------
% SECTION 7: DECISION RULES WITH CONTEXT
% ---------------------------------------------------------------------------

% decide_with_resources(+Strategy, +MyResources, +OppResources, -Action)
% Decide based on resource asymmetry

decide_with_resources(hawk, MyR, OppR, Action) :-
    ( MyR > OppR -> Action = fight
    ; MyR < OppR -> Action = retreat
    ; Action = fight      % Equal resources:hawk still fights
    ).

decide_with_resources(dove, _, _, Action) :- Action = display.

decide_with_resources(free_loader, MyR, OppR, Action) :-
    ( MyR > OppR -> Action = exploit
    ; Action = display
    ).

% ---------------------------------------------------------------------------
% SECTION 8: TEST CASES
% ---------------------------------------------------------------------------

% Test: Is Dove safe?
test_dove_safe :-
    ( is_safe(dove, Reason)
    -> format('Dove is safe: ~w~n', [Reason])
    ; format('Dove is NOT safe: ~w~n', [Reason])
    ).

% Test: Is Hawk safe?
test_hawk_safe :-
    ( is_safe(hawk, Reason)
    -> format('Hawk is safe: ~w~n', [Reason])
    ; format('Hawk is NOT safe: ~w~n', [Reason])
    ).

% Test: Basic payoffs
test_payoffs :-
    payoff(hawk, hawk, HH, _), format('Hawk vs Hawk: ~w~n', [HH]),
    payoff(hawk, dove, HD, _), format('Hawk vs Dove: ~w~n', [HD]),
    payoff(dove, dove, DD, _), format('Dove vs Dove: ~w~n', [DD]).

% Run all tests
test_all :-
    format('=== Hawk-Dove ESS Tests ===~n'),
    test_payoffs,
    format('~n'),
    test_dove_safe,
    test_hawk_safe.