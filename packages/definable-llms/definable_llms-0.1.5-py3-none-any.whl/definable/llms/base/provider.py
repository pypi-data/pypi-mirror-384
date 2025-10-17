"""Abstract base provider class for all LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional, List, Union, AsyncGenerator
import asyncio
import time
import logging
from contextlib import asynccontextmanager
import structlog
from tenacity import (
  retry,
  stop_after_attempt,
  wait_exponential,
  retry_if_exception_type,
  before_sleep_log,
)

from ..config import Settings
from .types import (
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ImageRequest,
  ImageResponse,
  EmbeddingRequest,
  EmbeddingResponse,
  ProviderCapabilities,
  ProviderInfo,
  ModelCapabilities,
  ModelInfo,
  Message,
)
from .exceptions import (
  RetryableError,
  NetworkError,
)


logger = structlog.get_logger()


class BaseProvider(ABC):
  """Abstract base class for all LLM providers."""

  def __init__(
    self,
    name: str,
    api_key: Optional[str] = None,
    config: Optional[Settings] = None,
    **kwargs,
  ):
    """Initialize the provider.

    Args:
        name: Provider name
        api_key: API key for authentication
        config: Configuration settings
        **kwargs: Additional provider-specific parameters
    """
    self.name = name
    self.api_key = api_key
    self.config = config or Settings()
    self.logger = logger.bind(provider=name)

    # Rate limiting state
    self._rate_limiter = None
    self._request_count = 0
    self._token_count = 0
    self._last_reset_time = time.time()

    # Cleanup state
    self._closed = False

    # Initialize provider-specific settings
    self._initialize(**kwargs)

  @abstractmethod
  def _initialize(self, **kwargs):
    """Initialize provider-specific settings."""
    pass

  @abstractmethod
  def get_capabilities(self) -> ProviderCapabilities:
    """Get provider capabilities (aggregated from all models).

    Note: This method is deprecated. Use get_model_capabilities() for specific models.
    """
    pass

  @abstractmethod
  async def get_model_capabilities(self, model: str) -> ModelCapabilities:
    """Get capabilities for a specific model.

    Args:
        model: Model name

    Returns:
        Model capabilities

    Raises:
        ValueError: If model is not supported
    """
    pass

  @abstractmethod
  async def get_supported_models(self) -> List[ModelInfo]:
    """Get list of all supported models with their information.

    Returns:
        List of model information
    """
    pass

  async def get_model_info(self, model: str) -> ModelInfo:
    """Get information for a specific model.

    Args:
        model: Model name

    Returns:
        Model information

    Raises:
        ValueError: If model is not supported
    """
    models = await self.get_supported_models()
    for model_info in models:
      if model_info.name == model:
        return model_info
    raise ValueError(f"Model '{model}' is not supported by provider '{self.name}'")

  @abstractmethod
  async def chat(self, request: ChatRequest, **kwargs) -> Union[ChatResponse, AsyncGenerator[StreamChunk, None]]:
    """Send a chat completion request.

    Args:
        request: Chat request
        **kwargs: Additional provider-specific parameters

    Returns:
        Chat response or stream of chunks
    """
    pass

  @abstractmethod
  async def generate_image(self, request: ImageRequest, **kwargs) -> Union[ImageResponse, AsyncGenerator]:
    """Generate images.

    Args:
        request: Image generation request
        **kwargs: Additional provider-specific parameters

    Returns:
        Image response or async generator for streaming (gpt-image-1 only)
    """
    pass

  @abstractmethod
  async def generate_embedding(self, request: EmbeddingRequest, **kwargs) -> EmbeddingResponse:
    """Generate text embeddings.

    Args:
        request: Embedding request
        **kwargs: Additional provider-specific parameters

    Returns:
        Embedding response
    """
    pass

  @abstractmethod
  async def validate_model(self, model: str) -> bool:
    """Validate if a model is supported.

    Args:
        model: Model name

    Returns:
        True if model is supported
    """
    pass

  async def get_info(self) -> ProviderInfo:
    """Get provider information.

    Returns:
        Provider information including capabilities and models
    """
    try:
      capabilities = self.get_capabilities()
      models = await self.get_supported_models()
      is_available = self.api_key is not None
      error_message = None if is_available else f"API key not configured for {self.name}"

      return ProviderInfo(
        name=self.name,
        type=self.__class__.__name__,
        version="1.0.0",
        capabilities=capabilities,
        models=models,
        is_available=is_available,
        error_message=error_message,
      )
    except Exception as e:
      self.logger.error(f"Failed to get provider info: {e}")
      return ProviderInfo(
        name=self.name,
        type=self.__class__.__name__,
        version="1.0.0",
        capabilities=ProviderCapabilities(),
        models=[],
        is_available=False,
        error_message=str(e),
      )

  async def _check_rate_limit(self, estimated_tokens: int = 0):
    """Check and enforce rate limits.

    Args:
        estimated_tokens: Estimated tokens for the request
    """
    if not self.config.rate_limit_enabled:
      return

    current_time = time.time()
    time_since_reset = current_time - self._last_reset_time

    # Reset counters if a minute has passed
    if time_since_reset >= 60:
      self._request_count = 0
      self._token_count = 0
      self._last_reset_time = current_time

    # Check request limit
    if self._request_count >= self.config.rate_limit_requests_per_minute:
      wait_time = 60 - time_since_reset
      self.logger.warning(f"Rate limit reached for requests. Waiting {wait_time:.2f} seconds")
      await asyncio.sleep(wait_time)
      self._request_count = 0
      self._token_count = 0
      self._last_reset_time = time.time()

    # Check token limit
    if estimated_tokens > 0:
      if self._token_count + estimated_tokens > self.config.rate_limit_tokens_per_minute:
        wait_time = 60 - time_since_reset
        self.logger.warning(f"Rate limit reached for tokens. Waiting {wait_time:.2f} seconds")
        await asyncio.sleep(wait_time)
        self._request_count = 0
        self._token_count = 0
        self._last_reset_time = time.time()

    # Update counters
    self._request_count += 1
    self._token_count += estimated_tokens

  def _get_retry_decorator(self):
    """Get retry decorator with provider-specific configuration."""
    return retry(
      stop=stop_after_attempt(self.config.retry_max_attempts),
      wait=wait_exponential(
        multiplier=self.config.retry_initial_delay,
        max=self.config.retry_max_delay,
        exp_base=self.config.retry_exponential_base,
      ),
      retry=retry_if_exception_type((RetryableError, NetworkError)),
      before_sleep=before_sleep_log(self.logger, logging.WARNING),
    )

  async def _make_request_with_retry(self, request_func, *args, **kwargs):
    """Make a request with retry logic.

    Args:
        request_func: Async function to call
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Response from the request
    """
    retry_decorator = self._get_retry_decorator()
    wrapped_func = retry_decorator(request_func)
    return await wrapped_func(*args, **kwargs)

  @asynccontextmanager
  async def _timed_request(self, operation: str, timeout: Optional[float] = None):
    """Context manager for timed requests with logging.

    Args:
        operation: Name of the operation
        timeout: Optional timeout in seconds
    """
    start_time = time.time()
    self.logger.info(f"Starting {operation}")

    try:
      if timeout:
        # For timeout handling, we'll rely on the underlying HTTP client's timeout
        # rather than using asyncio.timeout which may not be available in older Python versions
        pass
      yield
    except Exception as e:
      elapsed = time.time() - start_time
      self.logger.error(f"{operation} failed after {elapsed:.2f} seconds: {e}")
      raise
    else:
      elapsed = time.time() - start_time
      self.logger.info(f"Completed {operation} in {elapsed:.2f} seconds")

  def _estimate_tokens(self, messages: List[Message]) -> int:
    """Estimate token count for messages.

    Args:
        messages: List of messages

    Returns:
        Estimated token count
    """
    # Simple estimation: ~4 characters per token
    total_chars = 0
    for message in messages:
      if isinstance(message.content, str):
        total_chars += len(message.content)
      elif isinstance(message.content, list):
        for content in message.content:
          if content.text:
            total_chars += len(content.text)

    return total_chars // 4

  def _validate_request(self, request: Union[ChatRequest, ImageRequest, EmbeddingRequest]):
    """Validate a request before processing.

    Args:
        request: Request to validate

    Raises:
        InvalidRequestError: If request is invalid
    """
    # Override in subclasses for provider-specific validation
    pass

  async def health_check(self) -> bool:
    """Check if the provider is healthy and accessible.

    Returns:
        True if provider is healthy
    """
    try:
      # Base health check - just verify API key exists
      # Subclasses should implement actual connectivity checks
      return self.api_key is not None
    except Exception as e:
      self.logger.error(f"Health check failed: {e}")
      return False

  @abstractmethod
  async def close(self):
    """Close the provider and cleanup resources.

    Subclasses should override this to cleanup HTTP clients and other resources.
    """
    pass

  async def __aenter__(self):
    """Async context manager entry."""
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit."""
    await self.close()
    return False

  def __repr__(self) -> str:
    """String representation of the provider."""
    return f"{self.__class__.__name__}(name='{self.name}')"
