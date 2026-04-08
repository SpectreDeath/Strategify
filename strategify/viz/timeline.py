"""Timeline visualization for conflict events over time."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_timeline(
    model_history: list[Any],
    output_path: str | Path = "conflict_timeline.html",
) -> Path:
    """Export interactive timeline of conflicts and events.

    Creates a standalone HTML timeline showing escalation levels,
    diplomatic relations, and key events across simulation steps.

    Parameters
    ----------
    model_history:
        List of GeopolModel states at each timestep.
    output_path:
        Output file path (.html).

    Returns
    -------
    Path
        Path to saved timeline file.
    """
    path = Path(output_path)

    timeline_data = _build_timeline_data(model_history)

    html_content = _generate_timeline_html(timeline_data)

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("Exported timeline to %s", path)
    return path


def _build_timeline_data(model_history: list[Any]) -> dict[str, Any]:
    """Build timeline data from model history."""
    steps_data = []

    for step, model in enumerate(model_history):
        step_info = {
            "step": step,
            "agents": [],
            "diplomacy": {},
        }

        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            posture = getattr(agent, "posture", None)
            posture_str = posture.value if hasattr(posture, "value") else str(posture)

            step_info["agents"].append(
                {
                    "id": rid.upper(),
                    "posture": posture_str,
                    "personality": getattr(agent, "personality", "Unknown"),
                }
            )

        if hasattr(model, "relations"):
            agents = list(model.schedule.agents)
            for i, a in enumerate(agents):
                for j, b in enumerate(agents):
                    if i < j:
                        rid_a = getattr(a, "region_id", f"agent_{a.unique_id}").upper()
                        rid_b = getattr(b, "region_id", f"agent_{b.unique_id}").upper()
                        weight = model.relations.get_relation(a.unique_id, b.unique_id)
                        if weight != 0:
                            step_info["diplomacy"][f"{rid_a}-{rid_b}"] = weight

        steps_data.append(step_info)

    return {"steps": steps_data}


def _generate_timeline_html(timeline_data: dict[str, Any]) -> str:
    """Generate HTML timeline from data."""
    steps = timeline_data["steps"]

    steps_json = json.dumps(steps)

    return (
        """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Strategify Conflict Timeline</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }
        h1 { color: #00d4ff; }
        .controls { margin: 20px 0; }
        button { padding: 10px 20px; font-size: 14px; cursor: pointer; background: #00d4ff; border: none; border-radius: 4px; color: #1a1a2e; }
        button:hover { background: #00b8e6; }
        #timeline { display: flex; flex-direction: column; gap: 10px; }
        .step { background: #16213e; padding: 15px; border-radius: 8px; }
        .step-header { font-size: 18px; font-weight: bold; color: #00d4ff; margin-bottom: 10px; }
        .agents { display: flex; flex-wrap: wrap; gap: 10px; }
        .agent { padding: 5px 10px; border-radius: 4px; font-size: 12px; }
        .escalate { background: #ff4757; color: white; }
        .deescalate { background: #2ed573; color: #1a1a2e; }
        .maintain { background: #ffa502; color: #1a1a2e; }
        .unknown { background: #747d8c; color: white; }
        .diplomacy { margin-top: 10px; font-size: 12px; color: #a4b0be; }
    </style>
</head>
<body>
    <h1>Strategify Conflict Timeline</h1>
    <div class="controls">
        <button onclick="prevStep()">Previous</button>
        <button onclick="nextStep()">Next</button>
        <span id="step-indicator">Step: 0 / """
        + str(len(steps) - 1)
        + """</span>
    </div>
    <div id="timeline"></div>

    <script>
        const steps = """
        + steps_json
        + """;
        let currentStep = 0;

        function renderStep(stepIndex) {
            const step = steps[stepIndex];
            const container = document.getElementById('timeline');
            
            let html = '<div class="step"><div class="step-header">Step ' + stepIndex + '</div><div class="agents">';
            
            for (const agent of step.agents) {
                const postureClass = agent.posture.toLowerCase();
                html += '<span class="agent ' + postureClass + '">' + agent.id + ': ' + agent.posture + '</span>';
            }
            
            html += '</div>';
            
            if (Object.keys(step.diplomacy).length > 0) {
                html += '<div class="diplomacy">';
                for (const [pair, weight] of Object.entries(step.diplomacy)) {
                    const type = weight > 0 ? 'Alliance' : 'Rivalry';
                    html += '<span>' + pair + ': ' + type + ' (' + weight.toFixed(2) + ')</span> ';
                }
                html += '</div>';
            }
            
            html += '</div>';
            container.innerHTML = html;
            document.getElementById('step-indicator').textContent = 'Step: ' + stepIndex + ' / ' + (steps.length - 1);
        }

        function nextStep() {
            if (currentStep < steps.length - 1) {
                currentStep++;
                renderStep(currentStep);
            }
        }

        function prevStep() {
            if (currentStep > 0) {
                currentStep--;
                renderStep(currentStep);
            }
        }

        renderStep(0);
    </script>
</body>
</html>"""
    )
