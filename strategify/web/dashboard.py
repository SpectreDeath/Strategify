"""Streamlit dashboard for interactive geopolitical simulation.

Provides a unified web interface with:
- Interactive map visualization
- Diplomacy network graph
- Real-time simulation controls (play/pause/step/speed)
- Scenario editor (define actors, alliances, capabilities)
- Time series and analysis charts
- Export controls

Usage::

    streamlit run -m strategify.web.dashboard
    # or programmatically:
    from strategify.web.dashboard import run_dashboard
    run_dashboard()
"""

from __future__ import annotations

import json
import logging
import tempfile
import time
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def _apply_custom_styles(st) -> None:
    """Apply custom CSS for improved styling."""
    st.markdown(
        """
        <style>
        /* Dark mode enhancements */
        .stApp {
            background: linear-gradient(135deg, #0f1419 0%, #1a2332 100%);
        }

        /* Card styling */
        .metric-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        }

        /* Agent status badges */
        .status-escalate {
            background: #ff4757;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
        }
        .status-deescalate {
            background: #2ed573;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-weight: bold;
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 12px 20px;
            border-radius: 8px 8px 0 0;
            background: rgba(255,255,255,0.05);
        }
        .stTabs [aria-selected="true"] {
            background: rgba(59,130,246,0.2);
            border-bottom: 3px solid #3b82f6;
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: rgba(0,0,0,0.3);
            border-right: 1px solid rgba(255,255,255,0.1);
        }

        /* Button enhancements */
        .stButton > button {
            border-radius: 8px;
            transition: all 0.2s ease;
        }
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }

        /* Alert styling */
        .alert-critical {
            background: rgba(255,71,87,0.15);
            border: 1px solid #ff4757;
            border-radius: 8px;
            padding: 12px;
            color: #ff6b81;
        }
        .alert-warning {
            background: rgba(255,165,2,0.15);
            border: 1px solid #ffa502;
            border-radius: 8px;
            padding: 12px;
            color: #ffbe76;
        }
        .alert-watch {
            background: rgba(46,213,115,0.15);
            border: 1px solid #2ed573;
            border-radius: 8px;
            padding: 12px;
            color: #7bed9f;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def run_dashboard() -> None:
    """Launch the Streamlit dashboard.

    This function is the main entry point for the web dashboard.
    It initializes Streamlit components and runs the simulation loop.
    """
    import importlib.util

    if not importlib.util.find_spec("streamlit"):
        raise ImportError(
            "Streamlit and Plotly are required for the web dashboard. "
            "Install with: pip install strategify[web]"
        )

    import streamlit as st  # noqa: E402

    st.set_page_config(
        page_title="Geopol Sim Dashboard",
        page_icon="\u26f3",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _apply_custom_styles(st)

    st.title("\u26f3 Geopol Sim Dashboard")
    st.caption("Interactive geopolitical simulation with game theory and agent-based modeling")

    # Initialize session state
    _init_session_state(st)

    # Sidebar: scenario and controls
    with st.sidebar:
        _render_controls(st)

    # Main content tabs
    tab_map, tab_network, tab_timeseries, tab_analysis, tab_editor, tab_export = st.tabs(
        [
            "\ud83d\uddfa\ufe0f Map",
            "\ud83c\udf10 Network",
            "\ud83d\udcc8 Time Series",
            "\ud83d\udcca Analysis",
            "\u270f\ufe0f Scenario Editor",
            "\ud83d\udcbe Export",
        ]
    )

    model = st.session_state.get("model")
    if model is None:
        st.info("Configure a scenario in the sidebar and click **Initialize** to begin.")
        return

    with tab_map:
        _render_map_tab(st, model)

    with tab_network:
        _render_network_tab(st, model)

    with tab_timeseries:
        _render_timeseries_tab(st, model)

    with tab_analysis:
        _render_analysis_tab(st, model)

    with tab_editor:
        _render_editor_tab(st)

    with tab_export:
        _render_export_tab(st, model)


def _init_session_state(st) -> None:
    """Initialize Streamlit session state variables."""
    defaults = {
        "model": None,
        "scenario": "default",
        "n_steps": 20,
        "current_step": 0,
        "running": False,
        "history": [],
        "custom_scenario": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_controls(st) -> None:
    """Render sidebar controls for simulation configuration and playback."""
    st.header("\U0001f4cb Configuration")

    # Dark mode toggle
    dark_mode = st.toggle("Dark Mode", value=True, help="Toggle dark/light theme")
    if dark_mode:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] { background: #0f1419 !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )

    from strategify.config.scenarios import list_scenarios

    scenarios = list_scenarios()
    scenario = st.selectbox(
        "Scenario", scenarios, index=0 if scenarios else None, label_visibility="collapsed"
    )
    n_steps = st.slider("Max Steps", 5, 100, 20, 5)

    col1, col2 = st.columns(2, gap="small")
    with col1:
        if st.button("\u25b6 Initialize", use_container_width=True, type="primary"):
            from strategify.sim.model import GeopolModel

            st.session_state.model = GeopolModel(scenario=scenario)
            st.session_state.scenario = scenario
            st.session_state.n_steps = n_steps
            st.session_state.current_step = 0
            st.session_state.history = []
            st.success(f"Initialized: {scenario}")

    with col2:
        if st.button("\u21ba Reset", use_container_width=True):
            st.session_state.model = None
            st.session_state.current_step = 0
            st.session_state.history = []
            st.session_state.running = False
            st.rerun()

    model = st.session_state.get("model")
    if model is None:
        st.info("Configure a scenario and click **Initialize** to begin.")
        return

    st.divider()
    st.header("\U0001f3af Simulation Controls")

    # Auto-play controls
    st.markdown("**\U0001f3c1 Playback**")
    col_auto1, col_auto2, col_auto3 = st.columns([2, 1, 1])
    with col_auto1:
        auto_play = st.toggle(
            "Auto-play",
            value=st.session_state.get("running", False),
            help="Toggle auto-play (or press 'Space')",
        )
    with col_auto2:
        speed = st.select_slider(
            "Speed",
            options=["Slow", "Medium", "Fast", "Very Fast"],
            value="Medium",
            help="Simulation speed",
        )
    with col_auto3:
        st.write("")  # spacer
        st.caption("\u2328 Space = Step | \u23f8 = Stop")

    speed_map = {"Slow": 0.5, "Medium": 1, "Fast": 2, "Very Fast": 5}
    delay = 1.0 / speed_map[speed]

    # Update running state
    was_running = st.session_state.get("running", False)
    st.session_state.running = auto_play

    if auto_play and not was_running or auto_play and was_running:
        if st.session_state.current_step < st.session_state.n_steps:
            _step_simulation(st, model, 1)
            time.sleep(delay)
            st.rerun()
        else:
            st.session_state.running = False
            st.warning("Simulation complete!")
            st.rerun()

    steps_per_run = st.slider(
        "Manual Steps per run", 1, 20, 5, help="Number of simulation steps per execution"
    )

    col_a, col_b, col_c = st.columns(3, gap="small")
    with col_a:
        step_once = st.button("\u23ed Step", use_container_width=True, type="secondary")
    with col_b:
        run_btn = st.button("\u25b6 Run", use_container_width=True, type="primary")
    with col_c:
        stop_btn = st.button("\u23f8 Stop", use_container_width=True, type="secondary")

    if stop_btn:
        st.session_state.running = False
        st.rerun()

    if step_once:
        _step_simulation(st, model, 1)

    if run_btn:
        _step_simulation(st, model, steps_per_run)

    # Status display with improved styling
    st.divider()
    st.subheader("\U0001f4ca Status")

    # Progress bar
    progress = st.session_state.current_step / max(st.session_state.n_steps, 1)
    st.progress(progress, text=f"Step {st.session_state.current_step} / {st.session_state.n_steps}")

    # Metrics row
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Step", st.session_state.current_step)
    with col_m2:
        escalators = sum(1 for a in model.schedule.agents if a.posture == "Escalate")
        st.metric("Escalating", escalators)
    with col_m3:
        st.metric("Total Actors", len(list(model.schedule.agents)))

    # Agent status cards
    st.markdown("**Actor Status**")
    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "?")
        posture = getattr(agent, "posture", "?")
        mil = agent.capabilities.get("military", 0)
        eco = agent.capabilities.get("economic", 0)

        if posture == "Escalate":
            status_icon = "\U0001f6a8"
            status_class = "status-escalate"
        else:
            status_icon = "✌"
            status_class = "status-deescalate"

        st.markdown(
            f"""
            <div class="metric-card">
                <span style="font-size: 1.2em;">{status_icon}</span>
                <strong>{rid.upper()}</strong>
                <span class="{status_class}">{posture}</span>
                <br><small style="color: #888;">Mil: {mil:.1f} | Eco: {eco:.1f}</small>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _step_simulation(st, model, n: int) -> None:
    """Step the simulation n times and record history."""
    for _ in range(n):
        model.step()
        st.session_state.current_step += 1

        snapshot = {
            "step": st.session_state.current_step,
        }
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            snapshot[f"{rid}_posture"] = 1.0 if agent.posture == "Escalate" else 0.0
            snapshot[f"{rid}_military"] = agent.capabilities.get("military", 0)
            snapshot[f"{rid}_economic"] = agent.capabilities.get("economic", 0)

        if hasattr(model, "trade_network") and model.trade_network is not None:
            for agent in model.schedule.agents:
                rid = getattr(agent, "region_id", "unknown")
                snapshot[f"{rid}_gdp"] = model.trade_network.get_gdp(agent.unique_id)

        st.session_state.history.append(snapshot)


def _render_map_tab(st, model: Any) -> None:
    """Render the map visualization tab."""
    st.subheader("Geopolitical Map")

    import folium
    from streamlit_folium import st_folium

    from strategify.config.settings import get_region_hex_color

    m = folium.Map(location=[50, 30], zoom_start=4, tiles="cartodbpositron")

    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        posture = getattr(agent, "posture", "Deescalate")
        personality = getattr(agent, "personality", "Unknown")
        color = get_region_hex_color(rid)
        opacity = 0.8 if posture == "Escalate" else 0.3

        net_inf = 0.0
        if model.influence_map:
            net_inf = model.influence_map.get_net_influence(rid, agent.unique_id)

        popup = (
            f"<b>{rid.upper()}</b><br>"
            f"Posture: {posture}<br>"
            f"Personality: {personality}<br>"
            f"Net Influence: {net_inf:.2f}<br>"
            f"Military: {agent.capabilities.get('military', 0):.2f}<br>"
            f"Economic: {agent.capabilities.get('economic', 0):.2f}"
        )

        import json as _json

        geojson = _json.loads(_json.dumps(agent.geometry.__geo_interface__))
        folium.GeoJson(
            geojson,
            style_function=lambda x, c=color, o=opacity: {
                "fillColor": c,
                "color": c,
                "weight": 2,
                "fillOpacity": o,
            },
            popup=folium.Popup(popup, max_width=300),
            tooltip=rid.upper(),
        ).add_to(m)

    st_folium(m, width=800, height=500)


def _render_network_tab(st, model: Any) -> None:
    """Render the diplomacy network tab."""
    st.subheader("Diplomacy Network")

    import networkx as nx
    import plotly.graph_objects as go

    graph = model.relations.graph
    pos = nx.spring_layout(graph, seed=42) if graph.number_of_nodes() > 0 else {}

    # Edges
    edge_x, edge_y, edge_colors = [], [], []
    for u, v, data in graph.edges(data=True):
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            w = data.get("weight", 0)
            color = "#4CAF50" if w > 0.3 else "#F44336" if w < -0.3 else "#9E9E9E"
            edge_colors.append(color)

    # Nodes
    node_x, node_y, node_text, node_colors, node_sizes = [], [], [], [], []
    for agent in model.schedule.agents:
        uid = agent.unique_id
        if uid in pos:
            rid = getattr(agent, "region_id", "?")
            x, y = pos[uid]
            node_x.append(x)
            node_y.append(y)
            posture = getattr(agent, "posture", "?")
            mil = agent.capabilities.get("military", 0.5)
            node_text.append(f"{rid.upper()}\n{posture}\nMil: {mil:.2f}")
            node_colors.append("#F44336" if posture == "Escalate" else "#4CAF50")
            node_sizes.append(15 + mil * 30)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=edge_x,
            y=edge_y,
            mode="lines",
            line=dict(width=1, color="#CCCCCC"),
            hoverinfo="none",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            marker=dict(size=node_sizes, color=node_colors, line=dict(width=2)),
            text=[t.split("\n")[0] for t in node_text],
            textposition="top center",
            hovertext=node_text,
            hoverinfo="text",
        )
    )
    fig.update_layout(
        showlegend=False,
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, color="#888"),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, color="#888"),
        font=dict(color="#ddd"),
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_timeseries_tab(st, model: Any) -> None:
    """Render time series charts tab."""
    st.subheader("Escalation Time Series")

    import plotly.graph_objects as go

    history = st.session_state.get("history", [])
    if not history:
        st.info("Run the simulation to see time series data.")
        return

    df = pd.DataFrame(history)
    fig = go.Figure()

    for agent in model.schedule.agents:
        rid = getattr(agent, "region_id", "unknown")
        col = f"{rid}_posture"
        if col in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["step"],
                    y=df[col],
                    mode="lines+markers",
                    name=rid.upper(),
                    line=dict(width=2),
                )
            )

    fig.update_layout(
        xaxis_title="Step",
        yaxis_title="Escalation (0/1)",
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(30,30,30,0.5)",
        xaxis=dict(color="#aaa"),
        yaxis=dict(tickvals=[0, 1], ticktext=["Deescalate", "Escalate"], color="#aaa"),
        font=dict(color="#ccc"),
        legend=dict(font=dict(color="#ccc")),
    )
    st.plotly_chart(fig, use_container_width=True)

    # GDP chart if available
    gdp_cols = [c for c in df.columns if c.endswith("_gdp")]
    if gdp_cols:
        st.subheader("GDP Over Time")
        fig2 = go.Figure()
        for col in gdp_cols:
            rid = col.replace("_gdp", "").upper()
            fig2.add_trace(
                go.Scatter(
                    x=df["step"],
                    y=df[col],
                    mode="lines",
                    name=rid,
                )
            )
        fig2.update_layout(
            xaxis_title="Step",
            yaxis_title="GDP",
            height=300,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(30,30,30,0.5)",
            xaxis=dict(color="#aaa"),
            yaxis=dict(color="#aaa"),
            font=dict(color="#ccc"),
            legend=dict(font=dict(color="#ccc")),
        )
        st.plotly_chart(fig2, use_container_width=True)


