"""Early warning dashboard combining OSINT sentiment and risk analysis."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def create_early_warning_dashboard(
    model: Any,
    osint_data: dict[str, list[dict[str, Any]]] | None = None,
    output_path: str | Path = "early_warning.html",
) -> Path:
    """Generate early warning dashboard combining:
    - Current sentiment scores
    - Risk assessment metrics
    - Escalation probability
    - Historical trend charts

    Parameters
    ----------
    model:
        GeopolModel that has been stepped.
    osint_data:
        Optional dict of OSINT data per region: {"UKR": [...], "RUS": [...]}
    output_path:
        Output file path (.html).

    Returns
    -------
    Path
        Path to saved dashboard file.
    """
    path = Path(output_path)

    dashboard_data = _build_dashboard_data(model, osint_data)

    html_content = _generate_dashboard_html(dashboard_data)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Exported early warning dashboard to %s", path)
    return path


def _build_dashboard_data(
    model: Any,
    osint_data: dict[str, list[dict[str, Any]]] | None,
) -> dict[str, Any]:
    """Build dashboard data from model and OSINT."""
    from strategify.analysis.strategic_risk import assess_all_risks
    from strategify.osint.features import analyze_texts_sentiment

    data = {
        "step": model.schedule.steps,
        "agents": [],
        "risk_summary": {},
        "sentiment_summary": {},
    }

    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown").upper()
        posture = getattr(agent, "posture", None)
        posture_str = posture.value if hasattr(posture, "value") else str(posture)

        agent_info = {
            "id": rid,
            "posture": posture_str,
            "personality": getattr(agent, "personality", "Unknown"),
        }

        caps = getattr(agent, "capabilities", {})
        agent_info["military"] = caps.get("military", 0)
        agent_info["economic"] = caps.get("economic", 0)

        data["agents"].append(agent_info)

    try:
        risks = assess_all_risks(model)
        data["risk_summary"] = risks
    except Exception as exc:
        logger.warning("Risk assessment failed: %s", exc)

    if osint_data:
        for region, events in osint_data.items():
            texts = [e.get("text", "")[:200] for e in events[:10]]
            if texts:
                sentiment = analyze_texts_sentiment(texts)
                data["sentiment_summary"][region.upper()] = sentiment

    return data


def _generate_dashboard_html(data: dict[str, Any]) -> str:
    """Generate HTML dashboard."""
    agents_json = json.dumps(data["agents"])
    risks_json = json.dumps(data.get("risk_summary", {}))
    sentiment_json = json.dumps(data.get("sentiment_summary", {}))

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Strategify Early Warning Dashboard</title>
    <style>
        body {font - family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #0d1117; color: #c9d1d9; }
        h1, h2 {{ color: #58a6ff; }}
        .header {{ padding: 20px; border-bottom: 1px solid #30363d; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }}
        .card h3 {{ margin-top: 0; color: #8b949e; }}
        .agent {{ display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #30363d; }}
        .agent:last-child {{ border-bottom: none; }}
        .posture-escalate {{ color: #f85149; font-weight: bold; }}
        .posture-deescalate {{ color: #3fb950; }}
        .posture-maintain {{ color: #d29922; }}
        .risk-high {{ color: #f85149; }}
        .risk-medium {{ color: #d29922; }}
        .risk-low {{ color: #3fb950; }}
        .metric {{ display: inline-block; width: 45%; margin: 5px 0; }}
        .metric-label {{ color: #8b949e; }}
        .metric-value {{ font-weight: bold; }}
        .tension-bar {{ height: 20px; background: #30363d; border-radius: 4px; overflow: hidden; }}
        .tension-fill {{ height: 100%; transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Strategify Early Warning Dashboard</h1>
        <p>Simulation Step: {data["step"]}</p>
    </div>
    
    <div class="grid">
        <div class="card">
            <h3>Actor Status</h3>
            <div id="agents"></div>
        </div>
        
        <div class="card">
            <h3>Risk Assessment</h3>
            <div id="risks"></div>
        </div>
        
        <div class="card">
            <h3>OSINT Sentiment</h3>
            <div id="sentiment"></div>
        </div>
    </div>

    <script>
        const agents = {agents_json};
        const risks = {risks_json};
        const sentiment = {sentiment_json};
        
        // Render agents
        let agentHtml = '';
        for (const a of agents) {{
            const postureClass = 'posture-' + a.posture.toLowerCase();
            agentHtml += '<div class="agent">';
            agentHtml += '<span>' + a.id + '</span>';
            agentHtml += '<span class="' + postureClass + '">' + a.posture + '</span>';
            agentHtml += '<span>' + (a.military || 0).toFixed(2) + '</span>';
            agentHtml += '</div>';
        }}
        document.getElementById('agents').innerHTML = agentHtml;
        
        // Render risks
        let riskHtml = '';
        for (const [rid, r] of Object.entries(risks)) {{
            const level = (r.risk_level || 'unknown').toLowerCase();
            const levelClass = 'risk-' + (level === 'high' ? 'high' : level === 'medium' ? 'medium' : 'low');
            riskHtml += '<div class="agent">';
            riskHtml += '<span>' + rid + '</span>';
            riskHtml += '<span class="' + levelClass + '">' + (r.risk_level || 'N/A') + '</span>';
            riskHtml += '<span>' + ((r.threat_score || 0).toFixed(2)) + '</span>';
            riskHtml += '</div>';
        }}
        if (!riskHtml) riskHtml = '<p>No risk data available</p>';
        document.getElementById('risks').innerHTML = riskHtml;
        
        // Render sentiment
        let sentHtml = '';
        for (const [rid, s] of Object.entries(sentiment)) {{
            const tension = (s.tension_score || 0) * 100;
            const barColor = tension > 60 ? '#f85149' : tension > 30 ? '#d29922' : '#3fb950';
            sentHtml += '<div style="margin-bottom: 10px;">';
            sentHtml += '<div><strong>' + rid + '</strong>: ' + (s.overall_sentiment || 'neutral') + '</div>';
            sentHtml += '<div class="tension-bar"><div class="tension-fill" style="width:' + tension + '%; background:' + barColor + ';"></div></div>';
            sentHtml += '<div class="metric-label">Tension: ' + tension.toFixed(0) + '%</div>';
            sentHtml += '</div>';
        }}
        if (!sentHtml) sentHtml = '<p>No OSINT data available</p>';
        document.getElementById('sentiment').innerHTML = sentHtml;
    </script>
</body>
</html>"""
