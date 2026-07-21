"""Tests for complex reasoning, multi-horizon lookahead planning, combined-arms campaigns, deception, and Rubenstein bargaining."""

from strategify.reasoning.campaigns import CampaignPhase
from strategify.reasoning.deception import DeceptionEngine
from strategify.reasoning.negotiation import DiplomaticNegotiator
from strategify.reasoning.planner import StrategicDoctrine, StrategicPlanner
from strategify.sim.model import GeopolModel


def test_strategic_planner_doctrines_and_lookahead():
    model = GeopolModel(n_steps=1)
    agent = model.schedule.agents[0]
    planner = StrategicPlanner(agent=agent, doctrine=StrategicDoctrine.HEGEMONY, lookahead_depth=3)

    score_invade = planner.evaluate_lookahead_payoff("Invade", depth=3)
    score_deescalate = planner.evaluate_lookahead_payoff("Deescalate", depth=3)

    assert score_invade > score_deescalate
    best_action = planner.select_best_action(["Invade", "Deescalate"])
    assert best_action == "Invade"


def test_combined_arms_campaign_planner():
    model = GeopolModel(n_steps=1)
    agents = [a for a in model.schedule.agents if hasattr(a, "campaign_planner")]
    assert len(agents) >= 2

    planner = agents[0].campaign_planner
    campaign = planner.initiate_campaign(target_id="Bravo")

    assert campaign.current_phase == CampaignPhase.PHASE_1_PREPARATION
    res1 = planner.execute_current_campaign_step("Bravo", model)
    assert res1["executed"] is True
    assert res1["domain"] in ("cyber", "information")


def test_deception_engine():
    model = GeopolModel(n_steps=1)
    agent_a = model.schedule.agents[0]
    agent_b = model.schedule.agents[1]

    deception = DeceptionEngine(agent=agent_a)
    signal = deception.create_feint(target_id=agent_b.region_id, purported_posture="Invade")

    assert signal.purported_posture == "Invade"
    assert signal.target_agent_id == agent_b.region_id

    # Test deceptive intelligence injection
    injected = deception.inject_deceptive_intelligence(agent_b)
    assert isinstance(injected, bool)


def test_diplomatic_negotiator_rubenstein_bargaining():
    model = GeopolModel(n_steps=1)
    agent_a = model.schedule.agents[0]
    agent_b = model.schedule.agents[1]

    negotiator_a = DiplomaticNegotiator(agent=agent_a)
    negotiator_b = DiplomaticNegotiator(agent=agent_b)

    agent_a.negotiator = negotiator_a
    agent_b.negotiator = negotiator_b

    offer = negotiator_a.propose_deal(agent_b)
    assert offer.proposer_id == agent_a.region_id
    assert offer.receiver_id == agent_b.region_id

    result = negotiator_a.conduct_bargaining_round(agent_b)
    assert hasattr(result, "agreement_reached")
    assert hasattr(result, "proposer_utility")
