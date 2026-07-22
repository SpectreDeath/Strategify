"""Tests for CDC SODA, NIH RePORTER V2, and NLM RxNorm Federal APIs."""

from strategify.osint.cdc_soda_adapter import CDCSodaApiAdapter, SoQLQuery
from strategify.osint.nih_reporter_adapter import NIHReporterApiAdapter
from strategify.osint.rxnorm_adapter import RxNormApiAdapter

EXPECTED_LIMIT = 5
EXPECTED_COUNT = 2


def test_cdc_soda_api_adapter():
    adapter = CDCSodaApiAdapter()
    query = SoQLQuery(
        select="state, disease, cases",
        where="cases > 500",
        order="cases DESC",
        limit=EXPECTED_LIMIT,
    )
    params = adapter.build_soql_query_string(query)
    assert params["$limit"] == str(EXPECTED_LIMIT)
    assert params["$where"] == "cases > 500"

    records = adapter.query_dataset("n8mc-bfd4", query)
    assert len(records) > 0
    assert "state" in records[0]


def test_nih_reporter_api_adapter():
    adapter = NIHReporterApiAdapter()
    payload = adapter.build_search_payload(
        keywords=["epidemiology", "vaccine"],
        fiscal_years=[2024, 2025],
        limit=EXPECTED_LIMIT,
    )
    assert payload["limit"] == EXPECTED_LIMIT
    assert "epidemiology" in payload["criteria"]["advanced_text_search"]["search_text"]

    projects = adapter.search_projects(keywords=["epidemiology"], limit=EXPECTED_COUNT)
    assert len(projects) == EXPECTED_COUNT
    assert projects[0].award_amount > 0.0


def test_rxnorm_api_adapter():
    adapter = RxNormApiAdapter()
    concept = adapter.search_drug_concept("Paxlovid")
    assert concept.name == "Paxlovid"
    assert len(concept.rxcui) > 0
    assert len(concept.active_ingredients) > 0
