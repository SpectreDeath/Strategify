"""Tests for supply chain economics module."""

from strategify.economics.supply_chain import SupplyChainEngine


def test_supply_chain_engine_chokepoints():
    engine = SupplyChainEngine()
    engine.add_route("USA", "Ukraine", "semiconductors", capacity=100.0, flow=80.0)
    engine.add_route("Ukraine", "Poland", "grain", capacity=150.0, flow=120.0)

    chokepoints = engine.compute_chokepoints()
    assert len(chokepoints) > 0
    assert "Ukraine" in chokepoints
    assert chokepoints["Ukraine"].vulnerability_score >= 0.0

    facts = engine.export_prolog_facts()
    assert len(facts) == len(chokepoints)
    assert any("chokepoint_risk" in f for f in facts)
