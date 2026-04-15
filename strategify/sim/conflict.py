"""Conflict engine for resolving kinetic military engagements.

This module handles combat between units, terrain-based modifiers, and
the economic/demographic consequences of armed conflict.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from strategify.agents.military import Unit

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)

# Default terrain modifiers (attacker disadvantage factor)
_DEFAULT_TERRAIN_MODIFIERS = {
    "Forest": 0.8,
    "Mountain": 0.6,
    "Urban": 0.7,
    "Plain": 1.0,
}

# Global fallback for regions where GeoJSON property is missing
# (Can be extended via plugins or settings)
DEFAULT_TERRAIN_MAP: dict[str, str] = {
    "UKR": "Plain",
    "RUS": "Forest",
    "POL": "Forest",
    "BLR": "Forest",
    "Ukraine": "Plain",
    "Russia": "Forest",
}


class ConflictEngine:
    """Orchestrates military engagements between units.

    Parameters
    ----------
    model : GeopolModel
        The parent model.
    terrain_overrides : dict, optional
        ``{region_id: terrain_type}`` to override GeoJSON-derived terrain.
    """

    def __init__(self, model: GeopolModel, terrain_overrides: dict | None = None) -> None:
        self.model = model
        self.terrain_overrides = terrain_overrides or {}
        self.modifiers = dict(_DEFAULT_TERRAIN_MODIFIERS)
        self.modifiers = {
            "Forest": 0.8,  # Attacker disadvantage
            "Mountain": 0.6,  # Strong defender advantage
            "Urban": 0.7,  # Harder to root out
            "Plain": 1.0,  # Normal
        }

    def resolve_kinetic_combat(self) -> None:
        """Identify and resolve combat between non-allied units in range."""
        all_units: list[Unit] = []
        for agent in self.model.schedule.agents:
            if hasattr(agent, "military"):
                all_units.extend(agent.military.units)

        if not all_units:
            return

        # Simple O(N^2) for demo, can be optimized with spatial index
        engaged_pairs: list[tuple[Unit, Unit]] = []
        for i, u1 in enumerate(all_units):
            for u2 in all_units[i + 1 :]:
                if u1.owner == u2.owner:
                    continue
                if u1.owner.unique_id in self.model.relations.get_allies(u2.owner.unique_id):
                    continue

                # Use 50km as engagement range
                if u1.location.distance(u2.location) <= 50_000.0:
                    engaged_pairs.append((u1, u2))

        for u1, u2 in engaged_pairs:
            self._execute_combat(u1, u2)

    def _execute_combat(self, u1: Unit, u2: Unit) -> None:
        """Execute a round of combat between two units."""
        # Determine terrain modifier based on u1's location
        region_id = u1.owner.region_id

        terrain = self._get_terrain(region_id)
        modifier = self.modifiers.get(terrain, 1.0)

        p1 = u1.strength * u1.readiness * u1.combat_multiplier * modifier
        p2 = u2.strength * u2.readiness * u2.combat_multiplier

        # Phase 13: Asymmetric Surprise Bonus
        from strategify.agents.non_state import NonStateActor
        if isinstance(u1.owner, NonStateActor) and u1.owner.posture in ["Infiltrate", "HitAndRun"]:
            p1 *= 1.5  # Ambush bonus
        if isinstance(u2.owner, NonStateActor) and u2.owner.posture in ["Infiltrate", "HitAndRun"]:
            p2 *= 1.5

        # Phase 14: Peacekeeping suppression
        suppression_modifier = 1.0
        total_pk_strength = 0.0
        from strategify.agents.state_actor import StateActorAgent
        for agent in self.model.schedule.agents:
            if isinstance(agent, StateActorAgent):
                total_pk_strength += agent.military.get_peacekeeping_strength(region_id)
        
        # Max 80% reduction in damage from peacekeeping
        suppression = min(0.8, total_pk_strength / 4.0)
        suppression_modifier = 1.0 - suppression

        # Phase 17: Fast-Path Combat via Clojure Engine
        clojure_succeeded = False
        if hasattr(self.model, "clj_bridge") and self.model.clj_bridge and self.model.clj_bridge._available:
            payload = {
                "p1-strength": p1 * suppression_modifier,
                "p2-strength": p2 * suppression_modifier, # Pass suppressed strengths
                "terrain-modifier": modifier
            }
            import json
            code = f"""
            (require '[strategify.core :as s])
            (s/resolve-combat '{json.dumps(payload)})
            """
            result = self.model.clj_bridge.execute(code)
            if result and isinstance(result, dict) and "p1-remaining" in result:
                u1.strength = result.get("p1-remaining", u1.strength)
                u2.strength = result.get("p2-remaining", u2.strength)
                clojure_succeeded = True

        if not clojure_succeeded:
            # Fallback Damage calculation: base 10% loss to both, adjusted by power ratio
            base_dmg = 0.1 * suppression_modifier
            if p1 > p2 and p1 > 0:
                ratio = p2 / p1
                u1.strength = max(0.0, u1.strength - (base_dmg * ratio))
                u2.strength = max(0.0, u2.strength - base_dmg)
            elif p2 > 0:
                ratio = p1 / p2
                u1.strength = max(0.0, u1.strength - base_dmg)
                u2.strength = max(0.0, u2.strength - (base_dmg * ratio))
            else:
                u1.strength = max(0.0, u1.strength - base_dmg)
                u2.strength = max(0.0, u2.strength - base_dmg)

        # Readiness drop after combat
        u1.readiness = max(0.0, u1.readiness - 0.2)
        u2.readiness = max(0.0, u2.readiness - 0.2)

        # Economic/Pop consequences
        self._apply_collateral_damage(region_id)

    def _apply_collateral_damage(self, region_id: str) -> None:
        """Apply population and GDP reduction to a region in conflict."""
        # Reduce population by 0.1% for every combat event
        if self.model.population_model:
            agent = self.model._agent_registry.get(region_id)
            if agent:
                # Suppression also reduces collateral damage
                total_pk_strength = 0.0
                from strategify.agents.state_actor import StateActorAgent
                for a in self.model.schedule.agents:
                    if isinstance(a, StateActorAgent):
                        total_pk_strength += a.military.get_peacekeeping_strength(region_id)
                
                # Collateral suppression: max 90% reduction
                col_suppression = min(0.9, total_pk_strength / 3.0)
                loss_factor = 0.001 * (1.0 - col_suppression)
                
                pop = self.model.population_model.get_population(agent.unique_id)
                self.model.population_model.set_population(agent.unique_id, pop * (1.0 - loss_factor))

        # Reduce GDP growth or direct impact if trade network exists
        if self.model.trade_network:
            # Inject "Conflict Friction" into trade flows or GDP
            logger.info("Combat engagement in %s: collateral damage applied.", region_id)

    def _get_terrain(self, region_id: str) -> str:
        """Resolve terrain type for a region.

        Priority: explicit override → GeoDataFrame ``terrain`` column → ``DEFAULT_TERRAIN_MAP`` → ``"Plain"``.
        """
        if region_id in self.terrain_overrides:
            return self.terrain_overrides[region_id]

        gdf = getattr(self.model, "region_gdf", None)
        if gdf is not None and "terrain" in gdf.columns:
            row = gdf[gdf["region_id"] == region_id]
            if not row.empty:
                return str(row.iloc[0]["terrain"])

        # Secondary fallback: global map
        if region_id in DEFAULT_TERRAIN_MAP:
            return DEFAULT_TERRAIN_MAP[region_id]

        return "Plain"

    def step(self) -> None:
        """Step conflict engine: resolve all current engagements."""
        self.resolve_kinetic_combat()
