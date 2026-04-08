"""OSINT data source adapters for ACLED, GDELT, and World Bank.

Each adapter fetches events or indicators from a specific source,
normalizes them to a common schema, and returns a list of event dicts.

Common event schema::

    {
        "source": "acled" | "gdelt" | "worldbank",
        "timestamp": "ISO 8601 string",
        "region_id": "internal region ID",
        "text": "headline or description",
        "lat": float | None,
        "lon": float | None,
        "event_type": "conflict" | "protest" | "diplomacy" | "economic" | ...,
        "value": float | None,
        "metadata": dict,
    }
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Common schema
# ---------------------------------------------------------------------------


def _normalize_event(
    source: str,
    timestamp: str,
    region_id: str,
    text: str,
    lat: float | None = None,
    lon: float | None = None,
    event_type: str = "unknown",
    value: float | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]:
    """Create a normalized event dict."""
    return {
        "source": source,
        "timestamp": timestamp,
        "region_id": region_id,
        "text": text,
        "lat": lat,
        "lon": lon,
        "event_type": event_type,
        "value": value,
        "metadata": metadata or {},
    }


# ---------------------------------------------------------------------------
# Base adapter
# ---------------------------------------------------------------------------


class BaseAdapter(ABC):
    """Abstract base class for OSINT data adapters.

    Subclasses must implement ``fetch()`` to return normalized events.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name."""

    @abstractmethod
    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch events for the given regions.

        Parameters
        ----------
        region_keywords:
            ``{region_id: [keyword, ...]}``.
        date_range:
            Optional ``(start_iso, end_iso)`` tuple.
        max_records:
            Maximum events per region.

        Returns
        -------
        list[dict]
            Normalized event dicts.
        """


# ---------------------------------------------------------------------------
# GDELT adapter
# ---------------------------------------------------------------------------


class GDELTAdapter(BaseAdapter):
    """Adapter for the GDELT 2.0 GKG API.

    Fetches news articles matching geopolitical keywords and normalizes
    them to the common event schema.
    """

    _GKG_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

    @property
    def name(self) -> str:
        return "gdelt"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for region_id, keywords in region_keywords.items():
            query = " OR ".join(keywords)
            params = urllib.parse.urlencode(
                {
                    "query": query,
                    "mode": "artlist",
                    "maxrecords": min(max_records, 250),
                    "format": "json",
                    "timespan": "24h",
                }
            )
            url = f"{self._GKG_URL}?{params}"

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "strategify/0.5"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for article in data.get("articles", []):
                    text = article.get("title", "")
                    timestamp = article.get("seendate", "")
                    if timestamp and len(timestamp) >= 8:
                        try:
                            dt = datetime.strptime(timestamp[:19], "%Y%m%dT%H%M%S")
                            timestamp = dt.isoformat()
                        except ValueError:
                            pass

                    events.append(
                        _normalize_event(
                            source="gdelt",
                            timestamp=timestamp,
                            region_id=region_id,
                            text=text,
                            event_type=self._classify(text),
                            metadata={
                                "url": article.get("url", ""),
                                "domain": article.get("domain", ""),
                                "language": article.get("language", ""),
                            },
                        )
                    )

            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                json.JSONDecodeError,
                TimeoutError,
            ) as exc:
                logger.warning("GDELT fetch failed for region '%s': %s", region_id, exc)

        return events

    @staticmethod
    def _classify(text: str) -> str:
        """Simple keyword-based event classification."""
        text_lower = text.lower()
        if any(
            w in text_lower for w in ("military", "army", "troops", "war", "conflict", "attack")
        ):
            return "conflict"
        if any(w in text_lower for w in ("sanctions", "embargo", "trade war")):
            return "economic"
        if any(w in text_lower for w in ("diplomat", "summit", "treaty", "alliance", "negotiat")):
            return "diplomacy"
        if any(w in text_lower for w in ("protest", "rally", "demonstrat")):
            return "protest"
        return "general"


# ---------------------------------------------------------------------------
# ACLED adapter (stub)
# ---------------------------------------------------------------------------


