"""Legal Agent for dispute resolution simulation in geopolitical scenarios.

Provides agent-based modeling of legal disputes, international tribunals,
and conflict arbitration based on research into legal AI agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LegalDomain(Enum):
    """Legal domains for dispute resolution."""

    INTERNATIONAL = "international"
    TRADE = "trade"
    TERRITORIAL = "territorial"
    HUMANITARIAN = "humanitarian"
    ECONOMIC = "economic"
    MARITIME = "maritime"


class DisputeStatus(Enum):
    """Status of legal dispute."""

    FILING = "filing"
    MEDIATION = "mediation"
    HEARING = "hearing"
    RULING = "ruling"
    ENFORCEMENT = "enforcement"
    RESOLVED = "resolved"
    APPEAL = "appeal"


@dataclass
class LegalClaim:
    """A legal claim in a dispute."""

    claimant: str
    defendant: str
    legal_basis: str
    factual_basis: str
    relief_requested: str
    precedent_citations: list[str] = field(default_factory=list)


@dataclass
class LegalRuling:
    """A legal ruling from a tribunal."""

    ruling_id: str
    dispute_id: str
    tribunal: str
    ruling_body: str
    decision: str
    legal_reasoning: str
    precedent_relied_on: list[str]
    remedies: list[str]
    compliance_required: list[str]


class LegalAgent:
    """Agent representing a legal entity in dispute resolution.

    Can represent states, organizations, or individuals in legal proceedings.
    Based on MASER multi-agent legal simulation framework research.
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        legal_domain: LegalDomain,
        is_state_actor: bool = True,
    ) -> None:
        self.agent_id = agent_id
        self.name = name
        self.legal_domain = legal_domain
        self.is_state_actor = is_state_actor

        self.claims_filed: list[LegalClaim] = []
        self.defendants: list[str] = []
        self.rulings_received: list[LegalRuling] = []
        self.compliance_history: dict[str, bool] = {}

        self.legal_strategy: str = "cooperative"
        self.risk_tolerance: float = 0.5
        self.preference_for_appeal: bool = False

    def file_claim(
        self,
        defendant: str,
        legal_basis: str,
        factual_basis: str,
        relief_requested: str,
    ) -> LegalClaim:
        """File a legal claim against another party."""
        claim = LegalClaim(
            claimant=self.agent_id,
            defendant=defendant,
            legal_basis=legal_basis,
            factual_basis=factual_basis,
            relief_requested=relief_requested,
        )
        self.claims_filed.append(claim)
        self.defendants.append(defendant)
        return claim

    def respond_to_claim(
        self,
        claim: LegalClaim,
        defense: str,
        counterclaim: LegalClaim | None = None,
    ) -> dict[str, Any]:
        """Respond to a legal claim with defense and optional counterclaim."""
        response = {
            "respondent": self.agent_id,
            "claim_id": f"{claim.claimant}_{claim.defendant}",
            "defense": defense,
            "counterclaim": counterclaim,
            "legal_strategy": self.legal_strategy,
        }

        if counterclaim:
            self.claims_filed.append(counterclaim)

        return response

    def evaluate_ruling(self, ruling: LegalRuling) -> dict[str, Any]:
        """Evaluate a ruling and decide on compliance/appeal."""
        ruling_received = ruling
        self.rulings_received.append(ruling)

        if not self.preference_for_appeal and ruling.decision in ["favorable", "partial"]:
            compliance = True
        elif ruling.decision == "unfavorable":
            compliance = self.risk_tolerance < 0.6
        else:
            compliance = True

        self.compliance_history[ruling.ruling_id] = compliance

        return {
            "ruling_id": ruling.ruling_id,
            "compliance": compliance,
            "appeal_filed": not compliance and self.preference_for_appeal,
            "reasoning": self._get_ruling_reasoning(ruling, compliance),
        }

    def _get_ruling_reasoning(self, ruling: LegalRuling, compliance: bool) -> str:
        """Generate reasoning for ruling response."""
        if compliance:
            return f"Complied with {ruling.tribunal} ruling based on legal obligation"
        return f"Appealing {ruling.tribunal} ruling due to legal basis disagreement"

    def get_legal_position(self, dispute_topic: str) -> dict[str, Any]:
        """Get current legal position on a topic."""
        relevant_claims = [c for c in self.claims_filed if dispute_topic in c.factual_basis]
        relevant_rulings = [r for r in self.rulings_received if dispute_topic in r.legal_reasoning]

        return {
            "agent_id": self.agent_id,
            "domain": self.legal_domain.value,
            "claims_filed": len(relevant_claims),
            "rulings_received": len(relevant_rulings),
            "compliance_rate": self._calculate_compliance_rate(),
            "legal_strategy": self.legal_strategy,
        }

    def _calculate_compliance_rate(self) -> float:
        """Calculate compliance rate with rulings."""
        if not self.compliance_history:
            return 1.0
        return sum(self.compliance_history.values()) / len(self.compliance_history)

    def set_strategy(self, strategy: str, risk_tolerance: float) -> None:
        """Set legal strategy and risk tolerance."""
        self.legal_strategy = strategy
        self.risk_tolerance = risk_tolerance


