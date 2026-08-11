"""Unit tests for Strategify OSINT adapters and feed parsers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from strategify.osint.adapters import ACLEDAdapter, GDELTAdapter, WorldBankAdapter


class TestOSINTAdapters:
    @patch("urllib.request.urlopen")
    def test_gdelt_feed_fetch(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"""{
            "articles": [
                {
                    "title": "Diplomatic Summit Announced",
                    "url": "https://example.com/news1",
                    "seendate": "20260810T120000Z",
                    "domain": "example.com",
                    "language": "English",
                    "sourcecountry": "United States"
                }
            ]
        }"""
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        adapter = GDELTAdapter()
        events = adapter.fetch(region_keywords={"USA": ["diplomacy"]})
        assert len(events) == 1
        assert events[0]["text"] == "Diplomatic Summit Announced"

    @patch("urllib.request.urlopen")
    def test_acled_feed_fetch(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"""{
            "data": [
                {
                    "event_id_cnt": "ACLED1001",
                    "event_date": "2026-08-10",
                    "event_type": "Protests",
                    "actor1": "Protesters",
                    "country": "RegionA",
                    "fatalities": "0"
                }
            ]
        }"""
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        adapter = ACLEDAdapter(api_key="test_key", email="test@example.com")
        events = adapter.fetch(region_keywords={"RegionA": ["Protests"]})
        assert len(events) == 1
        assert events[0]["event_type"] == "conflict"

    @patch("urllib.request.urlopen")
    def test_worldbank_feed_fetch(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"""[
            {"page": 1, "pages": 1, "per_page": 50, "total": 1},
            [
                {
                    "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP"},
                    "country": {"id": "USA", "value": "United States"},
                    "value": 25000000000000,
                    "date": "2025"
                }
            ]
        ]"""
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        adapter = WorldBankAdapter()
        events = adapter.fetch(region_keywords={"USA": ["NY.GDP.MKTP.CD"]})
        assert len(events) == 1
        assert events[0]["value"] == 25000000000000
