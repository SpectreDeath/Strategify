"""Skill Flywheel API Client for Strategify Simulation Engine.

Allows simulation agents (e.g. StateActorAgent) to dynamically query
and execute skills hosted on Skill Flywheel's FastAPI server (port 8000).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class FlywheelSkillClient:
    """Client for interacting with the Skill Flywheel MCP skill server."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def search_skills(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search available skills on the Flywheel server.

        Args:
            query: Search query (e.g., "game theory", "optimization").
            limit: Max results.

        Returns:
            List of matching skill metadata dictionaries.
        """
        try:
            import httpx

            url = f"{self.base_url}/skills/search"
            response = httpx.get(url, params={"q": query, "limit": limit}, timeout=self.timeout)
            if response.status_code == 200:
                return response.json().get("skills", [])
        except Exception as e:
            logger.warning("Failed to reach Skill Flywheel server at %s: %s", self.base_url, e)
        return []

    def execute_skill(
        self, skill_name: str, input_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a skill on the Flywheel server.

        Args:
            skill_name: Name/ID of the skill.
            input_data: Keyword arguments/parameters for the skill.

        Returns:
            Execution result payload dictionary.
        """
        payload = {"input_data": input_data or {}}
        try:
            import httpx

            url = f"{self.base_url}/skills/execute/{skill_name}"
            response = httpx.post(url, json=payload, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "error": f"Server returned {response.status_code}"}
        except Exception as e:
            logger.warning("Failed to execute skill '%s' on Flywheel: %s", skill_name, e)
            return {"status": "fallback", "value": None, "warning": str(e)}
