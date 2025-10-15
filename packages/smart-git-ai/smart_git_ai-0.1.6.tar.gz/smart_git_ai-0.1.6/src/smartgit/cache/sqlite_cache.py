"""SQLite-backed cache implementation for persistent storage."""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from smartgit.cache.base import CacheBackend, CacheEntry, CacheKey


class SQLiteCache(CacheBackend):
    """
    SQLite-backed persistent cache.

    Provides:
    - Persistent storage across runs
    - Fast lookups with indexes
    - Query capabilities
    - ACID transactions
    """

    def __init__(self, db_path: Path):
        """
        Initialize SQLite cache.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database schema."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    commit_sha TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,
                    analysis_version TEXT NOT NULL,
                    provider_type TEXT NOT NULL,
                    repository_id TEXT NOT NULL,
                    cached_at TEXT NOT NULL,
                    accessed_at TEXT NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    data_json TEXT NOT NULL
                )
            """
            )

            # Create indexes for common queries
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_repository_id
                ON cache_entries(repository_id)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_commit_sha
                ON cache_entries(commit_sha)
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_accessed_at
                ON cache_entries(accessed_at)
            """
            )

            conn.commit()

    def get(self, key: CacheKey) -> Optional[CacheEntry]:
        """Retrieve a cache entry and update access statistics."""
        key_hash = key.to_hash()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM cache_entries WHERE key = ?", (key_hash,))
            row = cursor.fetchone()

            if not row:
                return None

            # Update access statistics
            conn.execute(
                """
                UPDATE cache_entries
                SET accessed_at = ?, access_count = access_count + 1
                WHERE key = ?
                """,
                (datetime.now().isoformat(), key_hash),
            )
            conn.commit()

            # Construct CacheEntry
            return CacheEntry(
                key=row["key"],
                commit_sha=row["commit_sha"],
                analysis_type=row["analysis_type"],
                analysis_version=row["analysis_version"],
                provider_type=row["provider_type"],
                repository_id=row["repository_id"],
                cached_at=datetime.fromisoformat(row["cached_at"]),
                accessed_at=datetime.fromisoformat(row["accessed_at"]),
                access_count=row["access_count"] + 1,  # Include the current access
                data=json.loads(row["data_json"]),
            )

    def put(self, key: CacheKey, data: Dict[str, Any]) -> None:
        """Store a cache entry."""
        now = datetime.now()
        key_hash = key.to_hash()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries
                (key, commit_sha, analysis_type, analysis_version, provider_type,
                repository_id, cached_at, accessed_at, access_count, data_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    key_hash,
                    key.commit_sha,
                    key.analysis_type,
                    key.analysis_version,
                    key.provider_type,
                    key.repository_id,
                    now.isoformat(),
                    now.isoformat(),
                    1,
                    json.dumps(data),
                ),
            )
            conn.commit()

    def delete(self, key: CacheKey) -> bool:
        """Delete a cache entry."""
        key_hash = key.to_hash()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE key = ?", (key_hash,))
            conn.commit()
            return cursor.rowcount > 0

    def clear(self) -> int:
        """Clear all cache entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache_entries")
            conn.commit()
            return cursor.rowcount

    def clear_repository(self, repository_id: str) -> int:
        """Clear all entries for a specific repository."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache_entries WHERE repository_id = ?", (repository_id,)
            )
            conn.commit()
            return cursor.rowcount

    def clear_by_commit(self, commit_sha: str) -> int:
        """Clear all entries for a specific commit."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE commit_sha = ?", (commit_sha,))
            conn.commit()
            return cursor.rowcount

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    COUNT(*) as total_entries,
                    SUM(access_count) as total_accesses,
                    COUNT(DISTINCT repository_id) as unique_repos,
                    COUNT(DISTINCT commit_sha) as unique_commits,
                    AVG(access_count) as avg_accesses_per_entry,
                    MIN(cached_at) as oldest_entry,
                    MAX(cached_at) as newest_entry
                FROM cache_entries
            """
            )
            row = cursor.fetchone()

            if not row or row[0] == 0:
                return {
                    "total_entries": 0,
                    "total_accesses": 0,
                    "unique_repos": 0,
                    "unique_commits": 0,
                    "avg_accesses_per_entry": 0.0,
                    "oldest_entry": None,
                    "newest_entry": None,
                    "db_size_kb": self.db_path.stat().st_size / 1024
                    if self.db_path.exists()
                    else 0,
                }

            return {
                "total_entries": row[0],
                "total_accesses": row[1] or 0,
                "unique_repos": row[2],
                "unique_commits": row[3],
                "avg_accesses_per_entry": round(row[4] or 0.0, 2),
                "oldest_entry": row[5],
                "newest_entry": row[6],
                "db_size_kb": round(self.db_path.stat().st_size / 1024, 2)
                if self.db_path.exists()
                else 0,
            }

    def evict_old_entries(self, max_age_days: int) -> int:
        """Evict entries older than max_age_days."""
        cutoff = (datetime.now() - timedelta(days=max_age_days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM cache_entries WHERE cached_at < ?", (cutoff,))
            conn.commit()
            return cursor.rowcount

    def evict_lru(self, keep_count: int) -> int:
        """Keep only the N most recently used entries."""
        with sqlite3.connect(self.db_path) as conn:
            # Get total count
            total = conn.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0]

            if total <= keep_count:
                return 0

            # Delete least recently used entries
            cursor = conn.execute(
                """
                DELETE FROM cache_entries
                WHERE key IN (
                    SELECT key FROM cache_entries
                    ORDER BY accessed_at ASC
                    LIMIT ?
                )
                """,
                (total - keep_count,),
            )
            conn.commit()
            return cursor.rowcount

    def list_entries(
        self,
        repository_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[CacheEntry]:
        """List cache entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if repository_id:
                cursor = conn.execute(
                    """
                    SELECT * FROM cache_entries
                    WHERE repository_id = ?
                    ORDER BY accessed_at DESC
                    LIMIT ?
                    """,
                    (repository_id, limit),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT * FROM cache_entries
                    ORDER BY accessed_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                )

            entries = []
            for row in cursor:
                entries.append(
                    CacheEntry(
                        key=row["key"],
                        commit_sha=row["commit_sha"],
                        analysis_type=row["analysis_type"],
                        analysis_version=row["analysis_version"],
                        provider_type=row["provider_type"],
                        repository_id=row["repository_id"],
                        cached_at=datetime.fromisoformat(row["cached_at"]),
                        accessed_at=datetime.fromisoformat(row["accessed_at"]),
                        access_count=row["access_count"],
                        data=json.loads(row["data_json"]),
                    )
                )

            return entries
