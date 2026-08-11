"""Unit tests for Multilateral Alliance Hypergraph Tracker in Strategify."""

import tempfile
from pathlib import Path

from strategify.hypergraph import MultilateralAllianceTracker


def test_multilateral_alliance_tracker():
    """Test alliance registration, query, overlap metrics, and GEXF export."""
    tracker = MultilateralAllianceTracker()

    tracker.register_treaty(
        alliance_id="NATO_Art5",
        member_states={"USA", "UKR", "POL", "DEU", "FRA"},
        commitment_level=0.95,
        metadata={"type": "mutual_defense"},
    )
    tracker.register_treaty(
        alliance_id="QUAD_Pact",
        member_states={"USA", "JPN", "AUS", "IND"},
        commitment_level=0.80,
        metadata={"type": "maritime_security"},
    )
    tracker.register_treaty(
        alliance_id="AUKUS",
        member_states={"USA", "UKR", "AUS"},
        commitment_level=0.85,
    )

    all_treaties = tracker.get_all_alliances()
    assert len(all_treaties) == 3

    # Shared treaties
    shared_usa_ukr = tracker.get_shared_alliances("USA", "UKR")
    assert len(shared_usa_ukr) == 2
    assert {e.edge_id for e in shared_usa_ukr} == {"NATO_Art5", "AUKUS"}

    # Alliance overlap score
    overlap_score = tracker.calculate_alliance_overlap("UKR", "POL")
    assert overlap_score > 0.0

    # GEXF export
    with tempfile.TemporaryDirectory() as temp_dir:
        export_path = Path(temp_dir) / "alliance_graph.gexf"
        xml = tracker.export_gexf(export_path, mode="bipartite")
        assert export_path.exists()
        assert "gexf" in xml
