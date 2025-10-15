"""Git repository operations using Repository pattern."""

from pathlib import Path
from typing import List, Optional

from git import GitCommandError, InvalidGitRepositoryError, Repo
from git.objects.commit import Commit

from smartgit.core.exceptions import (
    GitOperationError,
    GitRepositoryError,
    NoChangesError,
)
from smartgit.core.models import (
    BranchInfo,
    ChangeType,
    DiffAnalysis,
    FileChange,
    GitStatus,
    RepositoryInfo,
)


class GitRepository:
    """
    Repository pattern implementation for Git operations.

    Encapsulates all git operations and provides a clean interface
    for interacting with the repository.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        """
        Initialize git repository.

        Args:
            path: Path to the git repository. If None, uses current directory.

        Raises:
            GitRepositoryError: If path is not a valid git repository.
        """
        self.path = path or Path.cwd()
        try:
            self.repo = Repo(self.path, search_parent_directories=True)
            self.git = self.repo.git
        except InvalidGitRepositoryError as e:
            raise GitRepositoryError(
                f"Not a git repository: {self.path}",
                details=str(e),
            ) from e

    @property
    def root_path(self) -> Path:
        """Get the root path of the repository."""
        return Path(self.repo.working_dir)

    def get_status(self) -> GitStatus:
        """
        Get current repository status.

        Returns:
            GitStatus object with current repository state.
        """
        staged_files = self._get_staged_files()
        unstaged_files = self._get_unstaged_files()
        untracked_files = [Path(f) for f in self.repo.untracked_files]

        # Check for conflicts
        conflicts = []
        try:
            conflicted = self.git.diff("--name-only", "--diff-filter=U").split("\n")
            conflicts = [Path(f) for f in conflicted if f]
        except GitCommandError:
            pass

        is_clean = not staged_files and not unstaged_files and not untracked_files and not conflicts

        return GitStatus(
            branch=self.repo.active_branch.name,
            is_clean=is_clean,
            staged_files=staged_files,
            unstaged_files=unstaged_files,
            untracked_files=untracked_files,
            conflicts=conflicts,
        )

    def get_diff(self, staged: bool = True, context_lines: int = 3) -> DiffAnalysis:
        """
        Get diff of changes.

        Args:
            staged: If True, get staged changes. Otherwise, get unstaged changes.
            context_lines: Number of context lines in diff.

        Returns:
            DiffAnalysis object with diff information.

        Raises:
            NoChangesError: If there are no changes to diff.
        """
        try:
            if staged:
                # Get staged changes
                diff_index = self.repo.index.diff("HEAD")
                diff_text = self.git.diff("--cached", f"-U{context_lines}")
            else:
                # Get unstaged changes
                diff_index = self.repo.index.diff(None)
                diff_text = self.git.diff(f"-U{context_lines}")

            if not diff_index:
                raise NoChangesError("No changes to analyze")

            files = self._parse_diff_index(diff_index)

            return DiffAnalysis(
                files=files,
                diff_text=diff_text,
            )

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to get diff",
                details=str(e),
            ) from e

    def get_repository_info(self) -> RepositoryInfo:
        """Get repository information."""
        remote_url = None
        has_remote = False

        try:
            if self.repo.remotes:
                remote_url = self.repo.remotes.origin.url
                has_remote = True
        except (AttributeError, GitCommandError):
            pass

        return RepositoryInfo(
            root_path=self.root_path,
            current_branch=self.repo.active_branch.name,
            remote_url=remote_url,
            is_dirty=self.repo.is_dirty(),
            has_remote=has_remote,
        )

    def commit(self, message: str, add_all: bool = False) -> Commit:
        """
        Create a commit.

        Args:
            message: Commit message.
            add_all: If True, stage all changes before committing.

        Returns:
            The created commit object.

        Raises:
            NoChangesError: If there are no changes to commit.
            GitOperationError: If commit operation fails.
        """
        try:
            if add_all:
                self.repo.git.add(A=True)

            if not self.repo.index.diff("HEAD"):
                raise NoChangesError("No staged changes to commit")

            commit = self.repo.index.commit(message)
            return commit

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to create commit",
                details=str(e),
            ) from e

    def get_branches(self, include_remote: bool = False) -> List[BranchInfo]:
        """
        Get list of branches.

        Args:
            include_remote: Include remote branches.

        Returns:
            List of BranchInfo objects.
        """
        branches = []
        current_branch = self.repo.active_branch.name

        for branch in self.repo.branches:
            tracking_branch = branch.tracking_branch()
            branches.append(
                BranchInfo(
                    name=branch.name,
                    is_current=branch.name == current_branch,
                    last_commit_date=branch.commit.committed_datetime,
                    remote_tracking=tracking_branch.name if tracking_branch else None,
                )
            )

        return branches

    def undo_last_commit(self, keep_changes: bool = True) -> None:
        """
        Undo the last commit.

        Args:
            keep_changes: If True, keep changes as staged. If False, discard changes.

        Raises:
            GitOperationError: If undo operation fails.
        """
        try:
            if keep_changes:
                self.git.reset("--soft", "HEAD~1")
            else:
                self.git.reset("--hard", "HEAD~1")
        except GitCommandError as e:
            raise GitOperationError(
                "Failed to undo commit",
                details=str(e),
            ) from e

    def clean_merged_branches(self, remote: str = "origin") -> List[str]:
        """
        Delete local branches that have been merged.

        Args:
            remote: Remote name (default: origin).

        Returns:
            List of deleted branch names.

        Raises:
            GitOperationError: If cleanup operation fails.
        """
        try:
            # Get merged branches
            merged = self.git.branch("--merged").split("\n")
            deleted = []

            for branch_line in merged:
                branch_name = branch_line.strip().lstrip("* ")
                # Skip main/master/develop branches
                if branch_name in ("main", "master", "develop", ""):
                    continue

                try:
                    self.git.branch("-d", branch_name)
                    deleted.append(branch_name)
                except GitCommandError:
                    continue

            return deleted

        except GitCommandError as e:
            raise GitOperationError(
                "Failed to clean merged branches",
                details=str(e),
            ) from e

    def _get_staged_files(self) -> List[FileChange]:
        """Get list of staged files."""
        try:
            diff_index = self.repo.index.diff("HEAD")
            return self._parse_diff_index(diff_index)
        except GitCommandError:
            return []

    def _get_unstaged_files(self) -> List[FileChange]:
        """Get list of unstaged files."""
        try:
            diff_index = self.repo.index.diff(None)
            return self._parse_diff_index(diff_index)
        except GitCommandError:
            return []

    def _parse_diff_index(self, diff_index: list) -> List[FileChange]:
        """Parse GitPython diff index into FileChange objects."""
        files = []

        for diff_item in diff_index:
            change_type = self._get_change_type(diff_item.change_type)

            # Get stats
            try:
                stats = diff_item.diff.decode("utf-8", errors="ignore")
                additions = stats.count("\n+")
                deletions = stats.count("\n-")
            except (AttributeError, UnicodeDecodeError):
                additions = 0
                deletions = 0

            old_path = Path(diff_item.rename_from) if diff_item.renamed_file else None

            files.append(
                FileChange(
                    path=Path(diff_item.b_path or diff_item.a_path),
                    change_type=change_type,
                    additions=additions,
                    deletions=deletions,
                    old_path=old_path,
                )
            )

        return files

    def _get_change_type(self, git_change_type: str) -> ChangeType:
        """Convert GitPython change type to our ChangeType enum."""
        mapping = {
            "A": ChangeType.ADDED,
            "D": ChangeType.DELETED,
            "M": ChangeType.MODIFIED,
            "R": ChangeType.RENAMED,
            "C": ChangeType.COPIED,
        }
        return mapping.get(git_change_type, ChangeType.MODIFIED)
