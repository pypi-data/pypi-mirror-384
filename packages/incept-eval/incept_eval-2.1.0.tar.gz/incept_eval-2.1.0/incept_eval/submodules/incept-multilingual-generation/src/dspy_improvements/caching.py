"""
Smart Caching Layer for DSPy RAG
LRU cache with TTL for LLM responses and vector search results
"""

import hashlib
import json
import time
import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps
from collections import OrderedDict
from threading import Lock

logger = logging.getLogger(__name__)


class TTLCache:
    """Thread-safe LRU cache with Time-To-Live expiration"""

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 3600):
        self.maxsize = maxsize
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.lock = Lock()
        self.hits = 0
        self.misses = 0

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache entry is expired"""
        return (time.time() - timestamp) > self.ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            value, timestamp = self.cache[key]

            # Check expiration
            if self._is_expired(timestamp):
                del self.cache[key]
                self.misses += 1
                return None

            # Move to end (LRU)
            self.cache.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: str, value: Any):
        """Set value in cache"""
        with self.lock:
            # Remove oldest if at capacity
            if len(self.cache) >= self.maxsize and key not in self.cache:
                self.cache.popitem(last=False)

            self.cache[key] = (value, time.time())
            self.cache.move_to_end(key)

    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0.0
        return {
            'size': len(self.cache),
            'maxsize': self.maxsize,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'ttl_seconds': self.ttl_seconds
        }


class CacheManager:
    """
    Unified cache manager for DSPy RAG components.

    Separate caches for:
    - Query rewriting (LRU, 1h TTL)
    - Vector search results (LRU, 24h TTL)
    - LLM final outputs (LRU, 24h TTL)
    """

    def __init__(self):
        # Query rewrite cache: Short TTL, small size
        self.rewrite_cache = TTLCache(maxsize=500, ttl_seconds=3600)  # 1 hour

        # Vector search cache: Longer TTL, medium size
        self.search_cache = TTLCache(maxsize=2000, ttl_seconds=86400)  # 24 hours

        # LLM output cache: Long TTL, larger size
        self.llm_cache = TTLCache(maxsize=5000, ttl_seconds=86400)  # 24 hours

    @staticmethod
    def _hash_key(*args, **kwargs) -> str:
        """Generate deterministic cache key from arguments"""
        content = json.dumps({
            'args': args,
            'kwargs': {k: v for k, v in sorted(kwargs.items())}
        }, sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()

    def cache_rewrite(self, func: Callable) -> Callable:
        """Decorator for caching query rewrites"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._hash_key('rewrite', *args, **kwargs)
            cached = self.rewrite_cache.get(key)

            if cached is not None:
                logger.debug(f"🔍 Rewrite cache HIT: {key[:8]}")
                return cached

            result = func(*args, **kwargs)
            self.rewrite_cache.set(key, result)
            logger.debug(f"💾 Rewrite cache MISS: {key[:8]}")
            return result

        return wrapper

    def cache_search(self, func: Callable) -> Callable:
        """Decorator for caching vector search results"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._hash_key('search', *args, **kwargs)
            cached = self.search_cache.get(key)

            if cached is not None:
                logger.debug(f"🔍 Search cache HIT: {key[:8]}")
                return cached

            result = func(*args, **kwargs)
            self.search_cache.set(key, result)
            logger.debug(f"💾 Search cache MISS: {key[:8]}")
            return result

        return wrapper

    def cache_llm(self, func: Callable) -> Callable:
        """Decorator for caching LLM outputs"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._hash_key('llm', *args, **kwargs)
            cached = self.llm_cache.get(key)

            if cached is not None:
                logger.debug(f"🔍 LLM cache HIT: {key[:8]}")
                return cached

            result = func(*args, **kwargs)
            self.llm_cache.set(key, result)
            logger.debug(f"💾 LLM cache MISS: {key[:8]}")
            return result

        return wrapper

    def invalidate_all(self):
        """Invalidate all caches"""
        self.rewrite_cache.clear()
        self.search_cache.clear()
        self.llm_cache.clear()
        logger.info("🗑️ All caches invalidated")

    def stats(self) -> Dict[str, Any]:
        """Get statistics for all caches"""
        return {
            'rewrite': self.rewrite_cache.stats(),
            'search': self.search_cache.stats(),
            'llm': self.llm_cache.stats()
        }


# Global cache manager instance
cache_manager = CacheManager()


# Convenience decorators
def cache_rewrite(func: Callable) -> Callable:
    """Cache query rewrites (1h TTL)"""
    return cache_manager.cache_rewrite(func)


def cache_search(func: Callable) -> Callable:
    """Cache vector search results (24h TTL)"""
    return cache_manager.cache_search(func)


def cache_llm(func: Callable) -> Callable:
    """Cache LLM outputs (24h TTL)"""
    return cache_manager.cache_llm(func)
