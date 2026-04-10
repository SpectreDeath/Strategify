"""Export suite: publication-ready output formats.

Supports exporting simulation data and visualizations to multiple formats:
- CSV for data tables
- GeoJSON for spatial data
- GEXF for Gephi network analysis
- LaTeX tables for papers
- SVG/PNG charts via matplotlib
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import networkx as nx

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
        results["svg_escalation"] = export_chart_svg(model, output_dir / "escalation.svg", "escalation")
        results["svg_diplomacy"] = export_chart_svg(model, output_dir / "diplomacy.svg", "diplomacy")
    except ImportError:
        logger.warning("matplotlib not available, skipping SVG export")

    return results


def export_gexf(
    model: Any,
    path: str | Path = "diplomacy_network.gexf",
) -> Path:
    """Export diplomacy network to GEXF format for Gephi.

    GEXF (Graph Exchange XML Format) enables advanced network analysis in Gephi:
    - ForceAtlas2, Yifan Hu layout algorithms
    - Community detection with visual clustering
    - Centrality metrics (betweenness, degree, PageRank)
    - Temporal evolution analysis
    - Export to PDF/SVG/PNG for reports

    Parameters
    ----------
    model:
        GeopolModel with diplomacy_graph attribute.
    path:
        Output GEXF file path.

    Returns
    -------
    Path
        Path to saved GEXF file.
    """
    import networkx as nx

    path = Path(path)

    if not hasattr(model, "diplomacy_graph") or model.diplomacy_graph is None:
        logger.warning("No diplomacy_graph found, building from relations")
        G = _build_diplomacy_graph(model)
    else:
        G = model.diplomacy_graph

    _add_node_attributes(G, model)
    _add_edge_attributes(G, model)

    nx.write_gexf(G, str(path))
    logger.info("Exported GEXF to %s", path)
    return path


def _build_diplomacy_graph(model: Any) -> nx.Graph:
    """Build NetworkX graph from model relations."""
    import networkx as nx

    G = nx.Graph()

    agents = list(model.schedule.agents)
    for agent in agents:
        rid = getattr(agent, "region_id", f"agent_{agent.unique_id}")
        G.add_node(agent.unique_id, label=rid.upper())

    for i, a in enumerate(agents):
        for j, b in enumerate(agents):
            if i < j:
                weight = model.relations.get_relation(a.unique_id, b.unique_id)
                if weight != 0:
                    G.add_edge(a.unique_id, b.unique_id, weight=weight)

    return G


def _add_node_attributes(G: nx.Graph, model: Any) -> None:
    """Add node attributes from agent capabilities and state."""
    agents = list(model.schedule.agents)
    agent_map = {a.unique_id: a for a in agents}

    for node_id in G.nodes():
        if node_id in agent_map:
            agent = agent_map[node_id]
            posture = getattr(agent, "posture", None)
            G.nodes[node_id]["posture"] = posture.value if hasattr(posture, "value") else str(posture)
            G.nodes[node_id]["personality"] = getattr(agent, "personality", "Unknown")

            caps = getattr(agent, "capabilities", {})
            G.nodes[node_id]["military"] = caps.get("military", 0)
            G.nodes[node_id]["economic"] = caps.get("economic", 0)
            G.nodes[node_id]["diplomatic"] = caps.get("diplomatic", 0)
            G.nodes[node_id]["informational"] = caps.get("informational", 0)


def _add_edge_attributes(G: nx.Graph, model: Any) -> None:
    """Add edge attributes from relations."""
    for u, v in G.edges():
        weight = model.relations.get_relation(u, v)
        G.edges[u, v]["weight"] = weight
        G.edges[u, v]["relation_type"] = "alliance" if weight > 0 else "rivalry" if weight < 0 else "neutral"


def export_diplomacy_snapshot(
    model: Any,
    output_dir: str | Path = "gephi_snapshots",
    step: int | None = None,
) -> Path:
    """Export a diplomacy network snapshot for Gephi with optional timestep.

    Parameters
    ----------
    model:
        GeopolModel that has been stepped.
    output_dir:
        Directory for output files.
    step:
        Simulation step number (uses model.schedule.steps if None).

    Returns
    -------
    Path
        Path to saved GEXF file.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    step = step if step is not None else model.schedule.steps
    filename = f"diplomacy_step{step:04d}.gexf"

    return export_gexf(model, output_dir / filename)


