"""LLM provider abstractions for different LLM services."""

from abc import ABC, abstractmethod

from langchain_core.language_models import BaseLanguageModel
from langchain_openai import ChatOpenAI

from ..core.config import get_app_config
from ..core.models import LLMProvider, ReviewConfig


class LLMProviderBase(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: ReviewConfig):
        """Initialize the LLM provider.

        Args:
            config: Review configuration
        """
        self.config = config
        self.app_config = get_app_config()

    @abstractmethod
    def get_language_model(self) -> BaseLanguageModel:
        """Get the LangChain language model instance.

        Returns:
            Configured language model
        """
        pass

    @abstractmethod
    def validate_config(self) -> None:
        """Validate that the provider configuration is correct.

        Raises:
            ValueError: If configuration is invalid
        """
        pass


class OpenAIProvider(LLMProviderBase):
    """OpenAI LLM provider."""

    def validate_config(self) -> None:
        """Validate OpenAI configuration."""
        if not self.app_config.openai_api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable."
            )

        # Validate model name - include GPT-5 models
        valid_openai_models = [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-3.5-turbo",
            "gpt-5",  # Latest GPT-5
            "gpt-5-mini",  # GPT-5 mini version
            "gpt-5-nano",  # GPT-5 nano version
        ]

        if self.config.model_name not in valid_openai_models:
            raise ValueError(
                f"Invalid OpenAI model: {self.config.model_name}. "
                f"Valid models: {', '.join(valid_openai_models)}"
            )

    def get_language_model(self) -> BaseLanguageModel:
        """Get OpenAI language model instance.

        Returns:
            ChatOpenAI instance
        """
        # Some models only support default temperature (1.0)
        temperature = self.config.temperature
        if self.config.model_name.startswith("gpt-5"):
            temperature = 1.0
            print(f"🔧 Adjusting temperature to {temperature} for GPT-5 model")
        elif self.config.model_name.startswith("grok"):
            temperature = 1.0
            print(f"🔧 Adjusting temperature to {temperature} for Grok model")

        return ChatOpenAI(
            model_name=self.config.model_name,
            temperature=temperature,
            max_tokens=self.config.max_tokens,
            openai_api_key=self.app_config.openai_api_key,
        )


class XAIProvider(LLMProviderBase):
    """xAI LLM provider (formerly Grok)."""

    def validate_config(self) -> None:
        """Validate xAI configuration."""
        if not self.app_config.grok_api_key:
            raise ValueError(
                "xAI API key is required. Set GROK_API_KEY environment variable."
            )

        # Valid xAI models
        valid_grok_models = [
            "grok-4-0709",
            "grok-4-0709-eu",
            "grok-code-fast-1",
        ]

        if self.config.model_name not in valid_grok_models:
            raise ValueError(
                f"Invalid xAI model: {self.config.model_name}. "
                f"Valid models: {', '.join(valid_grok_models)}"
            )

    def get_language_model(self) -> BaseLanguageModel:
        """Get xAI language model instance.

        Returns:
            ChatOpenAI instance (Grok uses OpenAI-compatible API)
        """
        # xAI uses OpenAI-compatible API format
        return ChatOpenAI(
            model_name=self.config.model_name,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            openai_api_key=self.app_config.grok_api_key,
            openai_api_base="https://api.x.ai/v1",  # Grok API endpoint
        )


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""

    @staticmethod
    def create_provider(config: ReviewConfig) -> LLMProviderBase:
        """Create an LLM provider instance.

        Args:
            config: Review configuration

        Returns:
            Configured LLM provider instance

        Raises:
            ValueError: If provider is not supported
        """
        if config.llm_provider == LLMProvider.OPENAI:
            provider = OpenAIProvider(config)
        elif config.llm_provider == LLMProvider.XAI:
            provider = XAIProvider(config)
        else:
            raise ValueError(f"Unsupported LLM provider: {config.llm_provider}")

        provider.validate_config()
        return provider


def get_language_model(config: ReviewConfig) -> BaseLanguageModel:
    """Get a configured language model instance.

    Args:
        config: Review configuration

    Returns:
        Configured language model
    """
    provider = LLMProviderFactory.create_provider(config)
    return provider.get_language_model()
