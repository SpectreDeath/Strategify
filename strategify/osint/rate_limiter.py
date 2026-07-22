"""Federal API Rate Limiting & Caching Layer.

Implements token-bucket rate limiting throttlers to comply with federal API guidelines
(e.g., max 1 request/sec for NIH RePORTER V2 / NCBI E-Utilities) and caches responses
in SQLiteCache to prevent redundant network calls.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from strategify.osint.cache import SQLiteCache

logger = logging.getLogger(__name__)


class FederalApiCacheThrottle:
    """Rate-limiting throttler and SQLite cache for federal APIs.

    Parameters
    ----------
    min_interval_seconds : float
        Minimum delay between consecutive requests (default: 1.0s).
    db_path : str
        Path to SQLite cache database file.
    """

    def __init__(
        self,
        min_interval_seconds: float = 1.0,
        db_path: str = "federal_api_cache.db",
    ) -> None:
        self.min_interval_seconds = min_interval_seconds
        self.last_request_time: float = 0.0
        self.cache = SQLiteCache(db_path=db_path)

    def throttle(self) -> None:
        """Enforce rate limiting delay between consecutive requests."""
        now = time.time()
        elapsed = now - self.last_request_time
        if elapsed < self.min_interval_seconds:
            sleep_time = self.min_interval_seconds - elapsed
            logger.info("FederalApiCacheThrottle throttling for %.2f seconds", sleep_time)
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def execute_with_cache(
        self,
        cache_key: str,
        fetch_fn: Callable[[], Any],
        ttl_seconds: int = 3600,
    ) -> Any:
        """Execute request with rate limiting and SQLite caching.

        Parameters
        ----------
        cache_key : str
            Unique key for the cached payload.
        fetch_fn : Callable[[], Any]
            Function executing the underlying network fetch.
        ttl_seconds : int
            Cache time-to-live in seconds (default: 3600s / 1hr).

        Returns
        -------
        Any
            Cached or freshly fetched response.
        """
        cached_val = self.cache.get(cache_key)
        if cached_val is not None:
            logger.info("FederalApiCacheThrottle cache HIT for key '%s'", cache_key)
            return cached_val

        # Cache miss -> throttle and execute
        self.throttle()
        fresh_val = fetch_fn()
        self.cache.put(cache_key, fresh_val, ttl=ttl_seconds)
        logger.info("FederalApiCacheThrottle cache MISS for key '%s' -> fetched and cached", cache_key)
        return fresh_val
