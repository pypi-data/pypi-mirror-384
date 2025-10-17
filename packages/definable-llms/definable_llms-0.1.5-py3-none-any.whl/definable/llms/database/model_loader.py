"""Database model loader for provider configurations."""

from typing import List, Optional, Dict
import structlog

from .schema import ModelRegistry
from .models import ModelRegistryModel
from ..base.types import ModelCapabilities, ModelInfo
from sqlalchemy import select

logger = structlog.get_logger()


class DatabaseModelLoader:
  """Loads provider models and capabilities from database."""

  def __init__(self):
    self.logger = logger.bind(component="db_model_loader")
    self._cache: Dict[str, List[ModelRegistryModel]] = {}

  async def get_provider_models(self, provider: str, capability: Optional[str] = None) -> List[ModelRegistryModel]:
    """Get models for a provider from database.

    Args:
        provider: Provider name (e.g., "openai")
        capability: Optional capability filter ("chat", "embedding", "image_gen")

    Returns:
        List of model registry models
    """
    cache_key = f"{provider}:{capability or 'all'}"

    if cache_key in self._cache:
      return self._cache[cache_key]

    try:
      from . import get_db_session

      async with get_db_session() as db:
        query = select(ModelRegistry).where(ModelRegistry.provider == provider, ModelRegistry.is_active)

        if capability:
          query = query.where(ModelRegistry.capability == capability)

        result = await db.execute(query.order_by(ModelRegistry.model_name))
        models_data = result.scalars().all()

        models = [ModelRegistryModel.model_validate(model, from_attributes=True) for model in models_data]

        self._cache[cache_key] = models
        self.logger.info(f"Loaded {len(models)} models for {provider}:{capability or 'all'}")
        return models

    except Exception as e:
      self.logger.error(f"Failed to load models for {provider}: {e}")
      return []

  async def get_model_capabilities(self, provider: str, model_name: str) -> Optional[ModelCapabilities]:
    """Get capabilities for a specific model from database.

    Args:
        provider: Provider name
        model_name: Model name

    Returns:
        Model capabilities or None if not found
    """
    try:
      from . import get_db_session

      async with get_db_session() as db:
        result = await db.execute(
          select(ModelRegistry).where(
            ModelRegistry.provider == provider,
            ModelRegistry.model_name == model_name,
            ModelRegistry.is_active,
          )
        )
        model_data = result.scalar_one_or_none()

        if not model_data:
          return None

        # Convert database model to ModelCapabilities
        return self._convert_to_capabilities(model_data)

    except Exception as e:
      self.logger.error(f"Failed to get capabilities for {model_name}: {e}")
      return None

  async def get_supported_models_info(self, provider: str) -> List[ModelInfo]:
    """Get ModelInfo objects for all supported models.

    Args:
        provider: Provider name

    Returns:
        List of ModelInfo objects
    """
    models_info = []

    try:
      models = await self.get_provider_models(provider)

      for model in models:
        capabilities = self._convert_to_capabilities_from_model(model)

        models_info.append(
          ModelInfo(
            name=model.model_name,
            display_name=model.model_name.replace("-", " ").title(),
            description=model.description or f"{model.capability.title()} model",
            capabilities=capabilities,
            provider=provider,
            model_type="image"
            if model.capability == "image_gen"
            else ("chat" if model.capability == "chat" else "embedding"),  # Convert capabilities to model types
            is_deprecated=False,
          )
        )

      return models_info

    except Exception as e:
      self.logger.error(f"Failed to get model info for {provider}: {e}")
      return []

  async def validate_model(self, provider: str, model_name: str) -> bool:
    """Check if a model is supported and active.

    Args:
        provider: Provider name
        model_name: Model name to validate

    Returns:
        True if model is supported and active
    """
    try:
      from . import get_db_session

      async with get_db_session() as db:
        result = await db.execute(
          select(ModelRegistry.model_name).where(
            ModelRegistry.provider == provider,
            ModelRegistry.model_name == model_name,
            ModelRegistry.is_active,
          )
        )
        return result.scalar_one_or_none() is not None

    except Exception as e:
      self.logger.error(f"Failed to validate model {model_name}: {e}")
      return False

  def _convert_to_capabilities(self, model_data: ModelRegistry) -> ModelCapabilities:
    """Convert database model to ModelCapabilities."""
    return ModelCapabilities(
      chat=bool(model_data.capability == "chat"),
      streaming=bool(model_data.supports_streaming),
      function_calling=bool(model_data.supports_functions),
      vision=bool(model_data.supports_vision),
      audio=False,  # Not currently supported
      embeddings=bool(model_data.capability == "embedding"),
      image_generation=bool(model_data.capability == "image_gen"),
      reasoning=bool(model_data.supports_reasoning),
      max_context_length=int(model_data.max_context_length),
      max_output_tokens=int(model_data.max_output_tokens) if model_data.max_output_tokens else None,
      supported_file_types=[".png", ".jpg", ".jpeg", ".gif", ".webp"] if bool(model_data.supports_vision) else [],
      input_cost_per_token=float(model_data.input_cost_per_token),
      output_cost_per_token=float(model_data.output_cost_per_token) if model_data.output_cost_per_token else None,
      supports_system_messages=bool(model_data.capability == "chat"),
      supports_tool_calls=bool(model_data.supports_functions),
      supports_parallel_tool_calls=bool(model_data.supports_functions),
    )

  def _convert_to_capabilities_from_model(self, model: ModelRegistryModel) -> ModelCapabilities:
    """Convert ModelRegistryModel to ModelCapabilities."""
    return ModelCapabilities(
      chat=(model.capability == "chat"),
      streaming=model.supports_streaming,
      function_calling=model.supports_functions,
      vision=model.supports_vision,
      audio=False,  # Not currently supported
      embeddings=(model.capability == "embedding"),
      image_generation=(model.capability == "image_gen"),
      reasoning=model.supports_reasoning,
      max_context_length=model.max_context_length,
      max_output_tokens=model.max_output_tokens,
      supported_file_types=[".png", ".jpg", ".jpeg", ".gif", ".webp"] if model.supports_vision else [],
      input_cost_per_token=float(model.input_cost_per_token),
      output_cost_per_token=float(model.output_cost_per_token) if model.output_cost_per_token else None,
      supports_system_messages=(model.capability == "chat"),
      supports_tool_calls=model.supports_functions,
      supports_parallel_tool_calls=model.supports_functions,
    )

  def clear_cache(self):
    """Clear the model cache."""
    self._cache.clear()
    self.logger.info("Cleared model cache")


# Global instance for use across providers
db_model_loader = DatabaseModelLoader()
