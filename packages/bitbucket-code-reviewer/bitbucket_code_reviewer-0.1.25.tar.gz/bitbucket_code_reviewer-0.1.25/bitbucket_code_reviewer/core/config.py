"""Configuration management for the code review system."""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .models import LLMProvider, ReviewConfig


class AppConfig(BaseSettings):
    """Application configuration from environment variables."""

    # Bitbucket configuration
    bitbucket_token: str = Field(..., description="Bitbucket API token")
    bitbucket_auth_username: Optional[str] = Field(
        None,
        description="Bitbucket username for App Password auth",
        env="BB_AUTH_USERNAME",
    )
    bitbucket_workspace: str = Field(..., description="Default Bitbucket workspace")

    # LLM configuration
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    grok_api_key: Optional[str] = Field(None, description="xAI API key")

    # Default settings (none; all required via CLI)
    default_llm_provider: Optional[LLMProvider] = Field(
        default=None, description="Default LLM provider (unused; pass via CLI)"
    )
    default_model_name: Optional[str] = Field(
        default=None, description="Default model name (unused; pass via CLI)"
    )
    default_temperature: Optional[float] = Field(
        default=None, description="Default temperature (unused; pass via CLI)"
    )

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, env_prefix=""
    )


def create_review_config(
    llm_provider: Optional[LLMProvider] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    language: Optional[str] = None,
    max_tool_iterations: Optional[int] = None,
    working_directory: Optional[str] = None,
) -> ReviewConfig:
    """Create a review configuration from CLI options and defaults.

    Args:
        llm_provider: LLM provider to use
        model_name: Specific model name
        temperature: Temperature for LLM generation
        max_tokens: Maximum tokens for response
        language: Programming language for guidelines
        max_tool_iterations: Maximum tool iterations
        working_directory: Working directory for repo operations

    Returns:
        ReviewConfig object with merged settings
    """
    app_config = get_app_config()

    # Use CLI values; do not fall back to defaults (strict)
    config = ReviewConfig(
        llm_provider=llm_provider,
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        language=language,
        max_tool_iterations=max_tool_iterations or 50,
        working_directory=working_directory or ".",
    )

    # Validate that required API keys are available
    _validate_api_keys(config.llm_provider, app_config)

    return config


def _validate_api_keys(llm_provider: LLMProvider, app_config: AppConfig) -> None:
    """Validate that required API keys are available for the chosen provider.

    Args:
        llm_provider: The LLM provider being used
        app_config: Application configuration

    Raises:
        ValueError: If required API key is missing
    """
    if llm_provider == LLMProvider.OPENAI and not app_config.openai_api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
        )

    if llm_provider == LLMProvider.XAI and not app_config.grok_api_key:
        raise ValueError(
            "xAI API key is required. Set GROK_API_KEY environment variable."
        )


def get_app_config() -> AppConfig:
    """Get the application configuration.

    Returns:
        AppConfig object with environment variables and saved config merged
    """
    # Load saved configuration
    config_manager = get_config_manager()
    saved_config = config_manager.get_all()

    # Create a dictionary with the correct field names for AppConfig
    config_dict = {}

    # First, load from environment variables (these take precedence)
    import os
    if "BITBUCKET_TOKEN" in os.environ:
        config_dict["bitbucket_token"] = os.environ["BITBUCKET_TOKEN"]
    if "BITBUCKET_WORKSPACE" in os.environ:
        config_dict["bitbucket_workspace"] = os.environ["BITBUCKET_WORKSPACE"]
    if "BB_AUTH_USERNAME" in os.environ:
        config_dict["bitbucket_auth_username"] = os.environ["BB_AUTH_USERNAME"]
    if "OPENAI_API_KEY" in os.environ:
        config_dict["openai_api_key"] = os.environ["OPENAI_API_KEY"]
    if "GROK_API_KEY" in os.environ:
        config_dict["grok_api_key"] = os.environ["GROK_API_KEY"]

    # Then fill in any missing values from saved config
    for key, value in saved_config.items():
        if key == "bitbucket_token" and "bitbucket_token" not in config_dict:
            config_dict["bitbucket_token"] = value
        elif key == "default_workspace" and "bitbucket_workspace" not in config_dict:
            config_dict["bitbucket_workspace"] = value

    # Create AppConfig with merged values
    return AppConfig(**config_dict)


