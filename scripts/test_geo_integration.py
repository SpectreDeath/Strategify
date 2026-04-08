from pathlib import Path

import mesa_geo as mg
from mesa import Model


def test_geo_integration():
    geojson_path = Path("strategify/geo/real_world.geojson")

    # Check if mesa_geo can read this file
    class TestAgent(mg.GeoAgent):
        def __init__(self, unique_id, model, geometry, crs):
            super().__init__(unique_id, model, geometry, crs)

    class TestModel(Model):
        def __init__(self):
            super().__init__()
            self.space = mg.GeoSpace()

            # Use GeoAgentCreator
            ac = mg.GeoAgentCreator(agent_class=TestAgent, model=self)

            # Create agents from GeoJSON
            agents = ac.from_file(geojson_path)
            self.space.add_agents(agents)

            print(f"Loaded {len(agents)} GeoAgents into GeoSpace.")
            for agent in agents:
                print(f"Agent ID: {agent.unique_id}, Region: {getattr(agent, 'region_id', 'Unknown')}")

            # Test Adjacency
            print("\nAdjacency Test:")
            for agent in agents:
                neighbors = self.space.get_neighbors(agent)
                neighbor_ids = [n.region_id for n in neighbors if hasattr(n, 'region_id')]
                print(f"Agent {agent.region_id} borders: {neighbor_ids}")

if __name__ == "__main__":
    test_geo_integration()
