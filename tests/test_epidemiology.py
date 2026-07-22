"""Tests for Epidemiology & Biosecurity Strategy Engine."""

from strategify.epidemiology.countermeasures import BioDefenseComponent
from strategify.epidemiology.seir import PathogenVariant, SEIRHEngine
from strategify.epidemiology.spatial import GeoEpidemicMap
from strategify.epidemiology.strategy import BioStrategyGame
from strategify.sim.model import GeopolModel


def test_seirh_engine_compartment_dynamics():
    engine = SEIRHEngine(population=100_000, initial_infected=50)
    assert engine.susceptible == 99_950.0
    assert engine.infectious == 50.0

    res = engine.step(dt_days=1.0, npi_effectiveness=0.2, vaccination_rate=0.1)
    assert "susceptible" in res
    assert "rt" in res
    assert res["rt"] > 0.0


def test_pathogen_variant_mutation():
    variant = PathogenVariant(name="Omicron", r0=3.5, vaccine_evasion=0.2)
    assert variant.name == "Omicron"
    assert variant.r0 == 3.5


def test_biodefense_countermeasures():
    model = GeopolModel(n_steps=1)
    agent = model.schedule.agents[0]

    biodefense = BioDefenseComponent(agent)
    drag = biodefense.set_npi_policy(0.8)
    assert drag > 0.0
    assert biodefense.status.npi_level == 0.8

    rd_prog = biodefense.fund_vaccine_rd(0.2)
    assert rd_prog > 0.0

    icu_cap = biodefense.expand_icu_capacity(0.5)
    assert icu_cap == 1.5


def test_bio_strategy_game():
    game = BioStrategyGame()
    action = game.solve_optimal_policy(current_rt=2.5, gdp_budget=0.8)
    assert action in ["LaissezFaire", "TargetedQuarantine", "MassVaccination", "FullLockdown"]


def test_geo_epidemic_spatial_map():
    model = GeopolModel(n_steps=1)
    agent = model.schedule.agents[0]
    agent.seir_engine.infectious = 500.0

    geo_map = GeoEpidemicMap(model)
    exported = geo_map.step_spatial_transmission(cross_border_mobility_rate=0.05)
    assert isinstance(exported, dict)
