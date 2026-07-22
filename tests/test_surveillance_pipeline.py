"""Tests for CDC Surveillance Adapters and Parameter Fitting Engine."""

from strategify.epidemiology.parameter_fitting import SurveillanceParameterFitter
from strategify.osint.surveillance_adapters import (
    CDCCfaAdapter,
    CDCNNDSSAdapter,
    CDCWonderAdapter,
    HealthDataGovAdapter,
    NextstrainGenomicAdapter,
)

EXPECTED_WEEKS = 12


def test_cdc_wonder_adapter():
    adapter = CDCWonderAdapter()
    pop, mortality = adapter.fetch_population_and_mortality("US-CA")
    assert pop > 0
    assert mortality > 0.0


def test_cdc_nndss_adapter():
    adapter = CDCNNDSSAdapter()
    series = adapter.fetch_weekly_incidence("US-CA", "Respiratory")
    assert series.region_code == "US-CA"
    assert len(series.weekly_cases) == EXPECTED_WEEKS


def test_cdc_cfa_adapter():
    adapter = CDCCfaAdapter()
    benchmark = adapter.fetch_rt_benchmark("US-CA")
    assert benchmark["estimated_rt"] > 0.0


def test_healthdata_gov_adapter():
    adapter = HealthDataGovAdapter()
    cap = adapter.fetch_hospital_capacity("US-CA")
    assert 0.0 <= cap["icu_beds_used_pct"] <= 1.0


def test_nextstrain_genomic_adapter():
    adapter = NextstrainGenomicAdapter()
    metrics = adapter.fetch_genomic_strain_data("Variant-X")
    assert metrics.strain_name == "Variant-X"
    assert metrics.relative_competitiveness > 1.0


def test_surveillance_parameter_fitter():
    fitter = SurveillanceParameterFitter()
    weekly_cases = [10, 25, 60, 140, 220, 310, 280, 200, 120, 50]
    fit_res = fitter.fit_sir_parameters(weekly_cases, population=100_000)

    assert fit_res.estimated_beta > 0.0
    assert fit_res.estimated_gamma > 0.0
    assert fit_res.estimated_r0 > 0.0

    rt_curve = fitter.estimate_renewal_rt_curve(weekly_cases)
    assert len(rt_curve) == len(weekly_cases) - 1
