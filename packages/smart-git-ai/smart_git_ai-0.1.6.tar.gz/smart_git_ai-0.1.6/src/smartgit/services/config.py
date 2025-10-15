"""Configuration management using Pydantic."""

import os
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from smartgit.core.exceptions import ConfigurationError


class SmartGitConfig(BaseSettings):
    """
    Application configuration using Pydantic Settings.

    Supports loading from:
    - Environment variables (SMARTGIT_*)
    - Config file (~/.smartgit/config.yml or .smartgit.yml in repo)
    """

    model_config = SettingsConfigDict(
        env_prefix="SMARTGIT_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # AI Provider settings
    provider: str = Field(
        default="anthropic",
        description="AI provider to use (anthropic or openai)",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for the AI provider",
    )
    model: Optional[str] = Field(
        default=None,
        description="Model to use (defaults to provider default)",
    )

    # Commit message settings
    max_subject_length: int = Field(
        default=50,
        description="Maximum length for commit subject",
    )
    commit_style: str = Field(
        default="conventional",
        description="Commit message style (conventional or simple)",
    )
    auto_add: bool = Field(
        default=False,
        description="Automatically stage all changes before committing",
    )

    # Hook settings
    hook_enabled: bool = Field(
        default=True,
        description="Enable prepare-commit-msg hook",
    )
    hook_interactive: bool = Field(
        default=True,
        description="Allow editing AI-generated messages",
    )

    # Advanced settings
    context_lines: int = Field(
        default=3,
        description="Number of context lines in diff",
    )
    max_diff_size: int = Field(
        default=5000,
        description="Maximum diff size to send to AI (characters)",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate provider is supported."""
        if v not in ("anthropic", "openai"):
            raise ValueError(f"Unsupported provider: {v}")
        return v

    @field_validator("commit_style")
    @classmethod
    def validate_commit_style(cls, v: str) -> str:
        """Validate commit style."""
        if v not in ("conventional", "simple"):
            raise ValueError(f"Unsupported commit style: {v}")
        return v

    @model_validator(mode="before")
    @classmethod
    def load_provider_api_key(cls, values: dict) -> dict:
        """Load API key from provider-specific environment variables if not set."""
        # Check if api_key is not set
        if not values.get("api_key"):
            provider = values.get("provider", "anthropic")

            # Check for provider-specific API keys in environment
            if provider == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    values["api_key"] = api_key
            elif provider == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    values["api_key"] = api_key

        return values


class ConfigManager:
    """
    Manages application configuration (Singleton pattern).

    Loads configuration from multiple sources in order of precedence:
    1. Environment variables
    2. Repository config file (.smartgit.yml)
    3. User config file (~/.smartgit/config.yml)
    4. Defaults
    """

    _instance: Optional["ConfigManager"] = None
    _config: Optional[SmartGitConfig] = None

    def __new__(cls) -> "ConfigManager":
        """Ensure only one instance exists (Singleton)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize config manager."""
        if self._config is None:
            self._config = self._load_config()

    @property
    def config(self) -> SmartGitConfig:
        """Get current configuration."""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def reload(self) -> None:
        """Reload configuration from sources."""
        self._config = self._load_config()

    def _load_config(self) -> SmartGitConfig:
        """Load configuration from all sources."""
        # Load .env file from current directory into environment variables
        # This makes ANTHROPIC_API_KEY and other vars available to os.getenv()
        # override=True ensures .env values take precedence over existing env vars
        load_dotenv(override=True)

        # Start with config file data
        config_data = {}

        # Try to load from repository config
        repo_config = Path.cwd() / ".smartgit.yml"
        if repo_config.exists():
            try:
                config_data.update(self._load_yaml_file(repo_config))
            except Exception:
                pass

        # Try to load from user config
        user_config = Path.home() / ".smartgit" / "config.yml"
        if user_config.exists():
            try:
                user_data = self._load_yaml_file(user_config)
                # Repository config takes precedence, so only add missing keys
                for key, value in user_data.items():
                    if key not in config_data:
                        config_data[key] = value
            except Exception:
                pass

        # Create Pydantic settings (will also load from env vars)
        try:
            return SmartGitConfig(**config_data)
        except Exception as e:
            raise ConfigurationError(
                "Failed to load configuration",
                details=str(e),
            ) from e

    def _load_yaml_file(self, path: Path) -> dict:
        """Load YAML configuration file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
                return data
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML in {path}",
                details=str(e),
            ) from e

    def save_user_config(self, config_updates: dict) -> None:
        """Save configuration to user config file."""
        user_config_dir = Path.home() / ".smartgit"
        user_config_dir.mkdir(exist_ok=True)

        user_config_path = user_config_dir / "config.yml"

        # Load existing config if present
        existing_data = {}
        if user_config_path.exists():
            existing_data = self._load_yaml_file(user_config_path)

        # Merge updates
        existing_data.update(config_updates)

        # Save
        try:
            with open(user_config_path, "w") as f:
                yaml.safe_dump(existing_data, f, default_flow_style=False, sort_keys=False)
            self.reload()
        except Exception as e:
            raise ConfigurationError(
                "Failed to save user config",
                details=str(e),
            ) from e

    def save_repo_config(self, config_updates: dict) -> None:
        """Save configuration to repository config file."""
        repo_config_path = Path.cwd() / ".smartgit.yml"

        # Load existing config if present
        existing_data = {}
        if repo_config_path.exists():
            existing_data = self._load_yaml_file(repo_config_path)

        # Merge updates
        existing_data.update(config_updates)

        # Save
        try:
            with open(repo_config_path, "w") as f:
                yaml.safe_dump(existing_data, f, default_flow_style=False, sort_keys=False)
            self.reload()
        except Exception as e:
            raise ConfigurationError(
                "Failed to save repository config",
                details=str(e),
            ) from e


# Singleton instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
