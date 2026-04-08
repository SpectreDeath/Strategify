"""Tests for OSINT pipeline: adapters, cache, and feature computation."""

import tempfile
from pathlib import Path

from strategify.osint.adapters import (
    ACLEDAdapter,
    BaseAdapter,
    GDELTAdapter,
    WorldBankAdapter,
    _normalize_event,
)
from strategify.osint.cache import SQLiteCache
from strategify.osint.pipeline import FeaturePipeline

# ---------------------------------------------------------------------------
# SQLiteCache
# ---------------------------------------------------------------------------


class TestSQLiteCache:
    def test_put_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("key1", {"value": 42})
            assert cache.get("key1") == {"value": 42}

    def test_get_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            assert cache.get("missing") is None

    def test_ttl_expiry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("key1", "value1", ttl=0)
            # Immediately expired
            assert cache.get("key1") is None

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("key1", "value1")
            cache.delete("key1")
            assert cache.get("key1") is None

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("a", 1)
            cache.put("b", 2)
            cache.clear()
            assert cache.get("a") is None
            assert cache.get("b") is None

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("a", 1)
            cache.put("b", 2, ttl=0)  # expired
            stats = cache.stats()
            assert stats["total_entries"] == 2
            assert stats["expired_entries"] == 1

    def test_purge_expired(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("a", 1)
            cache.put("b", 2, ttl=0)
            deleted = cache.purge_expired()
            assert deleted == 1
            assert cache.get("a") == 1
            assert cache.get("b") is None

    def test_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = SQLiteCache(Path(tmpdir) / "test.db")
            cache.put("key", "old")
            cache.put("key", "new")
            assert cache.get("key") == "new"


# ---------------------------------------------------------------------------
# Adapters
# ---------------------------------------------------------------------------


class TestNormalizeEvent:
    def test_basic_event(self):
        event = _normalize_event(
            source="test",
            timestamp="2024-01-01T00:00:00",
            region_id="alpha",
            text="Test event",
        )
        assert event["source"] == "test"
        assert event["region_id"] == "alpha"
        assert event["text"] == "Test event"
        assert event["lat"] is None
        assert event["metadata"] == {}

    def test_event_with_location(self):
        event = _normalize_event(
            source="test",
            timestamp="2024-01-01",
            region_id="alpha",
            text="Test",
            lat=50.0,
            lon=30.0,
            event_type="conflict",
            value=5.0,
            metadata={"key": "val"},
        )
        assert event["lat"] == 50.0
        assert event["lon"] == 30.0
        assert event["event_type"] == "conflict"
        assert event["value"] == 5.0


class TestGDELTAdapter:
    def test_name(self):
        adapter = GDELTAdapter()
        assert adapter.name == "gdelt"

    def test_is_base_adapter(self):
        assert isinstance(GDELTAdapter(), BaseAdapter)

    def test_classify(self):
        assert GDELTAdapter._classify("Military troops deployed") == "conflict"
        assert GDELTAdapter._classify("Sanctions imposed on country") == "economic"
        assert GDELTAdapter._classify("Diplomatic summit held") == "diplomacy"
        assert GDELTAdapter._classify("Protest rally in capital") == "protest"
        assert GDELTAdapter._classify("Random news article") == "general"


class TestACLEDAdapter:
    def test_name(self):
        adapter = ACLEDAdapter()
        assert adapter.name == "acled"

    def test_no_api_key_returns_empty(self):
        adapter = ACLEDAdapter(api_key="")
        events = adapter.fetch({"alpha": ["Ukraine"]})
        assert events == []


class TestWorldBankAdapter:
    def test_name(self):
        adapter = WorldBankAdapter()
        assert adapter.name == "worldbank"

    def test_skips_non_iso_codes(self):
        adapter = WorldBankAdapter()
        events = adapter.fetch({"alpha": ["NotA3LetterCode"]})
        assert events == []


# ---------------------------------------------------------------------------
# FeaturePipeline
# ---------------------------------------------------------------------------


class TestFeaturePipeline:
    def test_empty_keywords_returns_empty(self):
        pipeline = FeaturePipeline()
        features = pipeline.compute()
        assert features == {}

    def test_compute_with_mock_adapter(self):
        """Test pipeline with a mock adapter that returns fixed events."""

        class MockAdapter(BaseAdapter):
            @property
            def name(self):
                return "mock"

            def fetch(self, region_keywords, **kwargs):
                events = []
                for rid, keywords in region_keywords.items():
                    events.append(
                        _normalize_event(
                            source="mock",
                            timestamp="2024-01-01",
                            region_id=rid,
                            text=f"Conflict in {keywords[0]}",
                            event_type="conflict",
                        )
                    )
                return events

        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = FeaturePipeline(
                adapters=[MockAdapter()],
                cache_path=str(Path(tmpdir) / "test.db"),
            )
            features = pipeline.compute({"alpha": ["Ukraine"], "bravo": ["Russia"]})

            assert "alpha" in features
            assert "bravo" in features
            assert features["alpha"]["event_count"] == 1.0
            assert features["alpha"]["conflict_count"] == 1.0
            assert features["alpha"]["tension_score"] >= 0.0

    def test_caching(self):
        """Verify pipeline caches results."""

        class MockAdapter(BaseAdapter):
            def __init__(self):
                self.fetch_count = 0

            @property
            def name(self):
                return "mock"

            def fetch(self, region_keywords, **kwargs):
                self.fetch_count += 1
                return [
                    _normalize_event(
                        source="mock",
                        timestamp="2024-01-01",
                        region_id="alpha",
                        text="Test",
                    )
                ]

        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = MockAdapter()
            pipeline = FeaturePipeline(
                adapters=[adapter],
                cache_path=str(Path(tmpdir) / "test.db"),
                cache_ttl=3600,
            )

            pipeline.compute({"alpha": ["test"]})
            assert adapter.fetch_count == 1

            # Second call should use cache
            pipeline.compute({"alpha": ["test"]})
            assert adapter.fetch_count == 1  # not incremented

            # Force refresh should bypass cache
            pipeline.compute({"alpha": ["test"]}, force_refresh=True)
            assert adapter.fetch_count == 2

    def test_summary(self):
        pipeline = FeaturePipeline(adapters=[GDELTAdapter()])
        summary = pipeline.summary()
        assert "adapters" in summary
        assert "gdelt" in summary["adapters"]

    def test_get_events_empty(self):
        pipeline = FeaturePipeline()
        assert pipeline.get_events("alpha") == []

    def test_get_features_empty(self):
        pipeline = FeaturePipeline()
        assert pipeline.get_features("alpha") == {}
