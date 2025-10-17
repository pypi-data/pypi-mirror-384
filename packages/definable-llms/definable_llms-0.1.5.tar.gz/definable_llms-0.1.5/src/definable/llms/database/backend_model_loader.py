"""Model loader that uses backend's models table instead of llms.lib's ModelRegistry."""

import structlog
from typing import Optional, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from ..base.types import ModelCapabilities, ModelInfo

logger = structlog.get_logger()


class BackendModelLoader:
  """Loads models from backend's models table (not llms.lib's ModelRegistry)."""

  def __init__(self, database_url: str):
    """Initialize with backend database URL.

    Args:
        database_url: PostgreSQL URL for your backend database
    """
    self.database_url = database_url
    self.engine = create_async_engine(database_url, echo=False)
    self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)
    self.logger = logger.bind(component="backend_model_loader")

  async def validate_model(self, provider: str, model_name: str) -> bool:
    """Check if model exists in backend's models table.

    Args:
        provider: Provider name (openai, anthropic, etc.)
        model_name: Model name (gpt-4.1, claude-sonnet-4-5, etc.)

    Returns:
        True if model exists and is active
    """
    try:
      async with self.async_session() as session:
        query = text("""
                    SELECT EXISTS(
                        SELECT 1 FROM models
                        WHERE provider = :provider
                        AND name = :model_name
                        AND is_active = true
                    )
                """)

        result = await session.execute(query, {"provider": provider, "model_name": model_name})
        exists = result.scalar()

        if exists:
          self.logger.debug(f"Model validated: {provider}:{model_name}")
        else:
          self.logger.warning(f"Model not found: {provider}:{model_name}")

        return bool(exists)

    except Exception as e:
      self.logger.error(f"Failed to validate model {provider}:{model_name}: {e}")
      return False

  async def get_model_capabilities(self, provider: str, model_name: str) -> Optional[ModelCapabilities]:
    """Get model capabilities from backend's models table.

    Args:
        provider: Provider name
        model_name: Model name

    Returns:
        ModelCapabilities if found, None otherwise
    """
    try:
      async with self.async_session() as session:
        query = text("""
                    SELECT config, props, model_metadata
                    FROM models
                    WHERE provider = :provider
                    AND name = :model_name
                    AND is_active = true
                """)

        result = await session.execute(query, {"provider": provider, "model_name": model_name})
        row = result.first()

        if not row:
          return None

        config, props, metadata = row

        # Build ModelCapabilities from backend data
        # Adjust field names based on your actual schema
        return ModelCapabilities(
          chat=props.get("chat", True),
          streaming=props.get("streaming", True),
          function_calling=props.get("function_calling", False),
          vision=props.get("vision", False),
          audio=props.get("audio", False),
          embeddings=props.get("embeddings", False),
          image_generation=props.get("image_generation", False),
          reasoning=props.get("reasoning", False),
          max_context_length=config.get("max_context_length", 128000),
          max_output_tokens=config.get("max_output_tokens", 4096),
          supported_file_types=props.get("supported_file_types", []),
          input_cost_per_token=float(config.get("input_cost_per_token", 0.0)),
          output_cost_per_token=float(config.get("output_cost_per_token", 0.0)),
          supports_system_messages=props.get("supports_system_messages", True),
          supports_tool_calls=props.get("supports_tool_calls", False),
          supports_parallel_tool_calls=props.get("supports_parallel_tool_calls", False),
        )

    except Exception as e:
      self.logger.error(f"Failed to get capabilities for {provider}:{model_name}: {e}")
      return None

  async def get_supported_models_info(self, provider: str) -> List[ModelInfo]:
    """Get all models for a provider from backend's models table.

    Args:
        provider: Provider name

    Returns:
        List of ModelInfo objects
    """
    try:
      async with self.async_session() as session:
        query = text("""
                    SELECT name, version, config, props, model_metadata
                    FROM models
                    WHERE provider = :provider
                    AND is_active = true
                    ORDER BY name
                """)

        result = await session.execute(query, {"provider": provider})
        rows = result.all()

        model_infos = []
        for row in rows:
          name, version, config, props, metadata = row

          # Get capabilities
          caps = await self.get_model_capabilities(provider, name)
          if not caps:
            continue

          model_infos.append(
            ModelInfo(
              name=name,
              display_name=metadata.get("display_name", name) if metadata else name,
              description=metadata.get("description", f"{provider} {name}") if metadata else f"{provider} {name}",
              capabilities=caps,
              provider=provider,
              model_type=metadata.get("model_type", "chat") if metadata else "chat",
              is_deprecated=False,
            )
          )

        return model_infos

    except Exception as e:
      self.logger.error(f"Failed to get models for {provider}: {e}")
      return []

  async def close(self):
    """Close database connection."""
    await self.engine.dispose()
