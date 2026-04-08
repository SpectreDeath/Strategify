"""Middle East conflict simulation scenario.

Simulates the Israeli-Palestinian conflict with neighboring Arab states,
incorporating real-world data, geopolitical theories, and domestic dynamics.

Usage:
    python scripts/middle_east_scenario.py
"""

import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO)

from strategify import GeopolModel  # noqa: E402
from strategify.analysis import (  # noqa: E402
    assess_all_risks,
    compute_threat_score,
    forecast_alliance_stability,
    generate_strategy_report,
)
from strategify.dynamics import FactionalPolitics, IdeologyModel  # noqa: E402
from strategify.geo import GeoJSONLoader, RegionSubsetConfig  # noqa: E402
from strategify.theory import DEFAULT_REGISTRY  # noqa: E402

# Middle East regional configuration
MIDDLE_EAST_CONFIG = {
    "Israel": {
        "country_name": "Israel",
        "id_map": "israel",
        "keywords": ["Israel", "Jerusalem", "Tel Aviv"],
    },
    "Palestine": {
        "country_name": "Palestine",
        "id_map": "palestine",
        "keywords": ["Palestine", "Gaza", "West Bank"],
    },
    "Lebanon": {
        "country_name": "Lebanon",
        "id_map": "lebanon",
        "keywords": ["Lebanon", "Beirut", "Hezbollah"],
    },
    "Syria": {
        "country_name": "Syria",
        "id_map": "syria",
        "keywords": ["Syria", "Damascus"],
    },
    "Jordan": {
        "country_name": "Jordan",
        "id_map": "jordan",
        "keywords": ["Jordan", "Amman"],
    },
    "Egypt": {
        "country_name": "Egypt",
        "id_map": "egypt",
        "keywords": ["Egypt", "Cairo", "Suez"],
    },
    "Saudi Arabia": {
        "country_name": "Saudi Arabia",
        "id_map": "saudi",
        "keywords": ["Saudi Arabia", "Riyadh"],
    },
    "Iran": {
        "country_name": "Iran",
        "id_map": "iran",
        "keywords": ["Iran", "Tehran", "Revolutionary Guard"],
    },
}


def load_middle_east_geometries():
    """Load Middle East geometries."""
    print("\n" + "=" * 60)
    print("LOADING MIDDLE EAST GEOMETRIES")
    print("=" * 60)

    config = RegionSubsetConfig(
        countries=list(MIDDLE_EAST_CONFIG.keys()),
        id_map={k: v["id_map"] for k, v in MIDDLE_EAST_CONFIG.items()},
        resolution="50m",
    )

    gdf = GeoJSONLoader.load(config)
    print(f"Loaded: {len(gdf)} regions")
    return gdf


def run_simulation():
    """Run Middle East conflict simulation."""
    print("\n" + "=" * 60)
    print("MIDDLE EAST CONFLICT SIMULATION")
    print("=" * 60)

    # Load geometries
    gdf = load_middle_east_geometries()

    # Create model
    print("\n[1] Creating GeopolModel...")
    model = GeopolModel(
        n_steps=20,
        region_gdf=gdf,
        enable_economics=True,
        enable_escalation_ladder=True,
    )
    print(f"    Model created with {model.schedule.get_agent_count()} state actors")


def analyze_conflict():
    """Analyze the conflict with all tools."""
    gdf = load_middle_east_geometries()
    model = GeopolModel(n_steps=10, region_gdf=gdf)

    for _ in range(10):
        model.step()

    print("\n" + "=" * 60)
    print("CONFLICT ANALYSIS")
    print("=" * 60)

    agents = [a for a in model.schedule.agents]

    # Risk Assessment
    print("\n[2] RISK ASSESSMENT")
    risks = assess_all_risks(model)
    for rid, data in sorted(risks.items()):
        score = data["threat_score"]
        level = data["risk_level"]
        posture = data["posture"]
        print(f"    {rid:10}: score={score:.2f} level={level} posture={posture}")

    # Individual threat scores
    print("\n[3] THREAT SCORES")
    for agent in agents:
        rid = getattr(agent, "region_id", "")
        score = compute_threat_score(model, rid)
        print(f"    {rid:10}: {score:.2f}")

    # Alliance Forecast
    print("\n[4] ALLIANCE FORECAST")
    stability = forecast_alliance_stability(model, n_future_steps=10)
    for rid, data in sorted(stability.items()):
        stability_val = data.stability_score
        fracture_val = data.fracture_probability
        print(f"    {rid:10}: stability={stability_val:.2f} fracture={fracture_val:.2f}")

    # Domestic Dynamics
    print("\n[5] DOMESTIC DYNAMICS")
    for agent in agents:
        rid = getattr(agent, "region_id", "")
        personality = getattr(agent, "personality", "Neutral")

        fp = FactionalPolitics(agent)
        ideology = IdeologyModel(personality)

        faction = fp.get_dominant_faction().value
        balance = fp.get_faction_balance()
        label = ideology.get_ideology_label()
        print(f"    {rid:10}: {faction} ({balance}) - {label}")

    # Strategic Recommendations
    print("\n[6] STRATEGIC RECOMMENDATIONS")
    for agent in agents:
        rid = getattr(agent, "region_id", "")
        report = generate_strategy_report(model, rid)
        print(f"    {rid:10}: {report.risk_assessment}")
        for rec in report.recommendations[:2]:
            print(f"      - {rec.action}: {rec.rationale}")


