"""Tests for legal AI modules."""

import pytest

from strategify.reasoning.courtroom_simulator import (
    BindingArbitrationSystem,
    CourtroomSimulator,
    ProceduralStage,
)
from strategify.reasoning.legal_agent import (
    DisputeResolutionSystem,
    LegalAgent,
    LegalDomain,
    LegalRuling,
)
from strategify.reasoning.legal_precedent_rag import (
    LegalPrecedentDatabase,
    LegalPrecedentRAG,
    RAGQuery,
)
from strategify.reasoning.treaty_compliance import (
    Treaty,
    TreatyComplianceChecker,
    TreatyRegistry,
    TreatyType,
)


class TestLegalAgent:
    """Tests for LegalAgent class."""

    def test_create_legal_agent(self):
        agent = LegalAgent("USA", "United States", LegalDomain.INTERNATIONAL)
        assert agent.agent_id == "USA"
        assert agent.name == "United States"
        assert agent.legal_domain == LegalDomain.INTERNATIONAL

    def test_file_claim(self):
        agent = LegalAgent("USA", "United States", LegalDomain.TERRITORIAL)
        claim = agent.file_claim(
            defendant="Russia",
            legal_basis="UN Charter Article 2(4)",
            factual_basis="Armed attack on territory",
            relief_requested="Withdrawal",
        )
        assert claim.claimant == "USA"
        assert claim.defendant == "Russia"
        assert len(agent.claims_filed) == 1

    def test_evaluate_ruling_favorable(self):
        agent = LegalAgent("USA", "United States", LegalDomain.INTERNATIONAL)
        ruling = LegalRuling(
            ruling_id="RUL_001",
            dispute_id="DISP_001",
            tribunal="ICJ",
            ruling_body="ICJ",
            decision="favorable",
            legal_reasoning="Test",
            precedent_relied_on=[],
            remedies=[],
            compliance_required=[],
        )
        result = agent.evaluate_ruling(ruling)
        assert result["compliance"] is True

    def test_evaluate_ruling_unfavorable_high_risk(self):
        agent = LegalAgent("USA", "United States", LegalDomain.INTERNATIONAL)
        agent.risk_tolerance = 0.7  # High risk tolerance means will defy unfavorable rulings
        ruling = LegalRuling(
            ruling_id="RUL_002",
            dispute_id="DISP_001",
            tribunal="ICJ",
            ruling_body="ICJ",
            decision="unfavorable",
            legal_reasoning="Test",
            precedent_relied_on=[],
            remedies=[],
            compliance_required=[],
        )
        result = agent.evaluate_ruling(ruling)
        assert result["compliance"] is False

    def test_set_strategy(self):
        agent = LegalAgent("USA", "United States", LegalDomain.INTERNATIONAL)
        agent.set_strategy("aggressive", 0.8)
        assert agent.legal_strategy == "aggressive"
        assert agent.risk_tolerance == 0.8


class TestDisputeResolutionSystem:
    """Tests for DisputeResolutionSystem."""

    def test_create_system(self):
        system = DisputeResolutionSystem("Test Tribunal")
        assert system.tribunal_name == "Test Tribunal"
        assert len(system.disputes) == 0

    def test_initiate_dispute(self):
        system = DisputeResolutionSystem()
        dispute_id = system.initiate_dispute(
            claimant_id="USA",
            defendant_id="Russia",
            domain=LegalDomain.TERRITORIAL,
            claim_details={
                "legal_basis": "UN Charter",
                "factual_basis": "Annexation",
                "relief_requested": "Restoration",
            },
        )
        assert dispute_id.startswith("DISP_")
        assert dispute_id in system.disputes
        assert system.disputes[dispute_id]["status"] == "filing"

    def test_advance_dispute(self):
        system = DisputeResolutionSystem()
        dispute_id = system.initiate_dispute("USA", "Russia", LegalDomain.TERRITORIAL, {})
        result = system.advance_dispute(dispute_id)
        assert result is True
        assert system.disputes[dispute_id]["status"] == "mediation"

    def test_issue_ruling(self):
        system = DisputeResolutionSystem()
        dispute_id = system.initiate_dispute("USA", "Russia", LegalDomain.TERRITORIAL, {})
        ruling = system.issue_ruling(
            dispute_id,
            "partial",
            "Based on evidence",
            ["withdrawal"],
            ["Nicaragua v. USA"],
        )
        assert ruling.ruling_id.startswith("RUL_")
        assert ruling.decision == "partial"


class TestTreatyRegistry:
    """Tests for TreatyRegistry."""

    def test_create_registry(self):
        registry = TreatyRegistry()
        assert len(registry.treaties) >= 3  # UN Charter, Vienna, Geneva

    def test_get_treaty(self):
        registry = TreatyRegistry()
        treaty = registry.get_treaty("un_charter")
        assert treaty is not None
        assert treaty.name == "Charter of the United Nations"

    def test_get_treaties_for_parties(self):
        registry = TreatyRegistry()
        treaties = registry.get_treaties_for_parties(["USA"])
        assert len(treaties) >= 3

    def test_register_custom_treaty(self):
        registry = TreatyRegistry()
        treaty = Treaty(
            treaty_id="custom_001",
            name="Custom Treaty",
            treaty_type=TreatyType.BILATERAL,
            parties=["USA", "UK"],
        )
        registry.register_treaty(treaty)
        assert "custom_001" in registry.treaties


