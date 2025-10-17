"""Anthropic provider implementation."""

import structlog
from typing import Optional, Dict, Any, List, Union, AsyncGenerator

from ...base import BaseProvider, ProviderCapabilities
from ...base.types import (
  ChatRequest,
  ChatResponse,
  StreamChunk,
  EmbeddingRequest,
  EmbeddingResponse,
  Message,
  MessageRole,
  Choice,
  Usage,
  FinishReason,
  ContentType,
  ModelCapabilities,
  ModelInfo,
  ImageRequest,
  ImageResponse,
)
from ...base.exceptions import (
  ProviderAuthenticationError,
  ProviderRateLimitError,
  ProviderQuotaExceededError,
  ProviderTimeoutError,
  ModelNotFoundError,
  InvalidRequestError,
  ContentFilterError,
  TokenLimitError,
)
from ...config import settings
from ...database.backend_model_loader import BackendModelLoader

try:
  from anthropic import AsyncAnthropic
except ImportError:
  raise ImportError("`anthropic` not installed. Please install it using `pip install anthropic`")


logger = structlog.get_logger()


class AnthropicProvider(BaseProvider):
  """Anthropic provider implementation with model management."""

  def __init__(self, api_key: Optional[str] = None, **kwargs):
    """Initialize Anthropic provider.

    Args:
        api_key: Anthropic API key
        **kwargs: Additional configuration
    """
    super().__init__("anthropic", api_key, **kwargs)

  def _initialize(self, **kwargs):
    """Initialize Anthropic-specific settings."""
    if not self.api_key:
      raise ProviderAuthenticationError("anthropic", "Anthropic API key is required")

    # Initialize async client
    self.client = AsyncAnthropic(
      api_key=self.api_key,
      timeout=kwargs.get("timeout", 60.0),
      max_retries=0,  # We handle retries ourselves
    )

    # Model configurations
    self.default_model = kwargs.get("default_model", settings.anthropic_default_model)
    self.default_temperature = kwargs.get("temperature", settings.anthropic_temperature)
    self.default_max_tokens = kwargs.get("max_tokens", settings.anthropic_max_tokens)

  def get_capabilities(self) -> ProviderCapabilities:
    """Get Anthropic provider capabilities.

    Note: This method is deprecated. Use get_model_capabilities() for specific models.
    """
    return ProviderCapabilities(
      chat=True,
      streaming=True,
      function_calling=True,
      vision=True,
      audio=False,
      embeddings=False,  # Anthropic doesn't provide embeddings
      image_generation=False,  # Anthropic doesn't provide image generation
      max_context_length=200000,  # Maximum across all models
      supported_models=[],  # Use get_supported_models() for list from database
      supported_file_types=[".png", ".jpg", ".jpeg", ".gif", ".webp"],
    )

  async def get_model_capabilities(self, model: str) -> ModelCapabilities:
    """Get capabilities for a specific model from cache or database.

    Args:
        model: Model name

    Returns:
        Model capabilities

    Raises:
        ValueError: If model is not supported
    """
    loader = BackendModelLoader(settings.database_url)
    try:
      capabilities = await loader.get_model_capabilities("anthropic", model)
      if capabilities is None:
        raise ValueError(f"Model '{model}' is not supported by Anthropic provider")
      return capabilities
    finally:
      await loader.close()

  async def get_supported_models(self) -> List[ModelInfo]:
    """Get list of all supported models from cache or database.

    Returns:
        List of model information
    """
    loader = BackendModelLoader(settings.database_url)
    try:
      return await loader.get_supported_models_info("anthropic")
    finally:
      await loader.close()

  async def validate_model(self, model: str) -> bool:
    """Validate that a model is supported using cache.

    Args:
        model: Model name to validate

    Returns:
        True if model is supported, False otherwise
    """
    loader = BackendModelLoader(settings.database_url)
    try:
      return await loader.validate_model("anthropic", model)
    finally:
      await loader.close()

  def _convert_message_to_anthropic(self, message: Message) -> Dict[str, Any]:
    """Convert internal message format to Anthropic format.

    Args:
        message: Internal message format

    Returns:
        Anthropic-compatible message dictionary
    """
    anthropic_message = {
      "role": "user" if message.role == MessageRole.USER else "assistant",
    }

    if isinstance(message.content, str):
      anthropic_message["content"] = message.content
    elif isinstance(message.content, list):
      content_parts = []

      for content in message.content:
        if content.type == ContentType.TEXT:
          content_parts.append({"type": "text", "text": content.text})
        elif content.type == ContentType.IMAGE:
          if content.image_base64:
            # Extract base64 data and media type
            image_data = content.image_base64
            media_type = "image/jpeg"

            if image_data.startswith("data:"):
              # Parse data URL
              parts = image_data.split(",", 1)
              if len(parts) == 2:
                header = parts[0]
                image_data = parts[1]
                if "image/" in header:
                  media_type = header.split(";")[0].replace("data:", "")

            content_parts.append({
              "type": "image",
              "source": {  # type: ignore[dict-item]
                "type": "base64",
                "media_type": media_type,
                "data": image_data,
              },
            })
          elif content.image_url:
            # Anthropic doesn't support image URLs directly
            # We'd need to download and convert to base64
            self.logger.warning("Image URLs not directly supported by Anthropic, skipping")

      anthropic_message["content"] = content_parts  # type: ignore

    # Handle tool calls
    if message.tool_calls:
      anthropic_message["content"] = []  # type: ignore
      for tool_call in message.tool_calls:
        anthropic_message["content"].append({  # type: ignore
          "type": "tool_use",
          "id": tool_call.id,
          "name": tool_call.function.name,
          "input": tool_call.function.arguments,
        })

    return anthropic_message

  def _convert_anthropic_message(self, anthropic_message: Dict[str, Any]) -> Message:
    """Convert Anthropic message format to internal format.

    Args:
        anthropic_message: Anthropic message dictionary

    Returns:
        Internal message format
    """
    if not anthropic_message:
      raise ValueError("Anthropic message cannot be None or empty")

    if "role" not in anthropic_message:
      raise ValueError("Anthropic message missing required 'role' field")

    role = MessageRole.ASSISTANT if anthropic_message["role"] == "assistant" else MessageRole.USER

    content = ""
    tool_calls = []

    if isinstance(anthropic_message.get("content"), str):
      content = anthropic_message["content"]
    elif isinstance(anthropic_message.get("content"), list):
      text_parts = []
      for item in anthropic_message["content"]:
        if item.get("type") == "text":
          text_parts.append(item.get("text", ""))
        elif item.get("type") == "tool_use":
          from ...base.types import ToolCall, FunctionCall

          tool_calls.append(
            ToolCall(
              id=item.get("id", ""),
              type="function",
              function=FunctionCall(
                name=item.get("name", ""),
                arguments=item.get("input", ""),
              ),
            )
          )
      content = " ".join(text_parts)

    message = Message(
      role=role,
      content=content,
    )

    if tool_calls:
      message.tool_calls = tool_calls

    return message

  def _handle_anthropic_error(self, error: Exception) -> Exception:
    """Convert Anthropic errors to our internal error types.

    Args:
        error: Original Anthropic error

    Returns:
        Converted exception
    """
    error_str = str(error)

    if "authentication" in error_str.lower() or "api key" in error_str.lower():
      return ProviderAuthenticationError("anthropic", error_str)
    elif "rate limit" in error_str.lower():
      return ProviderRateLimitError("anthropic", message=error_str)
    elif "quota" in error_str.lower() or "billing" in error_str.lower():
      return ProviderQuotaExceededError("anthropic", error_str)
    elif "timeout" in error_str.lower():
      return ProviderTimeoutError("anthropic")
    elif "model" in error_str.lower() and "not found" in error_str.lower():
      return ModelNotFoundError("anthropic", "unknown")
    elif "content policy" in error_str.lower() or "safety" in error_str.lower():
      return ContentFilterError(error_str)
    elif "token" in error_str.lower() and "limit" in error_str.lower():
      return TokenLimitError(error_str, 0, 0)
    else:
      return InvalidRequestError(f"Anthropic API error: {error_str}")

  def _extract_system_message(self, messages: List[Message]) -> tuple[Optional[str], List[Message]]:
    """Extract system message from messages list.

    Anthropic requires system messages to be passed separately.

    Args:
        messages: List of messages

    Returns:
        Tuple of (system_message, remaining_messages)
    """
    system_message = None
    remaining_messages = []

    for msg in messages:
      if msg.role == MessageRole.SYSTEM:
        if isinstance(msg.content, str):
          system_message = msg.content
        else:
          # Handle complex content
          text_parts = [c.text for c in msg.content if c.type == ContentType.TEXT and c.text]
          system_message = " ".join(text_parts) if text_parts else ""
      else:
        remaining_messages.append(msg)

    return system_message, remaining_messages

  async def chat(self, request: ChatRequest, **kwargs) -> Union[ChatResponse, AsyncGenerator[StreamChunk, None]]:
    """Send a chat completion request to Anthropic.

    Args:
        request: Chat completion request
        **kwargs: Additional Anthropic-specific parameters

    Returns:
        Chat response or async generator for streaming
    """
    # Validate request
    self._validate_request(request)

    # Estimate tokens for rate limiting
    estimated_tokens = self._estimate_tokens(request.messages)
    await self._check_rate_limit(estimated_tokens)

    # Extract system message
    system_message, messages = self._extract_system_message(request.messages)

    # Prepare Anthropic request
    anthropic_request = {
      "model": request.model or self.default_model,
      "messages": [self._convert_message_to_anthropic(msg) for msg in messages],
      "max_tokens": request.max_tokens or self.default_max_tokens,
      "stream": request.stream,
    }

    # Add system message if present
    # Priority: kwargs["system"] (for advanced features like cache_control) > extracted system_message
    if "system" in kwargs:
      # Use the system parameter from kwargs directly (supports cache_control and other Anthropic features)
      anthropic_request["system"] = kwargs.pop("system")
    elif system_message:
      anthropic_request["system"] = system_message

    # Add temperature (Anthropic supports 0-1)
    if request.temperature is not None:
      anthropic_request["temperature"] = request.temperature
    elif self.default_temperature is not None:
      anthropic_request["temperature"] = self.default_temperature

    # Add optional parameters
    if request.top_p is not None:
      anthropic_request["top_p"] = request.top_p
    if request.stop:
      anthropic_request["stop_sequences"] = request.stop if isinstance(request.stop, list) else [request.stop]

    # Handle Extended Thinking
    if request.reasoning:
      # Determine budget_tokens
      budget_tokens = request.reasoning_budget_tokens
      if budget_tokens is None or budget_tokens == 0:
        # Default to 10,000 tokens as recommended by Anthropic
        budget_tokens = 10000

      # Validate budget_tokens is less than max_tokens
      max_tokens = request.max_tokens or self.default_max_tokens
      if budget_tokens >= max_tokens:
        budget_tokens = max(1024, max_tokens // 2)  # Use half or minimum

      # remove temperature
      anthropic_request.pop("temperature", None)

      anthropic_request["thinking"] = {
        "type": "enabled",
        "budget_tokens": budget_tokens,
      }

      self.logger.debug(f"Extended thinking enabled with budget_tokens={budget_tokens}")

    # Handle tools (Anthropic's function calling)
    if request.tools:
      anthropic_request["tools"] = [
        {
          "name": tool.get("name", ""),
          "description": tool.get("description", ""),
          "input_schema": tool.get("input_schema", {}),
        }
        for tool in request.tools
      ]

    if request.tool_choice:
      if request.tool_choice == "auto":
        anthropic_request["tool_choice"] = {"type": "auto"}
      elif request.tool_choice == "none":
        anthropic_request["tool_choice"] = {"type": "any"}
      elif isinstance(request.tool_choice, dict):
        anthropic_request["tool_choice"] = {
          "type": "tool",
          "name": request.tool_choice.get("name", ""),
        }

    # Add metadata
    if request.user:
      anthropic_request["metadata"] = {"user_id": request.user}

    # Add any additional Anthropic-specific parameters
    anthropic_request.update(kwargs)

    try:
      async with self._timed_request(
        f"chat_completion:{anthropic_request['model']}",
        timeout=kwargs.get("timeout", 60.0),
      ):
        response = await self.client.messages.create(**anthropic_request)  # type: ignore[arg-type]

        if request.stream:
          return self._handle_streaming_response(response)
        else:
          return self._handle_chat_response(response)

    except Exception as e:
      self.logger.error(f"Anthropic chat completion failed: {e}")
      raise self._handle_anthropic_error(e)

  def _handle_chat_response(self, response) -> ChatResponse:
    """Convert Anthropic response to internal format.

    Args:
        response: Anthropic response object

    Returns:
        Internal chat response
    """
    if not response:
      raise ValueError("Anthropic response cannot be None")

    # Extract content
    content_text = ""
    reasoning_text = ""
    tool_calls = []

    if hasattr(response, "content") and response.content:
      for block in response.content:
        if hasattr(block, "type"):
          if block.type == "text":
            content_text += block.text
          elif block.type == "thinking":
            # Extended thinking block (Claude 3.7 full, Claude 4.x summarized)
            if hasattr(block, "thinking"):
              reasoning_text += block.thinking
            self.logger.debug(f"Received thinking block (length: {len(reasoning_text)} chars)")
          elif block.type == "redacted_thinking":
            # Safety-filtered thinking block - still billable, still usable
            reasoning_text += "[Redacted reasoning for safety]"
            self.logger.debug("Received redacted thinking block")
          elif block.type == "tool_use":
            from ...base.types import ToolCall, FunctionCall

            tool_calls.append(
              ToolCall(
                id=block.id,
                type="function",
                function=FunctionCall(
                  name=block.name,
                  arguments=str(block.input),
                ),
              )
            )

    # Create message
    message = Message(
      role=MessageRole.ASSISTANT,
      content=content_text,
      reasoning_content=reasoning_text or None,
    )

    if tool_calls:
      message.tool_calls = tool_calls

    # Map Anthropic stop reasons to internal finish reasons
    finish_reason = None
    if hasattr(response, "stop_reason"):
      stop_reason_map = {
        "end_turn": FinishReason.STOP,
        "max_tokens": FinishReason.LENGTH,
        "stop_sequence": FinishReason.STOP,
        "tool_use": FinishReason.TOOL_CALLS,
      }
      finish_reason = stop_reason_map.get(response.stop_reason)

    # Create choice
    choice = Choice(
      index=0,
      message=message,
      finish_reason=finish_reason,
    )

    # Create usage
    usage = None
    if hasattr(response, "usage"):
      usage = Usage(
        input_tokens=getattr(response.usage, "input_tokens", 0),
        output_tokens=getattr(response.usage, "output_tokens", 0),
        total_tokens=getattr(response.usage, "input_tokens", 0) + getattr(response.usage, "output_tokens", 0),
        cached_tokens=getattr(response.usage, "cache_creation_input_tokens", None) or getattr(response.usage, "cache_read_input_tokens", None),
      )

    return ChatResponse(
      id=getattr(response, "id", ""),
      created=0,  # Anthropic doesn't provide timestamp
      model=getattr(response, "model", ""),
      choices=[choice],
      usage=usage,
    )

  async def _handle_streaming_response(self, response) -> AsyncGenerator[StreamChunk, None]:
    """Handle streaming chat response with extended thinking support.

    Args:
        response: Anthropic streaming response

    Yields:
        Stream chunks (thinking deltas followed by text deltas)
    """

    thinking_started = False
    response_started = False

    input_tokens = 0
    output_tokens = 0
    cached_tokens = 0

    async for event in response:
      if event.type == "message_start":
        # Capture initial usage from message_start event
        if hasattr(event, "message") and hasattr(event.message, "usage"):
          input_tokens = getattr(event.message.usage, "input_tokens", 0)
          output_tokens = getattr(event.message.usage, "output_tokens", 0)
          # Handle cache tokens
          cache_creation = getattr(event.message.usage, "cache_creation_input_tokens", 0)
          cache_read = getattr(event.message.usage, "cache_read_input_tokens", 0)
          cached_tokens = cache_creation + cache_read

      elif event.type == "message_delta":
        # Accumulate additional output tokens from message_delta events
        if hasattr(event, "usage"):
          output_tokens += getattr(event.usage, "output_tokens", 0)
          # Handle additional cache tokens if present
          cache_creation = getattr(event.usage, "cache_creation_input_tokens", 0)
          cache_read = getattr(event.usage, "cache_read_input_tokens", 0)
          cached_tokens += cache_creation + cache_read

      elif event.type == "content_block_start":
        # Reset flags for each new block
        thinking_started = False
        response_started = False

      elif event.type == "content_block_delta":
        if event.delta.type == "thinking_delta":
          if not thinking_started:
            thinking_started = True
          yield StreamChunk(
            id=getattr(event, "id", ""),
            created=0,
            model="",
            choices=[
              {
                "index": event.index,
                "delta": {"type": "thinking", "content": event.delta.thinking},
                "finish_reason": None,
              }
            ],
          )
        elif event.delta.type == "text_delta":
          if not response_started:
            response_started = True
          yield StreamChunk(
            id=getattr(event, "id", ""),
            created=0,
            model="",
            choices=[
              {
                "index": event.index,
                "delta": {"type": "content", "content": event.delta.text},
                "finish_reason": None,
              }
            ],
          )

      elif event.type == "content_block_stop":
        if not thinking_started and not response_started:
          yield StreamChunk(
            id=getattr(event, "id", ""),
            created=0,
            model="",
            choices=[
              {
                "index": event.index,
                "delta": {},
                "finish_reason": None,
              }
            ],
          )

    # Yield final usage chunk
    try:
      usage = Usage(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cached_tokens=cached_tokens if cached_tokens > 0 else None,
      )
      yield StreamChunk(
        id="usage",
        created=0,
        model="",
        choices=[],
        usage=usage,
      )
    except Exception as e:
      self.logger.warning(f"Failed to process streaming usage data: {e}")

  async def generate_image(self, request: ImageRequest, **kwargs) -> ImageResponse:
    """Generate images.

    Args:
        request: Image generation request
        **kwargs: Additional provider-specific parameters

    Raises:
        NotImplementedError: Anthropic doesn't support image generation
    """
    raise NotImplementedError("Anthropic does not provide image generation. Please use OpenAI or another provider for image generation.")

  async def generate_embedding(self, request: EmbeddingRequest, **kwargs) -> EmbeddingResponse:
    """Generate text embeddings.

    Note: Anthropic does not provide embedding models.
    This method raises NotImplementedError.

    Args:
        request: Embedding request
        **kwargs: Additional parameters

    Raises:
        NotImplementedError: Anthropic doesn't support embeddings
    """
    raise NotImplementedError("Anthropic does not provide embedding models. Please use OpenAI or another provider for embeddings.")

  async def health_check(self) -> bool:
    """Check if Anthropic service is accessible.

    Returns:
        True if service is healthy
    """
    try:
      # Simple chat request to check connectivity
      test_request = ChatRequest(
        messages=[Message(role=MessageRole.USER, content="Hello")],
        max_tokens=10,
        temperature=None,
        top_p=None,
        top_k=None,
        frequency_penalty=None,
        presence_penalty=None,
        reasoning_budget_tokens=None,
      )
      await self.chat(test_request)
      return True
    except Exception as e:
      self.logger.error(f"Anthropic health check failed: {e}")
      return False

  async def close(self):
    """Close the Anthropic client and cleanup resources."""
    if self._closed:
      return

    try:
      if hasattr(self, "client") and self.client:
        await self.client.close()
        self.logger.debug("Closed Anthropic client")
    except Exception as e:
      self.logger.error(f"Error closing Anthropic client: {e}")
    finally:
      self._closed = True
