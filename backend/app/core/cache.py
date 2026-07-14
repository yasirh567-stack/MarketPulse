"""TTL cache abstraction: Redis if configured, otherwise a DB-backed table.

Redis is a nice-to-have accelerator, never a requirement — `get_cache()`
picks the backend once based on `REDIS_URL` and every caller uses the same
tiny interface regardless of which backend is active.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.cache import CacheEntry

class Cache(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl_seconds: int) -> None: ...


class DbCache:
    """Cache backed by the `cache_entries` table. Works with any DB engine
    the app already uses, so there's no new infra requirement for demo/local use."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str) -> Any | None:
        row = self.db.get(CacheEntry, key)
        if row is None:
            return None
        if row.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            self.db.delete(row)
            self.db.commit()
            return None
        return json.loads(row.value)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        row = self.db.get(CacheEntry, key)
        serialized = json.dumps(value, default=str)
        if row is None:
            row = CacheEntry(key=key, value=serialized, expires_at=expires_at)
            self.db.add(row)
        else:
            row.value = serialized
            row.expires_at = expires_at
        self.db.commit()


class RedisCache:
    """Thin wrapper so Redis satisfies the same Cache protocol. Only
    constructed when REDIS_URL is set and the `redis` package is importable."""

    def __init__(self, url: str):
        import redis  # local import: optional dependency

        self._client = redis.Redis.from_url(url)

    def get(self, key: str) -> Any | None:
        raw = self._client.get(key)
        return json.loads(raw) if raw is not None else None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._client.setex(key, ttl_seconds, json.dumps(value, default=str))


_redis_cache: RedisCache | None = None
_redis_unavailable = False


def get_cache(db: Session) -> Cache:
    """Return the active cache backend. Falls back to the DB cache if Redis
    is configured but unreachable (e.g. wrong URL, service not running)."""
    global _redis_cache, _redis_unavailable
    settings = get_settings()
    if settings.redis_url and not _redis_unavailable:
        if _redis_cache is None:
            try:
                _redis_cache = RedisCache(settings.redis_url)
                _redis_cache._client.ping()
            except Exception:
                _redis_unavailable = True
                _redis_cache = None
        if _redis_cache is not None:
            return _redis_cache
    return DbCache(db)
