"""Abstract base classes for caching system."""

import hashlib
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CacheKey:
    """
    Content-addressable cache key.

    Uses SHA256 hash of multiple factors to create unique cache keys.
    Similar to how git uses SHA1 for content addressing.
    """

    commit_sha: str
    analysis_type: str  # "commit_quality", "commit_message_gen", etc.
    analysis_version: str  # Semantic version, bump when algorithm changes
    provider_type: str  # "anthropic", "openai", "fallback"
    repository_id: str  # Hash of repository path

    def to_hash(self) -> str:
        """Generate SHA256 hash for this cache key."""
        key_string = f"{self.commit_sha}:{self.analysis_type}:{self.analysis_version}:{self.provider_type}:{self.repository_id}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    @staticmethod
    def create_repository_id(repo_path: str) -> str:
        """Create a unique repository ID from path."""
        return hashlib.sha256(repo_path.encode()).hexdigest()[:16]


@dataclass
class CacheEntry:
    """
    A single cache entry with metadata.

    Stores the cached data along with metadata for invalidation and debugging.
    """

    key: str  # SHA256 hash from CacheKey
    commit_sha: str
    analysis_type: str
    analysis_version: str
    provider_type: str
    repository_id: str
    cached_at: datetime
    accessed_at: datetime  # For LRU tracking
    access_count: int  # Usage statistics
    data: Dict[str, Any]  # The actual cached data (serialized)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result["cached_at"] = self.cached_at.isoformat()
        result["accessed_at"] = self.accessed_at.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheEntry":
        """Create from dictionary."""
        data["cached_at"] = datetime.fromisoformat(data["cached_at"])
        data["accessed_at"] = datetime.fromisoformat(data["accessed_at"])
        return cls(**data)


class CacheBackend(ABC):
    """
    Abstract base class for cache backends.

    Follows the Strategy pattern - allows swapping between different
    cache implementations (memory, SQLite, Redis, etc.) without
    changing client code.
    """

    @abstractmethod
    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """
        Retrieve a cache entry.

        Args:
            key: Cache key to look up.

        Returns:
            CacheEntry if found, None otherwise.
        """
        pass

    @abstractmethod
    def put(self, key: CacheKey, data: Dict[str, Any]) -> None:
        """
        Store a cache entry.

        Args:
            key: Cache key.
            data: Data to cache (must be JSON-serializable).
        """
        pass

    @abstractmethod
    def delete(self, key: CacheKey) -> bool:
        """
        Delete a cache entry.

        Args:
            key: Cache key to delete.

        Returns:
            True if entry was deleted, False if not found.
        """
        pass

    @abstractmethod
    def clear(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries deleted.
        """
        pass

    @abstractmethod
    def clear_repository(self, repository_id: str) -> int:
        """
        Clear all entries for a specific repository.

        Args:
            repository_id: Repository identifier.

        Returns:
            Number of entries deleted.
        """
        pass

    @abstractmethod
    def clear_by_commit(self, commit_sha: str) -> int:
        """
        Clear all entries for a specific commit.

        Args:
            commit_sha: Commit SHA to clear.

        Returns:
            Number of entries deleted.
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with statistics (size, hit_rate, etc.).
        """
        pass

    @abstractmethod
    def evict_old_entries(self, max_age_days: int) -> int:
        """
        Evict entries older than max_age_days.

        Args:
            max_age_days: Maximum age in days.

        Returns:
            Number of entries evicted.
        """
        pass

    @abstractmethod
    def list_entries(
        self,
        repository_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CacheEntry]:
        """
        List cache entries.

        Args:
            repository_id: Filter by repository (None = all).
            limit: Maximum number of entries to return.

        Returns:
            List of cache entries.
        """
        pass
