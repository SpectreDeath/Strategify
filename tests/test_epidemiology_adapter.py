"""Tests for Public Epidemiology Data Adapters."""

from strategify.osint.epidemiology_adapter import (
    EpidemiologyDataAdapter,
    GDELTEpidemicFilter,
    OWIDDataAdapter,
    WHOApiAdapter,
)


def test_who_api_adapter():
    adapter = WHOApiAdapter()
    res = adapter.fetch_health_indicator("UKR", "NURSES")
    assert res["country_code"] == "UKR"
    assert res["indicator"] == "NURSES"
    assert res["value"] > 0.0


def test_owid_data_adapter():
    adapter = OWIDDataAdapter()
    metrics = adapter.fetch_latest_metrics("UKR")

    assert metrics.country_code == "UKR"
    assert metrics.total_cases > 0
    assert metrics.effective_rt > 0.0
    assert 0.0 <= metrics.vaccination_coverage <= 1.0


def test_gdelt_epidemic_filter():
    filter_engine = GDELTEpidemicFilter()
    sample_events = [
        {"text": "Breaking news: Outbreak of new virus variant detected in region."},
        {"text": "Local economic market update for stocks."},
    ]
    summary = filter_engine.extract_outbreak_events("UKR", sample_events)
    assert summary["health_event_count"] == 1
    assert summary["panic_score"] > 0.0


def test_unified_epidemiology_data_adapter():
    master_adapter = EpidemiologyDataAdapter()
    profile = master_adapter.get_country_epidemic_profile("UKR")

    assert profile.country_code == "UKR"
    assert profile.effective_rt > 0.0
    assert profile.hospital_bed_capacity > 0.0
