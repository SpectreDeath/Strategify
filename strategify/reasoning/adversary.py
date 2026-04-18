"""Adversary personality profiles for red team simulation.

This module provides doctrine-based decision-making patterns that simulate
how different types of adversarial commanders might respond to situations.
Based on military AI research for digital enemy commanders.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AdversaryDoctrine(Enum):
    """Adversary doctrinal approaches based on military research."""

    AGGRESSIVE = "aggressive"
    CONSERVATIVE = "conservative"
    ADAPTIVE = "adaptive"
    FLAANKER = "flanker"
    DEFENSIVE = "defensive"
    IRREGULAR = "irregular"


@dataclass
class DoctrineProfile:
    """Doctrine-based behavioral profile for adversary agents."""

    doctrine: AdversaryDoctrine
    risk_tolerance: float
    prefer_offensive: bool
    flanking_bonus: float
    accept_high_casualties: bool
    use_reserves_threshold: float
    reposition_vs_commit: bool

    def get_action_bias(
        self,
        current_posture: str,
        military_power: float,
        enemy_military: float,
        terrain_advantage: float,
    ) -> dict[str, float]:
        """Calculate action bias based on doctrine.

        Returns bias weights for: escalate, deescalate, maintain, flank, reinforce
        """
        bias = {"escalate": 0.5, "deescalate": 0.5, "maintain": 0.0, "flank": 0.0, "reinforce": 0.0}

        power_ratio = military_power / max(enemy_military, 0.01)

        if self.prefer_offensive:
            if power_ratio > 1.2:
                bias["escalate"] += 0.3 * self.risk_tolerance
                if self.flanking_bonus > 0 and terrain_advantage > 0.3:
                    bias["flank"] += self.flanking_bonus * 0.4
            elif power_ratio < 0.8:
                bias["deescalate"] += 0.2

        if self.accept_high_casualties and power_ratio > 0.9:
            bias["escalate"] += 0.2

        if self.reposition_vs_commit and power_ratio < 0.7:
            bias["deescalate"] += 0.15
            bias["maintain"] += 0.1

        if self.use_reserves_threshold > 0:
            if military_power < self.use_reserves_threshold:
                bias["reinforce"] += 0.2

        total = sum(bias.values())
        if total > 0:
            for k in bias:
                bias[k] /= total

        return bias


DOCTRINE_PROFILES: dict[AdversaryDoctrine, DoctrineProfile] = {
    AdversaryDoctrine.AGGRESSIVE: DoctrineProfile(
        doctrine=AdversaryDoctrine.AGGRESSIVE,
        risk_tolerance=0.8,
        prefer_offensive=True,
        flanking_bonus=0.3,
        accept_high_casualties=True,
        use_reserves_threshold=0.4,
        reposition_vs_commit=False,
    ),
    AdversaryDoctrine.CONSERVATIVE: DoctrineProfile(
        doctrine=AdversaryDoctrine.CONSERVATIVE,
        risk_tolerance=0.3,
        prefer_offensive=False,
        flanking_bonus=0.1,
        accept_high_casualties=False,
        use_reserves_threshold=0.2,
        reposition_vs_commit=True,
    ),
    AdversaryDoctrine.ADAPTIVE: DoctrineProfile(
        doctrine=AdversaryDoctrine.ADAPTIVE,
        risk_tolerance=0.5,
        prefer_offensive=True,
        flanking_bonus=0.2,
        accept_high_casualties=False,
        use_reserves_threshold=0.3,
        reposition_vs_commit=True,
    ),
    AdversaryDoctrine.FLAANKER: DoctrineProfile(
        doctrine=AdversaryDoctrine.FLAANKER,
        risk_tolerance=0.7,
        prefer_offensive=True,
        flanking_bonus=0.6,
        accept_high_casualties=True,
        use_reserves_threshold=0.5,
        reposition_vs_commit=False,
    ),
    AdversaryDoctrine.DEFENSIVE: DoctrineProfile(
        doctrine=AdversaryDoctrine.DEFENSIVE,
        risk_tolerance=0.2,
        prefer_offensive=False,
        flanking_bonus=0.0,
        accept_high_casualties=False,
        use_reserves_threshold=0.15,
        reposition_vs_commit=True,
    ),
    AdversaryDoctrine.IRREGULAR: DoctrineProfile(
        doctrine=AdversaryDoctrine.IRREGULAR,
        risk_tolerance=0.9,
        prefer_offensive=True,
        flanking_bonus=0.4,
        accept_high_casualties=True,
        use_reserves_threshold=0.6,
        reposition_vs_commit=False,
    ),
}


def get_doctrine_profile(doctrine: AdversaryDoctrine) -> DoctrineProfile:
    """Get the doctrine profile for a given type."""
    return DOCTRINE_PROFILES.get(doctrine, DOCTRINE_PROFILES[AdversaryDoctrine.ADAPTIVE])


def apply_adversary_doctrine(
    agent: Any,
    doctrine: AdversaryDoctrine,
    military_power: float,
    enemy_power: float,
    terrain_advantage: float = 0.5,
) -> dict[str, float]:
    """Apply adversary doctrine to modify agent decision weights.

    This function can be called from agent decide() methods to incorporate
    doctrine-based decision making for red team scenarios.
    """
    profile = get_doctrine_profile(doctrine)
    return profile.get_action_bias(
        current_posture=agent.posture if hasattr(agent, "posture") else "Deescalate",
        military_power=military_power,
        enemy_military=enemy_power,
        terrain_advantage=terrain_advantage,
    )
