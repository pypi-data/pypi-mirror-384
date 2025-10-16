"""Scalable multi-provider LLM library for definable.ai."""

from typing import Optional
from pydantic import SecretStr
from .config import settings, Settings
from .base import *  # noqa: F403
from .providers import provider_factory, OpenAIProvider, AnthropicProvider

try:
  from .providers import GeminiProvider
except ImportError:
  GeminiProvider = None
from .sessions import session_manager, SessionManager
from .sessions.store import RedisSessionStore
from .processors import file_processor
from .utils import *  # noqa: F403

__version__ = "0.1.3"
__author__ = "definable.ai"
__description__ = "Scalable multi-provider LLM library"


def initialize(
  database_url: str,
  redis_url: str,
  openai_api_key: Optional[str] = None,
  anthropic_api_key: Optional[str] = None,
  deepseek_api_key: Optional[str] = None,
  gemini_api_key: Optional[str] = None,
  exa_api_key: Optional[str] = None,
  gcp_bucket: Optional[str] = None,
  gcp_creds: Optional[str] = None,
  session_ttl_seconds: int = 3600,
  session_max_history: int = 100,
  debug: bool = False,
  **kwargs,
) -> SessionManager:
  """Initialize llms.lib with backend configuration.

  Call this once at backend startup to configure the package.

  Args:
      database_url: PostgreSQL database URL (your backend's database)
      redis_url: Redis connection URL
      openai_api_key: OpenAI API key
      anthropic_api_key: Anthropic API key
      deepseek_api_key: DeepSeek API key
      gemini_api_key: Google Gemini API key
      exa_api_key: Exa search API key
      gcp_bucket: GCP Cloud Storage bucket name (optional, for image/video uploads)
      gcp_creds: GCP service account credentials as base64-encoded JSON (optional)
      session_ttl_seconds: Session TTL in seconds
      session_max_history: Max messages in session history
      debug: Enable debug mode
      **kwargs: Additional settings

  Returns:
      Configured SessionManager instance
  """
  global settings, session_manager

  # Update global settings
  settings.database_url = database_url  # Store backend's database URL
  settings.redis_url = redis_url
  settings.session_store_type = "redis"  # Ensure Redis is used
  settings.session_ttl_seconds = session_ttl_seconds
  settings.session_max_history = session_max_history
  settings.debug = debug

  # Set API keys (wrap in SecretStr)
  if openai_api_key:
    settings.openai_api_key = SecretStr(openai_api_key)
  if anthropic_api_key:
    settings.anthropic_api_key = SecretStr(anthropic_api_key)
  if deepseek_api_key:
    settings.deepseek_api_key = SecretStr(deepseek_api_key)
  if gemini_api_key:
    settings.gemini_api_key = SecretStr(gemini_api_key)
  if exa_api_key:
    settings.exa_api_key = SecretStr(exa_api_key)

  # Set GCP Cloud Storage settings
  if gcp_bucket:
    settings.gcp_bucket = gcp_bucket
  if gcp_creds:
    settings.gcp_creds = SecretStr(gcp_creds)

  # Apply any additional settings
  for key, value in kwargs.items():
    if hasattr(settings, key):
      setattr(settings, key, value)

  # Create Redis-backed session store
  store = RedisSessionStore(
    redis_url=redis_url,
    default_ttl_seconds=session_ttl_seconds,
  )

  # Update the global session_manager instance IN PLACE
  # Instead of reassigning, update its store and config
  session_manager.store = store
  session_manager.config = settings

  return session_manager


__all__ = [
  # Initialization
  "initialize",
  # Configuration
  "settings",
  "Settings",
  # Providers
  "provider_factory",
  "OpenAIProvider",
  "AnthropicProvider",
  # Session management
  "session_manager",
  "SessionManager",
  # File processing
  "file_processor",
  # Base types and exceptions are exported via star import
  # Utilities are exported via star import
]
