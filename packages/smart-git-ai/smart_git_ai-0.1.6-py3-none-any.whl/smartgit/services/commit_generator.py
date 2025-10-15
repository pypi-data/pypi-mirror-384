"""Commit message generation service."""

from typing import Optional

from smartgit.core.exceptions import NoChangesError
from smartgit.core.models import CommitMessage
from smartgit.core.repository import GitRepository
from smartgit.providers.base import AIProvider
from smartgit.providers.factory import ProviderFactory
from smartgit.services.config import ConfigManager


class CommitMessageGenerator:
    """
    Service for generating commit messages.

    Coordinates between repository, AI provider, and configuration.
    """

    def __init__(
        self,
        repository: GitRepository,
        config_manager: Optional[ConfigManager] = None,
        provider: Optional[AIProvider] = None,
    ) -> None:
        """
        Initialize commit message generator.

        Args:
            repository: Git repository instance.
            config_manager: Configuration manager (creates new if None).
            provider: AI provider (creates from config if None).
        """
        self.repository = repository
        self.config_manager = config_manager or ConfigManager()
        self.config = self.config_manager.config

        if provider:
            self.provider = provider
        else:
            # Create provider from config
            self.provider = ProviderFactory.create(
                provider_type=self.config.provider,
                api_key=self.config.api_key,
                model=self.config.model,
            )

    def generate_from_staged(
        self,
        context: Optional[str] = None,
        interactive: bool = False,
    ) -> CommitMessage:
        """
        Generate commit message from staged changes.

        Args:
            context: Additional context about the changes.
            interactive: If True, allow user to edit the message.

        Returns:
            Generated commit message.

        Raises:
            NoChangesError: If there are no staged changes.
        """
        # Get diff of staged changes
        try:
            diff_analysis = self.repository.get_diff(
                staged=True,
                context_lines=self.config.context_lines,
            )
        except NoChangesError:
            # Try to stage changes if auto_add is enabled
            if self.config.auto_add:
                status = self.repository.get_status()
                if status.unstaged_files or status.untracked_files:
                    self.repository.repo.git.add(A=True)
                    diff_analysis = self.repository.get_diff(staged=True)
                else:
                    raise
            else:
                raise

        # Limit diff size
        if len(diff_analysis.diff_text) > self.config.max_diff_size:
            diff_analysis.diff_text = diff_analysis.diff_text[: self.config.max_diff_size]

        # Generate message using AI
        commit_message = self.provider.generate_commit_message(
            diff_analysis=diff_analysis,
            context=context,
        )

        # Enforce subject length limit
        if len(commit_message.subject) > self.config.max_subject_length:
            commit_message.subject = (
                commit_message.subject[: self.config.max_subject_length - 3] + "..."
            )

        return commit_message

    def commit_with_generated_message(
        self,
        context: Optional[str] = None,
        dry_run: bool = False,
    ) -> tuple[CommitMessage, Optional[str]]:
        """
        Generate message and create commit.

        Args:
            context: Additional context about the changes.
            dry_run: If True, don't actually commit.

        Returns:
            Tuple of (commit_message, commit_sha).

        Raises:
            NoChangesError: If there are no changes to commit.
        """
        commit_message = self.generate_from_staged(context=context)

        if dry_run:
            return commit_message, None

        # Create commit
        formatted_message = commit_message.format(style=self.config.commit_style)
        commit = self.repository.commit(
            message=formatted_message,
            add_all=self.config.auto_add,
        )

        return commit_message, commit.hexsha