def _render_analysis_tab(st, model: Any) -> None:
    """Render analysis tab with early warning and summary stats."""
    st.subheader("Analysis")

    history = st.session_state.get("history", [])
    if not history:
        st.info("Run the simulation to see analysis.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**\U0001f4ca Escalation Summary**")
        df = pd.DataFrame(history)
        for agent in model.schedule.agents:
            rid = getattr(agent, "region_id", "unknown")
            col = f"{rid}_posture"
            if col in df.columns:
                esc_count = int(df[col].sum())
                total = len(df)
                pct = esc_count / total * 100
                bar = "\u2588" * int(pct / 10) + "\u2591" * (10 - int(pct / 10))
                color = "red" if pct > 50 else "orange" if pct > 25 else "green"
                st.markdown(
                    f"**{rid.upper()}**: [{bar}] {pct:.0f}%",
                    unsafe_allow_html=True,
                )

    with col2:
        st.markdown("**\U0001f4e1 Diplomacy**")
        for u, v, data in model.relations.graph.edges(data=True):
            w = data.get("weight", 0)
            if w > 0.3:
                rel = "\U0001f495 Alliance"
                color = "#2ed573"
            elif w < -0.3:
                rel = "\u2694\ufe0f Rivalry"
                color = "#ff4757"
            else:
                rel = "\U0001f91d Neutral"
                color = "#ffa502"
            st.markdown(
                f"<span style='color:{color}'>Agent {u} \u2014 Agent {v}: {rel}</span> ({w:+.1f})",
                unsafe_allow_html=True,
            )

    # Early warning with visual alerts
    if len(history) >= 5:
        st.divider()
        st.markdown("**\U0001f6a8 Early Warning System**")
        try:
            from strategify.analysis.alerts import run_early_warning

            posture_cols = [c for c in df.columns if c.endswith("_posture")]
            ts = df[posture_cols].rename(columns=lambda c: c.replace("_posture", ""))
            report = run_early_warning(ts, current_step=len(ts) - 1)

            if report["alert_count"] > 0:
                level_colors = {
                    "critical": "#ff4757",
                    "warning": "#ffa502",
                    "watch": "#2ed573",
                }
                _ = level_colors.get(report["overall_level"], "#888")  # noqa: F841
                st.markdown(
                    f"<div class='alert-{report['overall_level']}' style='font-size:1.1em;'>"
                    f"\U0001f6a8 <strong>{report['alert_count']} ALERTS</strong> "
                    f"(Level: {report['overall_level'].upper()})"
                    f"</div>",
                    unsafe_allow_html=True,
                )

                # Show individual alerts
                for alert in report["spikes"][:5]:
                    region = alert.get("region", "?")
                    step = alert["step"]
                    alert_type = alert.get("type", "unknown")
                    level = alert.get("level", "watch")
                    st.markdown(
                        f"  \u26a0\ufe0f [{level.upper()}] {alert_type}: "
                        f"{region.upper()} at step {step}",
                    )
            else:
                st.markdown(
                    "<div style='color:#2ed573; padding:12px; background:rgba(46,213,115,0.15); "
                    "border-radius:8px; border:1px solid #2ed573;'>"
                    "\U0001f7e2 No alerts detected - situation stable"
                    "</div>",
                    unsafe_allow_html=True,
                )
        except Exception as e:
            st.warning(f"Analysis unavailable: {e}")


