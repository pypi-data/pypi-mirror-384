"""Provider management endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException
import structlog

from ...base.types import (
  ProviderInfo,
  ProviderCapabilities,
  ModelInfo,
  ModelCapabilities,
)
from ...providers import provider_factory


logger = structlog.get_logger()
router = APIRouter()


@router.get("/providers", response_model=List[ProviderInfo])
async def list_providers():
  """Get list of all available providers."""
  try:
    providers_data = await provider_factory.get_available_providers()
    return [ProviderInfo(**provider) for provider in providers_data]

  except Exception as e:
    logger.error(f"Failed to list providers: {e}")
    raise HTTPException(status_code=500, detail="Failed to retrieve provider information")


@router.get("/providers/{provider_name}", response_model=ProviderInfo)
async def get_provider_info(provider_name: str):
  """Get detailed information about a specific provider."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)
    return provider.get_info()

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get provider info for {provider_name}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get information for provider '{provider_name}'",
    )


@router.get("/providers/{provider_name}/capabilities", response_model=ProviderCapabilities)
async def get_provider_capabilities(provider_name: str):
  """Get capabilities of a specific provider."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)
    return provider.get_capabilities()

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get capabilities for {provider_name}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get capabilities for provider '{provider_name}'",
    )


@router.post("/providers/{provider_name}/health")
async def check_provider_health(provider_name: str):
  """Check the health of a specific provider."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)

    # Perform health check
    is_healthy = await provider.health_check()

    return {
      "provider": provider_name,
      "healthy": is_healthy,
      "status": "healthy" if is_healthy else "unhealthy",
      "message": "Provider is operational" if is_healthy else "Provider health check failed",
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Health check failed for {provider_name}: {e}")
    return {
      "provider": provider_name,
      "healthy": False,
      "status": "error",
      "message": str(e),
    }


@router.get("/providers/{provider_name}/models")
async def list_provider_models(provider_name: str):
  """Get list of models supported by a provider."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)
    capabilities = provider.get_capabilities()

    return {
      "provider": provider_name,
      "models": capabilities.supported_models,
      "capabilities": {
        "chat": capabilities.chat,
        "streaming": capabilities.streaming,
        "function_calling": capabilities.function_calling,
        "vision": capabilities.vision,
        "audio": capabilities.audio,
        "embeddings": capabilities.embeddings,
        "image_generation": capabilities.image_generation,
      },
      "max_context_length": capabilities.max_context_length,
      "supported_file_types": capabilities.supported_file_types,
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get models for {provider_name}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get models for provider '{provider_name}'",
    )


@router.post("/providers/{provider_name}/validate-model")
async def validate_model(provider_name: str, model: str):
  """Validate if a model is supported by the provider."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)

    # Validate model
    is_valid = await provider.validate_model(model)

    return {
      "provider": provider_name,
      "model": model,
      "valid": is_valid,
      "message": f"Model '{model}' is {'supported' if is_valid else 'not supported'} by {provider_name}",
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Model validation failed for {provider_name}/{model}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to validate model '{model}' for provider '{provider_name}'",
    )


@router.get("/providers/{provider_name}/models", response_model=List[ModelInfo])
async def list_provider_models_detailed(provider_name: str):
  """Get detailed list of models supported by a provider."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)
    models = provider.get_supported_models()

    return models

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get detailed models for {provider_name}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get detailed models for provider '{provider_name}'",
    )


@router.get("/providers/{provider_name}/models/{model_name}", response_model=ModelInfo)
async def get_model_info(provider_name: str, model_name: str):
  """Get detailed information about a specific model."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)

    # Get model information
    try:
      model_info = provider.get_model_info(model_name)
      return model_info
    except ValueError:
      raise HTTPException(
        status_code=404,
        detail=f"Model '{model_name}' not found for provider '{provider_name}'",
      )

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get model info for {provider_name}/{model_name}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get model info for '{model_name}' in provider '{provider_name}'",
    )


@router.get(
  "/providers/{provider_name}/models/{model_name}/capabilities",
  response_model=ModelCapabilities,
)
async def get_model_capabilities(provider_name: str, model_name: str):
  """Get capabilities of a specific model."""
  try:
    # Check if provider is registered
    if not provider_factory.registry.is_registered(provider_name):
      raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    # Get provider instance
    provider = provider_factory.get_provider(provider_name)

    # Get model capabilities
    try:
      capabilities = provider.get_model_capabilities(model_name)
      return capabilities
    except ValueError:
      raise HTTPException(
        status_code=404,
        detail=f"Model '{model_name}' not found for provider '{provider_name}'",
      )

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to get model capabilities for {provider_name}/{model_name}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get capabilities for model '{model_name}' in provider '{provider_name}'",
    )


@router.get("/models")
async def list_all_models():
  """Get list of all models from all providers."""
  try:
    all_models = []
    providers_data = await provider_factory.get_available_providers()

    for provider_data in providers_data:
      if provider_data["is_available"]:
        try:
          provider = provider_factory.get_provider(provider_data["name"])
          models = await provider.get_supported_models()
          all_models.extend(models)
        except Exception as e:
          logger.warning(f"Failed to get models from provider {provider_data['name']}: {e}")
          continue

    return {
      "total_models": len(all_models),
      "models": all_models,
      "providers": len([p for p in providers_data if p["is_available"]]),
    }

  except Exception as e:
    logger.error(f"Failed to list all models: {e}")
    raise HTTPException(status_code=500, detail="Failed to retrieve models from all providers")


@router.get("/models/{model_name}")
async def find_model_across_providers(model_name: str):
  """Find a model across all providers."""
  try:
    found_models = []
    providers_data = await provider_factory.get_available_providers()

    for provider_data in providers_data:
      if provider_data["is_available"]:
        try:
          provider = provider_factory.get_provider(provider_data["name"])
          try:
            model_info = await provider.get_model_info(model_name)
            found_models.append(model_info)
          except ValueError:
            # Model not found in this provider, continue
            continue
        except Exception as e:
          logger.warning(f"Failed to check model in provider {provider_data['name']}: {e}")
          continue

    if not found_models:
      raise HTTPException(
        status_code=404,
        detail=f"Model '{model_name}' not found in any available provider",
      )

    return {
      "model_name": model_name,
      "found_in_providers": len(found_models),
      "models": found_models,
    }

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to find model {model_name}: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to search for model '{model_name}'")
