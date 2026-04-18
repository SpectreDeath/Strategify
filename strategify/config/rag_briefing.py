"""RAG (Retrieval Augmented Generation) for scenario briefing from historical data.

Enables generating scenario context and briefings from historical conflict data
using retrieval-augmented generation techniques.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class HistoricalScenarioRAG:
    """RAG system for retrieving relevant historical scenarios."""

    def __init__(self, data_path: str | None = None):
        self.data_path = data_path or self._get_default_path()
        self.scenarios: list[dict[str, Any]] = []
        self._load_scenarios()

    def _get_default_path(self) -> str:
        return str(Path(__file__).parent.parent / "config" / "historical_scenarios.json")

    def _load_scenarios(self) -> None:
        """Load historical scenarios from data file."""
        p = Path(self.data_path)
        if p.exists():
            try:
                self.scenarios = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                self.scenarios = self._get_default_scenarios()
        else:
            self.scenarios = self._get_default_scenarios()

    def _get_default_scenarios(self) -> list[dict[str, Any]]:
        """Return default scenario library."""
        return [
            {
                "id": "ukraine_2022",
                "name": "Ukraine 2022",
                "type": "conventional_war",
                "actors": ["Russia", "Ukraine", "NATO"],
                "key_features": ["high_mobility", "air_supremacy", "sanctions"],
                "lessons": ["logistics_challenge", " drone_wfare", "information_war"],
            },
            {
                "id": "gulf_1991",
                "name": "Gulf War 1991",
                "type": "high_tech_war",
                "actors": ["USA", "Iraq", "Coalition"],
                "key_features": ["air_dominance", "precision_strikes", "coalition"],
                "lessons": ["stealth_effectiveness", "scud_hunting", "rapid_maneuver"],
            },
            {
                "id": "afghanistan_2001",
                "name": "Afghanistan 2001+",
                "type": "counter_insurgency",
                "actors": ["USA", "Taliban", "NATO"],
                "key_features": ["irregular_warfare", "tribal_dynamics", "nation_building"],
                "lessons": ["insurgency_persistence", "pop_centric", "political_complexity"],
            },
            {
                "id": "cold_war_proxy",
                "name": "Cold War Proxy Conflicts",
                "type": "proxy_war",
                "actors": ["USA", "USSR", "local_forces"],
                "key_features": ["proxy_support", "ideological", "limited_engagement"],
                "lessons": ["proxy_efficiency", "deterrence", "escalation_control"],
            },
        ]

    def retrieve_similar(
        self,
        query_features: list[str],
        top_k: int = 3,
    ) -> list[dict[str, Any]]:
        """Retrieve scenarios similar to query features."""
        scores = []

        for scenario in self.scenarios:
            score = 0.0
            for feature in query_features:
                if feature in scenario.get("key_features", []):
                    score += 1.0
                if feature in scenario.get("type", "").lower():
                    score += 0.5
                if any(feature in a.lower() for a in scenario.get("actors", [])):
                    score += 0.3

            if score > 0:
                scores.append((score, scenario))

        scores.sort(key=lambda x: x[0], reverse=True)
        return [s[1] for s in scores[:top_k]]

    def generate_briefing(
        self,
        scenario_type: str,
        actors: list[str],
        context_features: list[str],
    ) -> dict[str, Any]:
        """Generate scenario briefing from historical data."""
        similar = self.retrieve_similar(context_features)

        briefing = {
            "scenario_type": scenario_type,
            "actors": actors,
            "relevant_history": similar,
            "context": {},
            "recommendations": [],
        }

        if similar:
            historical = similar[0]
            briefing["context"]["historical_analogy"] = historical.get("name")
            briefing["context"]["lessons"] = historical.get("lessons", [])

            for lesson in historical.get("lessons", []):
                if "logistics" in lesson:
                    briefing["recommendations"].append("Prepare robust logistics chain for sustained operations")
                if "air" in lesson or "drone" in lesson:
                    briefing["recommendations"].append("Invest in air superiority and drone capabilities")
                if "insurgency" in lesson or "irregular" in lesson:
                    briefing["recommendations"].append("Plan for long-term counter-insurgency operations")
                if "sanctions" in lesson:
                    briefing["recommendations"].append("Prepare economic contingency measures")

        return briefing


def generate_scenario_briefing(
    scenario_type: str,
    actors: list[str],
    context_features: list[str],
    rag_path: str | None = None,
) -> dict[str, Any]:
    """Generate a briefing for a scenario using RAG.

    This is the main entry point for generating scenario context.
    """
    rag = HistoricalScenarioRAG(rag_path)
    return rag.generate_briefing(scenario_type, actors, context_features)