class TestTreatyComplianceChecker:
    """Tests for TreatyComplianceChecker."""

    def test_create_checker(self):
        checker = TreatyComplianceChecker()
        assert checker.registry is not None

    def test_check_action_violation(self):
        checker = TreatyComplianceChecker()
        report = checker.check_action("USA", "armed_attack", "target")
        assert report.overall_status in ["violation", "compliant"]
        if report.overall_status == "violation":
            assert len(report.findings) > 0

    def test_check_action_compliant(self):
        checker = TreatyComplianceChecker()
        report = checker.check_action("USA", "diplomatic_negotiation", "target")
        assert report.overall_status == "compliant"

    def test_escalation_risk_calculation(self):
        checker = TreatyComplianceChecker()
        report = checker.check_action("USA", "armed_attack", "target")
        assert 0.0 <= report.escalation_risk <= 1.0


class TestLegalPrecedentDatabase:
    """Tests for LegalPrecedentDatabase."""

    def test_create_database(self):
        db = LegalPrecedentDatabase()
        assert len(db.precedents) >= 8

    def test_get_precedents_by_domain(self):
        db = LegalPrecedentDatabase()
        precedents = db.get_precedents_by_domain("international")
        assert len(precedents) > 0
        assert all(p.domain == "international" for p in precedents)


class TestLegalPrecedentRAG:
    """Tests for LegalPrecedentRAG."""

    def test_create_rag(self):
        rag = LegalPrecedentRAG()
        assert rag.database is not None

    def test_retrieve_precedents(self):
        rag = LegalPrecedentRAG()
        query = RAGQuery(
            query_text="use of force",
            domain="international",
            dispute_type="general",
        )
        results = rag.retrieve(query)
        assert len(results) > 0

    def test_build_legal_brief(self):
        rag = LegalPrecedentRAG()
        query = RAGQuery(
            query_text="self defense",
            domain="international",
            dispute_type="general",
        )
        brief = rag.build_legal_brief(query)
        assert "precedents" in brief
        assert "arguments" in brief
        assert brief["precedents_retrieved"] > 0


class TestCourtroomSimulator:
    """Tests for CourtroomSimulator."""

    def test_create_simulator(self):
        courtroom = CourtroomSimulator()
        assert len(courtroom.panels) >= 2

    def test_initiate_proceeding(self):
        courtroom = CourtroomSimulator()
        proceeding = courtroom.initiate_proceeding(
            "DISP_001",
            "panel_standard_001",
            {"USA": {}, "Russia": {}},
        )
        assert proceeding.dispute_id == "DISP_001"
        assert proceeding.stage == ProceduralStage.INITIAL_HEARING

    def test_advance_stage(self):
        courtroom = CourtroomSimulator()
        proceeding = courtroom.initiate_proceeding(
            "DISP_001",
            "panel_standard_001",
            {"USA": {}, "Russia": {}},
        )
        result = courtroom.advance_stage(proceeding.proceeding_id)
        assert result is True
        assert proceeding.stage == ProceduralStage.WRITTEN_SUBMISSIONS

    def test_issue_binding_ruling(self):
        courtroom = CourtroomSimulator()
        proceeding = courtroom.initiate_proceeding(
            "DISP_001",
            "panel_standard_001",
            {"USA": {}, "Russia": {}},
        )
        ruling = courtroom.issue_binding_ruling(
            proceeding.proceeding_id,
            "Russia_must_withdraw",
            "Based on UN Charter",
        )
        assert ruling.ruling_id.startswith("RUL_")
        assert ruling.status == "pending"

    def test_check_compliance(self):
        courtroom = CourtroomSimulator()
        proceeding = courtroom.initiate_proceeding(
            "DISP_001",
            "panel_standard_001",
            {"USA": {}, "Russia": {}},
        )
        ruling = courtroom.issue_binding_ruling(
            proceeding.proceeding_id,
            "Russia_must_withdraw",
            "Based on UN Charter",
        )
        result = courtroom.check_compliance(ruling.ruling_id, "Russia", "comply")
        assert result["compliant"] is True


class TestBindingArbitrationSystem:
    """Tests for BindingArbitrationSystem."""

    def test_create_system(self):
        system = BindingArbitrationSystem()
        assert system.courtroom is not None

    def test_submit_dispute(self):
        system = BindingArbitrationSystem()
        proceeding_id = system.submit_dispute(
            "DISP_001",
            "USA",
            "Russia",
            {"claims": ["annexation"], "defenses": ["self-defense"]},
        )
        assert proceeding_id.startswith("PRO_")

    def test_process_to_ruling(self):
        system = BindingArbitrationSystem()
        proceeding_id = system.submit_dispute("DISP_001", "USA", "Russia", {})
        ruling = system.process_dispute_to_ruling(
            "DISP_001",
            "partial_favorable",
            "Based on evidence presented",
        )
        assert ruling.decision == "partial_favorable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
