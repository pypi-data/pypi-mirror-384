#!/usr/bin/env python3
"""Script to warm Redis cache with model data from PostgreSQL."""

import asyncio
import sys

from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from definable.llms.database.redis_model_loader import redis_model_loader
from definable.llms.cache import get_model_cache
from definable.llms.database import init_database
from definable.llms.config import Settings


async def main():
  """Warm Redis cache with model data."""
  print("Warming Redis Cache from PostgreSQL...")
  print("=" * 50)

  try:
    # Initialize database first
    settings = Settings()
    await init_database(settings.db_url)
    print("PostgreSQL database initialized")

    cache = get_model_cache()

    # Test Redis connection
    if await cache.health_check():
      print("Redis connection: OK")
    else:
      print("Redis connection: FAILED")
      return

    # Warm cache for OpenAI
    print("\nLoading OpenAI models from PostgreSQL...")
    await redis_model_loader.warm_cache("openai")

    # Warm cache for Gemini
    print("\nLoading Gemini models from PostgreSQL...")
    await redis_model_loader.warm_cache("gemini")

    # Warm cache for Anthropic
    print("\nLoading Anthropic models from PostgreSQL...")
    await redis_model_loader.warm_cache("anthropic")

    # Verify cache warming
    models = await cache.get_provider_models("openai")
    if models:
      print(f"Cached {len(models)} OpenAI models in Redis")

      # Test a few model capabilities
      for model in models[:3]:
        caps = await cache.get_model_capabilities("openai", model)
        if caps:
          print(f"{model}: context={caps.max_context_length:,}, cost=${caps.input_cost_per_token:.8f}")

      models = await cache.get_provider_models("gemini")
      if models:
        print(f"Cached {len(models)} Gemini models in Redis")

        # Test a few model capabilities
        for model in models[:3]:
          caps = await cache.get_model_capabilities("gemini", model)
          if caps:
            print(f"{model}: context={caps.max_context_length:,}, cost=${caps.input_cost_per_token:.8f}")

      models = await cache.get_provider_models("anthropic")
      if models:
        print(f"Cached {len(models)} Anthropic models in Redis")

        # Test a few model capabilities
        for model in models[:3]:
          caps = await cache.get_model_capabilities("anthropic", model)
          if caps:
            print(f"{model}: context={caps.max_context_length:,}, cost=${caps.input_cost_per_token:.8f}")

    else:
      print("No models cached")

    print("\nRedis Cache Warmed Successfully!")

  except Exception as e:
    print(f"Cache warming failed: {e}")
    import traceback

    traceback.print_exc()

  finally:
    # Close connections
    cache = get_model_cache()
    await cache.close()


if __name__ == "__main__":
  asyncio.run(main())
