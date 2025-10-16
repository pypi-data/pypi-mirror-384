"""DeepSeek provider implementation."""

from typing import Optional, Dict, Any, AsyncGenerator
from openai import AsyncOpenAI
import structlog
import time

from definable.llms.config import settings

from ...base import BaseProvider, ProviderCapabilities
from ...base.types import (
  ChatRequest,
  ChatResponse,
  StreamChunk,
  Message,
  MessageRole,
  Choice,
  Usage,
  FinishReason,
  ModelCapabilities,
  ModelInfo,
)
from ...base.exceptions import (
  ProviderAuthenticationError,
  ProviderRateLimitError,
  ProviderQuotaExceededError,
  ProviderTimeoutError,
  ModelNotFoundError,
  InvalidRequestError,
)
from ...database.backend_model_loader import BackendModelLoader

logger = structlog.get_logger()


class DeepSeekProvider(BaseProvider):
  """DeepSeek provider implementation with Chat and Reasoner models."""

  def __init__(self, api_key: Optional[str] = None, **kwargs):
    """Initialize DeepSeek provider.

    Args:
        api_key: DeepSeek API key
        **kwargs: Additional configuration
    """
    super().__init__("deepseek", api_key, **kwargs)

  def _initialize(self, **kwargs):
    """Initialize DeepSeek-specific settings."""
    if not self.api_key:
      raise ProviderAuthenticationError("deepseek", "DeepSeek API key is required")

    # Initialize async client with OpenAI-compatible endpoint
    self.client = AsyncOpenAI(
      api_key=self.api_key,
      base_url="https://api.deepseek.com",
      timeout=None,
      max_retries=0,
    )

    self.default_model = kwargs.get("default_model", "deepseek-chat")
    self.default_temperature = kwargs.get("temperature", 0.1)

  def get_capabilities(self) -> ProviderCapabilities:
    """Get DeepSeek provider capabilities."""
    return ProviderCapabilities(
      chat=True,
      streaming=True,
      embeddings=False,
      image_generation=False,
      vision=False,
      function_calling=True,
    )

  async def get_model_capabilities(self, model: str) -> ModelCapabilities:
    """Get model-specific capabilities from backend database."""
    loader = BackendModelLoader(settings.database_url)
    try:
      capabilities = await loader.get_model_capabilities("deepseek", model)
      if capabilities is None:
        raise ValueError(f"Model '{model}' is not supported by DeepSeek provider")
      return capabilities
    finally:
      await loader.close()

  async def get_model_info(self, model: str) -> ModelInfo:
    """Get model information."""
    capabilities = await self.get_model_capabilities(model)
    return ModelInfo(
      name=model,
      capabilities=capabilities,
      provider="deepseek",
      model_type="chat",
    )

  async def chat(
    self,
    request: ChatRequest,
    **kwargs: Any,
  ) -> ChatResponse | AsyncGenerator[StreamChunk, None]:
    """Send chat completion request to DeepSeek.

    Args:
        request: Chat completion request
        timeout: Request timeout (None = no timeout)

    Returns:
        ChatResponse for non-streaming, AsyncGenerator for streaming
    """
    try:
      # Validate model exists
      if request.model:
        await self.get_model_info(request.model)

      # Prepare messages
      messages = []
      for msg in request.messages:
        message_dict = {"role": msg.role.value, "content": msg.content}
        messages.append(message_dict)

      # Prepare API parameters
      params = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "stream": request.stream,
      }

      # Add max_tokens if provided
      if request.max_tokens:
        params["max_tokens"] = request.max_tokens

      # Add top_p if provided
      if request.top_p:
        params["top_p"] = request.top_p

      # Add frequency_penalty if provided
      if request.frequency_penalty:
        params["frequency_penalty"] = request.frequency_penalty

      # Add presence_penalty if provided
      if request.presence_penalty:
        params["presence_penalty"] = request.presence_penalty

      logger.info(
        "Starting chat_completion",
        model=request.model,
        provider="deepseek",
        stream=request.stream,
      )

      if request.stream:
        return self._stream_chat(params, kwargs.get("timeout"))
      else:
        return await self._complete_chat(params, kwargs.get("timeout"))

    except Exception as e:
      logger.error(f"DeepSeek chat failed: {e}", model=request.model or "unknown")
      self._handle_error(e, request.model or "unknown")
      raise

  async def _complete_chat(self, params: Dict[str, Any], timeout: Optional[float]) -> ChatResponse:
    """Execute non-streaming chat completion."""
    response = await self.client.chat.completions.create(**params)

    # Convert to our ChatResponse format
    choices = []
    for choice in response.choices:
      choices.append(
        Choice(
          index=choice.index,
          message=Message(
            role=MessageRole(choice.message.role),
            content=choice.message.content or "",
          ),
          finish_reason=self._map_finish_reason(choice.finish_reason),
        )
      )

    usage = None
    if response.usage:
      usage = Usage(
        input_tokens=response.usage.prompt_tokens,
        output_tokens=response.usage.completion_tokens,
        total_tokens=response.usage.total_tokens,
      )

    return ChatResponse(
      id=response.id,
      model=response.model,
      choices=choices,
      usage=usage,
      created=response.created,
    )

  async def _stream_chat(self, params: Dict[str, Any], timeout: Optional[float]) -> AsyncGenerator[StreamChunk, None]:
    """Execute streaming chat completion."""
    stream = await self.client.chat.completions.create(**params)

    async for chunk in stream:
      # Check if this chunk contains usage information
      if hasattr(chunk, "usage") and chunk.usage:
        try:
          usage = Usage(
            input_tokens=getattr(chunk.usage, "prompt_tokens", 0),
            output_tokens=getattr(chunk.usage, "completion_tokens", 0),
            total_tokens=getattr(chunk.usage, "total_tokens", 0),
            cached_tokens=None,  # DeepSeek may not support cached tokens
          )
          yield StreamChunk(
            id="usage",
            created=0,
            model="",
            choices=[],
            usage=usage,
          )
        except Exception as e:
          logger.warning(f"Failed to process streaming usage data: {e}")
        continue

      if not chunk.choices:
        continue

      choice = chunk.choices[0]
      delta_content = choice.delta.content or ""

      yield StreamChunk(
        id=chunk.id,
        model=chunk.model,
        created=int(time.time()),
        choices=[
          {
            "index": choice.index,
            "delta": {"type": "content", "content": delta_content},
            "finish_reason": self._map_finish_reason(choice.finish_reason) if choice.finish_reason else None,
          }
        ],
      )

  def _map_finish_reason(self, reason: Optional[str]) -> Optional[FinishReason]:
    """Map DeepSeek finish reasons to our enum."""
    if not reason:
      return None

    mapping = {
      "stop": FinishReason.STOP,
      "length": FinishReason.LENGTH,
      "content_filter": FinishReason.CONTENT_FILTER,
      "tool_calls": FinishReason.TOOL_CALLS,
      "function_call": FinishReason.TOOL_CALLS,
    }
    return mapping.get(reason, FinishReason.STOP)

  def _handle_error(self, error: Exception, model: str):
    """Handle and map DeepSeek errors to our exceptions."""
    error_str = str(error).lower()

    if "authentication" in error_str or "api key" in error_str or "401" in error_str:
      raise ProviderAuthenticationError("deepseek", str(error))
    if "rate limit" in error_str or "429" in error_str:
      raise ProviderRateLimitError("deepseek", message=str(error))
    if "quota" in error_str or "insufficient" in error_str:
      raise ProviderQuotaExceededError("deepseek", str(error))
    if "timeout" in error_str:
      raise ProviderTimeoutError("deepseek", timeout=None)
    if "model" in error_str and "not found" in error_str:
      raise ModelNotFoundError("deepseek", model)
    if "invalid" in error_str:
      raise InvalidRequestError("deepseek", str(error))
    # Re-raise the original error if we can't map it
    raise

  async def get_supported_models(self) -> list[ModelInfo]:
    """Get list of supported models from Redis cache."""
    loader = BackendModelLoader(settings.database_url)
    try:
      return await loader.get_supported_models_info("deepseek")
    finally:
      await loader.close()

  async def validate_model(self, model: str) -> bool:
    """Validate if a model is supported."""
    try:
      await self.get_model_info(model)
      return True
    except Exception:
      return False

  async def generate_embedding(self, *args, **kwargs):
    """DeepSeek doesn't support embeddings."""
    raise NotImplementedError("DeepSeek does not support embeddings")

  async def generate_image(self, *args, **kwargs):
    """DeepSeek doesn't support image generation."""
    raise NotImplementedError("DeepSeek does not support image generation")

  async def close(self):
    """Close the provider client."""
    if hasattr(self, "client"):
      await self.client.close()
