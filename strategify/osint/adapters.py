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
