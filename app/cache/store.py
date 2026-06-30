"""
In-process TTL cache — a Redis-compatible interface using cachetools.
When Redis is available (REDIS_URL env var set), it proxies to Redis instead.
All cache keys are namespaced under "khap:".

Usage:
    from app.cache.store import cache
    cache.set("key", value, ttl=300)
    value = cache.get("key")
    cache.delete("key")
"""

import os
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL")
NAMESPACE = "khap:"


class _MemoryCache:
    """TTL-aware in-memory cache backed by cachetools."""

    def __init__(self):
        from cachetools import TTLCache
        self._default = TTLCache(maxsize=1024, ttl=300)
        self._stores: dict[int, Any] = {}

    def _store(self, ttl: int):
        if ttl not in self._stores:
            from cachetools import TTLCache
            self._stores[ttl] = TTLCache(maxsize=512, ttl=ttl)
        return self._stores[ttl]

    def get(self, key: str) -> Optional[Any]:
        for store in [self._default, *self._stores.values()]:
            if key in store:
                return store[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 300):
        self._store(ttl)[key] = value

    def delete(self, key: str):
        for store in [self._default, *self._stores.values()]:
            store.pop(key, None)

    def clear(self):
        self._default.clear()
        for s in self._stores.values():
            s.clear()


class _RedisCache:
    """Thin wrapper around Redis client with JSON serialisation."""

    def __init__(self, url: str):
        import redis
        self._r = redis.from_url(url, decode_responses=True)

    def get(self, key: str) -> Optional[Any]:
        try:
            val = self._r.get(NAMESPACE + key)
            return json.loads(val) if val is not None else None
        except Exception as e:
            logger.warning(f"Redis get failed: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        try:
            self._r.setex(NAMESPACE + key, ttl, json.dumps(value))
        except Exception as e:
            logger.warning(f"Redis set failed: {e}")

    def delete(self, key: str):
        try:
            self._r.delete(NAMESPACE + key)
        except Exception as e:
            logger.warning(f"Redis delete failed: {e}")

    def clear(self):
        try:
            for key in self._r.scan_iter(f"{NAMESPACE}*"):
                self._r.delete(key)
        except Exception as e:
            logger.warning(f"Redis clear failed: {e}")


def _build_cache():
    if REDIS_URL:
        try:
            c = _RedisCache(REDIS_URL)
            logger.info("Cache: using Redis")
            return c
        except Exception as e:
            logger.warning(f"Redis unavailable ({e}), falling back to memory cache")
    return _MemoryCache()


cache = _build_cache()


def cached(key_fn, ttl: int = 300):
    """Decorator — caches the return value of an async or sync function."""
    import functools
    import asyncio

    def decorator(fn):
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = cache.get(key)
            if hit is not None:
                return hit
            result = await fn(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            key = key_fn(*args, **kwargs)
            hit = cache.get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            cache.set(key, result, ttl=ttl)
            return result

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper
    return decorator
