"""Anthropic (Claude) AI provider implementation."""

import json
import os
import re
from typing import Optional

from anthropic import Anthropic, APIError

from smartgit.core.exceptions import AIProviderError
from smartgit.core.models import CommitMessage, DiffAnalysis
from smartgit.providers.base import AIProvider


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) AI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        """Initialize Anthropic provider."""
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise AIProviderError(
                "Anthropic API key not found",
                details="Set ANTHROPIC_API_KEY environment variable or pass api_key",
            )

        super().__init__(api_key, model)
        self.client = Anthropic(api_key=self.api_key)

    def get_default_model(self) -> str:
        """Get default Anthropic model."""
        return "claude-3-5-sonnet-20241022"

    def generate_commit_message(
        self,
        diff_analysis: DiffAnalysis,
        context: Optional[str] = None,
        max_tokens: int = 500,
    ) -> CommitMessage:
        """Generate commit message using Claude."""
        try:
            prompt = self._create_commit_prompt(diff_analysis, context)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            # Extract text from response
            content_block = response.content[0]
            if not hasattr(content_block, "text"):
                raise AIProviderError("Unexpected response format from Anthropic")
            content = content_block.text

            # Parse JSON response
            try:
                # Extract JSON from markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                # Try to find JSON in the content if it's mixed with other text
                json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)

                data = json.loads(content)
            except (json.JSONDecodeError, IndexError):
                # Fallback: create simple commit message
                return CommitMessage(
                    type=self._parse_commit_type("chore"),
                    scope=None,
                    subject=content[:50],
                    body=None,
                    breaking_change=False,
                    confidence_score=0.5,
                )

            return CommitMessage(
                type=self._parse_commit_type(data.get("type", "chore")),
                scope=data.get("scope"),
                subject=data["subject"],
                body=data.get("body"),
                breaking_change=data.get("breaking_change", False),
                confidence_score=data.get("confidence", 1.0),
            )

        except APIError as e:
            raise AIProviderError(
                "Failed to generate commit message with Anthropic",
                details=str(e),
            ) from e

    def suggest_branch_name(self, description: str) -> str:
        """Suggest a branch name using Claude."""
        try:
            prompt = f"""Given this description: "{description}"

Suggest a concise, descriptive git branch name following these rules:
- Use kebab-case (lowercase with hyphens)
- Start with type prefix: feature/, bugfix/, hotfix/, refactor/, docs/, or chore/
- Keep it under 50 characters
- Be specific but concise
- Use conventional naming

Respond with ONLY the branch name, nothing else."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}],
            )

            content_block = response.content[0]
            if not hasattr(content_block, "text"):
                raise AIProviderError("Unexpected response format from Anthropic")
            branch_name: str = str(content_block.text).strip()
            # Clean up any extra formatting
            branch_name = branch_name.strip("`\"' \n")

            return branch_name

        except APIError as e:
            raise AIProviderError(
                "Failed to suggest branch name with Anthropic",
                details=str(e),
            ) from e

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using Claude."""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            content_block = response.content[0]
            if not hasattr(content_block, "text"):
                raise AIProviderError("Unexpected response format from Anthropic")
            return str(content_block.text)

        except APIError as e:
            raise AIProviderError(
                "Failed to generate text with Anthropic",
                details=str(e),
            ) from e
