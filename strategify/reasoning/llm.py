"""LLM-augmented agent decisions: optional AI reasoning layer.

Provides an LLMDecisionEngine that can augment or replace Nash equilibrium
decisions with natural-language reasoning from a language model.

Usage::

    engine = LLMDecisionEngine(provider="openai", model="gpt-4o-mini")
    decision = engine.query(state_packet)

Falls back to Nash equilibrium on any parse failure or API error.
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from pydantic import BaseModel, field_validator

    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

if _HAS_PYDANTIC:

    class LLMDecision(BaseModel):
        """Pydantic-validated schema for LLM decision output.

        Fields
        ------
        action:
            Must be exactly ``"Escalate"`` or ``"Deescalate"``.
        reasoning:
            Free-text explanation of the decision.
        confidence:
            Optional confidence score in [0, 1]. Defaults to 0.5.
        """

        action: str
        reasoning: str = ""
        confidence: float = 0.5

        @field_validator("action")
        @classmethod
        def validate_action(cls, v: str) -> str:
            v = v.strip()
            if v not in ("Escalate", "Deescalate"):
                raise ValueError(f"action must be 'Escalate' or 'Deescalate', got '{v}'")
            return v

        @field_validator("confidence")
        @classmethod
        def validate_confidence(cls, v: float) -> float:
            return max(0.0, min(1.0, float(v)))

else:
    LLMDecision = None  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Decision Engine
# ---------------------------------------------------------------------------


class LLMDecisionEngine:
    """Queries a language model for geopolitical decision-making.

    Builds a structured state packet from the simulation and requests
    a JSON response with reasoning and action. Falls back to Nash
    equilibrium on any failure.

    Parameters
    ----------
    provider:
        LLM provider: ``"openai"``, ``"anthropic"``, or ``"local"``.
    model:
        Model identifier (e.g. ``"gpt-4o-mini"``, ``"claude-3-haiku"``).
    api_key:
        API key. If None, reads from environment variable.
    max_retries:
        Maximum retries on parse failure before falling back.
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: str | None = None,
        max_retries: int = 2,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.max_retries = max_retries
        self._cache = LLMStrategyCache()

    def _build_prompt(self, state: dict[str, Any]) -> str:
        """Build the decision prompt from simulation state."""
        return (
            "You are a geopolitical strategy advisor. Given the current state, "
            "recommend an action for the agent.\n\n"
            "Respond with EXACTLY this JSON format and nothing else:\n"
            '{"reasoning": "<brief analysis>", "action": "Escalate" or "Deescalate"}\n\n'
            f"State:\n{json.dumps(state, indent=2, default=str)}\n\n"
            "Consider: military balance, economic strength, alliances, "
            "escalation history, and current geopolitical tension.\n\n"
            "Response:"
        )

    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API and return the raw response text."""
        if self.provider == "openai":
            return self._call_openai(prompt)
        elif self.provider == "anthropic":
            return self._call_anthropic(prompt)
        elif self.provider == "local":
            return self._call_local(prompt)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI-compatible API."""
        import os
        import urllib.error
        import urllib.request

        api_key = self.api_key or os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("No OpenAI API key provided")

        url = "https://api.openai.com/v1/chat/completions"
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200,
                "temperature": 0.3,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic-compatible API."""
        import os
        import urllib.request

        api_key = self.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("No Anthropic API key provided")

        url = "https://api.anthropic.com/v1/messages"
        payload = json.dumps(
            {
                "model": self.model,
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["content"][0]["text"]

    def _call_local(self, prompt: str) -> str:
        """Call local Ollama-compatible endpoint."""
        import urllib.request

        url = "http://localhost:11434/api/generate"
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3},
            }
        ).encode("utf-8")

        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("response", "")

    def _parse_response(self, text: str) -> dict[str, str] | None:
        """Parse the LLM response into a structured decision.

        Uses pydantic validation when available for schema enforcement.
        Falls back to manual JSON parsing otherwise.
        """
        text = text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1] if "\n" in text else text[3:]
        if text.endswith("```"):
            text = text[:-3]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

        # Try pydantic-validated parsing first
        if _HAS_PYDANTIC:
            try:
                data = json.loads(text)
                validated = LLMDecision.model_validate(data)
                return {
                    "action": validated.action,
                    "reasoning": validated.reasoning,
                    "confidence": str(validated.confidence),
                }
            except (json.JSONDecodeError, Exception):
                pass  # Fall through to manual parsing

        # Manual JSON parsing fallback
        try:
            data = json.loads(text)
            action = data.get("action", "")
            if action in ("Escalate", "Deescalate"):
                return {"action": action, "reasoning": data.get("reasoning", "")}
        except json.JSONDecodeError:
            pass

        # Fallback: look for action keyword in text
        if "escalate" in text.lower() and "deescalate" not in text.lower():
            return {"action": "Escalate", "reasoning": "Parsed from unstructured response"}
        if "deescalate" in text.lower():
            return {"action": "Deescalate", "reasoning": "Parsed from unstructured response"}

        return None

    def query(self, state: dict[str, Any]) -> dict[str, str] | None:
        """Query the LLM for a decision based on simulation state.

        Parameters
        ----------
        state:
            State packet with keys: ``region_id``, ``military``, ``economic``,
            ``allies``, ``enemies``, ``escalation_level``, ``posture``, etc.

        Returns
        -------
        dict or None
            ``{"action": "Escalate"|"Deescalate", "reasoning": "..."}``
            Returns None on failure (caller should fall back to Nash).
        """
        # Check cache
        cached = self._cache.get(state)
        if cached is not None:
            return cached

        prompt = self._build_prompt(state)

        for attempt in range(self.max_retries + 1):
            try:
                raw = self._call_llm(prompt)
                decision = self._parse_response(raw)
                if decision is not None:
                    self._cache.put(state, decision)
                    return decision
            except Exception as exc:
                logger.warning("LLM query attempt %d failed: %s", attempt + 1, exc)

        logger.info("LLM failed after %d attempts, returning None for Nash fallback", self.max_retries + 1)
        return None

    def query_or_fallback(
        self,
        state: dict[str, Any],
        fallback_action: str = "Deescalate",
    ) -> dict[str, str]:
        """Query LLM or return a safe fallback action."""
        result = self.query(state)
        if result is not None:
            return result
        return {"action": fallback_action, "reasoning": "Nash equilibrium fallback"}


# ---------------------------------------------------------------------------
# Strategy Cache
# ---------------------------------------------------------------------------


class LLMStrategyCache:
    """Caches LLM decisions to avoid redundant API calls.

    Uses a simple hash of the state packet (region_id + key numeric values)
    for cache lookup.
    """

    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, dict[str, str]] = {}
        self._max_size = max_size

    def _make_key(self, state: dict[str, Any]) -> str:
        """Create a cache key from state."""
        key_parts = [
            str(state.get("region_id", "")),
            f"{state.get('military', 0):.1f}",
            f"{state.get('economic', 0):.1f}",
            str(state.get("posture", "")),
            str(state.get("escalation_level", "")),
        ]
        return "|".join(key_parts)

    def get(self, state: dict[str, Any]) -> dict[str, str] | None:
        """Get cached decision for a state."""
        return self._cache.get(self._make_key(state))

    def put(self, state: dict[str, Any], decision: dict[str, str]) -> None:
        """Cache a decision."""
        if len(self._cache) >= self._max_size:
            # Evict oldest entry
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[self._make_key(state)] = decision

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()
