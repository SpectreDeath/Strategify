"""Tests for Pipeline Integration, MCP Tool Bridge, and Federal Rate Limiting."""

import os
from strategify.osint.cdc_soda_adapter import SoQLQuery
from strategify.osint.pipeline_integration import SoQLToFitterPipeline
from strategify.osint.rate_limiter import FederalApiCacheThrottle
from strategify.plugins.mcp_bridge import EpidemiologyMCPBridge

TEST_CACHE_DB = "test_federal_throttle.db"
EXPECTED_DECLARATIONS_COUNT = 4


def test_federal_api_cache_throttle():
    if os.path.exists(TEST_CACHE_DB):
        os.remove(TEST_CACHE_DB)

    throttle_engine = FederalApiCacheThrottle(min_interval_seconds=0.01, db_path=TEST_CACHE_DB)

    fetch_calls = []

    def sample_fetch():
        fetch_calls.append(1)
        return {"data": "test_payload"}

    # First call -> cache miss
    val1 = throttle_engine.execute_with_cache("key1", sample_fetch)
    assert val1["data"] == "test_payload"
    assert len(fetch_calls) == 1

    # Second call -> cache hit
    val2 = throttle_engine.execute_with_cache("key1", sample_fetch)
    assert val2["data"] == "test_payload"
    assert len(fetch_calls) == 1

    if os.path.exists(TEST_CACHE_DB):
        os.remove(TEST_CACHE_DB)


def test_soql_to_fitter_pipeline():
    pipeline = SoQLToFitterPipeline()
    query = SoQLQuery(limit=5)
    outcome = pipeline.process_dataset("n8mc-bfd4", query=query, population=100_000)

    assert outcome.dataset_id == "n8mc-bfd4"
    assert outcome.record_count > 0
    assert outcome.fit_result.estimated_beta > 0.0
    assert outcome.fit_result.estimated_r0 > 0.0


def test_epidemiology_mcp_bridge():
    bridge = EpidemiologyMCPBridge()
    decls = bridge.get_tool_declarations()
    assert len(decls) == EXPECTED_DECLARATIONS_COUNT

    tool_names = [t["name"] for t in decls]
    assert "query_cdc_soda" in tool_names
    assert "search_nih_grants" in tool_names
    assert "lookup_rxnorm_drug" in tool_names
    assert "fit_soql_pipeline" in tool_names

    res_soda = bridge.execute_tool("query_cdc_soda", {"dataset_id": "n8mc-bfd4", "limit": 2})
    assert res_soda["status"] == "success"

    res_nih = bridge.execute_tool("search_nih_grants", {"keywords": ["vaccine"], "limit": 1})
    assert res_nih["status"] == "success"

    res_rxnorm = bridge.execute_tool("lookup_rxnorm_drug", {"drug_name": "Paxlovid"})
    assert res_rxnorm["status"] == "success"

    res_pipeline = bridge.execute_tool("fit_soql_pipeline", {"dataset_id": "n8mc-bfd4"})
    assert res_pipeline["status"] == "success"
    assert res_pipeline["estimated_r0"] > 0.0
