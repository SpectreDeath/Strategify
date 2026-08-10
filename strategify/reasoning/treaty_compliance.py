"""Treaty Compliance Checker for international law validation.

Validates diplomatic actions against international law including UN Charter,
Vienna Convention, custom treaties, and provides compliance verification for
geopolitical simulation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TreatyType(Enum):
    """Types of international treaties."""

    CHARTER = "charter"  # UN Charter, NATO Charter
    CONVENTION = "convention"  # Vienna Convention, Geneva Conventions
    BILATERAL = "bilateral"  # Trade agreements, defense pacts
    MULTILATERAL = "multilateral"  # Arms control, climate
    CUSTOM = "custom"  # Custom simulation treaties


class ViolationSeverity(Enum):
    """Severity levels for treaty violations."""

    CRITICAL = "critical"  # War crimes, crimes against humanity
    SERIOUS = "serious"  # Use of force violations, aggression
    MODERATE = "moderate"  # Procedural violations
    MINOR = "minor"  # Technical breaches


@dataclass
class TreatyArticle:
    """Article or provision within a treaty."""

    article_id: str
    title: str
    content: str
    prohibited_actions: list[str] = field(default_factory=list)
    permitted_actions: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)


@dataclass
class Treaty:
    """International treaty with articles."""

    treaty_id: str
    name: str
    treaty_type: TreatyType
    parties: list[str]
    articles: dict[str, TreatyArticle] = field(default_factory=dict)
    effective_date: str | None = None
    jurisdiction: str = "International Court of Justice"


@dataclass
class ComplianceFinding:
    """Finding from treaty compliance check."""

    treaty_id: str
    article_id: str | None
    action: str
    status: str  # "compliant", "violation", "ambiguous"
    reasoning: str
    severity: ViolationSeverity | None = None
    precedent_citations: list[str] = field(default_factory=list)


@dataclass
class ComplianceReport:
    """Complete compliance report for an action."""

    action: str
    actor: str
    timestamp: str
    findings: list[ComplianceFinding]
    overall_status: str  # "compliant", "violation", "partial", "ambiguous"
    recommendations: list[str] = field(default_factory=list)
    escalation_risk: float = 0.0


class TreatyRegistry:
    """Registry of international treaties for compliance checking."""

    def __init__(self) -> None:
        self.treaties: dict[str, Treaty] = {}
        self._load_default_treaties()

    def _load_default_treaties(self) -> None:
        """Load default international law treaties."""
        self.treaties["un_charter"] = self._create_un_charter()
        self.treaties["vienna_convention"] = self._create_vienna_convention()
        self.treaties["geneva_conventions"] = self._create_geneva_conventions()

    def _create_un_charter(self) -> Treaty:
        """Create UN Charter treaty."""
        charter = Treaty(
            treaty_id="un_charter",
            name="Charter of the United Nations",
            treaty_type=TreatyType.CHARTER,
            parties=["UN Members"],
            effective_date="1945-10-24",
            jurisdiction="International Court of Justice",
        )

        charter.articles["article_2_4"] = TreatyArticle(
            article_id="article_2_4",
            title="Prohibition of Force",
            content="All members shall refrain in their international relations from the threat or use of force against the territorial integrity or political independence of any state.",
            prohibited_actions=[
                "military_invasion",
                "armed_attack",
                "annexation",
                "threat_of_force",
            ],
        )

        charter.articles["article_2_7"] = TreatyArticle(
            article_id="article_2_7",
            title="Non-Intervention",
            content="Nothing shall authorize the United Nations to intervene in matters essentially within domestic jurisdiction.",
            prohibited_actions=[
                "intervention_internal_affairs",
                "regime_change",
                "election_interference",
            ],
        )

        charter.articles["article_33"] = TreatyArticle(
            article_id="article_33",
            title="Pacific Settlement",
            content="The parties to any dispute shall seek solution by negotiation, inquiry, mediation, conciliation, judicial settlement, resort to regional agencies, or other peaceful means.",
            requires=["negotiation", "mediation_attempt"],
        )

        return charter

    def _create_vienna_convention(self) -> Treaty:
        """Create Vienna Convention on Treaty Law."""
        vc = Treaty(
            treaty_id="vienna_convention",
            name="Vienna Convention on the Law of Treaties",
            treaty_type=TreatyType.CONVENTION,
            parties=["Treaty Parties"],
            effective_date="1980-01-27",
            jurisdiction="International Court of Justice",
        )

        vc.articles["article_26"] = TreatyArticle(
            article_id="article_26",
            title="Pacta Sunt Servanda",
            content="Every treaty in force is binding upon the parties to it and must be performed by them in good faith.",
            prohibited_actions=[
                "treaty_violation",
                "material_breach",
                "unilateral_withdrawal_violation",
            ],
        )

        vc.articles["article_31"] = TreatyArticle(
            article_id="article_31",
            title="Interpretation",
            content="A treaty shall be interpreted in good faith in accordance with the ordinary meaning given to the terms in their context and in light of its object and purpose.",
            requires=["good_faith_interpretation"],
        )

        vc.articles["article_62"] = TreatyArticle(
            article_id="article_62",
            title="Fundamental Change of Circumstances",
            content="A fundamental change of circumstances may not be invoked as terminating a treaty unless the existence of those circumstances constituted an essential basis of the consent to be bound by the treaty.",
            prohibited_actions=["unilateral_termination_without_basis"],
        )

        return vc

    def _create_geneva_conventions(self) -> Treaty:
        """Create Geneva Conventions treaty."""
        gc = Treaty(
            treaty_id="geneva_conventions",
            name="Geneva Conventions",
            treaty_type=TreatyType.CONVENTION,
            parties=["All States"],
            effective_date="1950-08-21",
            jurisdiction="International Criminal Court",
        )

        gc.articles["common_article_3"] = TreatyArticle(
            article_id="common_article_3",
            title="Humane Treatment",
            content="In the case of armed conflict not of an international character, persons taking no active part in hostilities shall be treated humanely.",
            prohibited_actions=[
                "torture",
                "cruel_treatment",
                "hostage_taking",
                "summary_execution",
                "indiscriminate_attacks",
            ],
        )

        gc.articles["article_48"] = TreatyArticle(
            article_id="article_48",
            title="Distinction",
            content="The parties to the conflict shall at all times distinguish between the civilian population and combatants.",
            prohibited_actions=[
                "indiscriminate_attacks",
                "targeting_civilians",
                "using_civilians_as_shields",
            ],
        )

        return gc

    def register_treaty(self, treaty: Treaty) -> None:
        """Register a custom treaty."""
        self.treaties[treaty.treaty_id] = treaty

    def get_treaty(self, treaty_id: str) -> Treaty | None:
        """Get treaty by ID."""
        return self.treaties.get(treaty_id)

    def get_treaties_for_parties(self, parties: list[str]) -> list[Treaty]:
        """Get all treaties that apply to given parties."""
        applicable = []
        for treaty in self.treaties.values():
            is_universal = False
            for party in treaty.parties:
                if "All" in party or party in ["UN Members", "Treaty Parties", "All States"]:
                    is_universal = True
                    break
            if is_universal or any(party in treaty.parties for party in parties):
                applicable.append(treaty)
        return applicable


class TreatyComplianceChecker:
    """Checker for treaty compliance of diplomatic/military actions."""

    def __init__(self, registry: TreatyRegistry | None = None) -> None:
        self.registry = registry or TreatyRegistry()
        self.compliance_history: list[ComplianceReport] = []

    def check_action(
        self,
        actor: str,
        action: str,
        target: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ComplianceReport:
        """Check if an action complies with international law."""
        findings = []

        action_lower = action.lower()
        context = context or {}

        for treaty in self.registry.get_treaties_for_parties([actor]):
            for article in treaty.articles.values():
                finding = self._check_article_compliance(treaty, article, actor, action_lower, target, context)
                if finding:
                    findings.append(finding)

        overall_status = self._determine_overall_status(findings)
        escalation_risk = self._calculate_escalation_risk(findings)

        report = ComplianceReport(
            action=action,
            actor=actor,
            timestamp=context.get("timestamp", "current"),
            findings=findings,
            overall_status=overall_status,
            recommendations=self._generate_recommendations(findings),
            escalation_risk=escalation_risk,
        )

        self.compliance_history.append(report)
        return report

    def _check_article_compliance(
        self,
        treaty: Treaty,
        article: TreatyArticle,
        actor: str,
        action: str,
        target: str | None,
        context: dict[str, Any],
    ) -> ComplianceFinding | None:
        """Check compliance against a specific article."""
        violation_detected = False
        severity = None

        for prohibited in article.prohibited_actions:
            if prohibited.replace("_", " ") in action or prohibited in action:
                violation_detected = True
                severity = self._determine_severity(prohibited, article)
                break

        if not violation_detected:
            return None

        return ComplianceFinding(
            treaty_id=treaty.treaty_id,
            article_id=article.article_id,
            action=action,
            status="violation",
            severity=severity,
            reasoning=f"Action violates {treaty.name} - {article.title}",
            precedent_citations=self._get_precedent_citations(article.article_id),
        )

    def _determine_severity(self, prohibited_action: str, article: TreatyArticle) -> ViolationSeverity:
        """Determine violation severity."""
        critical_actions = ["war_crime", "crime_against_humanity", "genocide", "annexation"]
        serious_actions = ["invasion", "armed_attack", "aggression", "torture"]
        moderate_actions = ["intervention", "interference", "violation"]

        if any(c in prohibited_action for c in critical_actions):
            return ViolationSeverity.CRITICAL
        elif any(s in prohibited_action for s in serious_actions):
            return ViolationSeverity.SERIOUS
        elif any(m in prohibited_action for m in moderate_actions):
            return ViolationSeverity.MODERATE
        return ViolationSeverity.MINOR

    def _determine_overall_status(self, findings: list[ComplianceFinding]) -> str:
        """Determine overall compliance status."""
        if not findings:
            return "compliant"

        critical = any(f.severity == ViolationSeverity.CRITICAL for f in findings)
        serious = any(f.severity == ViolationSeverity.SERIOUS for f in findings)

        if critical or serious:
            return "violation"
        elif findings:
            return "partial"
        return "compliant"

    def _calculate_escalation_risk(self, findings: list[ComplianceFinding]) -> float:
        """Calculate escalation risk based on findings."""
        if not findings:
            return 0.0

        severity_weights = {
            ViolationSeverity.CRITICAL: 1.0,
            ViolationSeverity.SERIOUS: 0.7,
            ViolationSeverity.MODERATE: 0.4,
            ViolationSeverity.MINOR: 0.1,
        }

        total = sum(severity_weights.get(f.severity, 0.1) for f in findings if f.severity)
        return min(total / len(findings), 1.0)

    def _get_precedent_citations(self, article_id: str) -> list[str]:
        """Get precedent citations for an article."""
        precedents = {
            "article_2_4": [
                "Nicaragua v. United States (1986)",
                "Military and Paramilitary Activities Case",
            ],
            "common_article_3": [
                "Tadic Case (1995)",
                "Prosecutor v. Delalic",
            ],
            "article_48": [
                "ICTY Prosecutor v. Galic",
                "Protocol I Article 48",
            ],
        }
        return precedents.get(article_id, [])

    def _generate_recommendations(self, findings: list[ComplianceFinding]) -> list[str]:
        """Generate recommendations based on findings."""
        if not findings:
            return ["Action appears compliant with international law"]

        recommendations = []
        if any(f.severity == ViolationSeverity.CRITICAL for f in findings):
            recommendations.append("Seek immediate legal review before proceeding")
            recommendations.append("Consider UN Security Council consultation")
        if any(f.severity == ViolationSeverity.SERIOUS for f in findings):
            recommendations.append("Pursue diplomatic channels before action")
            recommendations.append("Document legal justification for action")

        return recommendations

    def check_treaty_breach(
        self,
        actor: str,
        treaty_id: str,
        breach_type: str,
    ) -> ComplianceReport:
        """Check specific treaty breach scenario."""
        treaty = self.registry.get_treaty(treaty_id)
        if not treaty:
            return ComplianceReport(
                action=breach_type,
                actor=actor,
                timestamp="",
                findings=[],
                overall_status="ambiguous",
                recommendations=["Treaty not found in registry"],
            )

        action = f"treaty_breach_{breach_type}"
        return self.check_action(actor, action, context={"treaty": treaty_id})


def create_treaty_compliance_checker() -> TreatyComplianceChecker:
    """Factory function to create treaty compliance checker."""
    return TreatyComplianceChecker()


def check_diplomatic_action(
    actor: str,
    action: str,
    target: str | None = None,
) -> ComplianceReport:
    """Quick check function for diplomatic action compliance."""
    checker = create_treaty_compliance_checker()
    return checker.check_action(actor, action, target)
