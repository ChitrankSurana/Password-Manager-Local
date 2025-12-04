#!/usr/bin/env python3
"""
Personal Password Manager - Password Cache
===========================================

This module provides an in-memory caching system for password entries to improve
performance when dealing with large password databases.

Key Features:
- TTL-based expiration for security
- LRU (Least Recently Used) eviction policy
- Thread-safe operations
- Smart cache invalidation
- Performance metrics and statistics

Author: Personal Password Manager
Version: 2.2.0
"""

import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from .logging_config import get_logger
from .types import PasswordEntry

logger = get_logger(__name__)


class PasswordCache:
    """
    Thread-safe in-memory cache for password entries

    Implements LRU eviction with TTL-based security expiration.
    Designed to reduce database queries for frequently accessed passwords.
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 300,  # 5 minutes default
        enable_metrics: bool = True,
    ):
        """
        Initialize the password cache

        Args:
            max_size: Maximum number of entries to cache
            ttl_seconds: Time-to-live for cached entries (seconds)
            enable_metrics: Enable performance metrics tracking
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.enable_metrics = enable_metrics

        # Cache storage: {user_id: OrderedDict[cache_key: CacheEntry]}
        self._cache: Dict[int, OrderedDict] = {}

        # Thread lock for thread safety
        self._lock = threading.RLock()

        # Performance metrics
        self._metrics = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "invalidations": 0,
            "total_requests": 0,
        }

        logger.info(f"Password cache initialized (max_size={max_size}, ttl={ttl_seconds}s)")

    def get(self, user_id: int, cache_key: str) -> Optional[List[PasswordEntry]]:
        """
        Get cached password entries

        Args:
            user_id: User ID
            cache_key: Cache key (typically based on query parameters)

        Returns:
            List of password entries if found and not expired, None otherwise
        """
        with self._lock:
            self._metrics["total_requests"] += 1

            # Check if user has cached data
            if user_id not in self._cache:
                self._metrics["misses"] += 1
                return None

            user_cache = self._cache[user_id]

            # Check if key exists
            if cache_key not in user_cache:
                self._metrics["misses"] += 1
                return None

            # Get entry
            entry = user_cache[cache_key]

            # Check if expired
            if self._is_expired(entry):
                # Remove expired entry
                del user_cache[cache_key]
                self._metrics["misses"] += 1
                logger.debug(f"Cache expired for user {user_id}, key: {cache_key}")
                return None

            # Move to end (most recently used)
            user_cache.move_to_end(cache_key)

            # Cache hit
            self._metrics["hits"] += 1
            logger.debug(f"Cache hit for user {user_id}, key: {cache_key}")

            return entry["data"]

    def set(self, user_id: int, cache_key: str, data: List[PasswordEntry]) -> None:
        """
        Store password entries in cache

        Args:
            user_id: User ID
            cache_key: Cache key
            data: Password entries to cache
        """
        with self._lock:
            # Ensure user cache exists
            if user_id not in self._cache:
                self._cache[user_id] = OrderedDict()

            user_cache = self._cache[user_id]

            # Check cache size and evict if necessary
            while len(user_cache) >= self.max_size:
                # Remove least recently used (first item)
                evicted_key = next(iter(user_cache))
                del user_cache[evicted_key]
                self._metrics["evictions"] += 1
                logger.debug(f"Evicted cache entry for user {user_id}, key: {evicted_key}")

            # Add entry
            user_cache[cache_key] = {"data": data, "timestamp": time.time(), "access_count": 0}

            logger.debug(f"Cache set for user {user_id}, key: {cache_key}, entries: {len(data)}")

    def invalidate_user(self, user_id: int) -> None:
        """
        Invalidate all cache entries for a user

        Args:
            user_id: User ID to invalidate
        """
        with self._lock:
            if user_id in self._cache:
                count = len(self._cache[user_id])
                del self._cache[user_id]
                self._metrics["invalidations"] += count
                logger.debug(f"Invalidated {count} cache entries for user {user_id}")

    def invalidate_key(self, user_id: int, cache_key: str) -> None:
        """
        Invalidate a specific cache entry

        Args:
            user_id: User ID
            cache_key: Cache key to invalidate
        """
        with self._lock:
            if user_id in self._cache and cache_key in self._cache[user_id]:
                del self._cache[user_id][cache_key]
                self._metrics["invalidations"] += 1
                logger.debug(f"Invalidated cache entry for user {user_id}, key: {cache_key}")

    def invalidate_all(self) -> None:
        """Invalidate all cache entries"""
        with self._lock:
            total = sum(len(user_cache) for user_cache in self._cache.values())
            self._cache.clear()
            self._metrics["invalidations"] += total
            logger.info(f"Invalidated all cache entries ({total} total)")

    def cleanup_expired(self) -> int:
        """
        Remove all expired entries from cache

        Returns:
            Number of entries removed
        """
        with self._lock:
            removed = 0

            for user_id in list(self._cache.keys()):
                user_cache = self._cache[user_id]

                # Find expired entries
                expired_keys = [key for key, entry in user_cache.items() if self._is_expired(entry)]

                # Remove expired entries
                for key in expired_keys:
                    del user_cache[key]
                    removed += 1

                # Remove empty user caches
                if not user_cache:
                    del self._cache[user_id]

            if removed > 0:
                logger.debug(f"Cleaned up {removed} expired cache entries")

            return removed

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get cache performance metrics

        Returns:
            Dictionary with performance statistics
        """
        with self._lock:
            total_entries = sum(len(user_cache) for user_cache in self._cache.values())

            hit_rate = 0.0
            if self._metrics["total_requests"] > 0:
                hit_rate = (self._metrics["hits"] / self._metrics["total_requests"]) * 100

            return {
                "total_entries": total_entries,
                "users_cached": len(self._cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self._metrics["hits"],
                "misses": self._metrics["misses"],
                "hit_rate": hit_rate,
                "evictions": self._metrics["evictions"],
                "invalidations": self._metrics["invalidations"],
                "total_requests": self._metrics["total_requests"],
            }

    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        with self._lock:
            self._metrics = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "invalidations": 0,
                "total_requests": 0,
            }
            logger.debug("Cache metrics reset")

    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """
        Check if a cache entry is expired

        Args:
            entry: Cache entry to check

        Returns:
            True if expired, False otherwise
        """
        age = time.time() - entry["timestamp"]
        return age > self.ttl_seconds

    def get_cache_info(self, user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Get detailed cache information

        Args:
            user_id: Optional user ID to get specific user cache info

        Returns:
            Dictionary with cache information
        """
        with self._lock:
            if user_id is not None:
                if user_id not in self._cache:
                    return {"user_id": user_id, "entries": 0, "keys": []}

                user_cache = self._cache[user_id]
                return {
                    "user_id": user_id,
                    "entries": len(user_cache),
                    "keys": list(user_cache.keys()),
                    "oldest_entry": min(
                        (entry["timestamp"] for entry in user_cache.values()), default=None
                    ),
                    "newest_entry": max(
                        (entry["timestamp"] for entry in user_cache.values()), default=None
                    ),
                }
            else:
                # Global cache info
                return {
                    "total_entries": sum(len(uc) for uc in self._cache.values()),
                    "users": len(self._cache),
                    "user_ids": list(self._cache.keys()),
                }


