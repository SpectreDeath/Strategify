"""Multi-Domain Combined-Arms Campaign Planner.

Orchestrates multi-phase campaigns synchronizing Cyber, Information/Propaganda,
Economic Sanctions, Kinetic Deployment, and Legal Treaty justification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class CampaignPhase(Enum):
    """Phases of a combined-arms campaign."""

    PHASE_1_PREPARATION = "preparation"  # Cyber disruption + Propaganda
    PHASE_2_COERCION = "coercion"  # Sanctions + Subversion
    PHASE_3_ENFORCEMENT = "enforcement"  # Kinetic deployment + Legal justification
    COMPLETED = "completed"


@dataclass
class CampaignStep:
    """Individual action within a campaign phase."""

    domain: str  # 'cyber', 'information', 'economic', 'military', 'legal'
    action_name: str
    target_id: str
    executed: bool = False


@dataclass
class CombinedArmsCampaign:
    """Multi-phase strategic combined-arms campaign."""

    campaign_id: str
    target_id: str
    current_phase: CampaignPhase = CampaignPhase.PHASE_1_PREPARATION
    phase_steps: dict[CampaignPhase, list[CampaignStep]] = field(default_factory=dict)

    def advance_phase(self) -> CampaignPhase:
        """Advance to the next campaign phase."""
        phases = list(CampaignPhase)
        idx = phases.index(self.current_phase)
        if idx < len(phases) - 1:
            self.current_phase = phases[idx + 1]
        return self.current_phase


class CampaignPlanner:
    """Planner for orchestrating combined-arms campaigns for state actors."""

    def __init__(self, agent: Any) -> None:
        self.agent = agent
        self.active_campaigns: dict[str, CombinedArmsCampaign] = {}

    def initiate_campaign(self, target_id: str) -> CombinedArmsCampaign:
        """Initiate a 3-phase combined-arms campaign against a rival state.

        Parameters
        ----------
        target_id : str
            Target region_id or agent_id.

        Returns
        -------
        CombinedArmsCampaign
            The newly created campaign object.
        """
        campaign_id = f"campaign_{self.agent.region_id}_vs_{target_id}"

        p1_steps = [
            CampaignStep(domain="cyber", action_name="cyber_disruption", target_id=target_id),
            CampaignStep(domain="information", action_name="influence_campaign", target_id=target_id),
        ]
        p2_steps = [
            CampaignStep(domain="economic", action_name="impose_sanctions", target_id=target_id),
            CampaignStep(domain="covert", action_name="subvert_stability", target_id=target_id),
        ]
        p3_steps = [
            CampaignStep(domain="military", action_name="deploy_forces", target_id=target_id),
            CampaignStep(domain="legal", action_name="treaty_justification", target_id=target_id),
        ]

        campaign = CombinedArmsCampaign(
            campaign_id=campaign_id,
            target_id=target_id,
            phase_steps={
                CampaignPhase.PHASE_1_PREPARATION: p1_steps,
                CampaignPhase.PHASE_2_COERCION: p2_steps,
                CampaignPhase.PHASE_3_ENFORCEMENT: p3_steps,
            },
        )

        self.active_campaigns[target_id] = campaign
        logger.info("Agent %s initiated combined-arms campaign against %s", self.agent.region_id, target_id)
        return campaign

    def execute_current_campaign_step(self, target_id: str, model: Any) -> dict[str, Any]:
        """Execute current active step of a campaign against a target.

        Parameters
        ----------
        target_id : str
            Target state identifier.
        model : Any
            The GeopolModel simulation environment.

        Returns
        -------
        dict
            Execution status and domain action details.
        """
        campaign = self.active_campaigns.get(target_id)
        if not campaign or campaign.current_phase == CampaignPhase.COMPLETED:
            return {"executed": False, "reason": "no_active_campaign"}

        steps = campaign.phase_steps.get(campaign.current_phase, [])
        unexecuted = [s for s in steps if not s.executed]

        if not unexecuted:
            campaign.advance_phase()
            if campaign.current_phase == CampaignPhase.COMPLETED:
                return {"executed": True, "phase_completed": True, "campaign_id": campaign.campaign_id}
            steps = campaign.phase_steps.get(campaign.current_phase, [])
            unexecuted = [s for s in steps if not s.executed]

        current_step = unexecuted[0]
        current_step.executed = True

        logger.info(
            "Campaign %s [%s]: Executed %s in domain %s",
            campaign.campaign_id,
            campaign.current_phase.value,
            current_step.action_name,
            current_step.domain,
        )

        return {
            "executed": True,
            "domain": current_step.domain,
            "action": current_step.action_name,
            "phase": campaign.current_phase.value,
            "target": target_id,
        }
