"""
Caching system for smartgit.

Provides content-addressable caching for expensive operations like AI analysis.
Uses a hybrid approach with in-memory LRU cache backed by SQLite for persistence.

Architecture:
- base.py: Abstract cache interface
- memory_cache.py: In-memory LRU cache (fast, volatile)
- sqlite_cache.py: SQLite-backed cache (persistent, queryable)
- manager.py: Cache manager with smart invalidation
"""

from smartgit.cache.base import CacheBackend, CacheEntry, CacheKey
from smartgit.cache.manager import CacheManager, get_cache_manager

__all__ = [
    "CacheBackend",
    "CacheEntry",
    "CacheKey",
    "CacheManager",
    "get_cache_manager",
]
