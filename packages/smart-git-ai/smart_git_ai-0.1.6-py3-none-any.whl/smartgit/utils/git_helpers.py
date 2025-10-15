"""Git utility helper functions."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from git import GitCommandError

from smartgit.core.exceptions import GitOperationError
from smartgit.core.models import BranchInfo
from smartgit.core.repository import GitRepository


class GitUtilities:
    """
    Collection of git utility functions to help developers.

    Provides helpful operations for common scenarios where developers
    might find themselves stuck.
    """

    def __init__(self, repository: GitRepository) -> None:
        """Initialize git utilities."""
        self.repository = repository

    def find_stale_branches(self, days: int = 30) -> List[BranchInfo]:
        """
        Find branches that haven't been updated in specified days.

        Args:
            days: Number of days to consider a branch stale.

        Returns:
            List of stale branches.
        """
        cutoff_date = datetime.now(tz=None) - timedelta(days=days)
        branches = self.repository.get_branches()

        stale = []
        for branch in branches:
            if not branch.is_current and branch.last_commit_date:
                # Make cutoff_date timezone-aware if branch date is
                if branch.last_commit_date.tzinfo is not None:
                    cutoff_date = cutoff_date.replace(tzinfo=branch.last_commit_date.tzinfo)

                if branch.last_commit_date < cutoff_date:
                    stale.append(branch)

        return stale

    def interactive_conflict_resolver(self) -> List[Path]:
        """
        Help resolve merge conflicts interactively.

        Returns:
            List of resolved conflict files.
        """
        status = self.repository.get_status()

        if not status.has_conflicts:
            return []

        return status.conflicts

    def find_large_files(self, size_mb: float = 10.0) -> List[tuple[Path, float]]:
        """
        Find large files in the repository.

        Args:
            size_mb: Size threshold in megabytes.

        Returns:
            List of tuples (file_path, size_in_mb).
        """
        large_files = []
        threshold_bytes = size_mb * 1024 * 1024

        try:
            # Get all tracked files
            tracked_files = self.repository.git.ls_files().split("\n")

            for file_path_str in tracked_files:
                if not file_path_str:
                    continue

                file_path = self.repository.root_path / file_path_str
                if file_path.exists() and file_path.is_file():
                    size = file_path.stat().st_size
                    if size > threshold_bytes:
                        large_files.append((Path(file_path_str), size / (1024 * 1024)))

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to find large files",
                details=str(e),
            ) from e

        return sorted(large_files, key=lambda x: x[1], reverse=True)

    def suggest_gitignore_entries(self) -> List[str]:
        """
        Suggest .gitignore entries based on untracked files.

        Returns:
            List of suggested .gitignore patterns.
        """
        status = self.repository.get_status()
        suggestions = set()

        common_patterns = {
            ".pyc": "*.pyc",
            "__pycache__": "__pycache__/",
            ".egg-info": "*.egg-info/",
            ".env": ".env",
            ".venv": ".venv/",
            "node_modules": "node_modules/",
            ".DS_Store": ".DS_Store",
            "dist": "dist/",
            "build": "build/",
            ".coverage": ".coverage",
            ".pytest_cache": ".pytest_cache/",
            ".mypy_cache": ".mypy_cache/",
        }

        for untracked in status.untracked_files:
            for pattern_key, pattern_value in common_patterns.items():
                if pattern_key in str(untracked):
                    suggestions.add(pattern_value)
                    break

        return sorted(suggestions)

    def create_worktree(self, branch_name: str, path: Optional[Path] = None) -> Path:
        """
        Create a git worktree for parallel development.

        Args:
            branch_name: Name of the branch for the worktree.
            path: Path for the worktree (auto-generated if None).

        Returns:
            Path to the created worktree.

        Raises:
            GitOperationError: If worktree creation fails.
        """
        if path is None:
            path = (
                self.repository.root_path.parent / f"{self.repository.root_path.name}-{branch_name}"
            )

        try:
            self.repository.git.worktree("add", str(path), "-b", branch_name)
            return path
        except GitCommandError as e:
            raise GitOperationError(
                "Failed to create worktree",
                details=str(e),
            ) from e

    def safe_force_push(self, remote: str = "origin", branch: Optional[str] = None) -> bool:
        """
        Safely force push with lease (won't overwrite others' work).

        Args:
            remote: Remote name.
            branch: Branch name (uses current if None).

        Returns:
            True if push succeeded, False otherwise.

        Raises:
            GitOperationError: If operation fails.
        """
        if branch is None:
            branch = self.repository.repo.active_branch.name

        try:
            # Use --force-with-lease for safety
            self.repository.git.push(remote, branch, force_with_lease=True)
            return True
        except GitCommandError as e:
            if "stale info" in str(e) or "rejected" in str(e):
                return False
            raise GitOperationError(
                "Failed to force push",
                details=str(e),
            ) from e

    def create_fixup_commit(self, target_commit: str) -> str:
        """
        Create a fixup commit for later autosquashing.

        Args:
            target_commit: SHA or ref of commit to fix.

        Returns:
            SHA of the fixup commit.

        Raises:
            GitOperationError: If operation fails.
        """
        try:
            self.repository.git.commit(fixup=target_commit)
            commit_sha: str = str(self.repository.repo.head.commit.hexsha)
            return commit_sha
        except GitCommandError as e:
            raise GitOperationError(
                "Failed to create fixup commit",
                details=str(e),
            ) from e