def export_animation(
    model_history: list[Any],
    output_path: str | Path = "simulation_animation.gif",
    fps: int = 2,
) -> Path:
    """Export simulation as animated GIF.

    Parameters
    ----------
    model_history:
        List of GeopolModel states at each timestep.
    output_path:
        Output file path (.gif).
    fps:
        Frames per second.

    Returns
    -------
    Path
        Path to saved animation file.
    """
    import matplotlib.pyplot as plt

    path = Path(output_path)

    try:
        from PIL import Image
    except ImportError:
        logger.warning("Pillow not available, cannot create animation")
        return path

    frames = []

    for i, model in enumerate(model_history):
        fig, ax = plt.subplots(figsize=(8, 4))

        agents = list(model.schedule.agents)
        postures = [
            getattr(a, "posture", "Deescalate").value if hasattr(getattr(a, "posture", None), "value") else "Unknown"
            for a in agents
        ]

        posture_counts = {"Escalate": 0, "Deescalate": 0, "Maintain": 0}
        for p in postures:
            if p in posture_counts:
                posture_counts[p] += 1

        ax.bar(posture_counts.keys(), posture_counts.values(), color=["red", "green", "blue"])
        ax.set_title(f"Step {i}")
        ax.set_ylim(0, len(agents) + 1)

        fig.canvas.draw()
        image = Image.frombytes("RGB", fig.canvas.get_width_height(), fig.canvas.tostring_rgb())
        frames.append(image)
        plt.close(fig)

    if frames:
        frames[0].save(
            str(path),
            save_all=True,
            append_images=frames[1:],
            duration=1000 // fps,
            loop=0,
        )
        logger.info("Exported animation to %s", path)

    return path


def export_chart_png(
    model: Any,
    path: str | Path = "chart.png",
    chart_type: str = "escalation",
) -> Path:
    """Export a chart as PNG.

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
        Path to saved PNG file.
    """
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
                if "posture" in agent_data.columns:
                    escalation = (agent_data["posture"] == "Escalate").astype(int)
                    ax.plot(agent_data["Step"], escalation, marker="o", label=rid.upper(), linewidth=2)

            ax.set_xlabel("Step")
            ax.set_ylabel("Escalation")
            ax.set_yticks([0, 1])
            ax.set_yticklabels(["Deescalate", "Escalate"])
            ax.legend()
            ax.set_title("Escalation Trajectory")
            fig.tight_layout()
            fig.savefig(str(path), format="png")
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
        fig.savefig(str(path), format="png")
        plt.close(fig)

    logger.info("Exported PNG chart to %s", path)
    return path


def export_report_pdf(
    model: Any,
    output_path: str | Path = "simulation_report.pdf",
    include_maps: bool = True,
    include_charts: bool = True,
) -> Path:
    """Generate comprehensive PDF report with maps and charts.

    Parameters
    ----------
    model:
        GeopolModel that has been stepped.
    output_path:
        Output file path.
    include_maps:
        Include map visualizations.
    include_charts:
        Include chart visualizations.

    Returns
    -------
    Path
        Path to saved PDF file.
    """
    from matplotlib.backends.backend_pdf import PdfPages

    path = Path(output_path)

    try:
        import matplotlib.pyplot as plt

        with PdfPages(path) as pdf:
            title_fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.text(0.5, 0.5, "Strategify Simulation Report", fontsize=24, ha="center", va="center")
            ax.text(0.5, 0.4, f"Steps: {model.schedule.steps}", fontsize=16, ha="center", va="center")
            ax.text(
                0.5,
                0.35,
                f"Agents: {len(model.schedule.agents)}",
                fontsize=16,
                ha="center",
                va="center",
            )
            ax.axis("off")
            pdf.savefig(title_fig)
            plt.close(title_fig)

            if include_charts:
                chart_path = path.with_name("temp_chart.png")
                export_chart_png(model, chart_path, "escalation")
                img = plt.imread(chart_path)
                fig, ax = plt.subplots(figsize=(11, 8.5))
                ax.imshow(img)
                ax.axis("off")
                pdf.savefig(fig)
                plt.close(fig)
                chart_path.unlink()

                export_chart_png(model, chart_path, "diplomacy")
                img = plt.imread(chart_path)
                fig, ax = plt.subplots(figsize=(11, 8.5))
                ax.imshow(img)
                ax.axis("off")
                pdf.savefig(fig)
                plt.close(fig)
                chart_path.unlink()

            table_fig, ax = plt.subplots(figsize=(11, 8.5))
            ax.axis("off")
            ax.table(
                cellText=[
                    [
                        getattr(a, "region_id", "?").upper(),
                        getattr(a, "posture", "?").value if hasattr(getattr(a, "posture", None), "value") else "?",
                        getattr(a, "personality", "?"),
                    ]
                    for a in model.schedule.agents
                ],
                colLabels=["Region", "Posture", "Personality"],
                loc="center",
            )
            pdf.savefig(table_fig)
            plt.close(table_fig)

        logger.info("Exported PDF report to %s", path)
    except Exception as exc:
        logger.warning("PDF export failed: %s", exc)

    return path