class ACLEDAdapter(BaseAdapter):
    """Adapter for the ACLED conflict data API.

    Requires an ACLED API key (set via ``api_key`` parameter or
    ``ACLED_API_KEY`` environment variable).

    Note: This adapter returns an empty list if no API key is configured,
    allowing the pipeline to function with fallback data.
    """

    _ACLED_URL = "https://api.acleddata.com/acled/read"

    def __init__(self, api_key: str | None = None) -> None:
        import os

        self._api_key = api_key or os.environ.get("ACLED_API_KEY", "")

    @property
    def name(self) -> str:
        return "acled"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        if not self._api_key:
            logger.info("ACLED adapter: no API key configured, returning empty results")
            return []

        events: list[dict[str, Any]] = []
        for region_id, keywords in region_keywords.items():
            country = keywords[0] if keywords else ""
            params = urllib.parse.urlencode(
                {
                    "key": self._api_key,
                    "country": country,
                    "limit": max_records,
                    "format": "json",
                }
            )
            url = f"{self._ACLED_URL}?{params}"

            try:
                req = urllib.request.Request(url, headers={"User-Agent": "strategify/0.5"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for event in data.get("data", []):
                    events.append(
                        _normalize_event(
                            source="acled",
                            timestamp=event.get("event_date", ""),
                            region_id=region_id,
                            text=event.get("notes", ""),
                            lat=_safe_float(event.get("latitude")),
                            lon=_safe_float(event.get("longitude")),
                            event_type=event.get("event_type", "conflict").lower(),
                            value=_safe_float(event.get("fatalities", 0)),
                            metadata={
                                "actor1": event.get("actor1", ""),
                                "actor2": event.get("actor2", ""),
                                "sub_event_type": event.get("sub_event_type", ""),
                            },
                        )
                    )

            except (
                urllib.error.URLError,
                urllib.error.HTTPError,
                json.JSONDecodeError,
                TimeoutError,
            ) as exc:
                logger.warning("ACLED fetch failed for region '%s': %s", region_id, exc)

        return events


# ---------------------------------------------------------------------------
# World Bank adapter
# ---------------------------------------------------------------------------


class WorldBankAdapter(BaseAdapter):
    """Adapter for World Bank indicators API.

    Fetches economic/development indicators (GDP, population, etc.)
    and returns them as normalized events.
    """

    _WB_URL = "https://api.worldbank.org/v2"

    # Indicator codes → event type labels
    INDICATORS = {
        "NY.GDP.MKTP.CD": "gdp",
        "SP.POP.TOTL": "population",
        "NE.EXP.GNFS.CD": "exports",
        "NE.IMP.GNFS.CD": "imports",
        "MS.MIL.XPND.GD.ZS": "military_spending",
    }

    @property
    def name(self) -> str:
        return "worldbank"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for region_id, keywords in region_keywords.items():
            country_code = keywords[0] if keywords else ""
            if len(country_code) != 3:
                logger.debug("WorldBank: skipping '%s' (expected 3-letter ISO code)", country_code)
                continue

            for indicator_code, label in self.INDICATORS.items():
                url = (
                    f"{self._WB_URL}/country/{country_code}/indicator/"
                    f"{indicator_code}?format=json&per_page=5&date=2020:2025"
                )

                try:
                    req = urllib.request.Request(url, headers={"User-Agent": "strategify/0.5"})
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        data = json.loads(resp.read().decode("utf-8"))

                    if len(data) < 2:
                        continue

                    for entry in data[1]:
                        value = entry.get("value")
                        year = entry.get("date", "")
                        if value is not None:
                            events.append(
                                _normalize_event(
                                    source="worldbank",
                                    timestamp=f"{year}-01-01T00:00:00",
                                    region_id=region_id,
                                    text=f"{label}: {value:,.0f}"
                                    if isinstance(value, (int, float))
                                    else f"{label}: {value}",
                                    event_type="economic",
                                    value=float(value) if value else None,
                                    metadata={
                                        "indicator": indicator_code,
                                        "indicator_label": label,
                                        "country_code": country_code,
                                        "year": year,
                                    },
                                )
                            )

                except (
                    urllib.error.URLError,
                    urllib.error.HTTPError,
                    json.JSONDecodeError,
                    TimeoutError,
                ) as exc:
                    logger.debug(
                        "WorldBank fetch failed for %s/%s: %s",
                        region_id,
                        indicator_code,
                        exc,
                    )

        return events


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


# ---------------------------------------------------------------------------
# ReliefWeb Adapter (Free Humanitarian Data)
# ---------------------------------------------------------------------------


class ReliefWebAdapter(BaseAdapter):
    """Adapter for ReliefWeb API (free, no API key required).

    Provides humanitarian news, disaster alerts, and crisis data.
    API: https://reliefweb.int/help/api
    """

    _API_URL = "https://api.reliefweb.int/v1/reports"

    @property
    def name(self) -> str:
        return "reliefweb"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for region_id, keywords in region_keywords.items():
            query_term = " OR ".join(keywords[:3])

            post_data = {
                "limit": min(max_records, 100),
                "query": {"value": query_term, "operator": "OR"},
                "fields": {"include": ["title", "date", "primary_country", "url"]},
            }

            try:
                data = _post_json(self._API_URL, post_data)
                for item in data.get("data", []):
                    fields = item.get("fields", {})
                    country = fields.get("primary_country", {})
                    country_name = country.get("name", "") if isinstance(country, dict) else ""

                    events.append(
                        _normalize_event(
                            source="reliefweb",
                            timestamp=fields.get("date", {}).get("created", ""),
                            region_id=region_id,
                            text=fields.get("title", ""),
                            event_type="humanitarian",
                            metadata={
                                "url": fields.get("url", ""),
                                "country": country_name,
                            },
                        )
                    )
            except Exception as exc:
                logger.warning("ReliefWeb fetch failed for %s: %s", region_id, exc)

        return events


# ---------------------------------------------------------------------------
# Crisis Monitor Adapter (Free Conflict Data)
# ---------------------------------------------------------------------------


class CrisisMonitorAdapter(BaseAdapter):
    """Adapter for UC Berkeley's Crisis Data (free, no API key).

    Provides historical and current conflict event data.
    """

    _API_URL = "https://ucr.cre/pr/"

    @property
    def name(self) -> str:
        return "crisis_monitor"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for region_id, keywords in region_keywords.items():
            query = "+".join(keywords[:3])

            try:
                url = f"https://api.crisis-monitor.org/v1/events?q={query}&limit={max_records}"
                req = urllib.request.Request(
                    url,
                    headers={"User-Agent": "strategify/1.0", "Accept": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for event in data.get("events", []):
                    events.append(
                        _normalize_event(
                            source="crisis_monitor",
                            timestamp=event.get("date", ""),
                            region_id=region_id,
                            text=event.get("title", ""),
                            event_type=event.get("type", "conflict"),
                            value=event.get("fatalities"),
                            metadata=event.get("metadata", {}),
                        )
                    )
            except Exception as exc:
                logger.warning("CrisisMonitor fetch failed for %s: %s", region_id, exc)

        return events


def _post_json(url: str, data: dict[str, Any], timeout: int = 30) -> dict:
    """POST JSON data to URL and return parsed response."""
    import json

    json_data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=json_data,
        headers={
            "User-Agent": "strategify/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------------------------------------------------------------------------
# Wikipedia Events Adapter (Free Historical/Current Events)
# ---------------------------------------------------------------------------


class WikipediaEventAdapter(BaseAdapter):
    """Adapter for Wikipedia API (free, no API key required).

    Fetches current events and historical geopolitical events from Wikipedia.
    Uses the REST API for related pages and MediaWiki API for search.
    """

    _RELATED_URL = "https://en.wikipedia.org/api/rest_v1/page/related/"
    _SEARCH_URL = "https://en.wikipedia.org/w/api.php"

    _REGION_TOPICS: dict[str, list[str]] = {
        "UKR": ["2022_Russian_invasion_of_Ukraine", "War_in_Donbas", "Ukraine_crisis"],
        "RUS": ["Russia", "Russian_invasion_of_Ukraine", "Russia_Ukraine_war"],
        "USA": ["United_States", "NATO", "Foreign_relations_of_the_United_States"],
        "CHN": ["China", "South_China_Sea", "Taiwan"],
        "IRN": ["Iran", "Iran_nuclear_program", "Iran_Israel_conflict"],
        "ISR": ["Israel", "Israel_Gaza_war", "Israeli_Palestinian_conflict"],
        "IND": ["India", "India_Pakistan", "India_China"],
        "PAK": ["Pakistan", "India_Pakistan", "Afghanistan_Pakistan"],
    }

    @property
    def name(self) -> str:
        return "wikipedia"

    def fetch(
        self,
        region_keywords: dict[str, list[str]],
        date_range: tuple[str, str] | None = None,
        max_records: int = 50,
    ) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []

        for region_id, keywords in region_keywords.items():
            topic_pages = self._REGION_TOPICS.get(region_id, [])

            for topic in topic_pages[:3]:
                try:
                    topic_events = self._fetch_related_events(topic, region_id, max_records // 3)
                    events.extend(topic_events)
                except Exception as exc:
                    logger.warning("Wikipedia fetch failed for %s/%s: %s", region_id, topic, exc)

            search_events = self._search_events(keywords[:2], region_id, max_records // 3)
            events.extend(search_events)

        return events[:max_records]

    def _fetch_related_events(
        self, topic: str, region_id: str, max_records: int
    ) -> list[dict[str, Any]]:
        """Fetch events from Wikipedia related pages."""
        events: list[dict[str, Any]] = []

        try:
            url = f"{self._RELATED_URL}{topic}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "strategify/1.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for page in data.get("pages", [])[:max_records]:
                title = page.get("title", "")
                extract = page.get("extract", "")

                if title and extract:
                    timestamp = self._extract_date_from_title(
                        title
                    ) or self._extract_date_from_text(extract)
                    url_title = urllib.parse.quote(title.replace(" ", "_"))

                    events.append(
                        _normalize_event(
                            source="wikipedia",
                            timestamp=timestamp,
                            region_id=region_id,
                            text=f"{title}: {extract[:200]}",
                            event_type=self._classify_event(extract),
                            metadata={
                                "url": f"https://en.wikipedia.org/wiki/{url_title}",
                                "title": title,
                            },
                        )
                    )
        except Exception:
            pass

        return events

    def _search_events(
        self, keywords: list[str], region_id: str, max_records: int
    ) -> list[dict[str, Any]]:
        """Search Wikipedia for events matching keywords."""
        events: list[dict[str, Any]] = []

        query = " OR ".join(keywords)
        params = urllib.parse.urlencode(
            {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": max_records,
                "utf8": 1,
            }
        )

        try:
            url = f"{self._SEARCH_URL}?{params}"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "strategify/1.0"},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for result in data.get("query", {}).get("search", []):
                title = result.get("title", "")
                snippet = result.get("snippet", "").replace("<br>", " ")
                url_title = urllib.parse.quote(title.replace(" ", "_"))

                events.append(
                    _normalize_event(
                        source="wikipedia",
                        timestamp=datetime.now().isoformat(),
                        region_id=region_id,
                        text=f"{title}: {snippet[:150]}",
                        event_type=self._classify_event(snippet),
                        metadata={
                            "url": f"https://en.wikipedia.org/wiki/{url_title}",
                            "page_id": result.get("pageid"),
                        },
                    )
                )
        except Exception:
            pass

        return events

    def _extract_date_from_title(self, title: str) -> str | None:
        """Extract date from Wikipedia title."""
        import re

        patterns = [
            r"(\d{4})_",
            r"(\d{4})",
            r"(January|February|March|April|May|June|July|August|September|October|November|December)_(\d{4})",
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return f"{match.group(1)}-{match.group(2)}-01"

        return None

    def _extract_date_from_text(self, text: str) -> str:
        """Extract date from text or return current."""
        import re

        match = re.search(r"\b(19|20)\d{2}\b", text)
        if match:
            return f"{match.group(0)}-01-01"

        return datetime.now().isoformat()

    def _classify_event(self, text: str) -> str:
        """Classify event type from text."""
        text_lower = text.lower()

        conflict_keywords = [
            "war",
            "battle",
            "military",
            "invasion",
            "attack",
            "conflict",
            "casualties",
        ]
        if any(kw in text_lower for kw in conflict_keywords):
            return "conflict"

        diplomatic_keywords = [
            "summit",
            "treaty",
            "agreement",
            "diplomacy",
            "negotiation",
            "meeting",
        ]
        if any(kw in text_lower for kw in diplomatic_keywords):
            return "diplomacy"

        economic_keywords = ["sanctions", "trade", "economy", "gdp", "oil", "energy"]
        if any(kw in text_lower for kw in economic_keywords):
            return "economic"

        political_keywords = ["election", "government", "president", "parliament", "vote", "policy"]
        if any(kw in text_lower for kw in political_keywords):
            return "political"

        return "unknown"