def _render_editor_tab(st) -> None:
    """Render scenario editor tab."""
    st.subheader("Scenario Editor")
    st.caption("Define custom actors, alliances, and parameters")

    # Actor editor
    st.markdown("**Actors**")
    n_actors = st.number_input("Number of actors", 2, 20, 4)

    actors = {}
    for i in range(n_actors):
        cols = st.columns([2, 2, 1, 1, 2])
        with cols[0]:
            rid = st.text_input(f"Region ID {i + 1}", f"region_{i + 1}", key=f"eid_{i}")
        with cols[1]:
            name = st.text_input(f"Name {i + 1}", rid.title(), key=f"ename_{i}")
        with cols[2]:
            mil = st.number_input("Mil", 0.0, 1.0, 0.5, 0.1, key=f"emil_{i}")
        with cols[3]:
            eco = st.number_input("Eco", 0.0, 1.0, 0.5, 0.1, key=f"eeco_{i}")
        with cols[4]:
            personality = st.selectbox(
                "Personality",
                ["Neutral", "Aggressor", "Pacifist", "Tit-for-Tat", "Grudger"],
                key=f"epers_{i}",
            )
        actors[rid] = {
            "name": name,
            "capabilities": {"military": mil, "economic": eco},
            "role": "row" if i % 2 == 0 else "col",
            "personality": personality,
        }

    # Alliance editor
    st.markdown("**Alliances**")
    n_alliances = st.number_input("Number of alliances", 0, 20, 3)
    alliances = []
    actor_ids = list(actors.keys())
    for i in range(n_alliances):
        cols = st.columns([3, 3, 2])
        with cols[0]:
            src = st.selectbox("Source", actor_ids, key=f"easrc_{i}")
        with cols[1]:
            tgt = st.selectbox("Target", actor_ids, key=f"eatgt_{i}")
        with cols[2]:
            w = st.slider("Weight", -1.0, 1.0, 0.0, 0.1, key=f"eaw_{i}")
        alliances.append({"source": src, "target": tgt, "weight": w})

    # Resources
    st.markdown("**Region Resources**")
    resources = {}
    for rid in actors:
        resources[rid] = st.number_input(f"{rid} resources", 0.1, 5.0, 1.0, 0.1, key=f"eres_{rid}")

    # Save button
    if st.button("\ud83d\udcbe Save Scenario", use_container_width=True):
        scenario_data = {
            "name": "custom",
            "description": "User-defined scenario",
            "geojson": "real_world.geojson",
            "random_seed": 42,
            "n_steps": 20,
            "actors": actors,
            "region_resources": resources,
            "alliances": alliances,
        }
        st.session_state.custom_scenario = scenario_data

        # Save to file
        from strategify.config.settings import SCENARIOS_DIR

        path = SCENARIOS_DIR / "custom.json"
        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(scenario_data, f, indent=2)
        st.success(f"Saved to {path}")

    # Show JSON preview
    if st.session_state.get("custom_scenario"):
        with st.expander("Preview JSON"):
            st.code(
                json.dumps(st.session_state.custom_scenario, indent=2),
                language="json",
            )


