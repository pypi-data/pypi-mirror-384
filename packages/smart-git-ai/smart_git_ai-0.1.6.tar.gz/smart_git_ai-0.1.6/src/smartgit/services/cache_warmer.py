"""Background cache warming service for proactive commit analysis.

This service runs commit analysis in the background to populate the cache,
ensuring instant results when users run rescue commands.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from smartgit.core.repository import GitRepository
from smartgit.services.commit_analyzer import CommitAnalyzer
from smartgit.services.config import SmartGitConfig


class CacheWarmer:
    """
    Background cache warming service.

    Provides:
    - Asynchronous commit analysis
    - Proactive cache population
    - Silent background operation
    - Git hook integration
    """

    def __init__(
        self,
        repository: GitRepository,
        config: SmartGitConfig,
        analyzer: Optional[CommitAnalyzer] = None,
    ):
        """
        Initialize cache warmer.

        Args:
            repository: Git repository instance.
            config: SmartGit configuration.
            analyzer: Optional CommitAnalyzer instance (creates new if None).
        """
        self.repository = repository
        self.config = config
        self.analyzer = analyzer or CommitAnalyzer(repository, config)

    def warm_commit(
        self,
        commit_sha: str = "HEAD",
        silent: bool = True,
    ) -> bool:
        """
        Warm cache for a single commit.

        Args:
            commit_sha: Commit SHA or ref (default: HEAD).
            silent: Suppress all output (for background operation).

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Resolve commit SHA
            resolved_sha = self.repository.repo.rev_parse(commit_sha).hexsha

            # Analyze and cache (suppress progress for background)
            self.analyzer.analyze_commit(
                commit_sha=resolved_sha,
                use_cache=True,
            )

            if not silent:
                print(f"✓ Cached analysis for commit {resolved_sha[:8]}")

            return True

        except Exception as e:
            if not silent:
                print(f"✗ Failed to warm cache for {commit_sha}: {e}", file=sys.stderr)
            return False

    def warm_recent(
        self,
        count: int = 10,
        silent: bool = True,
    ) -> int:
        """
        Warm cache for recent commits.

        Args:
            count: Number of recent commits to analyze.
            silent: Suppress all output.

        Returns:
            Number of commits successfully cached.
        """
        try:
            # Get recent commits
            commits = list(self.repository.repo.iter_commits(max_count=count))

            if not commits:
                return 0

            # Analyze all commits (will use parallel processing if >5)
            results = self.analyzer.analyze_history(
                max_commits=count,
                use_cache=True,
                show_progress=not silent,
            )

            if not silent:
                print(f"✓ Cached analysis for {len(results)} commits")

            return len(results)

        except Exception as e:
            if not silent:
                print(f"✗ Failed to warm cache: {e}", file=sys.stderr)
            return 0

    @staticmethod
    def warm_in_background(
        commit_sha: str = "HEAD",
        repository_path: Optional[Path] = None,
    ) -> bool:
        """
        Launch cache warming in background process.

        This method spawns a detached subprocess to warm the cache,
        allowing the parent process to continue immediately.

        Args:
            commit_sha: Commit SHA or ref to warm.
            repository_path: Path to git repository (default: current dir).

        Returns:
            True if background process launched successfully.
        """
        try:
            # Build command
            cmd = [
                sys.executable,
                "-m",
                "smartgit.cli.main",
                "cache",
                "warm",
                "--commit",
                commit_sha,
                "--silent",
            ]

            if repository_path:
                cmd.extend(["--repo", str(repository_path)])

            # Launch detached background process
            # Use DEVNULL to prevent blocking on I/O
            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,  # Detach from parent
                cwd=repository_path or Path.cwd(),
            )

            return True

        except Exception:
            # Silent failure for background operations
            return False

    @staticmethod
    def warm_batch_in_background(
        count: int = 10,
        repository_path: Optional[Path] = None,
    ) -> bool:
        """
        Launch batch cache warming in background.

        Args:
            count: Number of recent commits to warm.
            repository_path: Path to git repository.

        Returns:
            True if background process launched successfully.
        """
        try:
            cmd = [
                sys.executable,
                "-m",
                "smartgit.cli.main",
                "cache",
                "warm",
                "--recent",
                str(count),
                "--silent",
            ]

            if repository_path:
                cmd.extend(["--repo", str(repository_path)])

            subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                cwd=repository_path or Path.cwd(),
            )

            return True

        except Exception:
            return False


def warm_cache_for_commit(
    commit_sha: str = "HEAD",
    repository_path: Optional[Path] = None,
    silent: bool = True,
) -> bool:
    """
    Convenience function to warm cache for a single commit.

    Args:
        commit_sha: Commit SHA or ref.
        repository_path: Path to repository (default: current dir).
        silent: Suppress output.

    Returns:
        True if successful.
    """
    try:
        from smartgit.services.config import get_config_manager

        # Initialize services
        repo_path = repository_path or Path.cwd()
        repository = GitRepository(repo_path)
        config = get_config_manager().config

        # Warm cache
        warmer = CacheWarmer(repository, config)
        return warmer.warm_commit(commit_sha, silent=silent)

    except Exception as e:
        if not silent:
            print(f"✗ Cache warming failed: {e}", file=sys.stderr)
        return False


def warm_cache_for_recent(
    count: int = 10,
    repository_path: Optional[Path] = None,
    silent: bool = True,
) -> int:
    """
    Convenience function to warm cache for recent commits.

    Args:
        count: Number of recent commits.
        repository_path: Path to repository.
        silent: Suppress output.

    Returns:
        Number of commits cached.
    """
    try:
        from smartgit.services.config import get_config_manager

        repo_path = repository_path or Path.cwd()
        repository = GitRepository(repo_path)
        config = get_config_manager().config

        warmer = CacheWarmer(repository, config)
        return warmer.warm_recent(count, silent=silent)

    except Exception as e:
        if not silent:
            print(f"✗ Cache warming failed: {e}", file=sys.stderr)
        return 0
