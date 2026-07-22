"""Interactive Epidemic Trajectory & Spatial Heatmap Plotter.

Renders multi-panel control trajectory curves (S, I, R, u(t)) and spatial
node infection heatmaps for visualization and reporting.
"""

from __future__ import annotations

import base64
import io
import logging

import matplotlib

matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

logger = logging.getLogger(__name__)


class EpidemicPlotter:
    """Plotting engine for epidemic trajectories and spatial node heatmaps."""

    def render_trajectory_plot(
        self,
        t: np.ndarray | list[float],
        susceptible: np.ndarray | list[float],
        infected: np.ndarray | list[float],
        recovered: np.ndarray | list[float],
        control_u: np.ndarray | list[float] | None = None,
        title: str = "Epidemic Compartment & Control Trajectories",
    ) -> str:
        """Render multi-panel epidemic compartment and intervention trajectory plot.

        Parameters
        ----------
        t : np.ndarray | list[float]
            Time array.
        susceptible : np.ndarray | list[float]
            S(t) array.
        infected : np.ndarray | list[float]
            I(t) array.
        recovered : np.ndarray | list[float]
            R(t) array.
        control_u : np.ndarray | list[float] | None
            Optional u(t) intervention control array.
        title : str
            Chart title.

        Returns
        -------
        str
            Base64-encoded PNG image payload.
        """
        fig, ax1 = plt.subplots(figsize=(8, 4.5))

        t_arr = np.array(t)
        ax1.plot(t_arr, susceptible, label="Susceptible", color="#1f77b4", linewidth=2)
        ax1.plot(t_arr, infected, label="Infected", color="#d62728", linewidth=2)
        ax1.plot(t_arr, recovered, label="Recovered", color="#2ca02c", linewidth=2)
        ax1.set_xlabel("Time (Days)")
        ax1.set_ylabel("Population Fraction")
        ax1.set_ylim(0.0, 1.05)
        ax1.grid(True, linestyle="--", alpha=0.5)

        if control_u is not None:
            ax2 = ax1.twinx()
            u_arr = np.array(control_u)
            ax2.plot(t_arr, u_arr, label="NPI Intervention u(t)", color="#ff7f0e", linestyle=":", linewidth=2.5)
            ax2.set_ylabel("Control Effort u(t)")
            ax2.set_ylim(0.0, 1.05)

        plt.title(title)
        fig.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)

        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        logger.info("EpidemicPlotter rendered trajectory plot '%s' (Base64 size: %d)", title, len(img_b64))
        return img_b64

    def render_spatial_node_heatmap(
        self,
        infected_matrix: np.ndarray,
        node_names: list[str] | None = None,
        title: str = "Spatial Node Infection Heatmap Over Time",
    ) -> str:
        """Render spatial node infection heatmap across time.

        Parameters
        ----------
        infected_matrix : np.ndarray
            Shape: (num_time_points, num_nodes).
        node_names : list[str] | None
            Optional node names.
        title : str
            Heatmap title.

        Returns
        -------
        str
            Base64-encoded PNG image payload.
        """
        fig, ax = plt.subplots(figsize=(8, 4))
        im = ax.imshow(infected_matrix.T, aspect="auto", cmap="YlOrRd", origin="lower")
        plt.colorbar(im, ax=ax, label="Infection Density")

        ax.set_xlabel("Time Steps")
        ax.set_ylabel("Spatial Graph Nodes")

        if node_names:
            ax.set_yticks(range(len(node_names)))
            ax.set_yticklabels(node_names)

        plt.title(title)
        fig.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)

        img_b64 = base64.b64encode(buf.read()).decode("utf-8")
        logger.info("EpidemicPlotter rendered spatial heatmap '%s' (Base64 size: %d)", title, len(img_b64))
        return img_b64
