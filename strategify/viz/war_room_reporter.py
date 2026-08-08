"""Automated Strategic War-Room Executive Report Generator.

Synthesizes multi-domain wargame states, LLM agent swarm transcripts,
counterfactual branch comparisons, and optimal control benchmarks into
standalone executive HTML war-room briefings.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategify.osint.live_feed import StrategifyLiveFeed
from strategify.reasoning.swarm import StrategifySwarm
from strategify.sim.counterfactual import CounterfactualSimulator
from strategify.sim.wargame import MultiDomainWargameEngine

logger = logging.getLogger(__name__)


@dataclass
class ExecutiveReportPayload:
    """Structured data payload representing an executive war-room report."""

    title: str
    actor_id: str
    threat_level: str
    readiness_score: float
    infection_cases: float
    gdp_growth_pct: float
    diplomatic_tension: float
    swarm_consensus_score: float
    swarm_proposals: list[dict[str, Any]]
    counterfactual_branches: dict[str, dict[str, Any]]
    html_content: str


class StrategifyWarRoomReporter:
    """Engine compiling comprehensive war-room intelligence reports."""

    def __init__(self, actor_id: str = "BlueLand") -> None:
        self.actor_id = actor_id

    def generate_report(self, steps: int = 3) -> ExecutiveReportPayload:
        """Generate a complete executive war-room report.

        Parameters
        ----------
        steps : int
            Wargame simulation steps.

        Returns
        -------
        ExecutiveReportPayload
            Report data payload with HTML string.
        """
        logger.info("Generating Strategic War-Room Executive Briefing for %s...", self.actor_id)

        # 1. Gather Multi-Domain State & Ingest OSINT
        feed = StrategifyLiveFeed()
        events = feed.fetch_live_events()

        engine = MultiDomainWargameEngine()
        snap = feed.calibrate_snapshot(engine.get_state_snapshot(), events, actor_id=self.actor_id)

        # 2. Run Swarm Deliberations
        swarm = StrategifySwarm(actor_id=self.actor_id)
        swarm_res = swarm.deliberate_step(engine)

        # 3. Simulate Counterfactual Branches
        sim = CounterfactualSimulator(actor_id=self.actor_id)
        branches = sim.simulate_branches(snap, steps=steps)

        # 4. Synthesize Metrics
        readiness = snap.military_readiness.get(self.actor_id, 100.0)
        infections = snap.epidemic_infections.get(self.actor_id, 0.0)
        gdp = snap.gdp_growth_rate.get(self.actor_id, 0.02)
        tension = snap.diplomatic_tensions

        threat_level = "CRITICAL" if tension > 0.6 or infections > 50.0 else "ELEVATED"

        # 5. Render Standalone HTML Document
        html_str = self._render_html_report(
            actor_id=self.actor_id,
            threat_level=threat_level,
            readiness=readiness,
            infections=infections,
            gdp=gdp,
            tension=tension,
            swarm_res=swarm_res,
            branches=branches,
            events=events,
        )

        return ExecutiveReportPayload(
            title=f"Executive War-Room Briefing: {self.actor_id}",
            actor_id=self.actor_id,
            threat_level=threat_level,
            readiness_score=readiness,
            infection_cases=infections,
            gdp_growth_pct=gdp * 100,
            diplomatic_tension=tension,
            swarm_consensus_score=swarm_res.consensus_score,
            swarm_proposals=[p.__dict__ for p in swarm_res.proposals],
            counterfactual_branches={k: v.__dict__ for k, v in branches.items()},
            html_content=html_str,
        )

    def _render_html_report(
        self,
        actor_id: str,
        threat_level: str,
        readiness: float,
        infections: float,
        gdp: float,
        tension: float,
        swarm_res: Any,
        branches: dict[str, Any],
        events: list[Any],
    ) -> str:
        """Render dark-mode executive briefing HTML document."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Strategify War-Room Briefing - {actor_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', system-ui, sans-serif;
            background: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 30px;
        }}
        .header {{
            border-bottom: 2px solid #38bdf8;
            padding-bottom: 15px;
            margin-bottom: 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .header h1 {{ margin: 0; color: #38bdf8; font-size: 2rem; }}
        .badge {{
            background: #ef4444;
            color: white;
            padding: 6px 14px;
            border-radius: 9999px;
            font-weight: bold;
            font-size: 0.9rem;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #1e293b;
            padding: 18px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .card h4 {{ margin: 0 0 8px 0; color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }}
        .card .val {{ font-size: 1.6rem; font-weight: bold; color: #34d399; }}
        .section {{ margin-bottom: 30px; }}
        .section h2 {{ color: #38bdf8; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        th, td {{ padding: 12px; border: 1px solid #334155; text-align: left; }}
        th {{ background: #1e293b; color: #94a3b8; }}
        .proposal-card {{
            background: #1e293b;
            border-left: 4px solid #38bdf8;
            padding: 12px 18px;
            margin-bottom: 10px;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>STRATEGIFY EXECUTIVE WAR-ROOM BRIEFING</h1>
            <small>Actor: {actor_id} | Real-Time Multi-Domain Analysis</small>
        </div>
        <span class="badge">THREAT: {threat_level}</span>
    </div>

    <div class="grid">
        <div class="card">
            <h4>Military Readiness</h4>
            <div class="val">{readiness:.1f}%</div>
        </div>
        <div class="card">
            <h4>Infection Cases</h4>
            <div class="val" style="color:#f87171;">{infections:.1f}</div>
        </div>
        <div class="card">
            <h4>Quarterly GDP Growth</h4>
            <div class="val">{gdp * 100:.2f}%</div>
        </div>
        <div class="card">
            <h4>Diplomatic Tension</h4>
            <div class="val" style="color:#fbbf24;">{tension:.2f}</div>
        </div>
    </div>

    <div class="section">
        <h2>Autonomous LLM Agent Swarm Deliberations (Consensus: {swarm_res.consensus_score * 100:.1f}%)</h2>
        {"".join(f'<div class="proposal-card"><strong>[{p.domain}] {p.persona_name}:</strong> {p.recommended_action}<br><small style="color:#94a3b8;">Reasoning: {p.reasoning_chain}</small></div>' for p in swarm_res.proposals)}
    </div>

    <div class="section">
        <h2>Counterfactual Branch Scenario Divergence</h2>
        <table>
            <thead>
                <tr>
                    <th>Branch</th>
                    <th>Description</th>
                    <th>Readiness</th>
                    <th>Infections</th>
                    <th>GDP Growth</th>
                    <th>Divergence Score</th>
                </tr>
            </thead>
            <tbody>
                {"".join(f"<tr><td><strong>{b.branch_name}</strong></td><td>{b.description}</td><td>{b.final_readiness:.1f}%</td><td>{b.final_infections:.1f}</td><td>{b.final_gdp_growth * 100:.2f}%</td><td>{b.divergence_score:.2f}</td></tr>" for b in branches.values())}
            </tbody>
        </table>
    </div>
</body>
</html>"""

    def export_html(self, output_path: str = "war_room_brief.html", steps: int = 3) -> str:
        """Export executive report as standalone HTML file.

        Parameters
        ----------
        output_path : str
            Output file path.
        steps : int
            Wargame steps.

        Returns
        -------
        str
            Absolute file path.
        """
        payload = self.generate_report(steps=steps)
        out_file = Path(output_path)
        out_file.write_text(payload.html_content, encoding="utf-8")
        logger.info("Exported War-Room Report to: %s", out_file.resolve())
        return str(out_file.resolve())
