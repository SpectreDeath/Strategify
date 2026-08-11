"""Unit tests for Strategify OSINT adapters and feed parsers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from strategify.osint.acled import ACLEDFeed
from strategify.osint.gdelt import GDELTFeed
from strategify.osint.worldbank import WorldBankFeed


class TestOSINTAdapters:
    @patch("httpx.get")
    def test_gdelt_feed_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [
                {
                    "title": "Diplomatic Summit Announced",
                    "url": "https://example.com/news1",
                    "seendate": "20260810T120000Z",
                    "socialimage": "",
                    "domain": "example.com",
                    "language": "English",
                    "sourcecountry": "United States",
                }
            ]
        }
        mock_get.return_value = mock_response

        feed = GDELTFeed()
        articles = feed.fetch_events(query="diplomacy", limit=5)
        assert len(articles) == 1
        assert articles[0]["title"] == "Diplomatic Summit Announced"

    @patch("httpx.get")
    def test_acled_feed_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "event_id_cnt": "ACLED1001",
                    "event_date": "2026-08-10",
                    "event_type": "Protests",
                    "actor1": "Protesters",
                    "country": "RegionA",
                    "fatalities": "0",
                }
            ]
        }
        mock_get.return_value = mock_response

        feed = ACLEDFeed()
        events = feed.fetch_events(country="RegionA", limit=5)
        assert len(events) == 1
        assert events[0]["event_type"] == "Protests"

    @patch("httpx.get")
    def test_worldbank_feed_fetch(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"page": 1, "pages": 1, "per_page": 50, "total": 1},
            [
                {
                    "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
                    "country": {"id": "USA", "value": "United States"},
                    "value": 25000000000000,
                    "date": "2025",
                }
            ],
        ]
        mock_get.return_value = mock_response

        feed = WorldBankFeed()
        data = feed.fetch_indicator(country="USA", indicator="NY.GDP.MKTP.CD")
        assert len(data) == 1
        assert data[0]["value"] == 25000000000000
