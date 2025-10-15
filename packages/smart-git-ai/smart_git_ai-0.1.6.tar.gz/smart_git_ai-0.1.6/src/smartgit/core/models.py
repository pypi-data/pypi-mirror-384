"""Domain models for Git AI."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional


class ChangeType(Enum):
    """Type of file change."""

    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"
    COPIED = "copied"
    UNTRACKED = "untracked"


class CommitType(Enum):
    """Conventional commit types."""

    FEAT = "feat"  # New feature
    FIX = "fix"  # Bug fix
    DOCS = "docs"  # Documentation
    STYLE = "style"  # Code style changes
    REFACTOR = "refactor"  # Code refactoring
    PERF = "perf"  # Performance improvements
    TEST = "test"  # Tests
    BUILD = "build"  # Build system changes
    CI = "ci"  # CI configuration changes
    CHORE = "chore"  # Other changes


@dataclass(frozen=True)
class FileChange:
    """Represents a single file change."""

    path: Path
    change_type: ChangeType
    additions: int = 0
    deletions: int = 0
    old_path: Optional[Path] = None  # For renames

    @property
    def is_significant(self) -> bool:
        """Check if this change is significant (more than trivial edits)."""
        return (self.additions + self.deletions) > 5


@dataclass
class DiffAnalysis:
    """Analysis of git diff."""

    files: List[FileChange]
    total_additions: int = 0
    total_deletions: int = 0
    diff_text: str = ""

    def __post_init__(self) -> None:
        """Calculate totals after initialization."""
        self.total_additions = sum(f.additions for f in self.files)
        self.total_deletions = sum(f.deletions for f in self.files)

    @property
    def file_count(self) -> int:
        """Get total number of changed files."""
        return len(self.files)

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return len(self.files) > 0


@dataclass
class CommitMessage:
    """Represents a generated commit message."""

    type: CommitType
    scope: Optional[str]
    subject: str
    body: Optional[str] = None
    breaking_change: bool = False
    footer: Optional[str] = None
    confidence_score: float = 1.0

    def format(self, style: str = "conventional") -> str:
        """Format the commit message according to style."""
        if style == "conventional":
            return self._format_conventional()
        elif style == "simple":
            return self.subject
        else:
            return self._format_conventional()

    def _format_conventional(self) -> str:
        """Format as conventional commit."""
        parts = [self.type.value]

        if self.scope:
            parts.append(f"({self.scope})")

        if self.breaking_change:
            parts.append("!")

        header = "".join(parts) + f": {self.subject}"

        message_parts = [header]

        if self.body:
            message_parts.append("")
            message_parts.append(self.body)

        if self.breaking_change and self.footer:
            message_parts.append("")
            message_parts.append(f"BREAKING CHANGE: {self.footer}")
        elif self.footer:
            message_parts.append("")
            message_parts.append(self.footer)

        return "\n".join(message_parts)


@dataclass
class BranchInfo:
    """Information about a git branch."""

    name: str
    is_current: bool
    last_commit_date: Optional[datetime] = None
    commits_ahead: int = 0
    commits_behind: int = 0
    remote_tracking: Optional[str] = None


@dataclass
class GitStatus:
    """Current status of the git repository."""

    branch: str
    is_clean: bool
    staged_files: List[FileChange] = field(default_factory=list)
    unstaged_files: List[FileChange] = field(default_factory=list)
    untracked_files: List[Path] = field(default_factory=list)
    conflicts: List[Path] = field(default_factory=list)

    @property
    def has_staged_changes(self) -> bool:
        """Check if there are staged changes."""
        return len(self.staged_files) > 0

    @property
    def has_conflicts(self) -> bool:
        """Check if there are merge conflicts."""
        return len(self.conflicts) > 0


@dataclass
class RepositoryInfo:
    """Information about the git repository."""

    root_path: Path
    current_branch: str
    remote_url: Optional[str] = None
    is_dirty: bool = False
    has_remote: bool = False
