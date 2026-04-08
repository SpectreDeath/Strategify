"""Export suite: publication-ready output formats.

Supports exporting simulation data and visualizations to multiple formats:
- CSV for data tables
- GeoJSON for spatial data
- LaTeX tables for papers
- SVG/PNG charts via matplotlib
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def export_csv(
    model: Any,
    path: str | Path = "simulation_output.csv",
) -> Path:
    """Export simulation data to CSV.

    Parameters
    ----------
    model:
        GeopolModel with datacollector.
    path:
        Output file path.

    Returns
    -------
    Path
        Path to saved CSV file.
    """
    path = Path(path)
    df = model.datacollector.get_agent_vars_dataframe()
    df.reset_index().to_csv(str(path), index=False)
    logger.info("Exported CSV to %s", path)
    return path


def export_geojson(
    model: Any,
    path: str | Path = "simulation_output.geojson",
) -> Path:
    """Export agent geometries and state to GeoJSON.

    Parameters
    ----------
    model:
        GeopolModel with GeoSpace agents.
    path:
        Output file path.

    Returns
    -------
    Path
        Path to saved GeoJSON file.
    """
    path = Path(path)

    features = []
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        geometry = json.loads(json.dumps(agent.geometry.__geo_interface__))

        properties = {
            "region_id": rid,
            "posture": getattr(agent, "posture", "Deescalate"),
            "personality": getattr(agent, "personality", "Unknown"),
            "military": agent.capabilities.get("military", 0),
            "economic": agent.capabilities.get("economic", 0),
        }

        # Add economic data if available
        if hasattr(model, "trade_network") and model.trade_network is not None:
            properties["gdp"] = model.trade_network.get_gdp(agent.unique_id)
            properties["trade_balance"] = model.trade_network.get_trade_balance(agent.unique_id)

        # Add escalation level if available
        if hasattr(model, "escalation_ladder") and model.escalation_ladder is not None:
            properties["escalation_level"] = model.escalation_ladder.get_level_name(agent.unique_id)

        features.append(
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": properties,
            }
        )

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    with open(path, "w") as f:
        json.dump(geojson, f, indent=2)

    logger.info("Exported GeoJSON to %s", path)
    return path


def export_latex_table(
    model: Any,
    path: str | Path = "actor_table.tex",
    caption: str = "Actor Status",
    label: str = "tab:actors",
) -> Path:
    """Export actor status as a LaTeX table.

    Parameters
    ----------
    model:
        GeopolModel instance.
    path:
        Output file path.
    caption:
        Table caption.
    label:
        LaTeX label for referencing.

    Returns
    -------
    Path
        Path to saved .tex file.
    """
    path = Path(path)

    rows = []
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown").upper()
        posture = getattr(agent, "posture", "Deescalate")
        personality = getattr(agent, "personality", "Unknown")
        mil = agent.capabilities.get("military", 0)
        eco = agent.capabilities.get("economic", 0)
        rows.append(f"  {rid} & {posture} & {personality} & {mil:.2f} & {eco:.2f} \\\\")

    body = "\n".join(rows)
    table = (
        r"\begin{table}[htbp]" + "\n"
        r"\centering" + "\n"
        rf"\caption{{{caption}}}" + "\n"
        rf"\label{{{label}}}" + "\n"
        r"\begin{tabular}{lcccc}" + "\n"
        r"\toprule" + "\n"
        r"Region & Posture & Personality & Military & Economic \\" + "\n"
        r"\midrule" + "\n"
        f"{body}\n"
        r"\bottomrule" + "\n"
        r"\end{tabular}" + "\n"
        r"\end{table}" + "\n"
    )

    with open(path, "w") as f:
        f.write(table)

    logger.info("Exported LaTeX table to %s", path)
    return path


def export_chart_svg(
    model: Any,
    path: str | Path = "escalation_chart.svg",
    chart_type: str = "escalation",
) -> Path:
    """Export a chart as SVG using matplotlib.

    Parameters
    ----------
    model:
        GeopolModel that has been stepped.
    path:
        Output file path.
    chart_type:
        ``"escalation"`` for posture over time,
        ``"diplomacy"`` for diplomacy weight matrix.

    Returns
    -------
    Path
        Path to saved SVG file.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path = Path(path)

    if chart_type == "escalation":
        try:
            df = model.datacollector.get_agent_vars_dataframe()
            df_reset = df.reset_index()

            fig, ax = plt.subplots(figsize=(10, 5))
            for agent in model.schedule.agents:
                rid = getattr(agent, "region_id", "unknown")
                agent_data = df_reset[df_reset["region_id"] == rid]
                escalation = (agent_data["posture"] == "Escalate").astype(int)
                ax.plot(agent_data["Step"], escalation, marker="o", label=rid.upper(), linewidth=2)

            ax.set_xlabel("Step")
            ax.set_ylabel("Escalation")
            ax.set_yticks([0, 1])
            ax.set_yticklabels(["Deescalate", "Escalate"])
            ax.legend()
            ax.set_title("Escalation Trajectory")
            fig.tight_layout()
            fig.savefig(str(path), format="svg")
            plt.close(fig)
        except Exception as exc:
            logger.warning("Escalation chart failed: %s", exc)

    elif chart_type == "diplomacy":
        import numpy as np

        agents = list(model.schedule.agents)
        n = len(agents)
        matrix = np.zeros((n, n))
        labels = [getattr(a, "region_id", "?").upper() for a in agents]

        for i, a in enumerate(agents):
            for j, b in enumerate(agents):
                if i != j:
                    matrix[i][j] = model.relations.get_relation(a.unique_id, b.unique_id)

        fig, ax = plt.subplots(figsize=(8, 6))
        im = ax.imshow(matrix, cmap="RdYlGn", vmin=-1, vmax=1)
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(labels)
        ax.set_yticklabels(labels)
        plt.colorbar(im, label="Relation Weight")
        ax.set_title("Diplomacy Matrix")
        fig.tight_layout()
        fig.savefig(str(path), format="svg")
        plt.close(fig)

    logger.info("Exported SVG chart to %s", path)
    return path


def export_all(
    model: Any,
    output_dir: str | Path = "export",
) -> dict[str, Path]:
    """Export all formats to a directory.

    Parameters
    ----------
    model:
        GeopolModel that has been stepped.
    output_dir:
        Directory for output files.

    Returns
    -------
    dict
        ``{format: path}`` for each exported file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}
    results["csv"] = export_csv(model, output_dir / "simulation.csv")
    results["geojson"] = export_geojson(model, output_dir / "simulation.geojson")
    results["latex"] = export_latex_table(model, output_dir / "actors.tex")

    try:
        results["svg_escalation"] = export_chart_svg(
            model, output_dir / "escalation.svg", "escalation"
        )
        results["svg_diplomacy"] = export_chart_svg(
            model, output_dir / "diplomacy.svg", "diplomacy"
        )
    except ImportError:
        logger.warning("matplotlib not available, skipping SVG export")

    return results
