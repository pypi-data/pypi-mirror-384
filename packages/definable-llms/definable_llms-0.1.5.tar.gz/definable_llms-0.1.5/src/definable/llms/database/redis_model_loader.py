"""Redis model loader - Redis as cache and PostgreSQL fallback."""

import structlog

from typing import Optional, List

from .model_loader import DatabaseModelLoader
from ..base.types import ModelCapabilities, ModelInfo
from ..cache import get_model_cache

logger = structlog.get_logger()


class RedisModelLoader(DatabaseModelLoader):
  """Model loader with Redis as cache, PostgreSQL as fallback"""

  def __init__(self):
    """Initialize Redis-first model loader."""
    super().__init__()
    self.cache = get_model_cache()
    self.logger = logger.bind(component="redis_model_loader")

  async def get_model_capabilities(self, provider: str, model: str) -> Optional[ModelCapabilities]:
    """
    Get model capabilities

    Flow:
    1. Check Redis
    2. If miss -> Query PostgreSQL
    3. Update Redis with PostgreSQL data
    4. Return capabilities
    """
    # Step 1: Check Redis cache
    capabilities = await self.cache.get_model_capabilities(provider, model)

    if capabilities:
      self.logger.debug(f"Cached: {provider}:{model}")
      return capabilities

    # Step 2: Cache miss - fallback to PostgreSQL
    self.logger.debug(f"Not cached: {provider}:{model} - querying database")
    capabilities = await super().get_model_capabilities(provider, model)

    if capabilities:
      # Step 3: Update Redis cache
      await self.cache.set_model_capabilities(provider, model, capabilities)
      self.logger.debug(f"Database -> Cache: {provider}:{model}")

    return capabilities

  async def get_provider_models(self, provider: str, capability: Optional[str] = None) -> List:
    """Get provider models"""
    # Check Redis cache first
    cached_models = await self.cache.get_provider_models(provider)

    if cached_models:
      # Get full model data from cache
      models = []
      for model_name in cached_models:
        caps = await self.cache.get_model_capabilities(provider, model_name)
        if caps:
          # Filter by capability if specified
          if capability and not (
            (capability == "chat" and caps.chat)
            or (capability == "embedding" and caps.embeddings)
            or (capability == "image_gen" and caps.image_generation)
          ):
            continue

          # Convert to model registry format (simplified)
          models.append(
            type(
              "Model",
              (),
              {
                "model_name": model_name,
                "provider": provider,
                "capability": "chat" if caps.chat else "embedding" if caps.embeddings else "image_gen",
                "max_context_length": caps.max_context_length,
                "max_output_tokens": caps.max_output_tokens,
                "input_cost_per_token": caps.input_cost_per_token,
                "output_cost_per_token": caps.output_cost_per_token,
                "supports_streaming": caps.streaming,
                "supports_functions": caps.function_calling,
                "supports_vision": caps.vision,
                "is_active": True,
              },
            )()
          )

      self.logger.debug(f"Provider models from cache: {provider} ({len(models)} models)")
      return models

    # Fallback to database
    models = await super().get_provider_models(provider)

    if models:
      # Cache the model list
      model_names = [m.model_name for m in models]
      await self.cache.set_provider_models(provider, model_names)

      # Cache individual model capabilities
      for model in models:
        caps = self._convert_to_capabilities_from_model(model)
        await self.cache.set_model_capabilities(provider, model.model_name, caps)

      self.logger.debug(f"Database -> Cache: {provider} provider models")

    return models

  async def get_supported_models_info(self, provider: str) -> List[ModelInfo]:
    """Get supported models info"""
    models = await self.get_provider_models(provider)

    model_infos = []
    for model in models:
      caps = await self.get_model_capabilities(provider, model.model_name)
      if caps:
        model_info = ModelInfo(
          name=model.model_name,
          display_name=getattr(model, "display_name", None) or model.model_name.replace("-", " ").title(),
          description=getattr(model, "description", None) or f"{provider} {model.model_name} model",
          capabilities=caps,
          provider=provider,
          model_type="chat" if caps.chat else "embedding" if caps.embeddings else "image",
          is_deprecated=False,
        )
        model_infos.append(model_info)

    return model_infos

  async def validate_model(self, provider: str, model: str) -> bool:
    """Validate model exists"""
    capabilities = await self.get_model_capabilities(provider, model)
    return capabilities is not None

  async def warm_cache(self, provider: str):
    """Warm Redis cache with all provider models from database."""
    self.logger.info(f"Warming cache for provider: {provider}")

    # Force load from database to populate cache
    models = await super().get_provider_models(provider)

    if models:
      # Cache model list
      model_names = [m.model_name for m in models]
      await self.cache.set_provider_models(provider, model_names)

      # Cache individual capabilities
      for model in models:
        caps = self._convert_to_capabilities_from_model(model)
        await self.cache.set_model_capabilities(provider, model.model_name, caps)

      self.logger.info(f"Warmed cache: {provider} ({len(models)} models)")
    else:
      self.logger.warning(f"No models found for provider: {provider}")


# Global Redis-first loader instance
redis_model_loader = RedisModelLoader()
