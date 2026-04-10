"""OSINT data sources: GDELT events API and news RSS feed ingestion.

Provides functions to fetch real-world geopolitical events and news
for use in simulation initialization and calibration.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

# GDELT GKG API base URL
GDELT_GKG_URL = "https://api.gdeltproject.org/api/v2/doc/doc"

# Default search terms for geopolitical events
DEFAULT_KEYWORDS = [
    "military",
    "sanctions",
    "diplomacy",
    "trade war",
    "nuclear",
    "border",
    "conflict",
    "alliance",
]


def fetch_gdelt_events(
    query: str,
    timespan: str = "24h",
    max_records: int = 50,
) -> list[dict[str, Any]]:
    """Fetch events from the GDELT 2.0 GKG API.

    Parameters
    ----------
    query:
        Search query (e.g. ``"Ukraine Russia"``, ``"sanctions"``).
    timespan:
        Time window: ``"24h"``, ``"1h"``, ``"15min"``.
    max_records:
        Maximum number of records to return.

    Returns
    -------
    list[dict]
        List of event dicts with keys: ``title``, ``url``, ``seendate``,
        ``domain``, ``language``, ``sourcecountry``.
    """
    params = urllib.parse.urlencode(
        {
            "query": query,
            "mode": "artlist",
            "maxrecords": max_records,
            "format": "json",
            "timespan": timespan,
        }
    )
    url = f"{GDELT_GKG_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "strategify/0.5"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("articles", [])
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
        TimeoutError,
    ) as exc:
        logger.warning("GDELT fetch failed for query '%s': %s", query, exc)
        return []


def fetch_gdelt_for_regions(
    region_keywords: dict[str, list[str]],
    timespan: str = "24h",
) -> dict[str, list[dict[str, Any]]]:
    """Fetch GDELT events for multiple regions.

    Parameters
    ----------
    region_keywords:
        Mapping of ``region_id`` -> list of search keywords.
        Example: ``{"alpha": ["Ukraine", "Kyiv"], "bravo": ["Russia", "Moscow"]}``
    timespan:
        Time window for GDELT query.

    Returns
    -------
    dict
        ``region_id`` -> list of event dicts.
    """
    results = {}
    for rid, keywords in region_keywords.items():
        query = " OR ".join(keywords)
        events = fetch_gdelt_events(query, timespan=timespan)
        results[rid] = events
        logger.info("Fetched %d events for region %s", len(events), rid)
    return results


def fetch_rss_feed(
    url: str,
    max_items: int = 20,
) -> list[dict[str, str]]:
    """Fetch and parse an RSS/Atom feed.

    Parameters
    ----------
    url:
        RSS or Atom feed URL.
    max_items:
        Maximum items to return.

    Returns
    -------
    list[dict]
        List of dicts with ``title``, ``link``, ``published``, ``summary``.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "strategify/0.3"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        logger.warning("RSS fetch failed for %s: %s", url, exc)
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        logger.warning("RSS parse failed for %s: %s", url, exc)
        return []

    items = []

    # RSS 2.0 format
    for item in root.iter("item"):
        if len(items) >= max_items:
            break
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        pub = item.findtext("pubDate", "") or item.findtext("published", "")
        desc = item.findtext("description", "") or item.findtext("summary", "")
        items.append(
            {
                "title": title,
                "link": link,
                "published": pub,
                "summary": desc[:500],
            }
        )

    # Atom format fallback
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            if len(items) >= max_items:
                break
            title = entry.findtext("atom:title", "", ns) or entry.findtext("{http://www.w3.org/2005/Atom}title", "")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link", ns)
            link = link_el.get("href", "") if link_el is not None else ""
            pub = entry.findtext("atom:published", "", ns) or entry.findtext(
                "{http://www.w3.org/2005/Atom}published", ""
            )
            summary = entry.findtext("atom:summary", "", ns) or entry.findtext(
                "{http://www.w3.org/2005/Atom}summary", ""
            )
            items.append(
                {
                    "title": title,
                    "link": link,
                    "published": pub,
                    "summary": summary[:500],
                }
            )

    return items


def events_to_texts(
    events: list[dict[str, Any]],
    field: str = "title",
) -> list[str]:
    """Extract text strings from event dicts for sentiment analysis.

    Parameters
    ----------
    events:
        List of event dicts (from GDELT or RSS).
    field:
        Which field to extract: ``"title"`` or ``"summary"``.

    Returns
    -------
    list[str]
        Non-empty text strings.
    """
    return [e[field] for e in events if e.get(field)]


def compute_event_features(
    events: list[dict[str, Any]],
) -> dict[str, float]:
    """Compute aggregate features from a list of events.

    Returns
    -------
    dict
        ``event_count``, ``unique_domains``, ``freshness_hours`` (avg).
    """
    if not events:
        return {"event_count": 0.0, "unique_domains": 0.0, "freshness_hours": 0.0}

    domains = set()
    hours_list = []
    now = datetime.now(UTC)

    for e in events:
        domains.add(e.get("domain", ""))
        seen = e.get("seendate", "")
        if seen:
            try:
                dt = datetime.strptime(seen[:19], "%Y%m%dT%H%M%S")
                hours_list.append((now - dt).total_seconds() / 3600)
            except (ValueError, TypeError):
                pass

    return {
        "event_count": float(len(events)),
        "unique_domains": float(len(domains)),
        "freshness_hours": sum(hours_list) / len(hours_list) if hours_list else 0.0,
    }
