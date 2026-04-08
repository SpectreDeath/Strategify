"""Tests for OSINT modules.

Tests feature pipeline, cache, and adapters.
"""

from typing import Any

from strategify.osint.adapters import BaseAdapter
from strategify.osint.cache import SQLiteCache
from strategify.osint.features import analyze_sentiment, analyze_texts_sentiment
from strategify.osint.pipeline import FeaturePipeline


class MockAdapter(BaseAdapter):
    """Mock adapter for testing."""

    def __init__(self, mock_data=None):
        self.mock_data = mock_data or []

    @property
    def name(self) -> str:
        return "mock"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        return self.mock_data


class TestFeaturePipeline:
    """Tests for FeaturePipeline."""

    def test_pipeline_init(self):
        pipeline = FeaturePipeline(
            region_keywords={"RUS": ["Russia"], "UKR": ["Ukraine"]},
            adapters=[MockAdapter([])],
            cache_ttl=60,
        )
        assert pipeline.cache_ttl == 60
        assert len(pipeline.adapters) == 1
        assert "RUS" in pipeline.region_keywords
        assert "UKR" in pipeline.region_keywords

    def test_pipeline_with_default_keywords(self):
        pipeline = FeaturePipeline()
        assert isinstance(pipeline.region_keywords, dict)

    def test_pipeline_with_custom_cache_ttl(self):
        pipeline = FeaturePipeline(cache_ttl=300)
        assert pipeline.cache_ttl == 300


class TestSQLiteCache:
    """Tests for SQLiteCache."""

    def test_cache_init_with_path(self, tmp_path):
        cache_path = tmp_path / "test_cache.db"
        cache = SQLiteCache(str(cache_path))
        assert cache._db_path is not None
        assert str(cache_path) in str(cache._db_path)

    def test_cache_with_default_path(self):
        cache = SQLiteCache()
        assert cache._db_path is not None


class TestSentimentAnalysis:
    """Tests for sentiment analysis."""

    def test_analyze_sentiment_returns_dict(self):
        result = analyze_sentiment("Peace talks resume in Geneva")
        assert isinstance(result, dict)
        assert "compound" in result

    def test_analyze_texts_sentiment_returns_dict(self):
        texts = ["Peace talks", "War escalation", "Trade deal"]
        result = analyze_texts_sentiment(texts)
        assert isinstance(result, dict)


class TestAdapterIntegration:
    """Tests for adapter integration."""

    def test_adapter_fetch_method_exists(self):
        adapter = MockAdapter([])
        assert callable(adapter.fetch)
