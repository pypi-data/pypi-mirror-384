"""Configuration management for the LLM library."""

from typing import Optional, Dict, Any, List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr
from enum import Enum

# Get the project root directory (where .env file is located)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class LogLevel(str, Enum):
  """Supported log levels."""

  DEBUG = "DEBUG"
  INFO = "INFO"
  WARNING = "WARNING"
  ERROR = "ERROR"
  CRITICAL = "CRITICAL"


class ProviderType(str, Enum):
  """Supported LLM providers."""

  OPENAI = "openai"
  GEMINI = "gemini"
  ANTHROPIC = "anthropic"
  DEEPSEEK = "deepseek"
  CUSTOM = "custom"


class Settings(BaseSettings):
  """Application configuration settings."""

  model_config = SettingsConfigDict(
    env_file=str(PROJECT_ROOT / ".env"),
    env_file_encoding="utf-8",
    case_sensitive=False,
    extra="ignore",
  )

  # Application settings
  app_name: str = Field(default="LLM Library", description="Application name")
  app_version: str = Field(default="0.1.0", description="Application version")
  debug: bool = Field(default=False, description="Debug mode")
  log_level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")

  # Database settings
  database_url: str = Field(
    default="postgresql+asyncpg://postgres.bpuzkwzxnmkqzskdecky:NSRYX1spvvliJIBJ@aws-1-us-east-2.pooler.supabase.com:5432/postgres",
    description="Database URL",
  )

  # Aliases for backward compatibility
  @property
  def db_url(self) -> str:
    """Alias for database_url."""
    return self.database_url

  # Redis Cache Settings - MUST be set in .env file
  redis_url: str = Field(default="redis://localhost:6379", description="Redis URL for caching")
  redis_ttl: int = Field(default=3600, description="Redis cache TTL in seconds")

  # ANALYTICS CONFIGURATION (ADD THESE):
  analytics_enabled: bool = Field(default=True, alias="ANALYTICS_ENABLED")
  cost_tracking_enabled: bool = Field(default=True, alias="COST_TRACKING_ENABLED")
  performance_tracking_enabled: bool = Field(default=True, alias="PERFORMANCE_TRACKING_ENABLED")

  # ANALYTICS SETTINGS (ADD THESE):
  analytics_batch_size: int = Field(default=100, alias="ANALYTICS_BATCH_SIZE")
  analytics_flush_interval: int = Field(default=30, alias="ANALYTICS_FLUSH_INTERVAL")  # seconds

  # API Keys (will be loaded from environment variables)
  openai_api_key: Optional[SecretStr] = Field(default=None, alias="OPENAI_API_KEY")
  gemini_api_key: Optional[SecretStr] = Field(default=None, alias="GEMINI_API_KEY")
  anthropic_api_key: Optional[SecretStr] = Field(default=None, alias="ANTHROPIC_API_KEY")
  deepseek_api_key: Optional[SecretStr] = Field(default=None, alias="DEEPSEEK_API_KEY")
  exa_api_key: Optional[SecretStr] = Field(default=None, alias="EXA_API_KEY")

  # GCP Cloud Storage settings
  gcp_bucket: Optional[str] = Field(default=None, alias="GCP_BUCKET")
  gcp_creds: Optional[SecretStr] = Field(default=None, alias="GCP_CREDS")

  # Provider configurations
  default_provider: ProviderType = Field(default=ProviderType.OPENAI, description="Default LLM provider")

  # Rate limiting
  rate_limit_enabled: bool = Field(default=True, description="Enable rate limiting")
  rate_limit_requests_per_minute: int = Field(default=60, description="Maximum requests per minute")
  rate_limit_tokens_per_minute: int = Field(default=90000, description="Maximum tokens per minute")

  # Retry configuration
  retry_max_attempts: int = Field(default=3, description="Maximum retry attempts")
  retry_initial_delay: float = Field(default=1.0, description="Initial retry delay in seconds")
  retry_max_delay: float = Field(default=60.0, description="Maximum retry delay in seconds")
  retry_exponential_base: float = Field(default=2.0, description="Exponential backoff base")

  # Session management
  session_store_type: str = Field(default="redis", description="Session store type (memory/redis)")
  session_ttl_seconds: int = Field(default=3600, description="Session TTL in seconds")
  session_max_history: int = Field(default=100, description="Maximum messages in session history")

  # File processing
  max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
  allowed_file_extensions: List[str] = Field(
    default=[
      ".pdf",
      ".docx",
      ".pptx",
      ".xlsx",
      ".csv",
      ".txt",
      ".md",
      ".json",
      ".xml",
      ".png",
      ".jpg",
      ".jpeg",
      ".gif",
      ".bmp",
    ],
    description="Allowed file extensions",
  )
  chunk_size: int = Field(default=1000, description="Default chunk size for documents")
  chunk_overlap: int = Field(default=200, description="Chunk overlap for documents")

  # Model configurations
  openai_default_model: str = Field(default="gpt-4-turbo-preview", description="Default OpenAI model")
  openai_temperature: float = Field(default=0.7, description="OpenAI temperature")
  openai_max_tokens: int = Field(default=4096, description="OpenAI max tokens")

  gemini_default_model: str = Field(default="gemini-2.5-flash", description="Default Gemini model")
  gemini_temperature: float = Field(default=0.7, description="Gemini temperature")
  gemini_max_tokens: Optional[int] = Field(default=None, description="Gemini max tokens (None = no limit)")

  anthropic_default_model: str = Field(default="claude-sonnet-4-5", description="Default Anthropic model")
  anthropic_temperature: float = Field(default=0.7, description="Anthropic temperature")
  anthropic_max_tokens: int = Field(default=4096, description="Anthropic max tokens")

  # API configuration
  api_host: str = Field(default="0.0.0.0", description="API host")
  api_port: int = Field(default=8000, description="API port")
  api_prefix: str = Field(default="/api/v1", description="API prefix")
  cors_enabled: bool = Field(default=True, description="Enable CORS")
  cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")

  # Security
  api_key_header: str = Field(default="X-API-Key", description="API key header name")
  require_api_key: bool = Field(default=False, description="Require API key for requests")
  api_keys: List[str] = Field(default=[], description="Valid API keys")

  # Feature flags
  enable_streaming: bool = Field(default=True, description="Enable streaming responses")
  enable_function_calling: bool = Field(default=True, description="Enable function calling")
  enable_vision: bool = Field(default=True, description="Enable vision capabilities")
  enable_embeddings: bool = Field(default=True, description="Enable embeddings")
  enable_knowledge_base: bool = Field(default=False, description="Enable knowledge base")
  enable_mcp: bool = Field(default=False, description="Enable MCP support")

  def get_provider_config(self, provider: ProviderType) -> Dict[str, Any]:
    """Get configuration for a specific provider."""
    if provider == ProviderType.OPENAI:
      return {
        "api_key": self.openai_api_key.get_secret_value() if self.openai_api_key else None,
        "default_model": self.openai_default_model,
        "temperature": self.openai_temperature,
        "max_tokens": self.openai_max_tokens,
      }
    elif provider == ProviderType.GEMINI:
      return {
        "api_key": self.gemini_api_key.get_secret_value() if self.gemini_api_key else None,
        "default_model": self.gemini_default_model,
        "temperature": self.gemini_temperature,
        "max_tokens": self.gemini_max_tokens,
      }
    elif provider == ProviderType.ANTHROPIC:
      return {
        "api_key": self.anthropic_api_key.get_secret_value() if self.anthropic_api_key else None,
        "default_model": self.anthropic_default_model,
        "temperature": self.anthropic_temperature,
        "max_tokens": self.anthropic_max_tokens,
      }
    elif provider == ProviderType.DEEPSEEK:
      return {"api_key": self.deepseek_api_key.get_secret_value() if self.deepseek_api_key else None, "default_model": "deepseek-chat"}
    else:
      return {}

  def validate_provider(self, provider: ProviderType) -> bool:
    """Check if a provider is properly configured."""
    config = self.get_provider_config(provider)
    return config.get("api_key") is not None


# Global settings instance
settings = Settings()
