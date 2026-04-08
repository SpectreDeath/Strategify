from pathlib import Path

import pytest

from strategify.sim.model import GeopolModel
from strategify.viz.maps import create_alliance_map, create_map
from strategify.viz.networks import create_diplomacy_network


@pytest.fixture
def model():
    model = GeopolModel()
    model.step()
    return model


def test_create_map(model, tmp_path):
    output = tmp_path / "test_map.html"
    result = create_map(model, output)
    assert Path(result).exists()
    content = Path(result).read_text()
    assert "geojson" in content.lower() or "leaflet" in content.lower()


def test_create_alliance_map(model, tmp_path):
    output = tmp_path / "test_alliance.html"
    result = create_alliance_map(model, output)
    assert Path(result).exists()


def test_create_diplomacy_network(model, tmp_path):
    output = tmp_path / "test_network.html"
    result = create_diplomacy_network(model, output)
    assert Path(result).exists()
    content = Path(result).read_text()
    assert "vis" in content.lower() or "network" in content.lower()
