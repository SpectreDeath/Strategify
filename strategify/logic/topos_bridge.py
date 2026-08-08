"""Topos Subobject Classifier Decision Bridge.

Connects Em-Cubed Topos Ω modal truth verifiers into Strategify's agent decision pipeline.
"""

from __future__ import annotations

import logging
from typing import Any

try:
    from em_cubed.ontology.topos import SubobjectClassifier, TruthValue
except ImportError:

    class TruthValue:  # type: ignore
        def __init__(self, value: str, satisfied: bool):
            self.value = value
            self.satisfied = satisfied

    class SubobjectClassifier:  # type: ignore
        @staticmethod
        def classify_truth(confidence_score: float) -> Any:
            class DummyTruth:
                modal_type = "Necessary"
                is_satisfied = True
                truth_degree = confidence_score

            return DummyTruth()


logger = logging.getLogger(__name__)


class ToposDecisionBridge:
    """Bridge evaluating state actor strategic actions using Topos Ω Subobject Classifier."""

    @staticmethod
    def evaluate_action_confidence(action: str, confidence_score: float) -> dict[str, Any]:
        """Evaluate action confidence rating into Topos Ω modal truth state.

        Parameters
        ----------
        action : str
            Candidate action name (e.g., "mobilize", "sanction", "de-escalate").
        confidence_score : float
            Continuous trust or model probability score [0.0, 1.0].

        Returns
        -------
        dict[str, Any]
            Topos Ω evaluation details including modal_type, satisfaction status, and confidence.
        """
        truth_val: TruthValue = SubobjectClassifier.evaluate_confidence(confidence_score)
        satisfied = truth_val.is_satisfied()

        logger.info(
            "Evaluated action '%s' in Topos Ω: ModalType=%s, Confidence=%.2f, Satisfied=%s",
            action,
            truth_val.modal_type.value,
            truth_val.confidence,
            satisfied,
        )

        return {
            "action": action,
            "confidence": truth_val.confidence,
            "modal_type": truth_val.modal_type.value,
            "satisfied": satisfied,
            "is_boolean": truth_val.is_boolean,
        }
