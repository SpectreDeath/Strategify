"""SQLite-backed cache for OSINT data and computed features.

Provides a simple key-value cache with TTL support for avoiding
redundant API calls and storing intermediate results.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = Path(__file__).resolve().parent / ".cache" / "osint_cache.db"


class SQLiteCache:
    """Thread-safe SQLite key-value cache with optional TTL.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file. Created on first use.
    """

    def __init__(self, db_path: str | Path | None = None) -> None:
        self._db_path = Path(db_path) if db_path else _DEFAULT_DB_PATH
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = self._conn()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_expires ON cache(expires_at)")
            conn.commit()
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value, or None if missing/expired.

        Parameters
        ----------
        key:
            Cache key.

        Returns
        -------
        Any or None
            Deserialized JSON value, or None.
        """
        conn = self._conn()
        try:
            row = conn.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,)).fetchone()
        finally:
            conn.close()

        if row is None:
            return None

        value_str, expires_at = row
        if expires_at is not None and expires_at < time.time():
            self.delete(key)
            return None

        return json.loads(value_str)

    def put(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache.

        Parameters
        ----------
        key:
            Cache key.
        value:
            JSON-serializable value.
        ttl:
            Time-to-live in seconds. None means no expiry.
        """
        value_str = json.dumps(value, default=str)
        created_at = time.time()
        expires_at = created_at + ttl if ttl is not None else None

        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created_at, expires_at) VALUES (?, ?, ?, ?)",
                (key, value_str, created_at, expires_at),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, key: str) -> None:
        """Remove a key from the cache."""
        conn = self._conn()
        try:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
        finally:
            conn.close()

    def clear(self) -> None:
        """Remove all cached entries."""
        conn = self._conn()
        try:
            conn.execute("DELETE FROM cache")
            conn.commit()
        finally:
            conn.close()

    def purge_expired(self) -> int:
        """Remove all expired entries. Returns count deleted."""
        conn = self._conn()
        try:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def stats(self) -> dict[str, Any]:
        """Return cache statistics."""
        conn = self._conn()
        try:
            total = conn.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
            expired = conn.execute(
                "SELECT COUNT(*) FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),),
            ).fetchone()[0]
        finally:
            conn.close()
        return {"total_entries": total, "expired_entries": expired}
