"""Shared Mesa visualization elements."""

from __future__ import annotations

from typing import TYPE_CHECKING

from mesa.visualization.modules import TextElement

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel


class ActorStatusElement(TextElement):
    """Renders each actor's region, posture, and influence as HTML."""

    def render(self, model: GeopolModel) -> str:  # type: ignore[override]
        imap = model.influence_map
        if imap is None:
            from strategify.reasoning.influence import InfluenceMap

            imap = InfluenceMap(model)
            imap.compute()

        lines: list[str] = [
            "<h3>World State</h3>",
            "<ul style='list-style-type:none; padding:0;'>",
        ]

        for rid, res in model.region_resources.items():
            cont = imap.get_contagion_level(rid)
            label = f"Region {rid.upper()}"
            lines.append(f"<li><b>{label}</b>: Resources: {res:.1f} | Contagion: {cont:.1f}</li>")

        lines.append("</ul><h3>Actor Status</h3>")

        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            net_inf = imap.get_net_influence(rid, agent.unique_id)
            allies = model.relations.get_allies(agent.unique_id)
            ally_str = f" (Allies: {allies})" if allies else ""
            personality = getattr(agent, "personality", "Unknown")
            posture = getattr(agent, "posture", "Unknown")

            lines.append(
                "<div style='margin-bottom:10px;"
                " border-left:4px solid #ccc; padding-left:10px;'>"
                f"<b>Region {rid.upper()}</b>"
                f" [{personality}] {ally_str}<br/>"
                f"Net Inf: <b>{net_inf:.2f}</b><br/>"
                f"Posture: <b>{posture}</b>"
                "</div>"
            )
        return "".join(lines)
