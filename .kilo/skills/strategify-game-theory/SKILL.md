---
name: strategify-game-theory
description: Use when working with game-theoretic decision modules, Nash equilibria, crisis games, or coalition formation
---

# Geopol-Sim Game Theory Skill

## Core Game Theory Modules

### Crisis Games

Located in `strategify/game_theory/crisis_games.py`:

```python
from strategify.game_theory.crisis_games import (
    escalation_game,
    calculate_payoffs,
    adjust_payoffs_by_capabilities,
)

# Basic escalation game (Chicken/Brinkmanship)
payoffs = escalation_game(
    action_a=2,  # Escalation level 0-4
    action_b=1,
    payoff_matrix=None,  # Uses default
)
# Returns (payoff_a, payoff_b)

# Dynamic payoffs based on capabilities
dynamic_game = adjust_payoffs_by_capabilities(
    base_payoffs=payoffs,
    cap_a=0.8,
    cap_b=0.5,
)
```

### Normal Form Games

```python
from strategify.game_theory.normal_form import NormalFormGame

# Create game with custom payoff matrix
payoffs = [
    [(3, 3), (0, 5)],   # Cooperate / Defect
    [(5, 0), (1, 1)],   
]
game = NormalFormGame(payoffs)

# Find Nash equilibria
equilibria = game.find_nash()
# Returns list of (strategy_a, strategy_b) tuples

# Find correlated equilibria
correlated = game.find_correlated_equilibrium()
```

### Coalition Formation

```python
from strategify.game_theory.coalition import (
    find_stable_coalitions,
    compute_shapley_value,
    negotiate_alliance,
)

# Find stable coalition structures
coalitions = find_stable_coalitions(
    agents=["RUS", "UKR", "POL", "BLR"],
    alliance_graph=diplomacy.get_network(),
    threshold=0.5,
)

# Compute Shapley value for fair payoff distribution
shapley = compute_shapley_value(
    agent="POL",
    coalition={"POL", "UKR"},
    value_function=game_value,
)

# Alliance negotiation
alliance = negotiate_alliance(
    proposer="POL",
    target="UKR",
    min_strength=0.6,
)
```

## Strategy Types (Axelrod)

Agents use Axelrod library strategies:

| Strategy | Behavior |
|----------|----------|
| `"Aggressor"` | Always escalates |
| `"Pacifist"` | Always de-escalates |
| `"TitForTat"` | Copies opponent's last move |
| `"Neutral"` | Random with bias toward middle |
| `"Grudger"` | Escalates if opponent ever escalated |

```python
from axelrod import Aggressor, TitForTat, Grudger

# Use in agent config
agent_config = {
    "strategy_type": "TitForTat",  # or use class directly
}
```

## Game Payoff Matrices

### Default Escalation Game (Chicken)

|   | Coop | Defect |
|---|------|--------|
| **Coop** | (3, 3) | (-1, 4) |
| **Defect** | (4, -1) | (0, 0) |

### Custom Payoffs

```python
custom_matrix = {
    "cooperate": {"cooperate": (3, 3), "defect": (0, 5)},
    "defect": {"cooperate": (5, 0), "defect": (1, 1)},
}

game = NormalFormGame(custom_matrix)
```

## Escalation Ladder

Agents move through escalation levels:

```
0 = Peace
1 = Diplomatic tension
2 = Economic sanctions
3 = Military buildup
4 = Armed conflict
```

```python
from strategify.agents.state_actor import StateActorAgent

agent = StateActorAgent(...)
print(agent.escalation_level)  # 0-4

# Escalate or de-escalate
agent.escalate()
agent.de_escalate()
```

## Game Theory in Agent Decisions

```python
# Agent decides using game theory
def decide(self, model):
    # Get opponent actions
    opponents = self.get_neighbors()
    
    # Build game
    game = escalation_game(
        action_a=self.last_action,
        action_b=opponents[0].last_action,
    )
    
    # Find best response
    best_action = game.best_response(self.strategy_type)
    return best_action
```

## Testing Game Theory

```bash
# Run game theory tests
pytest tests/test_crisis_games.py -v
pytest tests/test_game_theory.py -v
pytest tests/test_coalition.py -v
```

### Test Example

```python
def test_nash_equilibrium():
    game = NormalFormGame([[(3, 3), (0, 5)], [(5, 0), (1, 1)]])
    equilibria = game.find_nash()
    assert len(equilibria) > 0
    # Verify equilibrium
    for eq in equilibria:
        assert eq in [(0, 0), (1, 1)]
```

## Common Issues

### Issue: No Nash equilibrium found

**Cause:** May not exist for all games
**Fix:** Try finding correlated equilibrium instead

### Issue: Payoffs too extreme

**Cause:** Capabilities difference too large
**Fix:** Adjust scaling factor in `adjust_payoffs_by_capabilities`

### Issue: Coalition unstable

**Cause:** Threshold too high
**Fix:** Lower threshold or check alliance graph weights
