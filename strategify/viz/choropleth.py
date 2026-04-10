"""Headless choropleth renderer using Matplotlib.

Renders static map images of simulation state showing actor control,
influence, and escalation posture per region. Designed for batch runs,
CI pipelines, and environments without a browser.

Usage::

    from strategify.viz.choropleth import HeadlessChoropleth

    renderer = HeadlessChoropleth(model)
    renderer.render_step(step=5, output_path="step_005.png")
    renderer.render_all(output_dir="frames/")
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")  # non-interactive backend
import matplotlib.colors
import matplotlib.patheffects
import matplotlib.pyplot as plt

from strategify.config.settings import get_region_hex_color

if TYPE_CHECKING:
    from strategify.sim.model import GeopolModel

logger = logging.getLogger(__name__)

# Escalation color ramp: calm (blue) → tense (red)
_ESCALATION_CMAP = {
    "Cooperative": "#2196F3",
    "Diplomatic": "#FFC107",
    "Economic": "#FF9800",
    "Military": "#F44336",
}

_POSTURE_CMAP = {
    "Escalate": "#F44336",
    "Deescalate": "#4CAF50",
}


class HeadlessChoropleth:
    """Matplotlib-based static map renderer for simulation state.

    Collects per-region state from a GeopolModel and renders it as a
    colored polygon map. Supports multiple color modes.

    Parameters
    ----------
    model:
        The GeopolModel instance.
    color_mode:
        How to color regions. ``"posture"`` uses Escalate/Deescalate,
        ``"escalation_level"`` uses the 4-level ladder,
        ``"influence"`` uses a continuous influence gradient,
        ``"region"`` uses fixed region identity colors.
    figsize:
        Matplotlib figure size in inches.
    """

    def __init__(
        self,
        model: GeopolModel,
        color_mode: str = "posture",
        figsize: tuple[float, float] = (10, 8),
    ) -> None:
        self.model = model
        self.color_mode = color_mode
        self.figsize = figsize
        self._gdf_cache: gpd.GeoDataFrame | None = None

    def _build_gdf(self) -> gpd.GeoDataFrame:
        """Build a GeoDataFrame from the model's agents with current state."""
        records = []
        for agent in self.model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            posture = getattr(agent, "posture", "Deescalate")
            personality = getattr(agent, "personality", "Unknown")

            # Influence
            net_inf = 0.0
            if self.model.influence_map:
                net_inf = self.model.influence_map.get_net_influence(rid, agent.unique_id)

            # Escalation level
            esc_level = "Cooperative"
            if hasattr(self.model, "escalation_ladder") and self.model.escalation_ladder is not None:
                esc_level = self.model.escalation_ladder.get_level_name(agent.unique_id)

            records.append(
                {
                    "region_id": rid,
                    "geometry": agent.geometry,
                    "posture": posture,
                    "personality": personality,
                    "net_influence": net_inf,
                    "escalation_level": esc_level,
                    "military": agent.capabilities.get("military", 0.5),
                    "economic": agent.capabilities.get("economic", 0.5),
                }
            )

        return gpd.GeoDataFrame(records, crs="EPSG:4326")

    def _get_colors(self, gdf: gpd.GeoDataFrame) -> list[str]:
        """Assign fill colors based on the current color_mode."""
        if self.color_mode == "posture":
            return [_POSTURE_CMAP.get(p, "#9E9E9E") for p in gdf["posture"]]
        elif self.color_mode == "escalation_level":
            return [_ESCALATION_CMAP.get(e, "#9E9E9E") for e in gdf["escalation_level"]]
        elif self.color_mode == "influence":
            values = gdf["net_influence"].values
            if values.max() == values.min():
                return ["#9E9E9E"] * len(values)
            norm = (values - values.min()) / (values.max() - values.min())
            cmap = plt.cm.RdYlGn_r
            return [matplotlib.colors.to_hex(cmap(v)) for v in norm]
        elif self.color_mode == "region":
            return [get_region_hex_color(rid) for rid in gdf["region_id"]]
        else:
            return ["#9E9E9E"] * len(gdf)

    def render_step(
        self,
        output_path: str | Path,
        step: int | None = None,
        title: str | None = None,
        dpi: int = 150,
    ) -> Path:
        """Render the current model state as a PNG image.

        Parameters
        ----------
        output_path:
            Where to save the PNG.
        step:
            Optional step number for the title annotation.
        title:
            Optional custom title.
        dpi:
            Image resolution.

        Returns
        -------
        Path
            The saved file path.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        gdf = self._build_gdf()
        colors = self._get_colors(gdf)

        fig, ax = plt.subplots(1, 1, figsize=self.figsize)

        # Draw polygons
        for idx, row in gdf.iterrows():
            geom = row.geometry
            color = colors[idx]
            if geom.geom_type == "Polygon":
                xs, ys = geom.exterior.xy
                ax.fill(xs, ys, color=color, alpha=0.7, edgecolor="white", linewidth=1.5)
            elif geom.geom_type == "MultiPolygon":
                for part in geom.geoms:
                    xs, ys = part.exterior.xy
                    ax.fill(xs, ys, color=color, alpha=0.7, edgecolor="white", linewidth=1.5)

            # Label
            centroid = geom.centroid
            rid = row["region_id"]
            posture = row["posture"]
            label = f"{rid.upper()}\n{posture}"
            ax.annotate(
                label,
                xy=(centroid.x, centroid.y),
                ha="center",
                va="center",
                fontsize=8,
                fontweight="bold",
                color="white",
                path_effects=[matplotlib.patheffects.withStroke(linewidth=2, foreground="black")],
            )

        # Title
        if title is None:
            step_str = f"Step {step}" if step is not None else ""
            title = f"Geopol Sim — {self.color_mode.replace('_', ' ').title()} {step_str}"
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_aspect("equal")
        ax.axis("off")

        fig.tight_layout()
        fig.savefig(str(output_path), dpi=dpi, bbox_inches="tight", facecolor="white")
        plt.close(fig)

        logger.debug("Rendered choropleth to %s", output_path)
        return output_path

    def render_all(
        self,
        output_dir: str | Path,
        steps: int = 10,
        dpi: int = 150,
    ) -> list[Path]:
        """Run the model for N steps and render a frame at each step.

        Parameters
        ----------
        output_dir:
            Directory for output PNGs.
        steps:
            Number of steps to run.
        dpi:
            Image resolution.

        Returns
        -------
        list[Path]
            Paths to rendered PNGs.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        paths = []
        for step in range(steps):
            self.model.step()
            path = self.render_step(
                output_dir / f"step_{step:04d}.png",
                step=step + 1,
                dpi=dpi,
            )
            paths.append(path)

        return paths

    @staticmethod
    def render_from_csv(
        csv_path: str | Path,
        geojson_path: str | Path,
        output_dir: str | Path,
        color_mode: str = "posture",
        dpi: int = 150,
    ) -> list[Path]:
        """Render choropleth frames from a saved simulation CSV.

        Useful for post-hoc visualization without re-running the model.

        Parameters
        ----------
        csv_path:
            Path to simulation_output.csv from ``run_scenario``.
        geojson_path:
            Path to the GeoJSON with region geometries.
        output_dir:
            Directory for output PNGs.
        color_mode:
            Color mode (``"posture"`` or ``"escalation_level"``).
        dpi:
            Image resolution.

        Returns
        -------
        list[Path]
            Paths to rendered PNGs.
        """
        import pandas as pd

        csv_path = Path(csv_path)
        geojson_path = Path(geojson_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Auto-detect flat vs MultiIndex CSV format
        raw = pd.read_csv(csv_path, nrows=1)
        if "Step" in raw.columns and "AgentID" in raw.columns:
            df = pd.read_csv(csv_path)
        else:
            df = pd.read_csv(csv_path, index_col=[0, 1]).reset_index()

        regions = gpd.read_file(geojson_path)
        steps = df["Step"].unique()
        paths = []

        for step in steps:
            step_df = df[df["Step"] == step].copy()
            # step_df has columns: Step, AgentID, posture, region_id
            merged = regions.merge(step_df, on="region_id", how="left")

            fig, ax = plt.subplots(1, 1, figsize=(10, 8))

            posture_cmap = {"Escalate": "#F44336", "Deescalate": "#4CAF50"}

            for _, row in merged.iterrows():
                posture = row.get("posture", "Deescalate")
                color = posture_cmap.get(posture, "#9E9E9E")
                geom = row.geometry
                if geom.geom_type == "Polygon":
                    xs, ys = geom.exterior.xy
                    ax.fill(xs, ys, color=color, alpha=0.7, edgecolor="white", linewidth=1.5)
                elif geom.geom_type == "MultiPolygon":
                    for part in geom.geoms:
                        xs, ys = part.exterior.xy
                        ax.fill(xs, ys, color=color, alpha=0.7, edgecolor="white", linewidth=1.5)

                centroid = geom.centroid
                rid = row["region_id"]
                ax.annotate(
                    f"{rid.upper()}\n{posture}",
                    xy=(centroid.x, centroid.y),
                    ha="center",
                    va="center",
                    fontsize=8,
                    fontweight="bold",
                    color="white",
                    path_effects=[matplotlib.patheffects.withStroke(linewidth=2, foreground="black")],
                )

            ax.set_title(f"Step {step}", fontsize=12, fontweight="bold")
            ax.set_aspect("equal")
            ax.axis("off")
            fig.tight_layout()

            path = output_dir / f"step_{step:04d}.png"
            fig.savefig(str(path), dpi=dpi, bbox_inches="tight", facecolor="white")
            plt.close(fig)
            paths.append(path)

        return paths
