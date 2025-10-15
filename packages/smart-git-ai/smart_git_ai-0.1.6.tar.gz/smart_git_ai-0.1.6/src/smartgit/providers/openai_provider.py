"""OpenAI AI provider implementation."""

import json
import os
from typing import Optional

from openai import APIError, OpenAI

from smartgit.core.exceptions import AIProviderError
from smartgit.core.models import CommitMessage, DiffAnalysis
from smartgit.providers.base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI (GPT) AI provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        """Initialize OpenAI provider."""
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise AIProviderError(
                "OpenAI API key not found",
                details="Set OPENAI_API_KEY environment variable or pass api_key",
            )

        super().__init__(api_key, model)
        self.client = OpenAI(api_key=self.api_key)

    def get_default_model(self) -> str:
        """Get default OpenAI model."""
        return "gpt-4o"

    def generate_commit_message(
        self,
        diff_analysis: DiffAnalysis,
        context: Optional[str] = None,
        max_tokens: int = 500,
    ) -> CommitMessage:
        """Generate commit message using GPT."""
        try:
            prompt = self._create_commit_prompt(diff_analysis, context)

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates conventional commit messages.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise AIProviderError("Empty response from OpenAI")

            # Parse JSON response
            try:
                data = json.loads(content)
            except json.JSONDecodeError:
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
                "Failed to generate commit message with OpenAI",
                details=str(e),
            ) from e

    def suggest_branch_name(self, description: str) -> str:
        """Suggest a branch name using GPT."""
        try:
            prompt = f"""Given this description: "{description}"

Suggest a concise, descriptive git branch name following these rules:
- Use kebab-case (lowercase with hyphens)
- Start with type prefix: feature/, bugfix/, hotfix/, refactor/, docs/, or chore/
- Keep it under 50 characters
- Be specific but concise
- Use conventional naming

Respond with ONLY the branch name, nothing else."""

            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that suggests git branch names.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            content = response.choices[0].message.content
            if not content:
                raise AIProviderError("Empty response from OpenAI")

            branch_name: str = str(content).strip()
            # Clean up any extra formatting
            branch_name = branch_name.strip("`\"' \n")

            return branch_name

        except APIError as e:
            raise AIProviderError(
                "Failed to suggest branch name with OpenAI",
                details=str(e),
            ) from e

    def generate_text(self, prompt: str, max_tokens: int = 500) -> str:
        """Generate text using GPT."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            content = response.choices[0].message.content
            if not content:
                raise AIProviderError("Empty response from OpenAI")

            return str(content)

        except APIError as e:
            raise AIProviderError(
                "Failed to generate text with OpenAI",
                details=str(e),
            ) from e
