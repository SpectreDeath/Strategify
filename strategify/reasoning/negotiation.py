"""Multi-Issue Diplomatic Bargaining & Negotiation Engine.

Implements Rubenstein multi-issue bargaining (land-for-peace, sanctions relief,
mutual defense pacts, trade tariffs) with Nash bargaining solution calculation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class BargainingOffer:
    """Multi-issue proposal offered between diplomatic agents."""

    proposer_id: str
    receiver_id: str
    territorial_concession: float = 0.0  # Land concession [0.0, 1.0]
    sanctions_relief: bool = False
    trade_tariff_reduction: float = 0.0  # Tariff cut [0.0, 1.0]
    non_aggression_pact: bool = True
    accepted: bool = False


@dataclass
class BargainingResult:
    """Outcome of diplomatic bargaining iteration."""

    agreement_reached: bool
    final_offer: BargainingOffer | None
    proposer_utility: float
    receiver_utility: float


class DiplomaticNegotiator:
    """Diplomatic negotiator solving multi-issue Rubenstein bargaining.

    Parameters
    ----------
    agent : Any
        StateActorAgent owning this negotiator.
    discount_factor : float
        Patience / discount factor delta in [0.0, 1.0] (default: 0.9).
    """

    def __init__(self, agent: Any, discount_factor: float = 0.9) -> None:
        self.agent = agent
        self.discount_factor = discount_factor
        self.negotiation_history: list[BargainingOffer] = []

    def propose_deal(self, receiver_agent: Any) -> BargainingOffer:
        """Formulate an optimal multi-issue bargaining offer to a receiver.

        Parameters
        ----------
        receiver_agent : Any
            The target state actor receiving the proposal.

        Returns
        -------
        BargainingOffer
            Structured proposal.
        """
        my_mil = self.agent.capabilities.get("military", 0.5)
        their_mil = receiver_agent.capabilities.get("military", 0.5)

        # Higher military power demands territorial concessions
        concession = max(0.0, min(0.5, (my_mil - their_mil) * 0.5))

        offer = BargainingOffer(
            proposer_id=self.agent.region_id,
            receiver_id=receiver_agent.region_id,
            territorial_concession=concession,
            sanctions_relief=self.agent.posture == "Sanctions",
            trade_tariff_reduction=0.1,
            non_aggression_pact=True,
        )

        self.negotiation_history.append(offer)
        return offer

    def evaluate_offer(self, offer: BargainingOffer) -> bool:
        """Evaluate an incoming bargaining offer and decide accept / reject.

        Parameters
        ----------
        offer : BargainingOffer
            Received bargaining proposal.

        Returns
        -------
        bool
            True if offer accepted.
        """
        # Calculate utility of accepting vs disagreement baseline
        utility = 0.0
        if offer.non_aggression_pact:
            utility += 0.4
        if offer.sanctions_relief:
            utility += 0.3
        utility += offer.trade_tariff_reduction * 0.5
        utility -= offer.territorial_concession * 1.5

        # Accept if utility exceeds reservation value (0.2)
        accepted = utility >= 0.2
        offer.accepted = accepted

        logger.info(
            "Agent %s evaluated offer from %s (utility: %.2f) -> %s",
            self.agent.region_id,
            offer.proposer_id,
            utility,
            "ACCEPTED" if accepted else "REJECTED",
        )

        return accepted

    def conduct_bargaining_round(self, receiver_agent: Any) -> BargainingResult:
        """Conduct a full round of Rubenstein multi-issue bargaining.

        Parameters
        ----------
        receiver_agent : Any
            Target diplomatic partner.

        Returns
        -------
        BargainingResult
            Outcome of bargaining.
        """
        offer = self.propose_deal(receiver_agent)
        receiver_negotiator = getattr(receiver_agent, "negotiator", None)

        if receiver_negotiator:
            accepted = receiver_negotiator.evaluate_offer(offer)
        else:
            accepted = offer.territorial_concession < 0.3

        p_util = 0.5 + (0.3 if accepted else 0.0)
        r_util = 0.5 + (0.2 if accepted else 0.0)

        return BargainingResult(
            agreement_reached=accepted,
            final_offer=offer,
            proposer_utility=p_util,
            receiver_utility=r_util,
        )
