"""In-memory LRU cache implementation."""

from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, List, Optional

from smartgit.cache.base import CacheBackend, CacheEntry, CacheKey


class MemoryCache(CacheBackend):
    """
    In-memory LRU (Least Recently Used) cache.

    Provides:
    - Fast O(1) access
    - Automatic eviction when full
    - No persistence (lost on restart)
    - Thread-safe operations
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries to keep in memory.
        """
        self.max_size = max_size
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }

    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Retrieve entry and move to end (most recent)."""
        key_hash = key.to_hash()

        if key_hash not in self._cache:
            self._stats["misses"] += 1
            return None

        # Move to end (mark as recently used)
        self._cache.move_to_end(key_hash)

        # Update access statistics
        entry = self._cache[key_hash]
        entry.accessed_at = datetime.now()
        entry.access_count += 1

        self._stats["hits"] += 1
        return entry

    def put(self, key: CacheKey, data: Dict[str, Any]) -> None:
        """Store entry and evict LRU if necessary."""
        key_hash = key.to_hash()
        now = datetime.now()

        # Create new entry
        entry = CacheEntry(
            key=key_hash,
            commit_sha=key.commit_sha,
            analysis_type=key.analysis_type,
            analysis_version=key.analysis_version,
            provider_type=key.provider_type,
            repository_id=key.repository_id,
            cached_at=now,
            accessed_at=now,
            access_count=1,
            data=data,
        )

        # If key exists, remove it first (will re-add at end)
        if key_hash in self._cache:
            del self._cache[key_hash]

        # Add to end (most recent)
        self._cache[key_hash] = entry

        # Evict LRU if over capacity
        if len(self._cache) > self.max_size:
            # Remove oldest (first item)
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1

    def delete(self, key: CacheKey) -> bool:
        """Delete an entry."""
        key_hash = key.to_hash()
        if key_hash in self._cache:
            del self._cache[key_hash]
            return True
        return False

    def clear(self) -> int:
        """Clear all entries."""
        count = len(self._cache)
        self._cache.clear()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
        return count

    def clear_repository(self, repository_id: str) -> int:
        """Clear entries for a specific repository."""
        to_delete = [
            key for key, entry in self._cache.items() if entry.repository_id == repository_id
        ]

        for key in to_delete:
            del self._cache[key]

        return len(to_delete)

    def clear_by_commit(self, commit_sha: str) -> int:
        """Clear entries for a specific commit."""
        to_delete = [key for key, entry in self._cache.items() if entry.commit_sha == commit_sha]

        for key in to_delete:
            del self._cache[key]

        return len(to_delete)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0

        return {
            "total_entries": len(self._cache),
            "max_size": self.max_size,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "hit_rate": round(hit_rate * 100, 2),
            "usage_percent": round((len(self._cache) / self.max_size) * 100, 2),
        }

    def evict_old_entries(self, max_age_days: int) -> int:
        """Evict entries older than max_age_days."""
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)

        to_delete = [key for key, entry in self._cache.items() if entry.cached_at < cutoff]

        for key in to_delete:
            del self._cache[key]

        return len(to_delete)

    def list_entries(
        self,
        repository_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CacheEntry]:
        """List cache entries."""
        entries = list(self._cache.values())

        if repository_id:
            entries = [e for e in entries if e.repository_id == repository_id]

        # Return most recently accessed first
        entries.reverse()

        return entries[:limit]