class DisputeResolutionSystem:
    """System for managing legal disputes and arbitration."""

    def __init__(self, tribunal_name: str = "International Tribunal") -> None:
        self.tribunal_name = tribunal_name
        self.disputes: dict[str, dict[str, Any]] = {}
        self.legal_agents: dict[str, LegalAgent] = {}
        self.rulings: list[LegalRuling] = []
        self.dispute_counter = 0

    def register_agent(self, agent: LegalAgent) -> None:
        """Register a legal agent in the system."""
        self.legal_agents[agent.agent_id] = agent

    def initiate_dispute(
        self,
        claimant_id: str,
        defendant_id: str,
        domain: LegalDomain,
        claim_details: dict[str, str],
    ) -> str:
        """Initiate a new legal dispute."""
        self.dispute_counter += 1
        dispute_id = f"DISP_{self.dispute_counter:04d}"

        self.disputes[dispute_id] = {
            "dispute_id": dispute_id,
            "claimant": claimant_id,
            "defendant": defendant_id,
            "domain": domain.value,
            "status": DisputeStatus.FILING.value,
            "claims": [],
            "evidence": [],
            "rulings": [],
        }

        if claimant_id in self.legal_agents:
            claim = self.legal_agents[claimant_id].file_claim(
                defendant=defendant_id,
                legal_basis=claim_details.get("legal_basis", ""),
                factual_basis=claim_details.get("factual_basis", ""),
                relief_requested=claim_details.get("relief_requested", ""),
            )
            self.disputes[dispute_id]["claims"].append(claim)

        return dispute_id

    def advance_dispute(self, dispute_id: str) -> bool:
        """Advance dispute to next stage."""
        if dispute_id not in self.disputes:
            return False

        current_status = self.disputes[dispute_id]["status"]
        status_order = [
            DisputeStatus.FILING,
            DisputeStatus.MEDIATION,
            DisputeStatus.HEARING,
            DisputeStatus.RULING,
            DisputeStatus.ENFORCEMENT,
            DisputeStatus.RESOLVED,
        ]

        try:
            current_idx = status_order.index(DisputeStatus(current_status))
            if current_idx < len(status_order) - 1:
                self.disputes[dispute_id]["status"] = status_order[current_idx + 1].value
                return True
        except ValueError:
            pass

        return False

    def issue_ruling(
        self,
        dispute_id: str,
        decision: str,
        reasoning: str,
        remedies: list[str],
        precedent: list[str],
    ) -> LegalRuling:
        """Issue a ruling in a dispute."""
        if dispute_id not in self.disputes:
            raise ValueError(f"Dispute {dispute_id} not found")

        dispute = self.disputes[dispute_id]
        self.dispute_counter += 1

        ruling = LegalRuling(
            ruling_id=f"RUL_{self.dispute_counter:04d}",
            dispute_id=dispute_id,
            tribunal=self.tribunal_name,
            ruling_body=self.tribunal_name,
            decision=decision,
            legal_reasoning=reasoning,
            precedent_relied_on=precedent,
            remedies=remedies,
            compliance_required=[dispute["defendant"], dispute["claimant"]],
        )

        self.rulings.append(ruling)
        dispute["rulings"].append(ruling)
        dispute["status"] = DisputeStatus.RULING.value

        return ruling

    def get_dispute_status(self, dispute_id: str) -> dict[str, Any]:
        """Get current status of a dispute."""
        if dispute_id not in self.disputes:
            return {"error": "Dispute not found"}

        dispute = self.disputes[dispute_id]
        return {
            "dispute_id": dispute_id,
            "status": dispute["status"],
            "domain": dispute["domain"],
            "parties": {"claimant": dispute["claimant"], "defendant": dispute["defendant"]},
            "claim_count": len(dispute["claims"]),
            "ruling_count": len(dispute["rulings"]),
        }


def create_legal_agent(
    agent_id: str,
    name: str,
    domain: LegalDomain,
    is_state: bool = True,
) -> LegalAgent:
    """Factory function to create a legal agent."""
    return LegalAgent(agent_id, name, domain, is_state)
