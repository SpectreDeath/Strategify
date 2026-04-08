

from strategify.sim.model import GeopolModel


def test_crs_projection_in_model():
    # Load model with default (which should now be EPSG:3857)
    model = GeopolModel(scenario="default")

    assert model.region_gdf.crs is not None
    assert str(model.region_gdf.crs).lower() == "epsg:3857"

    # Check that distances are in meters (large)
    g1 = model.region_gdf.geometry.iloc[0]
    g2 = model.region_gdf.geometry.iloc[1]
    dist = g1.centroid.distance(g2.centroid)

    # Between countries in Eastern Europe (alpha/bravo/charlie/delta),
    # distance should be many kilometers -> millions of meters.
    # If it was EPSG:4326, it would be a few decimal degrees.
    print(f"Distance between centroids: {dist}")
    assert dist > 1000  # Definitely not degrees

def test_adjacency_builder_with_projection():
    from strategify.geo.loader import AdjacencyBuilder
    model = GeopolModel(scenario="default")
    adj = AdjacencyBuilder.build(model.region_gdf)

    # Ensure neighbor graph still forms correctly after reprojection
    assert len(adj) > 0
    # For eastern_europe_crisis, alpha (Ukraine) should have neighbors
    assert len(adj["alpha"]) > 0

def test_weighted_contagion():
    from strategify.reasoning.influence import InfluenceMap
    model = GeopolModel(scenario="default")

    # Set Russia (bravo) to Escalate
    russia = next(a for a in model.schedule.agents if a.region_id == "bravo")
    russia.posture = "Escalate"

    inf = InfluenceMap(model)
    inf.compute()

    # Poland (delta) has Russia (bravo) as a neighbor
    # Ukraine (alpha) also has Russia (bravo) as a neighbor

    c_ukraine = inf.get_contagion_level("alpha")
    c_poland = inf.get_contagion_level("delta")

    print(f"Ukraine contagion from Russia: {c_ukraine}")
    print(f"Poland contagion from Russia: {c_poland}")

    # In a weighted model, Ukraine (much longer border with Russia)
    # should typically have higher exposure/contagion than Poland (shorter border),
    # or at least a non-zero weighted value.
    assert c_ukraine > 0
    assert c_poland > 0
    # The sum of weights in get_contagion_level is 1.0, so if Russia is the ONLY
    # escalating neighbor, the contagion is (weight_russia / total_neighbor_length).

if __name__ == "__main__":
    test_crs_projection_in_model()
    test_adjacency_builder_with_projection()
