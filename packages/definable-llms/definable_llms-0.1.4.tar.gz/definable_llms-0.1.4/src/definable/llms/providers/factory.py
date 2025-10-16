"""Provider factory for creating and managing LLM providers."""

from typing import Dict, Type, Optional, Any, List
import structlog

from ..base import BaseProvider
from ..base.exceptions import ProviderNotFoundError, ConfigurationError
from ..config import Settings, ProviderType


logger = structlog.get_logger()


class ProviderRegistry:
  """Registry for managing available providers."""

  def __init__(self):
    """Initialize the provider registry."""
    self._providers: Dict[str, Type[BaseProvider]] = {}
    self._instances: Dict[str, BaseProvider] = {}
    self.logger = logger.bind(component="provider_registry")

    # Register built-in providers
    self._register_builtin_providers()

  def _register_builtin_providers(self):
    """Register built-in providers."""
    try:
      from .openai import OpenAIProvider

      self.register("openai", OpenAIProvider)
    except ImportError as e:
      self.logger.warning(f"Failed to register OpenAI provider: {e}")

    try:
      from .gemini import GeminiProvider

      self.register("gemini", GeminiProvider)
    except ImportError as e:
      self.logger.warning(f"Failed to register Gemini provider: {e}")

    try:
      from .anthropic import AnthropicProvider

      self.register("anthropic", AnthropicProvider)
    except ImportError as e:
      self.logger.warning(f"Failed to register Anthropic provider: {e}")

    try:
      from .deepseek import DeepSeekProvider

      self.register("deepseek", DeepSeekProvider)
    except ImportError as e:
      self.logger.warning(f"Failed to register DeepSeek provider: {e}")

  def register(self, name: str, provider_class: Type[BaseProvider]):
    """Register a provider class.

    Args:
        name: Provider name
        provider_class: Provider class
    """
    if not issubclass(provider_class, BaseProvider):
      raise ConfigurationError(f"Provider class {provider_class} must inherit from BaseProvider")

    self._providers[name.lower()] = provider_class
    self.logger.info(f"Registered provider: {name}")

  def unregister(self, name: str):
    """Unregister a provider.

    Args:
        name: Provider name
    """
    name_lower = name.lower()
    if name_lower in self._providers:
      del self._providers[name_lower]
      # Also remove any cached instances
      if name_lower in self._instances:
        del self._instances[name_lower]
      self.logger.info(f"Unregistered provider: {name}")

  def get_provider_class(self, name: str) -> Type[BaseProvider]:
    """Get a provider class by name.

    Args:
        name: Provider name

    Returns:
        Provider class

    Raises:
        ProviderNotFoundError: If provider is not registered
    """
    name_lower = name.lower()
    if name_lower not in self._providers:
      raise ProviderNotFoundError(name)

    return self._providers[name_lower]

  def list_providers(self) -> List[str]:
    """List all registered provider names.

    Returns:
        List of provider names
    """
    return list(self._providers.keys())

  def is_registered(self, name: str) -> bool:
    """Check if a provider is registered.

    Args:
        name: Provider name

    Returns:
        True if provider is registered
    """
    return name.lower() in self._providers

  def clear(self):
    """Clear all registered providers and instances."""
    self._providers.clear()
    self._instances.clear()
    self.logger.info("Cleared all providers")