class CacheKeyBuilder:
    """
    Helper class to build consistent cache keys

    Provides standardized cache key generation for different query types.
    """

    @staticmethod
    def all_passwords(user_id: int) -> str:
        """Cache key for all passwords query"""
        return f"all_{user_id}"

    @staticmethod
    def search_query(user_id: int, query: str) -> str:
        """Cache key for search query"""
        # Normalize query for consistent caching
        normalized_query = query.lower().strip()
        return f"search_{user_id}_{normalized_query}"

    @staticmethod
    def website_filter(user_id: int, website: str) -> str:
        """Cache key for website filter"""
        normalized_website = website.lower().strip()
        return f"website_{user_id}_{normalized_website}"

    @staticmethod
    def favorites(user_id: int) -> str:
        """Cache key for favorites query"""
        return f"favorites_{user_id}"

    @staticmethod
    def recent(user_id: int, limit: int = 10) -> str:
        """Cache key for recent passwords query"""
        return f"recent_{user_id}_{limit}"


# Factory function
def create_password_cache(max_size: int = 1000, ttl_seconds: int = 300) -> PasswordCache:
    """
    Create a password cache instance

    Args:
        max_size: Maximum cache size
        ttl_seconds: Time-to-live for cached entries

    Returns:
        PasswordCache instance
    """
    return PasswordCache(max_size=max_size, ttl_seconds=ttl_seconds)


if __name__ == "__main__":
    print("Password Cache Module")
    print("=" * 50)
    print("✓ Module loaded successfully")
    print("\nFeatures:")
    print("  - Thread-safe LRU cache")
    print("  - TTL-based expiration")
    print("  - Performance metrics")
    print("  - Smart invalidation")
