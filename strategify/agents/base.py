"""Abstract base class for all actor agents in strategify."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import mesa_geo as mg
from shapely.geometry import base as shp_base


class BaseActorAgent(mg.GeoAgent, ABC):
    """Abstract Mesa-Geo agent representing a geopolitical actor.

    Properties like ``region_id`` are populated from the GeoJSON data by the GeoAgentCreator.
    """

    def __init__(
        self,
        unique_id: int,
        model: Any,
        geometry: shp_base.BaseGeometry,
        crs: str,
    ) -> None:
        super().__init__(unique_id, model, geometry, crs)
        self.state: dict = {}  # beliefs / intentions / memory

    # ------------------------------------------------------------------
    # Mesa lifecycle hooks
    # ------------------------------------------------------------------

    def observe(self) -> None:
        """Read relevant model state into ``self.state``.

        Override in subclasses to populate beliefs from the model.
        """

    @abstractmethod
    def decide(self) -> dict:
        """Return an action dict, e.g. ``{"action": "Escalate", "target_region": "bravo"}``."""

    def step(self) -> None:
        """Standard Mesa step: observe -> decide -> apply."""
        self.observe()
        action = self.decide()
        self._apply(action)

    def _apply(self, action: dict) -> None:
        """Apply action effects to self.

        Override or extend in subclasses to implement additional effects.
        """
        self.state["last_action"] = action
