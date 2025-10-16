"""OpenAI provider implementation."""

from typing import Optional, Dict, Any, List, Union, AsyncGenerator
import structlog
import base64

from ...base import BaseProvider, ProviderCapabilities
from ...base.types import (
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ImageRequest,
  ImageResponse,
  ImageStreamChunk,
  EmbeddingRequest,
  EmbeddingResponse,
  Message,
  MessageRole,
  Choice,
  Usage,
  ImageData,
  Embedding,
  FinishReason,
  ContentType,
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
  ContentFilterError,
  TokenLimitError,
)
from ...config import settings
from ...database.backend_model_loader import BackendModelLoader
from ...utils import get_gcp_client, GCPUploadError

try:
  from openai import AsyncOpenAI
except ImportError:
  raise ImportError("`openai` not installed. Please install it using `pip install openai`")


logger = structlog.get_logger()


class OpenAIProvider(BaseProvider):
  """OpenAI provider implementation with model management."""

  # Model management (no more hardcoded data!)

  def __init__(self, api_key: Optional[str] = None, **kwargs):
    """Initialize OpenAI provider.

    Args:
        api_key: OpenAI API key
        **kwargs: Additional configuration
    """
    super().__init__("openai", api_key, **kwargs)

  def _initialize(self, **kwargs):
    """Initialize OpenAI-specific settings."""
    if not self.api_key:
      raise ProviderAuthenticationError("openai", "OpenAI API key is required")

      # Initialize async client with no timeout
    self.client = AsyncOpenAI(
      api_key=self.api_key,
      timeout=None,  # No timeout
      max_retries=0,  # We handle retries ourselves
    )

    # Model configurations
    self.default_model = kwargs.get("default_model", settings.openai_default_model)
    self.default_temperature = kwargs.get("temperature", settings.openai_temperature)
    self.default_max_tokens = kwargs.get("max_tokens", settings.openai_max_tokens)

  def get_capabilities(self) -> ProviderCapabilities:
    """Get OpenAI provider capabilities

    Note: This method is deprecated. Use get_model_capabilities() for specific models.
    """
    # Note: This method provides general capabilities. Use get_model_capabilities() for specific models.
    return ProviderCapabilities(
      chat=True,
      streaming=True,
      function_calling=True,
      vision=True,
      audio=False,  # Not implemented yet
      embeddings=True,
      image_generation=True,
      max_context_length=1000000,  # Maximum across all models
      supported_models=[],  # Use get_supported_models() for list from database (model registry)
      supported_file_types=[".png", ".jpg", ".jpeg", ".gif", ".webp"],
    )

  async def get_model_capabilities(self, model: str) -> ModelCapabilities:
    """Get capabilities for a specific model from backend database.

    Args:
        model: Model name

    Returns:
        Model capabilities

    Raises:
        ValueError: If model is not supported
    """
    # Use backend model loader if available
    loader = BackendModelLoader(settings.database_url)
    try:
      capabilities = await loader.get_model_capabilities("openai", model)
      if capabilities is None:
        raise ValueError(f"Model '{model}' is not supported by OpenAI provider")
      return capabilities
    finally:
      await loader.close()

  async def get_supported_models(self) -> List[ModelInfo]:
    """Get list of all supported models from backend database.

    Returns:
        List of model information
    """
    loader = BackendModelLoader(settings.database_url)
    try:
      return await loader.get_supported_models_info("openai")
    finally:
      await loader.close()

  def _get_model_description(self, model: str) -> str:
    """Get a description for a specific model."""
    descriptions = {
      "gpt-5": "Latest flagship model with advanced reasoning, 45% fewer errors, 80% fewer hallucinations",
      "gpt-5-mini": "Fast and cost-efficient version of GPT-5 for defined tasks",
      "gpt-5-nano": "Ultra-compact speed demon for low-latency needs",
      "gpt-4.1": "Enhanced coding model with 1M token context, 21.4% improvement in coding benchmarks",
      "text-embedding-3-large": "Highest performance embedding model with up to 3072 dimensions",
      "text-embedding-3-small": "Cost-effective embedding model with 1536 dimensions",
      "gpt-image-1": "Latest multimodal image generation with advanced text rendering and C2PA watermarking",
      "dall-e-3": "Advanced image generation model with style control and HD quality options",
    }
    return descriptions.get(model, f"OpenAI {model} model")

  async def validate_model(self, model: str) -> bool:
    """Validate that a model is supported using backend database.

    Args:
        model: Model name to validate

    Returns:
        True if model is supported, False otherwise
    """
    loader = BackendModelLoader(settings.database_url)
    try:
      return await loader.validate_model("openai", model)
    finally:
      await loader.close()

  def _convert_message_to_openai(self, message: Message) -> Dict[str, Any]:
    """Convert internal message format to OpenAI format.

    Args:
        message: Internal message format

    Returns:
        OpenAI-compatible message dictionary
    """
    openai_message = {
      "role": message.role.value,
    }

    if isinstance(message.content, str):
      openai_message["content"] = message.content
    elif isinstance(message.content, list):
      content_parts = []

      for content in message.content:
        if content.type == ContentType.TEXT:
          content_parts.append({"type": "text", "text": content.text})
        elif content.type == ContentType.IMAGE:
          if content.image_url:
            content_parts.append({
              "type": "image_url",
              "image_url": {"url": content.image_url},  # type: ignore
            })
          elif content.image_base64:
            # Ensure proper data URL format
            if not content.image_base64.startswith("data:"):
              content.image_base64 = f"data:image/jpeg;base64,{content.image_base64}"

            content_parts.append({
              "type": "image_url",
              "image_url": {"url": content.image_base64},  # type: ignore
            })

      openai_message["content"] = content_parts  # type: ignore

    # Add function call information if present
    if message.function_call:
      openai_message["function_call"] = {  # type: ignore
        "name": message.function_call.name,
        "arguments": message.function_call.arguments,
      }

    if message.tool_calls:
      openai_message["tool_calls"] = [  # type: ignore
        {
          "id": tool_call.id,
          "type": "function",
          "function": {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments,
          },
        }
        for tool_call in message.tool_calls
      ]

    if message.name:
      openai_message["name"] = message.name

    return openai_message

  def _convert_openai_message(self, openai_message: Dict[str, Any]) -> Message:
    """Convert OpenAI message format to internal format.

    Args:
        openai_message: OpenAI message dictionary

    Returns:
        Internal message format
    """
    # Handle None or missing openai_message
    if not openai_message:
      raise ValueError("OpenAI message cannot be None or empty")

    # Handle missing required fields safely
    if "role" not in openai_message:
      raise ValueError("OpenAI message missing required 'role' field")

    role = MessageRole(openai_message["role"])
    content = openai_message.get("content", "")

    # Extract reasoning/thinking content if present (for reasoning models)
    reasoning_content = None
    if isinstance(openai_message.get("content"), list):
      for item in openai_message["content"]:
        if isinstance(item, dict) and item.get("type") == "reasoning":
          reasoning_content = item.get("text")
          break

    message = Message(
      role=role,
      content=content,
      name=openai_message.get("name"),
      reasoning_content=reasoning_content,
    )

    # Handle function calls
    if "function_call" in openai_message and openai_message["function_call"]:
      from ...base.types import FunctionCall

      function_call = openai_message["function_call"]
      if function_call and isinstance(function_call, dict) and "name" in function_call:
        message.function_call = FunctionCall(
          name=function_call["name"],
          arguments=function_call.get("arguments", ""),
        )

    if "tool_calls" in openai_message and openai_message["tool_calls"]:
      from ...base.types import ToolCall, FunctionCall

      tool_calls = openai_message["tool_calls"]
      if tool_calls and isinstance(tool_calls, list):
        message.tool_calls = []
        for tool_call in tool_calls:
          if (
            tool_call
            and isinstance(tool_call, dict)
            and "id" in tool_call
            and "function" in tool_call
            and tool_call["function"]
            and isinstance(tool_call["function"], dict)
          ):
            message.tool_calls.append(
              ToolCall(
                id=tool_call["id"],
                type="function",
                function=FunctionCall(
                  name=tool_call["function"].get("name", ""),
                  arguments=tool_call["function"].get("arguments", ""),
                ),
              )
            )

    return message

  def _handle_openai_error(self, error: Exception) -> Exception:
    """Convert OpenAI errors to our internal error types.

    Args:
        error: Original OpenAI error

    Returns:
        Converted exception
    """
    error_str = str(error)

    if "authentication" in error_str.lower() or "api key" in error_str.lower():
      return ProviderAuthenticationError("openai", error_str)
    elif "rate limit" in error_str.lower():
      # Try to extract retry_after from the error
      return ProviderRateLimitError("openai", message=error_str)
    elif "quota" in error_str.lower() or "billing" in error_str.lower():
      return ProviderQuotaExceededError("openai", error_str)
    elif "timeout" in error_str.lower():
      return ProviderTimeoutError("openai")
    elif "model" in error_str.lower() and "not found" in error_str.lower():
      return ModelNotFoundError("openai", "unknown")
    elif "content policy" in error_str.lower() or "safety" in error_str.lower():
      return ContentFilterError(error_str)
    elif "token" in error_str.lower() and "limit" in error_str.lower():
      return TokenLimitError(error_str, 0, 0)  # Will be filled with actual values if available
    else:
      return InvalidRequestError(f"OpenAI API error: {error_str}")

  async def chat(self, request: ChatRequest, **kwargs) -> Union[ChatResponse, AsyncGenerator[StreamChunk, None]]:
    """Send a chat completion request to OpenAI.

    Args:
        request: Chat completion request
        **kwargs: Additional OpenAI-specific parameters

    Returns:
        Chat response or async generator for streaming
    """
    # Validate request
    self._validate_request(request)

    # Estimate tokens for rate limiting
    estimated_tokens = self._estimate_tokens(request.messages)
    await self._check_rate_limit(estimated_tokens)

    # Prepare OpenAI request
    openai_request = {
      "model": request.model or self.default_model,
      "input": [self._convert_message_to_openai(msg) for msg in request.messages],
      "temperature": request.temperature or self.default_temperature,
      "stream": request.stream,
    }

    # Handle model-specific parameter requirements
    model = request.model or self.default_model

    # Reasoning models (o1, o3 series) have specific requirements
    is_reasoning_model = model.startswith("o1") or model.startswith("o3")

    if is_reasoning_model:
      # Reasoning models don't support temperature, max_tokens, system messages
      openai_request.pop("temperature", None)
      # Use max_completion_tokens for reasoning models
      if "max_tokens" in openai_request:
        openai_request["max_completion_tokens"] = openai_request.pop("max_tokens")

      # Note: Reasoning is built into o1/o3 models and doesn't require special parameters

    # GPT-5 series models only support temperature = 1 (default)
    elif model.startswith("gpt-5"):
      if "temperature" in openai_request and openai_request["temperature"] != 1:
        openai_request.pop("temperature")

    if request.reasoning:
      openai_request["reasoning"] = {
        "effort": "low",
        "summary": "auto",
      }

    # Add optional parameters
    if request.top_p is not None:
      openai_request["top_p"] = request.top_p
    if request.frequency_penalty is not None:
      openai_request["frequency_penalty"] = request.frequency_penalty
    if request.presence_penalty is not None:
      openai_request["presence_penalty"] = request.presence_penalty
    if request.stop:
      openai_request["stop"] = request.stop
    if request.functions:
      openai_request["functions"] = request.functions
    if request.function_call:
      openai_request["function_call"] = request.function_call
    if request.tools:
      openai_request["tools"] = request.tools
    if request.tool_choice:
      openai_request["tool_choice"] = request.tool_choice
    if request.user:
      openai_request["user"] = request.user
    if request.seed is not None:
      openai_request["seed"] = request.seed
    if request.response_format:
      openai_request["response_format"] = request.response_format
    if request.logit_bias:
      openai_request["logit_bias"] = request.logit_bias
    if request.logprobs is not None:
      openai_request["logprobs"] = request.logprobs
    if request.top_logprobs is not None:
      openai_request["top_logprobs"] = request.top_logprobs
    if request.n != 1:
      openai_request["n"] = request.n

    # Add any additional OpenAI-specific parameters
    openai_request.update(kwargs)

    try:
      async with self._timed_request(
        f"chat_completion:{openai_request['model']}",
        timeout=kwargs.get("timeout", 30.0),
      ):
        response = await self.client.responses.create(**openai_request)  # type: ignore[arg-type]

        if request.stream:
          return self._handle_streaming_response(response)
        else:
          return self._handle_chat_response(response)

    except Exception as e:
      self.logger.error(f"OpenAI chat completion failed: {e}")
      raise self._handle_openai_error(e)

  def _handle_chat_response(self, response) -> ChatResponse:
    """Convert OpenAI response to internal format.

    Args:
        response: OpenAI response object

    Returns:
        Internal chat response
    """
    # Handle None response
    if not response:
      raise ValueError("OpenAI response cannot be None")

    # Handle missing choices
    if not hasattr(response, "choices") or not response.choices:
      raise ValueError("OpenAI response missing choices")

    choices = []

    for choice in response.choices:
      # Handle missing message
      if not hasattr(choice, "message") or not choice.message:
        raise ValueError("OpenAI choice missing message")

      # Handle the message conversion more safely
      try:
        message_dict = choice.message.model_dump() if hasattr(choice.message, "model_dump") else choice.message.__dict__
      except Exception as e:
        self.logger.error(f"Failed to convert choice.message to dict: {e}")
        # Fallback - create minimal message dict
        message_dict = {
          "role": getattr(choice.message, "role", "assistant"),
          "content": getattr(choice.message, "content", ""),
        }

      internal_message = self._convert_openai_message(message_dict)

      finish_reason = None
      if hasattr(choice, "finish_reason") and choice.finish_reason:
        try:
          finish_reason = FinishReason(choice.finish_reason)
        except ValueError:
          # Log unknown finish reason but don't fail
          self.logger.warning(f"Unknown finish reason: {choice.finish_reason}")

      logprobs_data = None
      if hasattr(choice, "logprobs") and choice.logprobs:
        try:
          logprobs_data = choice.logprobs.model_dump() if hasattr(choice.logprobs, "model_dump") else choice.logprobs.__dict__
        except Exception as e:
          self.logger.warning(f"Failed to process logprobs: {e}")

      choices.append(
        Choice(
          index=getattr(choice, "index", 0),
          message=internal_message,
          finish_reason=finish_reason,
          logprobs=logprobs_data,
        )
      )

    usage = None
    if hasattr(response, "usage") and response.usage:
      try:
        usage = Usage(
          input_tokens=getattr(response.usage, "prompt_tokens", 0),
          output_tokens=getattr(response.usage, "completion_tokens", 0),
          total_tokens=getattr(response.usage, "total_tokens", 0),
        )
      except Exception as e:
        self.logger.warning(f"Failed to process usage data: {e}")

    try:
      return ChatResponse(
        id=getattr(response, "id", ""),
        created=getattr(response, "created", 0),
        model=getattr(response, "model", ""),
        choices=choices,
        usage=usage,
        system_fingerprint=getattr(response, "system_fingerprint", None),
      )
    except Exception as e:
      self.logger.error(f"Failed to create ChatResponse: {e}")
      raise ValueError(f"Failed to create ChatResponse: {e}")

  async def _handle_streaming_response(self, response) -> AsyncGenerator[StreamChunk, None]:
    """Handle streaming chat response.

    Args:
        response: OpenAI streaming response

    Yields:
        Stream chunks
    """
    async for event in response:
      # Check if this is the final completion event with usage
      if event.type == "response.completed" and hasattr(event, "response") and event.response:
        try:
          final_response = event.response
          if hasattr(final_response, "usage") and final_response.usage:
            usage = Usage(
              input_tokens=getattr(final_response.usage, "input_tokens", 0),
              output_tokens=getattr(final_response.usage, "output_tokens", 0),
              total_tokens=getattr(final_response.usage, "total_tokens", 0),
              cached_tokens=getattr(final_response.usage, "cache_creation_input_tokens", None)
              or getattr(final_response.usage, "cache_read_input_tokens", None),
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
        continue

      if event.type == "response.reasoning_summary_text.delta":
        yield StreamChunk(
          id=getattr(event, "item_id", ""),
          created=0,
          model="",
          choices=[
            {
              "index": 0,
              "delta": {"type": "thinking", "content": event.delta},
              "finish_reason": None,
            }
          ],
        )
      elif event.type == "response.output_text.delta":
        yield StreamChunk(
          id=getattr(event, "item_id", ""),
          created=0,
          model="",
          choices=[
            {
              "index": 0,
              "delta": {"type": "content", "content": event.delta},
              "finish_reason": None,
            }
          ],
        )

  async def generate_image(self, request: ImageRequest, **kwargs):
    """Generate images using DALL-E or GPT-Image with optional streaming.

    Args:
        request: Image generation request
        **kwargs: Additional parameters

    Returns:
        ImageResponse for non-streaming, AsyncGenerator for streaming (gpt-image-1 only)
    """
    # Check rate limits
    await self._check_rate_limit()

    # Prepare request
    model = request.model or "gpt-image-1"

    # Handle model-specific size parameter
    if request.size:
      if model.startswith("gpt-image"):
        # GPT-Image models support: '1024x1024', '1024x1536', '1536x1024', 'auto'
        size_mapping = {
          "1024x1024": "1024x1024",
          "1792x1024": "1536x1024",  # Map unsupported size to closest supported
          "1024x1792": "1024x1536",  # Map unsupported size to closest supported
          "1536x1024": "1536x1024",
          "1024x1536": "1024x1536",
        }
        mapped_size = size_mapping.get(request.size.value, "1024x1024")
      else:
        # DALL-E models support different sizes
        mapped_size = request.size.value
    else:
      mapped_size = "1024x1024"  # Default size

    dalle_request = {
      "prompt": request.prompt,
      "model": model,
      "n": request.n,
      "size": mapped_size,
    }

    # Add quality parameter with model-specific handling
    if request.quality:
      if model.startswith("gpt-image"):
        # GPT-Image models use different quality values: 'low', 'medium', 'high', 'auto'
        quality_mapping = {
          "standard": "medium",  # Map standard quality to medium for GPT-Image
          "hd": "high",  # Map HD quality to high for GPT-Image
        }
        dalle_request["quality"] = quality_mapping.get(request.quality.value, "medium")
      else:
        # DALL-E models use 'standard' and 'hd'
        dalle_request["quality"] = request.quality.value

    # Add response_format only for models that support it (not gpt-image-1)
    if request.response_format and not model.startswith("gpt-image"):
      dalle_request["response_format"] = request.response_format

    # Add style only for models that support it (not gpt-image-1)
    if request.style and not model.startswith("gpt-image"):
      dalle_request["style"] = request.style.value
    if request.user:
      dalle_request["user"] = request.user

    dalle_request.update(kwargs)

    # Check if streaming is requested (only supported for gpt-image-1)
    if request.stream and model.startswith("gpt-image"):
      # Pass upload_to_gcp from request to streaming handler via kwargs
      streaming_kwargs = {**kwargs, "upload_to_gcp": request.upload_to_gcp or kwargs.get("upload_to_gcp", False)}
      return self._handle_streaming_image_response(dalle_request, **streaming_kwargs)

    # Non-streaming generation
    try:
      async with self._timed_request(
        f"image_generation:{dalle_request['model']}",
        timeout=kwargs.get("timeout", 90.0),  # Increased timeout for image generation
      ):
        # Remove upload_to_gcp from dalle_request before calling OpenAI API
        dalle_request.pop("upload_to_gcp", None)
        response = await self.client.images.generate(**dalle_request)  # type: ignore[arg-type, call-overload]

        # Check if GCP upload is requested (check both request object and kwargs)
        upload_to_gcp = request.upload_to_gcp or kwargs.get("upload_to_gcp", False)
        gcp = None
        if upload_to_gcp:
          gcp = get_gcp_client()
          if not gcp:
            self.logger.warning("GCP upload requested but GCP is not configured properly")

        image_data = []
        for idx, item in enumerate(response.data):
          original_url = item.url
          b64_json = item.b64_json
          url: Optional[str] = None

          # Upload to GCP if requested and properly configured
          if gcp:
            try:
              import time

              timestamp = int(time.time())

              if original_url and not model.startswith("gpt-image"):
                # For DALL-E models, download and upload to GCP
                import aiohttp

                async with aiohttp.ClientSession() as session:
                  async with session.get(original_url) as img_response:
                    if img_response.status == 200:
                      image_bytes = await img_response.read()
                      gcp_key = f"images/dalle_{model.replace('-', '_')}_{timestamp}_{idx}.png"
                      url = await gcp.upload_file(
                        file=image_bytes,
                        key=gcp_key,
                        content_type="image/png",
                      )
                      # Only clear base64 if we got a valid URL back
                      if url:
                        b64_json = None  # Clear b64_json since we uploaded to GCP
                      else:
                        self.logger.warning("GCP upload returned empty URL, keeping base64")
                        url = None
                    else:
                      self.logger.warning(f"Failed to download DALL-E image: HTTP {img_response.status}")

              elif b64_json:
                # For GPT-Image models (or DALL-E with b64), upload the base64 data to GCP
                image_bytes = base64.b64decode(b64_json)
                gcp_key = f"images/{model.replace('-', '_')}_{timestamp}_{idx}.png"
                url = await gcp.upload_file(
                  file=image_bytes,
                  key=gcp_key,
                  content_type="image/png",
                )
                # Only clear base64 if we got a valid URL back
                if url:
                  b64_json = None  # Clear b64_json since we uploaded to GCP
                else:
                  self.logger.warning("GCP upload returned empty URL, keeping base64")
                  url = None

            except GCPUploadError as e:
              self.logger.error(f"GCP upload failed: {e}")
              url = None
              # Keep base64 as fallback
            except Exception as e:
              self.logger.error(f"Unexpected error during GCP upload: {e}")
              url = None
              # Keep base64 as fallback

          image_data.append(
            ImageData(
              url=url,
              b64_json=b64_json,
              revised_prompt=item.revised_prompt,
            )
          )

        return ImageResponse(created=response.created, data=image_data)

    except Exception as e:
      self.logger.error(f"OpenAI image generation failed: {e}")
      raise self._handle_openai_error(e)

  async def _handle_streaming_image_response(self, dalle_request: dict, **kwargs):
    """Handle streaming image generation response (gpt-image-1 only).

    Args:
        dalle_request: Request parameters
        **kwargs: Additional parameters

    Yields:
        ImageStreamChunk: Streaming image chunks
    """
    # Add streaming parameters
    dalle_request["stream"] = True
    dalle_request["partial_images"] = kwargs.get("partial_images", 3)

    # Get GCP client info before removing from dalle_request
    upload_to_gcp = dalle_request.get("upload_to_gcp", False) or kwargs.get("upload_to_gcp", False)

    try:
      async with self._timed_request(
        f"image_generation_stream:{dalle_request['model']}",
        timeout=kwargs.get("timeout", 120.0),  # Longer timeout for streaming
      ):
        self.logger.info(
          f"Starting streaming image generation: {dalle_request['model']}",
          partial_images=dalle_request["partial_images"],
        )

        # Remove upload_to_gcp from dalle_request before calling OpenAI API
        dalle_request.pop("upload_to_gcp", None)
        stream = await self.client.images.generate(**dalle_request)

        # Get GCP client if upload is requested
        gcp = None
        streaming_image_url: Optional[str] = None
        streaming_gcp_key: Optional[str] = None

        if upload_to_gcp:
          gcp = get_gcp_client()
          if not gcp:
            self.logger.warning("GPT-Image-1 streaming: GCP upload requested but GCP is not configured properly")
          else:
            # Generate a single GCP key for all partial + final images
            # This way the URL stays the same, we just keep overwriting the image
            import time

            timestamp = int(time.time())
            user_id = dalle_request.get("user", "unknown")
            streaming_gcp_key = f"images/streaming_{user_id}_{timestamp}.png"

        async for event in stream:
          self.logger.info(f"GPT-Image-1: Received event type: {event.type}")

          if event.type == "image_generation.partial_image":
            # Upload partial images to the SAME GCP key (overwrites previous)
            if gcp and streaming_gcp_key:
              try:
                image_bytes = base64.b64decode(event.b64_json)
                streaming_image_url = await gcp.upload_file(
                  file=image_bytes,
                  key=streaming_gcp_key,
                  content_type="image/png",
                )
                # Return the same URL for all partials - image content updates automatically
                yield ImageStreamChunk(
                  type="partial_image",
                  partial_image_index=event.partial_image_index,
                  b64_json=None,
                  url=streaming_image_url,
                )
              except Exception as e:
                self.logger.error(f"GPT-Image-1: Failed to upload partial image: {e}")
                # Fallback to base64
                yield ImageStreamChunk(
                  type="partial_image",
                  partial_image_index=event.partial_image_index,
                  b64_json=event.b64_json,
                  url=None,
                )
            else:
              # No GCP - return base64
              yield ImageStreamChunk(
                type="partial_image",
                partial_image_index=event.partial_image_index,
                b64_json=event.b64_json,
                url=None,
              )

          elif event.type == "image_generation.completed":
            self.logger.info("GPT-Image-1: Processing completed event")
            # Event has b64_json directly, not in a data array
            b64_json = getattr(event, "b64_json", None)
            url: Optional[str] = None

            self.logger.info(f"GPT-Image-1: Final b64 length: {len(b64_json) if b64_json else 0}")

            if gcp and streaming_gcp_key and b64_json:
              try:
                self.logger.info("GPT-Image-1: Uploading final image to GCP")
                image_bytes = base64.b64decode(b64_json)
                # Overwrite the same key with final image
                url = await gcp.upload_file(
                  file=image_bytes,
                  key=streaming_gcp_key,
                  content_type="image/png",
                )
                if url:
                  self.logger.info(f"GPT-Image-1: Final uploaded: {url}")
                  b64_json = None
                else:
                  self.logger.warning("GPT-Image-1: Upload returned None")
                  url = None
              except Exception as e:
                self.logger.error(f"GPT-Image-1: Upload failed: {e}")
                url = None

            image_data = [
              ImageData(
                url=url,
                b64_json=b64_json,
                revised_prompt=getattr(event, "revised_prompt", None),
              )
            ]

            yield ImageStreamChunk(
              type="complete",
              data=image_data,
            )

        self.logger.info(f"Completed streaming image generation: {dalle_request['model']}")

    except Exception as e:
      self.logger.error(f"OpenAI streaming image generation failed: {e}")
      raise self._handle_openai_error(e)

  async def generate_embedding(self, request: EmbeddingRequest, **kwargs) -> EmbeddingResponse:
    """Generate text embeddings.

    Args:
        request: Embedding request
        **kwargs: Additional parameters

    Returns:
        Embedding response
    """
    # Check rate limits
    estimated_tokens = len(str(request.input)) // 4
    await self._check_rate_limit(estimated_tokens)

    # Prepare request
    embedding_request = {
      "input": request.input,
      "model": request.model or "text-embedding-3-large",
      "encoding_format": request.encoding_format,
    }

    if request.dimensions:
      embedding_request["dimensions"] = request.dimensions  # type: ignore
    if request.user:
      embedding_request["user"] = request.user

    embedding_request.update(kwargs)

    try:
      async with self._timed_request(
        f"embedding:{embedding_request['model']}",
        timeout=kwargs.get("timeout", 30.0),
      ):
        response = await self.client.embeddings.create(**embedding_request)  # type: ignore[arg-type]

        embeddings = []
        for item in response.data:
          embeddings.append(Embedding(index=item.index, embedding=item.embedding))

        usage = Usage(
          input_tokens=response.usage.prompt_tokens,
          output_tokens=0,
          total_tokens=response.usage.total_tokens,
        )

        return EmbeddingResponse(data=embeddings, model=response.model, usage=usage)

    except Exception as e:
      self.logger.error(f"OpenAI embedding generation failed: {e}")
      raise self._handle_openai_error(e)

  async def health_check(self) -> bool:
    """Check if OpenAI service is accessible.

    Returns:
        True if service is healthy
    """
    try:
      # Simple embedding request to check connectivity
      test_request = EmbeddingRequest(input="health check")
      await self.generate_embedding(test_request)
      return True
    except Exception as e:
      self.logger.error(f"OpenAI health check failed: {e}")
      return False

  async def deep_research(self, prompt: str, model: str = "o4-mini-deep-research", system_message: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Execute deep research using OpenAI Responses API.

    Args:
        prompt: The research query/prompt
        model: Deep research model to use
        system_message: Optional system/developer message
        **kwargs: Additional parameters

    Returns:
        Raw response from responses API
    """
    import time

    self.logger.info(f"Starting deep_research:{model}")
    start_time = time.time()

    try:
      # Build input for responses API
      input_messages = []

      # Add developer/system message if provided
      if system_message:
        input_messages.append({"role": "developer", "content": [{"type": "input_text", "text": system_message}]})

      # Add user prompt
      input_messages.append({"role": "user", "content": [{"type": "input_text", "text": prompt}]})

      # Build request for responses API
      request_params = {
        "model": model,
        "input": input_messages,
        "reasoning": {"summary": "auto"},
      }

      # Add tools if specified
      tools = kwargs.get("tools")
      if tools:
        request_params["tools"] = tools

      # Make the API call using responses endpoint
      # Note: We rely on the client's default timeout (300s)
      response = await self.client.responses.create(**request_params)  # type: ignore[arg-type, call-overload]

      elapsed = time.time() - start_time
      self.logger.info(f"Completed deep_research:{model} in {elapsed:.2f} seconds")

      return response

    except Exception as e:
      elapsed = time.time() - start_time
      self.logger.error(f"deep_research:{model} failed after {elapsed:.2f} seconds: {e}")
      raise self._handle_openai_error(e)

  async def close(self):
    """Close the OpenAI client and cleanup resources."""
    if self._closed:
      return

    try:
      if hasattr(self, "client") and self.client:
        await self.client.close()
        self.logger.debug("Closed OpenAI client")
    except Exception as e:
      self.logger.error(f"Error closing OpenAI client: {e}")
    finally:
      self._closed = True
