"""Information warfare: propaganda, disinformation spread, and media actors.

Models how information (true and false) spreads through influence maps,
affects agent decision-making, and can be weaponized by state actors.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Narrative:
    """A piece of information (true or false) circulating in the simulation."""

    def __init__(
        self,
        content: str,
        source_id: int,
        target_id: int | None = None,
        credibility: float = 0.5,
        is_disinformation: bool = False,
        potency: float = 1.0,
    ):
        self.content = content
        self.source_id = source_id
        self.target_id = target_id
        self.credibility = credibility  # 0-1
        self.is_disinformation = is_disinformation
        self.potency = potency  # Influence strength
        self.age: int = 0
        self.spread_count: int = 0

    def decay(self, rate: float = 0.1) -> None:
        """Decay potency over time."""
        self.potency *= 1.0 - rate
        self.age += 1

    @property
    def effective_potency(self) -> float:
        """Potency adjusted by credibility."""
        return self.potency * self.credibility


class PropagandaEngine:
    """Manages information warfare operations in the simulation.

    Tracks narratives, their spread, and their effects on agent
    decision-making and diplomacy relations.

    Parameters
    ----------
    model:
        The parent GeopolModel.
    """

    def __init__(self, model: Any) -> None:
        self.model = model
        self.narratives: list[Narrative] = []
        self.narrative_counter: int = 0
        # agent_credibility[uid] = how credible agents perceive information
        self.agent_credibility: dict[int, float] = {}
        # media_influence[uid] = media agent's reach
        self.media_influence: dict[int, float] = {}
        self._propaganda_log: list[dict] = []

    def initialize(self) -> None:
        """Set up initial credibility ratings."""
        for agent in self.model.schedule.agents:
            self.agent_credibility[agent.unique_id] = 0.5

    def broadcast(
        self,
        source_id: int,
        content: str,
        target_id: int | None = None,
        is_disinformation: bool = False,
        potency: float = 1.0,
    ) -> Narrative:
        """Broadcast a narrative into the information space.

        Parameters
        ----------
        source_id:
            Unique ID of the broadcasting agent.
        content:
            Description of the narrative.
        target_id:
            Optional target agent (for targeted propaganda).
        is_disinformation:
            Whether this is deliberately false information.
        potency:
            Initial influence strength.

        Returns
        -------
        Narrative
            The created narrative object.
        """
        credibility = 0.3 if is_disinformation else 0.8
        narrative = Narrative(
            content=content,
            source_id=source_id,
            target_id=target_id,
            credibility=credibility,
            is_disinformation=is_disinformation,
            potency=potency,
        )
        self.narratives.append(narrative)
        self.narrative_counter += 1

        self._propaganda_log.append(
            {
                "step": self.model.schedule.steps,
                "source": source_id,
                "target": target_id,
                "disinfo": is_disinformation,
                "content": content,
            }
        )

        logger.debug(
            "Narrative broadcast: source=%d, target=%s, disinfo=%s",
            source_id,
            target_id,
            is_disinformation,
        )
        return narrative

    def step(self) -> None:
        """Advance information dynamics by one step."""
        # Spread narratives to neighbors
        new_narratives = []
        for narrative in self.narratives:
            if narrative.potency < 0.05:
                continue  # Dead narrative

            # Spread to neighbors
            spread_targets = self._get_spread_targets(narrative)
            for target_uid in spread_targets:
                # Credibility check
                target_cred = self.agent_credibility.get(target_uid, 0.5)
                if self.model.random.random() < narrative.credibility * target_cred:
                    # Spread succeeds — create a weaker copy
                    new_narrative = Narrative(
                        content=narrative.content,
                        source_id=narrative.source_id,
                        target_id=target_uid,
                        credibility=narrative.credibility * 0.9,
                        is_disinformation=narrative.is_disinformation,
                        potency=narrative.potency * 0.7,
                    )
                    new_narratives.append(new_narrative)
                    narrative.spread_count += 1

                    # Disinformation degrades credibility when exposed
                    if narrative.is_disinformation:
                        self.agent_credibility[target_uid] = max(0.1, target_cred - 0.05)

            narrative.decay()

        self.narratives.extend(new_narratives)

        # Apply narrative effects to agent decisions
        self._apply_narrative_effects()

        # Prune dead narratives
        self.narratives = [n for n in self.narratives if n.potency > 0.01]

    def _get_spread_targets(self, narrative: Narrative) -> list[int]:
        """Get potential spread targets for a narrative."""
        targets = []
        source = next(
            (a for a in self.model.schedule.agents if a.unique_id == narrative.source_id),
            None,
        )
        if source is None:
            return targets

        try:
            neighbors = self.model.space.get_neighbors(source)
            for neighbor in neighbors:
                if neighbor.unique_id != narrative.source_id:
                    targets.append(neighbor.unique_id)
        except Exception:
            # Fallback: spread to random agents
            for agent in self.model.schedule.agents:
                if agent.unique_id != narrative.source_id:
                    targets.append(agent.unique_id)

        # Include specific target if set
        if narrative.target_id is not None and narrative.target_id not in targets:
            targets.append(narrative.target_id)

        return targets

    def _apply_narrative_effects(self) -> None:
        """Modify agent parameters based on received narratives."""
        for agent in self.model.schedule.agents:
            uid = agent.unique_id

            # Collect narratives targeting or reaching this agent
            relevant = [n for n in self.narratives if n.target_id == uid or n.target_id is None]

            if not relevant:
                continue

            # Disinformation effect: increase paranoia/escalation tendency
            disinfo_potency = sum(n.effective_potency for n in relevant if n.is_disinformation)
            truthful_potency = sum(n.effective_potency for n in relevant if not n.is_disinformation)

            # Net effect on agent's threat perception
            threat_shift = disinfo_potency * 0.3 - truthful_potency * 0.1
            if threat_shift > 0.1 and hasattr(agent, "capabilities"):
                # Disinformation makes agents more militaristic
                mil = agent.capabilities.get("military", 0.5)
                agent.capabilities["military"] = min(1.0, mil + threat_shift * 0.1)

    def get_narrative_landscape(self) -> dict[str, Any]:
        """Return summary of current information environment."""
        disinfo_count = sum(1 for n in self.narratives if n.is_disinformation)
        truthful_count = len(self.narratives) - disinfo_count
        total_potency = sum(n.potency for n in self.narratives)
        disinfo_potency = sum(n.potency for n in self.narratives if n.is_disinformation)

        return {
            "total_narratives": len(self.narratives),
            "disinformation_count": disinfo_count,
            "truthful_count": truthful_count,
            "total_potency": total_potency,
            "disinfo_ratio": disinfo_potency / total_potency if total_potency > 0 else 0.0,
            "total_broadcasts": self.narrative_counter,
        }

    def get_agent_exposure(self, unique_id: int) -> dict[str, float]:
        """Return information exposure summary for an agent."""
        received = [n for n in self.narratives if n.target_id == unique_id or n.target_id is None]
        disinfo = sum(n.effective_potency for n in received if n.is_disinformation)
        truth = sum(n.effective_potency for n in received if not n.is_disinformation)
        return {
            "disinfo_exposure": disinfo,
            "truthful_exposure": truth,
            "net_trust": self.agent_credibility.get(unique_id, 0.5),
        }
