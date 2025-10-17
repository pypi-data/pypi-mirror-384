"""Redis cache for model capabilities"""

import json
import structlog
import redis.asyncio as aioredis

from typing import Optional, List

from ..base.types import ModelCapabilities
from ..config import Settings

logger = structlog.get_logger()


class ModelCache:
  """Redis-based model cache."""

  def __init__(self, settings: Optional[Settings] = None):
    """Initialize Redis cache."""
    self.settings = settings or Settings()
    self._redis: Optional[aioredis.Redis] = None
    self.logger = logger.bind(component="model_cache")

  async def _get_redis(self) -> Optional[aioredis.Redis]:
    """Get Redis connection."""
    if not self.settings.redis_url:
      return None

    if self._redis is None:
      try:
        self._redis = aioredis.from_url(
          self.settings.redis_url,
          decode_responses=True,
          retry_on_timeout=True,
          socket_connect_timeout=2,
        )
        # Test connection
        await self._redis.ping()
        self.logger.info("Redis cache connected")
      except Exception as e:
        self.logger.warning(f"Redis connection failed, cache disabled: {e}")
        self._redis = None

    return self._redis

  def _model_key(self, provider: str, model: str) -> str:
    """Generate Redis key for model capabilities."""
    return f"model:{provider}:{model}"

  def _provider_key(self, provider: str) -> str:
    """Generate Redis key for provider models."""
    return f"provider:{provider}:models"

  async def get_model_capabilities(self, provider: str, model: str) -> Optional[ModelCapabilities]:
    """Get model capabilities from Redis cache."""
    redis = await self._get_redis()
    if not redis:
      return None

    try:
      key = self._model_key(provider, model)
      data = await redis.get(key)

      if data:
        caps_dict = json.loads(data)
        return ModelCapabilities(**caps_dict)

    except Exception as e:
      self.logger.warning(f"Redis get failed for {provider}:{model}: {e}")

    return None

  async def set_model_capabilities(self, provider: str, model: str, capabilities: ModelCapabilities) -> bool:
    """Set model capabilities in Redis cache."""
    redis = await self._get_redis()
    if not redis:
      return False

    try:
      key = self._model_key(provider, model)
      data = json.dumps(capabilities.model_dump())

      await redis.setex(key, self.settings.redis_ttl, data)
      self.logger.debug(f"Cached model capabilities: {provider}:{model}")
      return True

    except Exception as e:
      self.logger.warning(f"Redis set failed for {provider}:{model}: {e}")
      return False

  async def get_provider_models(self, provider: str) -> Optional[List[str]]:
    """Get provider model list from Redis cache."""
    redis = await self._get_redis()
    if not redis:
      return None

    try:
      key = self._provider_key(provider)
      models = await redis.smembers(key)  # type: ignore
      return list(models) if models else None

    except Exception as e:
      self.logger.warning(f"Redis get provider models failed for {provider}: {e}")
      return None

  async def set_provider_models(self, provider: str, models: List[str]) -> bool:
    """Set provider model list in Redis cache."""
    redis = await self._get_redis()
    if not redis:
      return False

    try:
      key = self._provider_key(provider)
      # Clear existing set
      await redis.delete(key)
      # Add all models
      if models:
        await redis.sadd(key, *models)  # type: ignore
        await redis.expire(key, self.settings.redis_ttl)

      self.logger.debug(f"Cached provider models: {provider} ({len(models)} models)")
      return True

    except Exception as e:
      self.logger.warning(f"Redis set provider models failed for {provider}: {e}")
      return False

  async def invalidate_provider(self, provider: str) -> bool:
    """Invalidate all cached data for a provider from Redis cache."""
    redis = await self._get_redis()
    if not redis:
      return False

    try:
      # Get pattern for all provider models
      pattern = f"model:{provider}:*"
      keys = await redis.keys(pattern)

      # Add provider models key
      keys.append(self._provider_key(provider))

      if keys:
        await redis.delete(*keys)
        self.logger.info(f"Invalidated {len(keys)} cache entries for {provider}")

      return True

    except Exception as e:
      self.logger.warning(f"Redis invalidation failed for {provider}: {e}")
      return False

  async def health_check(self) -> bool:
    """Check Redis connection health"""
    redis = await self._get_redis()
    if not redis:
      return False

    try:
      await redis.ping()
      return True
    except Exception:
      return False

  async def close(self):
    """Close Redis connection."""
    if self._redis:
      await self._redis.close()
      self._redis = None


# Global cache instance
_cache_instance: Optional[ModelCache] = None


def get_model_cache() -> ModelCache:
  """Get global model cache instance."""
  global _cache_instance
  if _cache_instance is None:
    _cache_instance = ModelCache()
  return _cache_instance
