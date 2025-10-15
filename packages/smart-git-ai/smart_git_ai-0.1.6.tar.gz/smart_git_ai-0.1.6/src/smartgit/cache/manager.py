"""Cache manager with intelligent caching strategies."""

import threading
from pathlib import Path
from typing import Any, Dict, List, Optional

from smartgit.cache.base import CacheEntry, CacheKey
from smartgit.cache.memory_cache import MemoryCache
from smartgit.cache.sqlite_cache import SQLiteCache


class CacheManager:
    """
    Intelligent cache manager with two-tier storage.

    Architecture:
    - L1: Memory cache (fast, volatile) - recent 100 entries
    - L2: SQLite cache (persistent, durable) - all entries

    Provides:
    - Transparent caching with optimal performance
    - Thread-safe operations
    - Automatic promotion (L2 → L1)
    - Smart invalidation strategies
    """

    # Analysis version - bump when algorithm changes
    ANALYSIS_VERSION = "1.0.0"

    def __init__(
        self,
        repository_path: Path,
        cache_dir: Optional[Path] = None,
        memory_size: int = 100,
        enabled: bool = True,
        use_memory_cache: bool = True,
    ):
        """
        Initialize cache manager.

        Args:
            repository_path: Path to git repository.
            cache_dir: Directory for cache storage (default: <repo>/.smartgit/cache).
            memory_size: Size of L1 memory cache.
            enabled: Whether caching is enabled.
            use_memory_cache: Whether to use L1 memory cache.
        """
        self.repository_path = repository_path
        self.repository_id = CacheKey.create_repository_id(str(repository_path))
        self.enabled = enabled
        self.use_memory_cache = use_memory_cache

        # Thread safety
        self._lock = threading.Lock()

        if not self.enabled:
            self.memory_cache = None
            self.sqlite_cache = None
            return

        # Initialize caches
        if cache_dir is None:
            # Store cache in project directory: <repo>/.smartgit/cache/
            cache_dir = repository_path / ".smartgit" / "cache"

        cache_dir.mkdir(parents=True, exist_ok=True)

        # L2: SQLite (persistent)
        db_path = cache_dir / "commits.db"
        self.sqlite_cache = SQLiteCache(db_path)

        # L1: Memory (optional, fast)
        if use_memory_cache:
            self.memory_cache = MemoryCache(max_size=memory_size)
        else:
            self.memory_cache = None

    def get_commit_quality(
        self,
        commit_sha: str,
        provider_type: str = "fallback",
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached commit quality analysis.

        Args:
            commit_sha: Git commit SHA.
            provider_type: AI provider type.

        Returns:
            Cached data if found, None otherwise.
        """
        if not self.enabled:
            return None

        key = CacheKey(
            commit_sha=commit_sha,
            analysis_type="commit_quality",
            analysis_version=self.ANALYSIS_VERSION,
            provider_type=provider_type,
            repository_id=self.repository_id,
        )

        with self._lock:
            # Try L1 (memory) first
            if self.memory_cache:
                entry = self.memory_cache.get(key)
                if entry:
                    return entry.data

            # Try L2 (SQLite)
            if self.sqlite_cache:
                entry = self.sqlite_cache.get(key)
                if entry:
                    # Promote to L1
                    if self.memory_cache:
                        self.memory_cache.put(key, entry.data)
                    return entry.data

        return None

    def put_commit_quality(
        self,
        commit_sha: str,
        provider_type: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Store commit quality analysis in cache.

        Args:
            commit_sha: Git commit SHA.
            provider_type: AI provider type.
            data: Analysis data to cache (must be JSON-serializable).
        """
        if not self.enabled:
            return

        key = CacheKey(
            commit_sha=commit_sha,
            analysis_type="commit_quality",
            analysis_version=self.ANALYSIS_VERSION,
            provider_type=provider_type,
            repository_id=self.repository_id,
        )

        with self._lock:
            # Store in both layers
            if self.memory_cache:
                self.memory_cache.put(key, data)

            if self.sqlite_cache:
                self.sqlite_cache.put(key, data)

    def clear(self, scope: str = "repository") -> int:
        """
        Clear cache.

        Args:
            scope: "all", "repository", or "memory"

        Returns:
            Number of entries cleared.
        """
        if not self.enabled:
            return 0

        with self._lock:
            count = 0

            if scope == "memory":
                if self.memory_cache:
                    count = self.memory_cache.clear()

            elif scope == "repository":
                if self.memory_cache:
                    count += self.memory_cache.clear_repository(self.repository_id)
                if self.sqlite_cache:
                    count += self.sqlite_cache.clear_repository(self.repository_id)

            elif scope == "all":
                if self.memory_cache:
                    count += self.memory_cache.clear()
                if self.sqlite_cache:
                    count += self.sqlite_cache.clear()

            return count

    def clear_commit(self, commit_sha: str) -> int:
        """
        Clear cache for a specific commit.

        Args:
            commit_sha: Commit SHA to clear.

        Returns:
            Number of entries cleared.
        """
        if not self.enabled:
            return 0

        with self._lock:
            count = 0

            if self.memory_cache:
                count += self.memory_cache.clear_by_commit(commit_sha)

            if self.sqlite_cache:
                count += self.sqlite_cache.clear_by_commit(commit_sha)

            return count

    def evict_old(self, max_age_days: int = 30) -> int:
        """
        Evict entries older than max_age_days.

        Args:
            max_age_days: Maximum age in days.

        Returns:
            Number of entries evicted.
        """
        if not self.enabled:
            return 0

        with self._lock:
            count = 0

            if self.memory_cache:
                count += self.memory_cache.evict_old_entries(max_age_days)

            if self.sqlite_cache:
                count += self.sqlite_cache.evict_old_entries(max_age_days)

            return count

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        if not self.enabled:
            return {"enabled": False}

        stats = {
            "enabled": True,
            "repository_id": self.repository_id,
            "analysis_version": self.ANALYSIS_VERSION,
        }

        if self.memory_cache:
            stats["memory"] = self.memory_cache.get_stats()

        if self.sqlite_cache:
            stats["sqlite"] = self.sqlite_cache.get_stats()

        return stats

    def list_entries(self, limit: int = 100) -> List[CacheEntry]:
        """
        List cached entries for this repository.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of cache entries.
        """
        if not self.enabled or not self.sqlite_cache:
            return []

        return self.sqlite_cache.list_entries(repository_id=self.repository_id, limit=limit)


# Global cache manager instance (singleton per repository)
_cache_managers: Dict[str, CacheManager] = {}
_manager_lock = threading.Lock()


def get_cache_manager(repository_path: Path, **kwargs) -> CacheManager:
    """
    Get or create cache manager for a repository.

    Args:
        repository_path: Path to git repository.
        **kwargs: Additional arguments for CacheManager.

    Returns:
        CacheManager instance.
    """
    repo_key = str(repository_path.resolve())

    with _manager_lock:
        if repo_key not in _cache_managers:
            _cache_managers[repo_key] = CacheManager(repository_path, **kwargs)

        return _cache_managers[repo_key]


def clear_all_cache_managers() -> None:
    """Clear all cache manager instances (useful for testing)."""
    global _cache_managers
    with _manager_lock:
        _cache_managers.clear()