class ProviderFactory:
  """Factory for creating and managing provider instances."""

  def __init__(self, config: Optional[Settings] = None):
    """Initialize the provider factory.

    Args:
        config: Configuration settings
    """
    self.config = config or Settings()
    self.registry = ProviderRegistry()
    self._cache: Dict[str, BaseProvider] = {}
    self.logger = logger.bind(component="provider_factory")

  def create_provider(
    self,
    provider_type: str,
    api_key: Optional[str] = None,
    cache: bool = True,
    **kwargs,
  ) -> BaseProvider:
    """Create a provider instance.

    Args:
        provider_type: Type of provider to create
        api_key: API key for the provider
        cache: Whether to cache the instance
        **kwargs: Additional provider-specific parameters

    Returns:
        Provider instance

    Raises:
        ProviderNotFoundError: If provider type is not supported
        ConfigurationError: If provider configuration is invalid
    """
    provider_type_lower = provider_type.lower()

    # Check if we have a cached instance and caching is enabled
    cache_key = f"{provider_type_lower}:{api_key or 'default'}"
    if cache and cache_key in self._cache:
      return self._cache[cache_key]

    # Get provider class
    provider_class = self.registry.get_provider_class(provider_type_lower)

    # Get configuration for the provider
    provider_config = self.config.get_provider_config(ProviderType(provider_type_lower))

    # Use provided API key or fall back to config
    if not api_key:
      api_key = provider_config.get("api_key")

    if not api_key:
      raise ConfigurationError(f"No API key provided for {provider_type} provider")

    # Merge provider config with kwargs
    merged_config = {**provider_config, **kwargs}
    merged_config["api_key"] = api_key

    try:
      # Create provider instance
      provider = provider_class(
        api_key=api_key,
        config=self.config,
        **{k: v for k, v in merged_config.items() if k != "api_key"},
      )

      # Cache the instance if requested
      if cache:
        self._cache[cache_key] = provider

      self.logger.info(f"Created provider instance: {provider_type}")
      return provider

    except Exception as e:
      self.logger.error(f"Failed to create {provider_type} provider: {e}")
      raise ConfigurationError(f"Failed to create {provider_type} provider: {str(e)}")

  def get_provider(
    self,
    provider_type: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs,
  ) -> BaseProvider:
    """Get a provider instance, using default if not specified.

    Args:
        provider_type: Type of provider (uses default if None)
        api_key: API key for the provider
        **kwargs: Additional provider-specific parameters

    Returns:
        Provider instance
    """
    if not provider_type:
      provider_type = self.config.default_provider.value

    return self.create_provider(provider_type, api_key, **kwargs)

  async def get_available_providers(self) -> List[Dict[str, Any]]:
    """Get list of available providers with their info.

    Returns:
        List of provider information dictionaries
    """
    providers = []

    for provider_name in self.registry.list_providers():
      try:
        # Try to create a provider instance to check availability
        provider_config = self.config.get_provider_config(ProviderType(provider_name))

        if provider_config.get("api_key"):
          provider = self.create_provider(provider_name, cache=False)
          info = await provider.get_info()
        else:
          # Create info without instantiating
          provider_class = self.registry.get_provider_class(provider_name)
          dummy_provider = provider_class("", api_key="dummy")
          info = await dummy_provider.get_info()
          info.is_available = False
          info.error_message = "API key not configured"

        providers.append(info.model_dump())

      except Exception as e:
        self.logger.warning(f"Failed to get info for provider {provider_name}: {e}")
        providers.append({
          "name": provider_name,
          "type": "Unknown",
          "version": "Unknown",
          "capabilities": {},
          "is_available": False,
          "error_message": str(e),
        })

    return providers

  def clear_cache(self):
    """Clear the provider instance cache."""
    self._cache.clear()
    self.logger.info("Cleared provider cache")

  async def close_all(self):
    """Close all cached provider instances and cleanup resources."""
    for cache_key, provider in list(self._cache.items()):
      try:
        await provider.close()
        self.logger.debug(f"Closed provider: {cache_key}")
      except Exception as e:
        self.logger.error(f"Error closing provider {cache_key}: {e}")

    self._cache.clear()
    self.logger.info("Closed all providers and cleared cache")

  async def __aenter__(self):
    """Async context manager entry."""
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit."""
    await self.close_all()
    return False

  def register_provider(self, name: str, provider_class: Type[BaseProvider]):
    """Register a custom provider.

    Args:
        name: Provider name
        provider_class: Provider class
    """
    self.registry.register(name, provider_class)


# Global factory instance
provider_factory = ProviderFactory()
