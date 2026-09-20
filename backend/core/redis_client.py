import time
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class InMemoryCache:
    """Thread-safe and async-safe in-memory cache fallback for offline forensic workstations."""
    def __init__(self):
        self._store = {}
        self._expiry = {}
        self.hits = 0
        self.misses = 0

    async def get(self, key: str) -> Optional[str]:
        if key in self._store:
            exp = self._expiry.get(key)
            if exp and time.time() > exp:
                del self._store[key]
                del self._expiry[key]
                self.misses += 1
                return None
            self.hits += 1
            return self._store[key]
        self.misses += 1
        return None

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        self._store[key] = value
        if ex:
            self._expiry[key] = time.time() + ex
        elif key in self._expiry:
            del self._expiry[key]
        return True

    async def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        self._expiry.pop(key, None)
        return True

    def get_stats(self) -> dict:
        total = self.hits + self.misses
        ratio = round((self.hits / total * 100), 2) if total > 0 else 0.0
        return {
            "mode": "in_memory",
            "hits": self.hits,
            "misses": self.misses,
            "hit_ratio_pct": ratio,
            "total_keys": len(self._store)
        }

class ForensicCacheManager:
    def __init__(self):
        self.client = InMemoryCache()
        self.is_redis = False

    async def connect(self):
        try:
            import redis.asyncio as aioredis
            from backend.core.config import settings
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=1.0)
            await r.ping()
            self.client = r
            self.is_redis = True
            logger.info("Connected to Redis cache cluster.")
        except Exception:
            self.client = InMemoryCache()
            self.is_redis = False
            logger.info("Operating with local in-memory forensic cache (offline mode).")

    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        return await self.client.set(key, value, ex=ex)

    async def set_json(self, key: str, data: Any, ex: Optional[int] = None) -> bool:
        return await self.set(key, json.dumps(data), ex=ex)

    async def get_json(self, key: str) -> Optional[Any]:
        val = await self.get(key)
        if val:
            try:
                return json.loads(val)
            except Exception:
                return None
        return None

    def get_stats(self) -> dict:
        if hasattr(self.client, "get_stats"):
            return self.client.get_stats()
        return {"mode": "redis", "is_connected": self.is_redis}

cache = ForensicCacheManager()