def get_available_models(provider: LLMProvider) -> list[str]:
    """Get available models for a given provider.

    Args:
        provider: The LLM provider

    Returns:
        List of available model names
    """
    if provider == LLMProvider.OPENAI:
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-5",  # Latest GPT-5
            "gpt-5-mini",  # GPT-5 mini version
            "gpt-5-nano",  # GPT-5 nano version
        ]
    elif provider == LLMProvider.XAI:
        return [
            "grok-4-0709",
            "grok-4-0709-eu",
            "grok-code-fast-1",
        ]
    else:
        return []


class ConfigManager:
    """Manages persistent configuration stored in a JSON file."""

    def __init__(self, config_file: str = "~/.bb-review-config.json"):
        """Initialize config manager.

        Args:
            config_file: Path to config file (defaults to ~/.bb-review-config.json)
        """
        self.config_file = Path(config_file).expanduser()
        self._config: dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    self._config = json.load(f)
            except (OSError, json.JSONDecodeError):
                # If config file is corrupted, start fresh
                self._config = {}
        else:
            self._config = {}

    def _save_config(self) -> None:
        """Save configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self._save_config()

    def delete(self, key: str) -> None:
        """Delete a configuration value.

        Args:
            key: Configuration key to delete
        """
        if key in self._config:
            del self._config[key]
            self._save_config()

    def get_all(self) -> dict[str, Any]:
        """Get all configuration values.

        Returns:
            Dictionary of all configuration values
        """
        return self._config.copy()

    def clear(self) -> None:
        """Clear all configuration values."""
        self._config = {}
        self._save_config()


# Global config manager instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get the global config manager instance.

    Returns:
        ConfigManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


class CacheManager:
    """Manages caching of API responses and LLM results for performance."""

    def __init__(self, cache_dir: str = "~/.bb-review-cache", max_age_hours: int = 24):
        """Initialize cache manager.

        Args:
            cache_dir: Directory to store cache files
            max_age_hours: Maximum age of cache entries in hours
        """
        self.cache_dir = Path(cache_dir).expanduser()
        self.max_age_hours = max_age_hours
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, data: Any) -> str:
        """Generate a cache key from data.

        Args:
            data: Data to generate key for

        Returns:
            Cache key string
        """
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.sha256(data_str.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key.

        Args:
            cache_key: Cache key

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if a cache entry is still valid.

        Args:
            cache_path: Path to cache file

        Returns:
            True if cache is valid, False otherwise
        """
        if not cache_path.exists():
            return False

        import time

        cache_age = time.time() - cache_path.stat().st_mtime
        max_age_seconds = self.max_age_hours * 3600

        return cache_age < max_age_seconds

    def get(self, cache_key: str) -> Optional[Any]:
        """Get cached data.

        Args:
            cache_key: Cache key

        Returns:
            Cached data or None if not found/expired
        """
        cache_path = self._get_cache_path(cache_key)

        if not self._is_cache_valid(cache_path):
            return None

        try:
            with open(cache_path, encoding="utf-8") as f:
                cache_data = json.load(f)
            return cache_data.get("data")
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, cache_key: str, data: Any) -> None:
        """Store data in cache.

        Args:
            cache_key: Cache key
            data: Data to cache
        """
        cache_path = self._get_cache_path(cache_key)

        cache_entry = {"data": data, "timestamp": int(time.time())}

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, indent=2, ensure_ascii=False)
        except OSError:
            # Silently fail if we can't write to cache
            pass

    def invalidate(self, cache_key: str) -> None:
        """Invalidate a cache entry.

        Args:
            cache_key: Cache key to invalidate
        """
        cache_path = self._get_cache_path(cache_key)
        if cache_path.exists():
            cache_path.unlink()

    def clear(self) -> None:
        """Clear all cache entries."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_files = 0
        total_size = 0
        valid_entries = 0

        for cache_file in self.cache_dir.glob("*.json"):
            total_files += 1
            total_size += cache_file.stat().st_size

            if self._is_cache_valid(cache_file):
                valid_entries += 1

        return {
            "total_entries": total_files,
            "valid_entries": valid_entries,
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance.

    Returns:
        CacheManager instance
    """
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
