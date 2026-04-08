"""Automated report generation: HTML reports with maps, charts, and summaries.

Generates self-contained HTML reports from simulation runs combining
maps, network graphs, time series charts, and narrative summaries.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def generate_report(
    model: Any,
    output_path: str | Path = "simulation_report.html",
    title: str = "Geopolitical Simulation Report",
    include_map: bool = True,
    include_network: bool = True,
    include_alerts: bool = True,
) -> Path:
    """Generate an HTML report from the current simulation state.

    Parameters
    ----------
    model:
        A GeopolModel that has been stepped.
    output_path:
        Where to save the HTML report.
    title:
        Report title.
    include_map:
        Whether to embed the Folium map.
    include_network:
        Whether to embed the diplomacy network.
    include_alerts:
        Whether to run and include early warning analysis.

    Returns
    -------
    Path
        Path to the saved report.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sections = []

    # Header
    timestamp = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    scenario = getattr(model, "scenario_name", "default")
    n_agents = len(model.schedule.agents)

    sections.append(f"""
    <div class="header">
        <h1>{title}</h1>
        <p>Scenario: <strong>{scenario}</strong> |
           Agents: <strong>{n_agents}</strong> |
           Generated: {timestamp}</p>
    </div>
    """)

    # Actor summary
    sections.append(_generate_actor_summary(model))

    # Escalation ladder
    if hasattr(model, "escalation_ladder") and model.escalation_ladder is not None:
        sections.append(_generate_escalation_summary(model))

    # Economics
    if hasattr(model, "trade_network") and model.trade_network is not None:
        sections.append(_generate_economic_summary(model))

    # Diplomacy
    sections.append(_generate_diplomacy_summary(model))

    # Early warning
    if include_alerts:
        sections.append(_generate_alert_section(model))

    # Data summary
    sections.append(_generate_data_summary(model))

    # Build HTML
    html = _wrap_html(title, "\n".join(sections))

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    logger.info("Report saved to %s", output_path)
    return output_path


