"""Unit test suite for Tri-Engine Synergy Bridges connecting Strategify, Em-Cubed, and SME."""

from strategify.epidemiology.zkp_bridge import ZKPBiodefenseAttestor
from strategify.logic.topos_bridge import ToposDecisionBridge
from strategify.osint.sme_adapter import SMEOSINTBridge
from strategify.sim.dl_guard import DLConflictGuard

EXPECTED_TENSION = 0.72
EXPECTED_TRUST = 0.89


def test_sme_osint_bridge():
    bridge = SMEOSINTBridge()
    res = bridge.fetch_epistemic_tension("Ukraine")
    assert res["region_id"] == "Ukraine"
    assert res["tension_score"] == EXPECTED_TENSION
    assert res["epistemic_trust_score"] == EXPECTED_TRUST


def test_topos_decision_bridge():
    res = ToposDecisionBridge.evaluate_action_confidence("mobilize", 0.92)
    assert res["action"] == "mobilize"
    assert res["satisfied"] is True
    assert res["modal_type"] == "Necessary"


def test_dl_conflict_guard():
    res_allowed = DLConflictGuard.guard_escalation("cyber_attack")
    assert res_allowed["is_allowed"] is True

    res_denied = DLConflictGuard.guard_escalation("full_scale_assault")
    assert res_denied["is_allowed"] is False


def test_zkp_biodefense_attestor():
    res = ZKPBiodefenseAttestor.generate_biodefense_proof("MiddleEast", 0.85, 1.2)
    assert "proof_id" in res
    assert "merkle_state_root" in res
    assert "signature" in res
