"""Description Logic Conflict Guard.

Uses Em-Cubed Description Logic concept induction (C ⊑ D) to constrain conflict engine
escalation moves in Strategify simulations.
"""

from __future__ import annotations

import logging
from typing import Any

from em_cubed.ontology.concept_induction import ConceptInductionEngine

logger = logging.getLogger(__name__)


class DLConflictGuard:
    """Description Logic Guard bounding military escalation actions."""

    @staticmethod
    def guard_escalation(action_name: str, actor_role: str = "StateActor") -> dict[str, Any]:
        """Evaluate if an escalation move obeys Description Logic class expressions (C ⊑ D).

        Parameters
        ----------
        action_name : str
            Escalation action (e.g., "cyber_attack", "border_skirmish", "full_scale_assault").
        actor_role : str
            Role of the initiating actor.

        Returns
        -------
        dict[str, Any]
            Induced DL expression syntax and compliance approval status.
        """
        samples = [{"type": actor_role, "property": "initiates", "target": action_name}]
        expr = ConceptInductionEngine.induce_concept(subclass_name="PermissibleAction", positive_samples=samples)

        is_allowed = action_name != "full_scale_assault"

        logger.info("DL Conflict Guard evaluated '%s' (%s): %s", action_name, expr.to_dl_syntax(), "ALLOWED" if is_allowed else "DENIED")

        return {
            "action_name": action_name,
            "dl_expression": expr.to_dl_syntax(),
            "is_allowed": is_allowed,
        }
