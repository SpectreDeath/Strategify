"""Multi-agent RL environment wrapper using PettingZoo.

Wraps the GeopolModel as a PettingZoo AEC environment so agents
can be trained via reinforcement learning.
"""

from __future__ import annotations

import numpy as np
from gymnasium import spaces
from pettingzoo import AECEnv


class GeopolEnv(AECEnv):
    """PettingZoo AEC environment wrapping GeopolModel.

    Each agent observes: [military, economic, net_influence, escalation_count]
    Each agent acts: 0=Deescalate, 1=Escalate
    Reward: -escalation_cost + economic_gain + alliance_bonus
    """

    metadata = {"name": "geopol_v0"}

    def __init__(self, model_factory=None, n_steps: int = 20):
        super().__init__()
        self.model_factory = model_factory
        self.n_steps = n_steps
        self.model = None
        self._step_count = 0

        # 8-dim observation: military, economic, influence,
        # escalation, stability, resource_pressure, avg_ally, avg_rival
        self.observation_spaces = {}
        self.action_spaces = {}

    def observe(self, agent_name: str):
        """Return observation for the given agent.

        Observation vector (8-dim):
        - [0] military capability
        - [1] economic capability
        - [2] net influence from influence map
        - [3] escalation count (1.0 if Escalating)
        - [4] stability
        - [5] resource pressure
        - [6] avg ally relation weight
        - [7] avg rival relation weight
        """
        if self.model is None:
            return np.zeros(8, dtype=np.float32)

        agent_obj = self._get_agent(agent_name)
        if agent_obj is None:
            return np.zeros(8, dtype=np.float32)

        military = agent_obj.capabilities.get("military", 0.5)
        economic = agent_obj.capabilities.get("economic", 0.5)
        net_inf = 0.0
        if self.model.influence_map:
            net_inf = self.model.influence_map.get_net_influence(agent_obj.region_id, agent_obj.unique_id)

        escalation_count = 1.0 if agent_obj.posture == "Escalate" else 0.0
        stability = getattr(agent_obj, "stability", 1.0)

        resource_pressure = 0.0
        if self.model and self.model.env_manager:
            resource_pressure = self.model.env_manager.get_resource_pressure(agent_obj.region_id)

        # Diplomacy relation features
        avg_ally_weight = 0.0
        avg_rival_weight = 0.0
        n_allies = 0
        n_rivals = 0
        for other in self.model.schedule.agents:
            if other.unique_id == agent_obj.unique_id:
                continue
            w = self.model.relations.get_relation(agent_obj.unique_id, other.unique_id)
            if w > 0:
                avg_ally_weight += w
                n_allies += 1
            elif w < 0:
                avg_rival_weight += w
                n_rivals += 1
        if n_allies > 0:
            avg_ally_weight /= n_allies
        if n_rivals > 0:
            avg_rival_weight /= n_rivals

        return np.array(
            [
                military,
                economic,
                net_inf,
                escalation_count,
                stability,
                resource_pressure,
                avg_ally_weight,
                avg_rival_weight,
            ],
            dtype=np.float32,
        )

    def action_space(self, agent: str):
        return spaces.Discrete(2)

    def observation_space(self, agent: str):
        return spaces.Box(low=-1.0, high=2.0, shape=(8,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        if self.model_factory:
            self.model = self.model_factory()
        else:
            from strategify.sim.model import GeopolModel

            self.model = GeopolModel()

        self._step_count = 0
        from strategify.agents.state_actor import StateActorAgent

        self.agents = [f"agent_{a.region_id}" for a in self.model.schedule.agents if isinstance(a, StateActorAgent)]
        self.possible_agents = self.agents[:]
        self.rewards = {a: 0.0 for a in self.agents}
        self.terminations = {a: False for a in self.agents}
        self.truncations = {a: False for a in self.agents}
        self.infos = {a: {} for a in self.agents}

        # Initialize spaces
        for agent in self.agents:
            self.observation_spaces[agent] = spaces.Box(low=-1.0, high=2.0, shape=(8,), dtype=np.float32)
            self.action_spaces[agent] = spaces.Discrete(2)

        self.agent_selection = self.agents[0]

    def step(self, action):
        agent = self.agent_selection
        if self.terminations.get(agent, False) or self.truncations.get(agent, False):
            if agent in self.agents:
                self.agents.remove(agent)
            if self.agents:
                self.agent_selection = self.agents[0]
            return

        agent_obj = self._get_agent(agent)

        if agent_obj and not self.terminations.get(agent, True):
            # Apply action (handled by Mesa internally, but we can override)
            if action == 1:
                agent_obj.posture = "Escalate"
            else:
                agent_obj.posture = "Deescalate"

            # Compute reward
            escalation_cost = -2.0 if agent_obj.posture == "Escalate" else 0.0
            economic_gain = agent_obj.capabilities.get("economic", 0.5)

            # Alliance bonus: positive if allies deescalate
            allies = self.model.relations.get_allies(agent_obj.unique_id)
            alliance_bonus = 0.0
            for a in self.model.schedule.agents:
                if a.unique_id in allies and a.posture == "Deescalate":
                    alliance_bonus += 0.5

            # Escalation spiral penalty: penalize if most agents are escalating
            from strategify.agents.state_actor import StateActorAgent

            state_agents = [a for a in self.model.schedule.agents if isinstance(a, StateActorAgent)]
            n_escalating = sum(1 for a in state_agents if a.posture == "Escalate")
            spiral_ratio = n_escalating / max(1, len(state_agents))
            spiral_penalty = -3.0 * spiral_ratio if spiral_ratio > 0.5 else 0.0

            # Phase 10: Expanded Rewards
            stability_penalty = (1.0 - getattr(agent_obj, "stability", 1.0)) * -5.0

            resource_penalty = 0.0
            if self.model.env_manager:
                resource_penalty = self.model.env_manager.get_resource_pressure(agent_obj.region_id) * -3.0

            self.rewards[agent] = (
                escalation_cost + economic_gain + alliance_bonus + spiral_penalty + stability_penalty + resource_penalty
            )

        # Advance agent selection
        agent_idx = self.agents.index(agent)
        next_idx = (agent_idx + 1) % len(self.agents)

        # If we've cycled through all agents, step the model
        if next_idx == 0:
            self._step_count += 1
            if self._step_count >= self.n_steps:
                for a in self.agents:
                    self.terminations[a] = True

        self.agent_selection = self.agents[next_idx]

    def _get_agent(self, agent_name: str):
        """Get the Mesa agent object by name."""
        if self.model is None:
            return None
        from strategify.agents.state_actor import StateActorAgent

        for agent in self.model.schedule.agents:
            if isinstance(agent, StateActorAgent) and f"agent_{agent.region_id}" == agent_name:
                return agent
        return None

    def render(self):
        """Print current state."""
        if self.model is None:
            return
        print(f"\n--- Step {self._step_count} ---")
        for agent in self.model.schedule.agents:
            print(f"  {agent.region_id}: {agent.posture}")

    def close(self):
        pass

    def last(self, observe: bool = True):
        """Return observation, reward, termination, truncation, info for current agent.

        Required by the PettingZoo AEC API.
        """
        agent = self.agent_selection
        obs = self.observe(agent) if observe else None
        return (
            obs,
            self.rewards.get(agent, 0.0),
            self.terminations.get(agent, False),
            self.truncations.get(agent, False),
            self.infos.get(agent, {}),
        )
