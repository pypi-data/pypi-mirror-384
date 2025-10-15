"""Custom exceptions for Git AI."""

from typing import Optional


class GitAIError(Exception):
    """Base exception for all Git AI errors."""

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        self.message = message
        self.details = details
        super().__init__(self.message)


class GitRepositoryError(GitAIError):
    """Raised when there's an issue with the git repository."""

    pass


class GitOperationError(GitAIError):
    """Raised when a git operation fails."""

    pass


class AIProviderError(GitAIError):
    """Raised when an AI provider operation fails."""

    pass


class ConfigurationError(GitAIError):
    """Raised when there's a configuration issue."""

    pass


class HookInstallationError(GitAIError):
    """Raised when hook installation fails."""

    pass


class InvalidCommitError(GitAIError):
    """Raised when commit operation is invalid."""

    pass


class NoChangesError(GitAIError):
    """Raised when there are no changes to commit."""

    pass
