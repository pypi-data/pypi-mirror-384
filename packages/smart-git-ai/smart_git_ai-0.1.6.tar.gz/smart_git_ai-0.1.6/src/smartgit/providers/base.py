"""Base AI provider interface using Strategy pattern."""

from abc import ABC, abstractmethod
from typing import Optional

from smartgit.core.models import CommitMessage, CommitType, DiffAnalysis


class AIProvider(ABC):
    """
    Abstract base class for AI providers (Strategy pattern).

    This allows swapping between different AI providers (OpenAI, Anthropic, etc.)
    without changing the client code.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        """
        Initialize the AI provider.

        Args:
            api_key: API key for the provider.
            model: Model name/ID to use.
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()

    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        pass

    @abstractmethod
    def generate_commit_message(
        self,
        diff_analysis: DiffAnalysis,
        context: Optional[str] = None,
        max_tokens: int = 500,
    ) -> CommitMessage:
        """
        Generate a commit message based on diff analysis.

        Args:
            diff_analysis: Analysis of the git diff.
            context: Additional context about the changes.
            max_tokens: Maximum tokens for generation.

        Returns:
            Generated CommitMessage object.

        Raises:
            AIProviderError: If generation fails.
        """
        pass

    @abstractmethod
    def suggest_branch_name(self, description: str) -> str:
        """
        Suggest a branch name based on description.

        Args:
            description: Description of what the branch is for.

        Returns:
            Suggested branch name (kebab-case).

        Raises:
            AIProviderError: If suggestion fails.
        """
        pass

    @abstractmethod
    def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate text based on a prompt.

        Args:
            prompt: The prompt to generate from.
            max_tokens: Maximum tokens for generation.

        Returns:
            Generated text.

        Raises:
            AIProviderError: If generation fails.
        """
        pass

    def _create_commit_prompt(
        self, diff_analysis: DiffAnalysis, context: Optional[str] = None
    ) -> str:
        """Create a prompt for commit message generation."""
        files_summary = self._summarize_files(diff_analysis)

        prompt = f"""Generate a conventional commit message for the following changes:

Files changed: {diff_analysis.file_count}
Additions: {diff_analysis.total_additions}
Deletions: {diff_analysis.total_deletions}

Changed files:
{files_summary}

Diff:
```
{diff_analysis.diff_text[:3000]}  # Limit diff size
```
"""

        if context:
            prompt += f"\nAdditional context: {context}\n"

        prompt += """
Please analyze these changes and provide:
1. The appropriate commit type (feat, fix, docs, style, refactor, perf, test, build, ci, chore)
2. An optional scope (component/module affected)
3. A concise subject line (50 chars max, imperative mood)
   - CRITICAL: The subject must ONLY contain the description, NOT the type or scope prefix
   - The type and scope are separate fields and will be formatted automatically
   - Use imperative mood: "add feature" not "added feature" or "adds feature"
4. An optional body explaining what and why (if changes are complex)
5. Whether this is a breaking change

EXAMPLES:

✓ CORRECT format - subject contains only the description:
{
    "type": "chore",
    "scope": "git",
    "subject": "add SmartGit cache directory to gitignore",
    "body": null,
    "breaking_change": false,
    "confidence": 0.95
}

✗ INCORRECT format - DO NOT include type/scope in subject:
{
    "type": "chore",
    "scope": "git",
    "subject": "chore(git): add SmartGit cache directory to gitignore",
    "body": null,
    "breaking_change": false,
    "confidence": 0.95
}

Respond in this JSON format with separate fields:
{
    "type": "feat|fix|docs|style|refactor|perf|test|build|ci|chore",
    "scope": "optional scope or null",
    "subject": "description only, no type/scope prefix",
    "body": "optional detailed explanation or null",
    "breaking_change": false,
    "confidence": 0.0-1.0
}
"""
        return prompt

    def _summarize_files(self, diff_analysis: DiffAnalysis) -> str:
        """Create a summary of changed files."""
        lines = []
        for file_change in diff_analysis.files[:20]:  # Limit to 20 files
            change_icon = {
                "added": "+",
                "modified": "~",
                "deleted": "-",
                "renamed": "→",
            }.get(file_change.change_type.value, "?")

            lines.append(
                f"{change_icon} {file_change.path} "
                f"(+{file_change.additions}/-{file_change.deletions})"
            )

        if diff_analysis.file_count > 20:
            lines.append(f"... and {diff_analysis.file_count - 20} more files")

        return "\n".join(lines)

    def _parse_commit_type(self, type_str: str) -> CommitType:
        """Parse commit type string to enum."""
        try:
            return CommitType(type_str.lower())
        except ValueError:
            return CommitType.CHORE