def _render_export_tab(st, model: Any) -> None:
    """Render export tab with various download options."""
    st.subheader("Export")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Simulation Data**")

        history = st.session_state.get("history", [])
        if history:
            df = pd.DataFrame(history)
            csv = df.to_csv(index=False)
            st.download_button(
                "\ud83d\udcc4 Download CSV",
                csv,
                "simulation_output.csv",
                "text/csv",
                use_container_width=True,
            )

        # Agent data
        try:
            agent_df = model.datacollector.get_agent_vars_dataframe()
            csv2 = agent_df.reset_index().to_csv(index=False)
            st.download_button(
                "\ud83d\udcc4 Agent Data CSV",
                csv2,
                "agent_data.csv",
                "text/csv",
                use_container_width=True,
            )
        except Exception:
            pass

    with col2:
        st.markdown("**Reports & Maps**")

        if st.button("\ud83d\udcd8 Generate Report", use_container_width=True):
            from strategify.viz.reports import generate_report

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                path = generate_report(model, f.name)
                with open(path) as rf:
                    html = rf.read()
                st.download_button(
                    "\ud83d\udcfa Download Report",
                    html,
                    "simulation_report.html",
                    "text/html",
                    use_container_width=True,
                )

        if st.button("\ud83d\uddfa\ufe0f Export Map", use_container_width=True):
            from strategify.viz.maps import create_map

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                path = create_map(model, f.name)
                with open(path) as rf:
                    html = rf.read()
                st.download_button(
                    "\ud83d\udcfa Download Map",
                    html,
                    "simulation_map.html",
                    "text/html",
                    use_container_width=True,
                )

        if st.button("\ud83c\udf10 Export Network", use_container_width=True):
            from strategify.viz.networks import create_diplomacy_network

            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                path = create_diplomacy_network(model, f.name)
                with open(path) as rf:
                    html = rf.read()
                st.download_button(
                    "\ud83d\udcfa Download Network",
                    html,
                    "diplomacy_network.html",
                    "text/html",
                    use_container_width=True,
                )

    # State export
    st.divider()
    st.markdown("**Simulation State**")
    if st.button("\ud83d\udcbe Save Checkpoint", use_container_width=True):
        from strategify.sim.persistence import save_state

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = save_state(model, f.name)
            with open(path) as rf:
                state_json = rf.read()
            st.download_button(
                "\ud83d\udcbe Download State",
                state_json,
                "simulation_state.json",
                "application/json",
                use_container_width=True,
            )
