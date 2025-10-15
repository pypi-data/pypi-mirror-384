"""Factory for creating AI providers."""

from enum import Enum
from typing import Optional

from smartgit.core.exceptions import ConfigurationError
from smartgit.providers.base import AIProvider


class ProviderType(Enum):
    """Supported AI provider types."""

    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class ProviderFactory:
    """
    Factory for creating AI provider instances (Factory pattern).

    Centralizes the creation logic and makes it easy to add new providers.
    """

    @staticmethod
    def create(
        provider_type: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_type: Type of provider ("anthropic" or "openai").
            api_key: API key for the provider.
            model: Model name/ID to use.

        Returns:
            AIProvider instance.

        Raises:
            ConfigurationError: If provider type is unsupported.
        """
        # Import here to avoid circular dependencies
        from smartgit.providers.anthropic_provider import AnthropicProvider
        from smartgit.providers.openai_provider import OpenAIProvider

        provider_map = {
            ProviderType.ANTHROPIC.value: AnthropicProvider,
            ProviderType.OPENAI.value: OpenAIProvider,
        }

        provider_class = provider_map.get(provider_type.lower())

        if not provider_class:
            supported = ", ".join(p.value for p in ProviderType)
            raise ConfigurationError(
                f"Unsupported provider: {provider_type}",
                details=f"Supported providers: {supported}",
            )

        try:
            instance = provider_class(api_key=api_key, model=model)
            return instance
        except Exception as e:
            raise ConfigurationError(
                f"Failed to create {provider_type} provider",
                details=str(e),
            ) from e

    @staticmethod
    def get_supported_providers() -> list[str]:
        """Get list of supported provider names."""
        return [p.value for p in ProviderType]
