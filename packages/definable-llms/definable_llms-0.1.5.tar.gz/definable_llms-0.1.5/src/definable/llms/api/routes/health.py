"""Health check endpoints."""

from datetime import datetime
from fastapi import APIRouter
from typing import Dict, Any
import structlog

from ...base.types import HealthCheck, ProviderInfo
from ...config import settings
from ...providers import provider_factory


logger = structlog.get_logger()
router = APIRouter()


@router.get("/health", response_model=HealthCheck)
async def health_check():
  """Get system health status."""

  # Check provider availability
  providers = []
  provider_errors = []

  try:
    available_providers = await provider_factory.get_available_providers()

    for provider_data in available_providers:
      provider_info = ProviderInfo(**provider_data)
      providers.append(provider_info)

      if not provider_info.is_available:
        provider_errors.append(f"{provider_info.name}: {provider_info.error_message}")

  except Exception as e:
    logger.error(f"Failed to check provider availability: {e}")
    provider_errors.append(f"Provider check failed: {e}")

  # Perform various health checks
  checks = {
    "api": True,  # If we got here, the API is working
    "providers": len(providers) > 0,
    "configuration": _check_configuration(),
    "dependencies": _check_dependencies(),
  }

  # Determine overall status
  if all(checks.values()) and not provider_errors:
    status = "healthy"
  elif any(checks.values()):
    status = "degraded"
  else:
    status = "unhealthy"

  return HealthCheck(
    status=status,  # type: ignore
    timestamp=datetime.now(),
    version=settings.app_version,
    providers=providers,
    checks=checks,
    errors=provider_errors,
  )


@router.get("/health/simple")
async def simple_health_check():
  """Simple health check that just returns OK."""
  return {"status": "ok", "timestamp": datetime.now()}


@router.get("/health/detailed")
async def detailed_health_check():
  """Detailed health check with system information."""

  # Get basic health check
  health_data = await health_check()

  # Add additional system information
  system_info = {
    "python_version": _get_python_version(),
    "memory_usage": _get_memory_usage(),
    "disk_usage": _get_disk_usage(),
    "uptime": _get_uptime(),
    "environment": {
      "debug": settings.debug,
      "log_level": settings.log_level.value,
      "rate_limit_enabled": settings.rate_limit_enabled,
      "cors_enabled": settings.cors_enabled,
      "session_store_type": settings.session_store_type,
    },
  }

  return {**health_data.model_dump(), "system_info": system_info}


def _check_configuration() -> bool:
  """Check if basic configuration is valid."""
  try:
    # Check that at least one provider is configured
    if settings.openai_api_key or settings.gemini_api_key or settings.anthropic_api_key:
      return True

    logger.warning("No LLM provider API keys configured")
    return False

  except Exception as e:
    logger.error(f"Configuration check failed: {e}")
    return False


def _check_dependencies() -> bool:
  """Check if required dependencies are available."""
  required_modules = [
    "fastapi",
    "pydantic",
    "structlog",
    "tenacity",
  ]

  for module in required_modules:
    try:
      __import__(module)
    except ImportError:
      logger.error(f"Required module not available: {module}")
      return False

  return True


def _get_python_version() -> str:
  """Get Python version information."""
  import sys

  return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def _get_memory_usage() -> Dict[str, Any]:
  """Get memory usage information."""
  try:
    import psutil
    import os

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    return {
      "rss": memory_info.rss,  # Resident Set Size
      "vms": memory_info.vms,  # Virtual Memory Size
      "percent": process.memory_percent(),
    }
  except ImportError:
    return {"error": "psutil not available"}
  except Exception as e:
    return {"error": str(e)}


def _get_disk_usage() -> Dict[str, Any]:
  """Get disk usage information."""
  try:
    import psutil

    disk_usage = psutil.disk_usage("/")

    return {
      "total": disk_usage.total,
      "used": disk_usage.used,
      "free": disk_usage.free,
      "percent": (disk_usage.used / disk_usage.total) * 100,
    }
  except ImportError:
    return {"error": "psutil not available"}
  except Exception as e:
    return {"error": str(e)}


def _get_uptime() -> Dict[str, Any]:
  """Get application uptime."""
  try:
    import psutil
    import os
    import time

    process = psutil.Process(os.getpid())
    create_time = process.create_time()
    uptime_seconds = time.time() - create_time

    return {
      "seconds": uptime_seconds,
      "started_at": datetime.fromtimestamp(create_time).isoformat(),
    }
  except ImportError:
    return {"error": "psutil not available"}
  except Exception as e:
    return {"error": str(e)}
