"""Epidemiology Model Context Protocol (MCP) Tool Bridge.

Exposes CDC SODA, NIH RePORTER V2, RxNorm, SurveillanceParameterFitter, and EpidemicEnv RL tools
for Model Context Protocol (MCP) external agent tool execution.
"""

from __future__ import annotations

import logging
from typing import Any

from strategify.osint.cdc_soda_adapter import CDCSodaApiAdapter, SoQLQuery
from strategify.osint.nih_reporter_adapter import NIHReporterApiAdapter
from strategify.osint.pipeline_integration import SoQLToFitterPipeline
from strategify.osint.rxnorm_adapter import RxNormApiAdapter
from strategify.rl.benchmark import RLControlBenchmark
from strategify.rl.epidemic_env import EpidemicEnv

logger = logging.getLogger(__name__)


class EpidemiologyMCPBridge:
    """MCP Bridge registering federal epidemiology, RL, and data tools."""

    def __init__(self) -> None:
        self.soda_adapter = CDCSodaApiAdapter()
        self.nih_adapter = NIHReporterApiAdapter()
        self.rxnorm_adapter = RxNormApiAdapter()
        self.pipeline = SoQLToFitterPipeline()
        self.env = EpidemicEnv()
        self.benchmark_engine = RLControlBenchmark(env=self.env)

    def get_tool_declarations(self) -> list[dict[str, Any]]:
        """Get MCP tool declarations schema for external LLM agents.

        Returns
        -------
        list[dict[str, Any]]
            MCP tool declarations.
        """
        return [
            {
                "name": "query_cdc_soda",
                "description": "Query CDC Socrata datasets (data.cdc.gov) using SoQL queries.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_id": {"type": "string"},
                        "where": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                    "required": ["dataset_id"],
                },
            },
            {
                "name": "search_nih_grants",
                "description": "Search NIH RePORTER V2 for research grants and publications.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {"type": "array", "items": {"type": "string"}},
                        "limit": {"type": "integer"},
                    },
                },
            },
            {
                "name": "lookup_rxnorm_drug",
                "description": "Lookup normalized clinical drug concepts in NLM RxNorm.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "drug_name": {"type": "string"},
                    },
                    "required": ["drug_name"],
                },
            },
            {
                "name": "fit_soql_pipeline",
                "description": "Stream SoQL dataset into ODE parameter fitter to estimate beta, gamma, and R0.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dataset_id": {"type": "string"},
                        "population": {"type": "integer"},
                    },
                },
            },
            {
                "name": "step_epidemic_env",
                "description": "Advance EpidemicEnv simulation step with action [u_NPI, u_vax, u_icu].",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "array", "items": {"type": "number"}},
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "benchmark_rl_vs_optimal",
                "description": "Benchmark trained RL policy against Pontryagin optimal control baseline.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "num_episodes": {"type": "integer"},
                    },
                },
            },
            {
                "name": "server_discover",
                "description": "Exposes MCP 2026-07-28 stateless server capabilities, spec version, and routing header requirements.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute an MCP tool call.

        Parameters
        ----------
        tool_name : str
            Name of tool to execute.
        arguments : dict[str, Any]
            Arguments passed to the tool.

        Returns
        -------
        dict[str, Any]
            Execution payload response.
        """
        if tool_name == "server_discover" or tool_name == "serverDiscover":
            return {
                "status": "success",
                "spec_version": "2026-07-28",
                "protocolVersion": "2026-07-28",
                "stateless": True,
                "server_info": {"name": "strategify-mcp-bridge", "version": "1.0.0"},
                "capabilities": {
                    "stateless_transport": True,
                    "routing_headers": ["MCP-Method", "MCP-Name"],
                    "interactive_mode": "input_required",
                    "tools": len(self.get_tool_declarations()),
                },
                "_meta": {
                    "handshake_required": False,
                    "mcp_session_id_deprecated": True,
                },
            }

        elif tool_name == "query_cdc_soda":
            query = SoQLQuery(
                where=arguments.get("where"),
                limit=arguments.get("limit", 5),
            )
            records = self.soda_adapter.query_dataset(dataset_id=arguments.get("dataset_id", "n8mc-bfd4"), query=query)
            return {"status": "success", "records": records}

        elif tool_name == "search_nih_grants":
            projects = self.nih_adapter.search_projects(
                keywords=arguments.get("keywords", ["epidemiology"]),
                limit=arguments.get("limit", 5),
            )
            return {"status": "success", "projects": [p.__dict__ for p in projects]}

        elif tool_name == "lookup_rxnorm_drug":
            concept = self.rxnorm_adapter.search_drug_concept(drug_name=arguments.get("drug_name", "Paxlovid"))
            return {"status": "success", "concept": concept.__dict__}

        elif tool_name == "fit_soql_pipeline":
            outcome = self.pipeline.process_dataset(
                dataset_id=arguments.get("dataset_id", "n8mc-bfd4"),
                population=arguments.get("population", 1_000_000),
            )
            return {
                "status": "success",
                "estimated_beta": outcome.fit_result.estimated_beta,
                "estimated_gamma": outcome.fit_result.estimated_gamma,
                "estimated_r0": outcome.fit_result.estimated_r0,
            }

        elif tool_name == "step_epidemic_env":
            act = arguments.get("action", [0.5, 0.1, 0.1])
            obs, reward, term, trunc, info = self.env.step(act)
            return {
                "status": "success",
                "observation": obs.tolist(),
                "reward": reward,
                "terminated": term,
                "truncated": trunc,
                "info": info,
            }

        elif tool_name == "benchmark_rl_vs_optimal":
            res = self.benchmark_engine.compare_rl_vs_pontryagin(
                num_episodes=arguments.get("num_episodes", 5),
            )
            return {
                "status": "success",
                "optimality_gap_pct": res.optimality_gap_pct,
                "trajectory_mse": res.trajectory_mse,
                "rl_total_cost_j": res.rl_total_cost_j,
                "pontryagin_optimal_cost_j": res.pontryagin_optimal_cost_j,
            }

        else:
            return {"status": "error", "message": f"Unknown tool: {tool_name}"}