def run_theory_analysis():
    """Run geopolitical theory analysis with conflict-specific personalities."""
    gdf = load_middle_east_geometries()
    model = GeopolModel(n_steps=5, region_gdf=gdf)

    # Set conflict-specific personalities manually
    agent_map = {getattr(a, "region_id", ""): a for a in model.schedule.agents}

    # Key conflict personality assignments
    personality_map = {
        "israel": "Aggressor",
        "palestine": "Pacifist",
        "iran": "Grudger",
        "saudi": "Grudger",
        "egypt": "Tit-for-Tat",
        "jordan": "Tit-for-Tat",
        "syria": "Grudger",
        "lebanon": "Tit-for-Tat",
    }

    for rid, agent in agent_map.items():
        if rid in personality_map:
            agent.personality = personality_map[rid]

    model.step()

    print("\n" + "=" * 60)
    print("GEOPOLITICAL THEORY ANALYSIS")
    print("=" * 60)

    agents = [a for a in model.schedule.agents]

    # Key conflict actors
    key_actors = ["israel", "palestine", "iran", "saudi", "egypt"]

    for agent in agents:
        rid = getattr(agent, "region_id", "")
        if rid not in key_actors:
            continue

        print(f"\n[{rid.upper()}] (personality: {getattr(agent, 'personality', 'Neutral')})")

        # Domestic dynamics
        fp = FactionalPolitics(agent)
        ideo = IdeologyModel(getattr(agent, "personality", "Neutral"))
        print(f"  Domestic: {fp.get_dominant_faction().value} - {fp.get_faction_balance()}")
        print(f"  Ideology: {ideo.get_ideology_label()}")

        # Analyze with different theories
        theories_to_test = [
            "Realpolitik",
            "Democratic Peace",
            "Power Transition",
            "Constructivism",
        ]

        print("  Theory predictions:")
        for theory_name in theories_to_test:
            result = DEFAULT_REGISTRY.decide(agent, model, theory_name)
            print(f"    {theory_name:20}: {result.recommended_action:12}")


def compare_conflict_parties():
    """Compare Israel and Palestine specifically with personalities."""
    gdf = load_middle_east_geometries()
    model = GeopolModel(n_steps=5, region_gdf=gdf)

    # Set conflict-specific personalities
    agent_map = {getattr(a, "region_id", ""): a for a in model.schedule.agents}

    personality_map = {
        "israel": "Aggressor",
        "palestine": "Pacifist",
    }

    for rid, agent in agent_map.items():
        if rid in personality_map:
            agent.personality = personality_map[rid]

    model.step()

    print("\n" + "=" * 60)
    print("ISRAEL vs PALESTINE COMPARISON")
    print("=" * 60)

    israel = agent_map.get("israel")
    palestine = agent_map.get("palestine")

    if israel and palestine:
        # Ideology comparison
        print("\n[IDEOLOGY]")
        ideo_israel = IdeologyModel(getattr(israel, "personality", "Neutral"))
        ideo_pal = IdeologyModel(getattr(palestine, "personality", "Neutral"))

        print(f"  Israel:    {ideo_israel.get_ideology_label()}")
        print(f"  Palestine: {ideo_pal.get_ideology_label()}")

        compatibility = ideo_israel.get_compatibility(ideo_pal)
        print(f"  Compatibility: {compatibility:.2f}")

        # Factional politics
        print("\n[DOMESTIC FACTIONS]")
        fp_israel = FactionalPolitics(israel)
        fp_pal = FactionalPolitics(palestine)

        israel_faction = fp_israel.get_dominant_faction().value
        israel_balance = fp_israel.get_faction_balance()
        print(f"  Israel:    {israel_faction} ({israel_balance})")

        pal_faction = fp_pal.get_dominant_faction().value
        pal_balance = fp_pal.get_faction_balance()
        print(f"  Palestine: {pal_faction} ({pal_balance})")

        # Theory comparison
        print("\n[THEORY PREDICTIONS]")
        for theory_name in ["Realpolitik", "Constructivism"]:
            r1 = DEFAULT_REGISTRY.decide(israel, model, theory_name)
            r2 = DEFAULT_REGISTRY.decide(palestine, model, theory_name)
            print(f"  {theory_name}:")
            print(f"    Israel:     {r1.recommended_action}")
            print(f"    Palestine: {r2.recommended_action}")


def main():
    """Run complete analysis."""
    print("""
============================================================
     MIDDLE EAST CONFLICT SIMULATION
     Testing with real-world conflict scenario
============================================================
    """)

    # Run all analyses
    analyze_conflict()
    run_theory_analysis()
    compare_conflict_parties()

    print("\n" + "=" * 60)
    print("SIMULATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