def _wrap_html(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
       max-width: 900px; margin: 0 auto; padding: 20px; background: #fafafa; }}
.header {{
    background: #1a237e; color: white; padding: 20px;
    border-radius: 8px; margin-bottom: 20px;
}}
.header h1 {{ margin: 0 0 8px 0; }}
.header p {{ margin: 0; opacity: 0.9; }}
.section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 16px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
.section h2 {{
    margin-top: 0; color: #1a237e;
    border-bottom: 2px solid #e8eaf6; padding-bottom: 8px;
}}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ text-align: left; padding: 8px 12px; border-bottom: 1px solid #e0e0e0; }}
th {{ background: #f5f5f5; font-weight: 600; }}
.alert-watch {{ color: #f57f17; font-weight: bold; }}
.alert-warning {{ color: #e65100; font-weight: bold; }}
.alert-critical {{ color: #b71c1c; font-weight: bold; }}
.badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; }}
.badge-escalate {{ background: #ffebee; color: #c62828; }}
.badge-deescalate {{ background: #e8f5e9; color: #2e7d32; }}
</style>
</head>
<body>
{body}
</body>
</html>"""


def _generate_actor_summary(model: Any) -> str:
    rows = []
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        posture = getattr(agent, "posture", "Deescalate")
        personality = getattr(agent, "personality", "Unknown")
        military = agent.capabilities.get("military", 0)
        economic = agent.capabilities.get("economic", 0)
        badge_class = "badge-escalate" if posture == "Escalate" else "badge-deescalate"

        rows.append(f"""
        <tr>
            <td><strong>{rid.upper()}</strong></td>
            <td><span class="badge {badge_class}">{posture}</span></td>
            <td>{personality}</td>
            <td>{military:.2f}</td>
            <td>{economic:.2f}</td>
        </tr>""")

    return f"""
    <div class="section">
        <h2>Actor Status</h2>
        <table>
            <tr><th>Region</th><th>Posture</th><th>Personality</th><th>Military</th><th>Economic</th></tr>
            {"".join(rows)}
        </table>
    </div>"""


def _generate_escalation_summary(model: Any) -> str:
    ladder = model.escalation_ladder
    rows = []
    for rid, data in ladder.summary().items():
        rows.append(f"""
        <tr>
            <td>{rid.upper()}</td>
            <td>{data["level"]}</td>
            <td>{data["numeric"]}</td>
            <td>{data["total_cost"]:.3f}</td>
        </tr>""")

    return f"""
    <div class="section">
        <h2>Escalation Ladder</h2>
        <table>
            <tr><th>Region</th><th>Level</th><th>Numeric</th><th>Total Cost</th></tr>
            {"".join(rows)}
        </table>
    </div>"""


def _generate_economic_summary(model: Any) -> str:
    tn = model.trade_network
    rows = []
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        gdp = tn.get_gdp(agent.unique_id)
        balance = tn.get_trade_balance(agent.unique_id)
        total = tn.get_total_trade(agent.unique_id)
        rows.append(f"""
        <tr>
            <td>{rid.upper()}</td>
            <td>{gdp:.3f}</td>
            <td>{balance:+.3f}</td>
            <td>{total:.3f}</td>
        </tr>""")

    return f"""
    <div class="section">
        <h2>Economic Overview</h2>
        <table>
            <tr><th>Region</th><th>GDP</th><th>Trade Balance</th><th>Total Trade</th></tr>
            {"".join(rows)}
        </table>
    </div>"""


def _generate_diplomacy_summary(model: Any) -> str:
    edges = []
    for u, v, data in model.relations.graph.edges(data=True):
        weight = data.get("weight", 0)
        if weight > 0.3:
            rel = "Alliance"
        elif weight < -0.3:
            rel = "Rivalry"
        else:
            rel = "Neutral"
        edges.append(
            f"<li>Agent {u} &mdash; Agent {v}: <strong>{rel}</strong> ({weight:+.1f})</li>"
        )

    return f"""
    <div class="section">
        <h2>Diplomatic Relations</h2>
        <ul>{"".join(edges) if edges else "<li>No relations defined</li>"}</ul>
    </div>"""


def _generate_alert_section(model: Any) -> str:
    try:
        from strategify.analysis.alerts import run_early_warning
        from strategify.analysis.timeseries import prepare_agent_timeseries

        df = model.datacollector.get_agent_vars_dataframe()
        ts = prepare_agent_timeseries(df)
        report = run_early_warning(ts, current_step=len(ts) - 1)
    except Exception:
        return ""

    if report["alert_count"] == 0:
        return """
        <div class="section">
            <h2>Early Warning</h2>
            <p>No alerts detected.</p>
        </div>"""

    alerts_html = []
    for alert in report["spikes"] + report["reversals"] + report["contagion"]:
        level_class = f"alert-{alert['level']}"
        alerts_html.append(
            f'<li class="{level_class}">{alert["type"]}: '
            f"{alert.get('region', alert.get('regions', 'N/A'))} "
            f"(step {alert['step']}) [{alert['level']}]</li>"
        )

    return f"""
    <div class="section">
        <h2>Early Warning ({report["alert_count"]} alerts)</h2>
        <p>Overall level: <strong class="alert-{report["overall_level"]}">
            {report["overall_level"].upper()}</strong></p>
        <ul>{"".join(alerts_html)}</ul>
    </div>"""


def _generate_data_summary(model: Any) -> str:
    try:
        df = model.datacollector.get_agent_vars_dataframe()
        n_records = len(df)
    except Exception:
        n_records = 0

    steps = model.schedule.steps if hasattr(model, "schedule") else 0

    return f"""
    <div class="section">
        <h2>Data Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Steps completed</td><td>{steps}</td></tr>
            <tr><td>Data records</td><td>{n_records}</td></tr>
            <tr><td>Agents</td><td>{len(model.schedule.agents)}</td></tr>
            <tr><td>Diplomacy edges</td><td>{model.relations.graph.number_of_edges()}</td></tr>
        </table>
    </div>"""
