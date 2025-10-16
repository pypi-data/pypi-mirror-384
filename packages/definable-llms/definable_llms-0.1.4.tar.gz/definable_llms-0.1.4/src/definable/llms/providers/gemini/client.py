"""Gemini provider implementation."""

from typing import Any, Optional, List, Union, AsyncGenerator
import structlog

from ...base import BaseProvider, ProviderCapabilities
from ...base.types import (
  ChatRequest,
  ChatResponse,
  StreamChunk,
  ImageRequest,
  ImageResponse,
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
from ...utils import get_gcp_client, GCPUploadError
from ...database.backend_model_loader import BackendModelLoader

try:
  from google import genai
  from google.genai.errors import ClientError, ServerError
  from google.genai.types import (
    Content,
    GenerateContentConfig,
    Part,
  )
except ImportError:
  raise ImportError("`google-genai` not installed. Please install it using `pip install google-genai`")


logger = structlog.get_logger()


class GeminiProvider(BaseProvider):
  """Gemini provider implementation with model management."""

  client: Optional[Any]  # genai.Client

  def __init__(self, api_key: Optional[str] = None, **kwargs):
    """Initialize Gemini provider.

    Args:
        api_key: Gemini API key
        **kwargs: Additional configuration
    """
    super().__init__("gemini", api_key, **kwargs)

  def _initialize(self, **kwargs):
    """Initialize Gemini-specific settings."""
    if not self.api_key:
      raise ProviderAuthenticationError("gemini", "Gemini API key is required")

    # Initialize client
    self.client = genai.Client(api_key=self.api_key)

    # Model configurations
    self.default_model = kwargs.get("default_model", settings.gemini_default_model)
    self.default_temperature = kwargs.get("temperature", settings.gemini_temperature)
    self.default_max_tokens = kwargs.get("max_tokens", settings.gemini_max_tokens)

  def get_capabilities(self) -> ProviderCapabilities:
    """Get Gemini provider capabilities

    Note: This method is deprecated. Use get_model_capabilities() for specific models.
    """
    return ProviderCapabilities(
      chat=True,
      streaming=True,
      function_calling=True,
      vision=True,
      audio=True,
      embeddings=True,
      image_generation=True,
      max_context_length=2000000,  # Maximum across all models (Gemini 2.0 Flash Thinking)
      supported_models=[],  # Use get_supported_models() for list from database
      supported_file_types=[
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".pdf",
        ".txt",
      ],
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
      capabilities = await loader.get_model_capabilities("gemini", model)
      if capabilities is None:
        raise ValueError(f"Model '{model}' is not supported by Gemini provider")
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
      return await loader.get_supported_models_info("gemini")
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
      return await loader.validate_model("gemini", model)
    finally:
      await loader.close()

  def _convert_message_to_gemini(self, message: Message) -> Content:
    """Convert internal message format to Gemini format.

    Args:
        message: Internal message format

    Returns:
        Gemini-compatible Content object
    """
    # Map roles
    role_map = {
      "user": "user",
      "assistant": "model",
      "system": "user",  # Gemini uses system instructions separately
      "tool": "user",
    }

    role = role_map.get(message.role.value, "user")
    parts = []

    # Handle content
    if isinstance(message.content, str):
      parts.append(Part.from_text(text=message.content))
    elif isinstance(message.content, list):
      for content in message.content:
        if content.type == ContentType.TEXT:
          if content.text:
            parts.append(Part.from_text(text=content.text))
        elif content.type == ContentType.IMAGE:
          if content.image_url:
            # For URLs, we need to download and convert to bytes
            parts.append(Part.from_uri(file_uri=content.image_url, mime_type="image/jpeg"))
          elif content.image_base64:
            # Handle base64 images
            import base64

            # Remove data URL prefix if present
            if content.image_base64.startswith("data:"):
              content.image_base64 = content.image_base64.split(",", 1)[1]
            image_bytes = base64.b64decode(content.image_base64)
            parts.append(Part.from_bytes(mime_type="image/jpeg", data=image_bytes))

    # Handle function calls (tool calls)
    if message.tool_calls:
      for tool_call in message.tool_calls:
        import json

        parts.append(
          Part.from_function_call(
            name=tool_call.function.name,
            args=json.loads(tool_call.function.arguments),
          )
        )

    return Content(role=role, parts=parts)

  def _convert_gemini_message(self, content: Content, finish_reason: Optional[str] = None) -> Message:
    """Convert Gemini Content format to internal message format.

    Args:
        content: Gemini Content object
        finish_reason: Finish reason from the response

    Returns:
        Internal message format
    """
    # Map Gemini roles back to our internal roles
    role_map = {
      "model": MessageRole.ASSISTANT,
      "user": MessageRole.USER,
    }

    from ...base.types import ToolCall, FunctionCall

    role = role_map.get(content.role or "model", MessageRole.ASSISTANT)
    message_content = ""
    reasoning_content = ""
    tool_calls: List[ToolCall] = []

    # Extract content from parts
    if content.parts:
      for part in content.parts:
        if hasattr(part, "text") and part.text:
          # Check if this is a thought/reasoning part (Gemini 2.5 thinking)
          if hasattr(part, "thought") and part.thought:
            reasoning_content += part.text
          else:
            message_content += part.text

        # Handle function calls
        if hasattr(part, "function_call") and part.function_call:
          import json

          call_id = part.function_call.id if hasattr(part.function_call, "id") and part.function_call.id else f"call_{len(tool_calls)}"
          tool_calls.append(
            ToolCall(
              id=call_id,
              type="function",
              function=FunctionCall(
                name=part.function_call.name or "",
                arguments=json.dumps(part.function_call.args) if part.function_call.args else "",
              ),
            )
          )

    message = Message(
      role=role,
      content=message_content,
      reasoning_content=reasoning_content or None,
      tool_calls=tool_calls or None,
    )

    return message

  def _handle_gemini_error(self, error: Exception) -> Exception:
    """Convert Gemini errors to our internal error types.

    Args:
        error: Original Gemini error

    Returns:
        Converted exception
    """
    error_str = str(error)

    if isinstance(error, ClientError):
      if error.code == 401 or "api key" in error_str.lower():
        return ProviderAuthenticationError("gemini", error_str)
      elif error.code == 429 or "rate limit" in error_str.lower():
        return ProviderRateLimitError("gemini", message=error_str)
      elif error.code == 403 or "quota" in error_str.lower():
        return ProviderQuotaExceededError("gemini", error_str)
      elif error.code == 404:
        return ModelNotFoundError("gemini", "unknown")
      elif "content" in error_str.lower() and "safety" in error_str.lower():
        return ContentFilterError(error_str)
      elif "token" in error_str.lower() and "limit" in error_str.lower():
        return TokenLimitError(error_str, 0, 0)
      else:
        return InvalidRequestError(f"Gemini API error: {error_str}")
    elif isinstance(error, ServerError):
      return ProviderTimeoutError("gemini")
    elif "authentication" in error_str.lower() or "api key" in error_str.lower():
      return ProviderAuthenticationError("gemini", error_str)
    elif "rate limit" in error_str.lower():
      return ProviderRateLimitError("gemini", message=error_str)
    elif "quota" in error_str.lower():
      return ProviderQuotaExceededError("gemini", error_str)
    elif "timeout" in error_str.lower():
      return ProviderTimeoutError("gemini")
    elif "model" in error_str.lower() and "not found" in error_str.lower():
      return ModelNotFoundError("gemini", "unknown")
    elif "content" in error_str.lower() or "safety" in error_str.lower():
      return ContentFilterError(error_str)
    elif "token" in error_str.lower() and "limit" in error_str.lower():
      return TokenLimitError(error_str, 0, 0)
    else:
      return InvalidRequestError(f"Gemini API error: {error_str}")

  async def chat(self, request: ChatRequest, **kwargs) -> Union[ChatResponse, AsyncGenerator[StreamChunk, None]]:
    """Send a chat completion request to Gemini.

    Args:
        request: Chat completion request
        **kwargs: Additional Gemini-specific parameters

    Returns:
        Chat response or async generator for streaming
    """
    # Validate request
    self._validate_request(request)

    # Estimate tokens for rate limiting
    estimated_tokens = self._estimate_tokens(request.messages)
    await self._check_rate_limit(estimated_tokens)

    # Extract system message if present
    system_instruction = None
    messages = []
    for msg in request.messages:
      if msg.role == MessageRole.SYSTEM:
        system_instruction = msg.content
      else:
        messages.append(self._convert_message_to_gemini(msg))

    # Prepare Gemini request config
    config_params = {
      "temperature": request.temperature or self.default_temperature,
      "max_output_tokens": request.max_tokens or self.default_max_tokens,
    }

    if system_instruction:
      config_params["system_instruction"] = system_instruction

    if request.top_p is not None:
      config_params["top_p"] = request.top_p
    if request.top_k is not None:
      config_params["top_k"] = request.top_k
    if request.stop:
      config_params["stop_sequences"] = request.stop

    # Handle tools/functions
    if request.tools:
      # Convert tools to Gemini function declarations format
      from google.genai.types import Tool, FunctionDeclaration

      function_declarations = []
      for tool in request.tools:
        if tool.get("type") == "function":
          func = tool.get("function", {})
          function_declarations.append(
            FunctionDeclaration(
              name=func.get("name"),
              description=func.get("description"),
              parameters=func.get("parameters"),
            )
          )

      if function_declarations:
        config_params["tools"] = [Tool(function_declarations=function_declarations)]

    # Handle Thinking (Gemini 2.5 models)
    if request.reasoning:
      from google.genai.types import ThinkingConfig

      config_params["thinking_config"] = ThinkingConfig(
        thinking_budget=request.reasoning_budget_tokens if request.reasoning_budget_tokens is not None else -1,
        include_thoughts=True,
      )

    config = GenerateContentConfig(**config_params)  # type: ignore[arg-type]

    model = request.model or self.default_model

    try:
      if request.stream:
        return self._handle_streaming_response(model, messages, config, **kwargs)
      else:
        async with self._timed_request(
          f"chat_completion:{model}",
          timeout=kwargs.get("timeout", 45.0),
        ):
          response = await self.client.aio.models.generate_content(  # type: ignore
            model=model,
            contents=messages,
            config=config,
          )

          return self._handle_chat_response(response, model)

    except (ClientError, ServerError) as e:
      self.logger.error(f"Gemini chat completion failed: {e}")
      raise self._handle_gemini_error(e)
    except Exception as e:
      self.logger.error(f"Gemini chat completion failed: {e}")
      raise self._handle_gemini_error(e)

  def _handle_chat_response(self, response, model: str) -> ChatResponse:
    """Convert Gemini response to internal format.

    Args:
        response: Gemini response object
        model: Model name

    Returns:
        Internal chat response
    """
    if not response or not response.candidates:
      raise ValueError("Gemini response missing candidates")

    choices = []

    for idx, candidate in enumerate(response.candidates):
      if not candidate.content:
        continue

      internal_message = self._convert_gemini_message(
        candidate.content,
        finish_reason=candidate.finish_reason if hasattr(candidate, "finish_reason") else None,
      )

      finish_reason = None
      if hasattr(candidate, "finish_reason") and candidate.finish_reason:
        # Map Gemini finish reasons to our internal format
        finish_reason_map = {
          "STOP": FinishReason.STOP,
          "MAX_TOKENS": FinishReason.LENGTH,
          "SAFETY": FinishReason.CONTENT_FILTER,
          "RECITATION": FinishReason.CONTENT_FILTER,
          "OTHER": FinishReason.STOP,
        }
        finish_reason = finish_reason_map.get(candidate.finish_reason, FinishReason.STOP)

      choices.append(
        Choice(
          index=idx,
          message=internal_message,
          finish_reason=finish_reason,
        )
      )

    usage = None
    if hasattr(response, "usage_metadata") and response.usage_metadata:
      # Handle Gemini's token counting
      # Gemini 2.5 models use thoughts_token_count for thinking/reasoning tokens
      prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", None) or 0
      candidates_tokens = getattr(response.usage_metadata, "candidates_token_count", None) or 0
      thoughts_tokens = getattr(response.usage_metadata, "thoughts_token_count", None) or 0
      total_tokens = getattr(response.usage_metadata, "total_token_count", None) or 0

      # For thinking models (2.5 Pro), completion tokens = candidates + thoughts
      # For non-thinking models, thoughts_token_count is None/0
      completion_tokens = candidates_tokens + thoughts_tokens

      usage = Usage(
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        total_tokens=total_tokens,
      )

    return ChatResponse(
      id=f"gemini-{hash(str(response))}",  # Gemini doesn't provide an ID
      created=0,  # Gemini doesn't provide timestamp
      model=model,
      choices=choices,
      usage=usage,
    )

  async def _handle_streaming_response(
    self,
    model: str,
    messages: List[Content],
    config: GenerateContentConfig,
    **kwargs,
  ) -> AsyncGenerator[StreamChunk, None]:
    """Handle streaming chat response.

    Args:
        model: Model name
        messages: List of Gemini Content objects
        config: Generation config
        **kwargs: Additional parameters

    Yields:
        Stream chunks
    """
    # Start timing
    self.logger.info(f"Starting chat_completion_stream:{model}")
    import time

    start_time = time.time()

    try:
      # Generate content stream returns an awaitable that resolves to an async iterator
      async_stream = await self.client.aio.models.generate_content_stream(  # type: ignore
        model=model,
        contents=messages,
        config=config,
      )

      # Stream chunks following Agno's approach
      async for chunk in async_stream:
        # Process content first
        content_processed = False

        # Check if chunk has .text property directly (simple API)
        if hasattr(chunk, "text") and chunk.text:
          yield StreamChunk(
            id=f"gemini-stream-{id(chunk)}",
            created=0,
            model=model,
            choices=[
              {
                "index": 0,
                "delta": {"content": chunk.text},
                "finish_reason": None,
              }
            ],
          )
          content_processed = True

        # Otherwise parse candidates structure (complex API response)
        if not content_processed and hasattr(chunk, "candidates") and chunk.candidates:
          for candidate in chunk.candidates:
            if not hasattr(candidate, "content") or not candidate.content:
              continue

            content = candidate.content
            if not hasattr(content, "parts") or not content.parts:
              continue

            for part in content.parts:
              # Extract text from part
              if hasattr(part, "text") and part.text:
                # Check if this is a thought/reasoning part (Gemini 2.5 thinking)
                if hasattr(part, "thought") and part.thought:
                  yield StreamChunk(
                    id=f"gemini-stream-{id(chunk)}",
                    created=0,
                    model=model,
                    choices=[
                      {
                        "index": 0,
                        "delta": {"type": "thinking", "content": part.text},
                        "finish_reason": None,
                      }
                    ],
                  )
                else:
                  yield StreamChunk(
                    id=f"gemini-stream-{id(chunk)}",
                    created=0,
                    model=model,
                    choices=[
                      {
                        "index": 0,
                        "delta": {"type": "content", "content": part.text},
                        "finish_reason": None,
                      }
                    ],
                  )
                content_processed = True

            # Send finish reason if available
            if hasattr(candidate, "finish_reason") and candidate.finish_reason:
              finish_reason_map = {
                "STOP": "stop",
                "MAX_TOKENS": "length",
                "SAFETY": "content_filter",
                "RECITATION": "content_filter",
                "OTHER": "stop",
              }
              finish_reason = finish_reason_map.get(str(candidate.finish_reason), "stop")

              yield StreamChunk(
                id=f"gemini-stream-finish-{id(chunk)}",
                created=0,
                model=model,
                choices=[
                  {
                    "index": 0,
                    "delta": {},
                    "finish_reason": finish_reason,
                  }
                ],
              )

        # After processing content, check if this chunk has usage metadata (final chunk)
        if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
          try:
            usage = Usage(
              input_tokens=getattr(chunk.usage_metadata, "prompt_token_count", 0),
              output_tokens=getattr(chunk.usage_metadata, "candidates_token_count", 0),
              total_tokens=getattr(chunk.usage_metadata, "total_token_count", 0),
              cached_tokens=getattr(chunk.usage_metadata, "cached_content_token_count", None),
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

      # Log completion
      elapsed = time.time() - start_time
      self.logger.info(f"Completed chat_completion_stream:{model} in {elapsed:.2f} seconds")

    except (ClientError, ServerError) as e:
      elapsed = time.time() - start_time
      self.logger.error(f"chat_completion_stream:{model} failed after {elapsed:.2f} seconds: {e}")
      raise self._handle_gemini_error(e)
    except Exception as e:
      elapsed = time.time() - start_time
      self.logger.error(f"Gemini streaming failed after {elapsed:.2f} seconds: {e}")
      raise self._handle_gemini_error(e)

  async def generate_image(self, request: ImageRequest, **kwargs) -> ImageResponse:
    """Generate images using Imagen 4.0.

    Args:
        request: Image generation request
        **kwargs: Additional parameters

    Returns:
        Image generation response
    """
    # Check rate limits
    await self._check_rate_limit()

    # Prepare request
    model = request.model or "imagen-4.0-generate-001"

    from google.genai.types import GenerateImagesConfig

    config_params = {
      "number_of_images": request.n,
    }

    # Gemini uses different parameters than OpenAI
    # No direct "quality" mapping - Gemini uses guidance_scale, enhance_prompt, etc.
    # Note: aspect_ratio would need to be passed properly based on size

    config = GenerateImagesConfig(**config_params)  # type: ignore[arg-type]

    try:
      async with self._timed_request(
        f"image_generation:{model}",
        timeout=kwargs.get("timeout", 90.0),
      ):
        response = await self.client.aio.models.generate_images(  # type: ignore
          model=model,
          prompt=request.prompt,
          config=config,
        )

      if hasattr(response, "usage_metadata") and response.usage_metadata:
        # Handle Gemini's token counting (for future use)
        pass

      image_data = []

      # Get GCP client if upload is requested (check both request object and kwargs)
      gcp = None
      upload_to_gcp = request.upload_to_gcp or kwargs.get("upload_to_gcp", False)
      if upload_to_gcp:
        gcp = get_gcp_client()
        if not gcp:
          self.logger.warning("GCP upload requested but GCP is not configured properly")

      import time

      timestamp = int(time.time())

      for idx, generated_image in enumerate(getattr(response, "generated_images", [])):
        # Gemini returns GeneratedImage objects with google.genai.types.Image
        import base64

        image_bytes = None

        # Extract bytes from google.genai.types.Image object
        if hasattr(generated_image, "image") and generated_image.image:
          image_obj = generated_image.image

          # Google's Image object has image_bytes attribute with raw bytes
          if hasattr(image_obj, "image_bytes") and image_obj.image_bytes:
            image_bytes = image_obj.image_bytes
          else:
            self.logger.error("Image object missing image_bytes attribute")

        if image_bytes:
          b64_image: Optional[str] = base64.b64encode(bytes(image_bytes)).decode("utf-8")
          url: Optional[str] = None

          # Upload to GCP if requested
          if gcp:
            try:
              gcp_key = f"images/imagen_{model.replace('-', '_')}_{timestamp}_{idx}.png"
              url = await gcp.upload_file(
                file=bytes(image_bytes),
                key=gcp_key,
                content_type="image/png",
              )
              # Only clear base64 if we got a valid URL back
              if url:
                b64_image = None  # Clear b64_json since we uploaded to GCP
              else:
                self.logger.warning("GCP upload returned empty URL, keeping base64")
                url = None
            except GCPUploadError as e:
              self.logger.error(f"GCP upload failed for Imagen: {e}")
              url = None
              # Keep base64 as fallback
            except Exception as e:
              self.logger.error(f"Unexpected error during Imagen GCP upload: {e}")
              url = None
              # Keep base64 as fallback

          image_data.append(
            ImageData(
              url=url,
              b64_json=b64_image,
            )
          )
        else:
          self.logger.warning(f"Could not extract image bytes from generated_image: {type(getattr(generated_image, 'image', None))}")

      return ImageResponse(
        created=0,  # Gemini doesn't provide timestamp
        data=image_data,
      )

    except Exception as e:
      self.logger.error(f"Gemini image generation failed: {e}")
      raise self._handle_gemini_error(e)

  async def generate_video(self, prompt: str, model: str = "veo-3.0-generate-001", **kwargs):
    """Generate videos using Veo 3.0.

    Args:
        prompt: Video generation prompt
        model: Model to use for video generation
        **kwargs: Additional parameters

    Returns:
        Video generation response
    """
    # Check rate limits
    await self._check_rate_limit()

    try:
      async with self._timed_request(
        f"video_generation:{model}",
        timeout=kwargs.get("timeout", 180.0),  # Longer timeout for video
      ):
        import asyncio

        # Generate videos returns an operation that needs to be polled
        operation = await self.client.aio.models.generate_videos(  # type: ignore
          model=model,
          prompt=prompt,
        )

        # Poll the operation until it's done (similar to official docs)
        max_wait_time = kwargs.get("timeout", 180.0)
        start_time = asyncio.get_event_loop().time()
        poll_interval = 5  # seconds

        # Log initial operation state
        self.logger.info(
          "Video operation started",
          operation_type=type(operation).__name__,
          is_done=getattr(operation, "done", None),
          has_name=hasattr(operation, "name"),
        )

        while not operation.done:
          elapsed = asyncio.get_event_loop().time() - start_time
          if elapsed > max_wait_time:
            raise TimeoutError(f"Video generation timed out after {max_wait_time} seconds")

          self.logger.info(f"Waiting for video generation to complete... ({int(elapsed)}s elapsed)")
          await asyncio.sleep(poll_interval)
          # Refresh operation status using the operation object directly
          operation = await self.client.aio.operations.get(operation)  # type: ignore

        # Check if operation completed with an error
        if hasattr(operation, "error") and operation.error:
          error_message = getattr(operation.error, "message", str(operation.error))
          self.logger.error(f"Video generation failed with error: {error_message}")
          raise InvalidRequestError(f"Unable to generate video: {error_message}. Please try a different prompt.")

        # Check if operation has a response
        if not hasattr(operation, "response") or not operation.response:
          self.logger.error("Video generation completed but no response was returned")
          raise InvalidRequestError("Unable to generate video for this prompt. The content may violate safety policies. Please try another prompt.")

        # Check if response has generated videos
        if not hasattr(operation.response, "generated_videos") or not operation.response.generated_videos:
          self.logger.warning("Video generation completed but no videos were generated")
          raise InvalidRequestError("Unable to generate video for this prompt. The content may violate safety policies. Please try another prompt.")

        # Extract video data from completed operation
        videos = []

        # Get GCP client if upload is requested
        gcp = None
        if kwargs.get("upload_to_gcp", False) is True:
          gcp = get_gcp_client()
          if not gcp:
            self.logger.warning("GCP upload requested but GCP is not configured properly")

        import time

        timestamp = int(time.time())

        for idx, generated_video in enumerate(operation.response.generated_videos):
          # Validate that generated_video has video object
          if not hasattr(generated_video, "video") or not generated_video.video:
            self.logger.warning(f"Generated video at index {idx} has no video object")
            continue

          # Get video object
          video_obj = generated_video.video
          video_uri = video_obj.uri if hasattr(video_obj, "uri") else None
          mime_type = video_obj.mime_type if hasattr(video_obj, "mime_type") else None

          # Upload to GCP if requested
          gcp_url = None
          if gcp:
            try:
              # Download video bytes
              video_bytes = await self.download_video_bytes(video_obj)
              gcp_key = f"videos/veo_{model.replace('-', '_')}_{timestamp}_{idx}.mp4"
              gcp_url = await gcp.upload_file(
                file=video_bytes,
                key=gcp_key,
                content_type=mime_type or "video/mp4",
              )
              self.logger.info(f"Successfully uploaded video to GCP: {gcp_key}")
            except GCPUploadError as e:
              self.logger.error(f"GCP upload failed for Veo video: {e}")
            except Exception as e:
              self.logger.error(f"Unexpected error during Veo video GCP upload: {e}")

          video_info = {
            "video": video_obj,
            "uri": video_uri,
            "mime_type": mime_type,
            "gcp_url": gcp_url,
          }
          videos.append(video_info)

        # Final check - if no videos were successfully extracted
        if not videos:
          raise InvalidRequestError("Unable to generate video for this prompt. Please try another prompt.")

        # Log for debugging
        self.logger.info(
          "Video generation completed",
          video_count=len(videos),
          operation_done=operation.done,
        )

        return {"videos": videos, "model": model, "operation": operation}

    except Exception as e:
      self.logger.error(f"Gemini video generation failed: {e}")
      raise self._handle_gemini_error(e)

  async def download_video_bytes(self, video_obj) -> bytes:
    """Download video and return as bytes.

    Args:
        video_obj: Video object from generate_video response

    Returns:
        Video file bytes
    """
    import asyncio
    import tempfile
    import os
    from functools import partial

    if not self.client:
      raise Exception("Gemini client not initialized")

    try:
      # Download to temp file first (Google SDK requires file path)
      with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        temp_path = tmp.name

      try:
        # Download using Google SDK (sync call)
        loop = asyncio.get_event_loop()
        download_func = partial(self.client.files.download, file=video_obj)
        await loop.run_in_executor(None, download_func)

        # Save to temp file
        save_func = partial(video_obj.save, temp_path)
        await loop.run_in_executor(None, save_func)

        # Read bytes
        with open(temp_path, "rb") as f:
          video_bytes = f.read()

        self.logger.info(f"Downloaded video: {len(video_bytes)} bytes ({len(video_bytes) / 1024 / 1024:.2f} MB)")
        return video_bytes

      finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
          os.unlink(temp_path)

    except Exception as e:
      self.logger.error(f"Failed to download video bytes: {e}")
      raise

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

    model = request.model or "gemini-embedding-001"

    from google.genai.types import EmbedContentConfig

    config = None
    if request.task_type or request.title:
      try:  # noqa: SIM105
        from google.genai.types import TaskType  # type: ignore[attr-defined, no-redef]
      except (ImportError, AttributeError):
        TaskType = None  # type: ignore[assignment, misc]

      if request.task_type and TaskType:
        # Map task types
        task_type_map = {
          "RETRIEVAL_QUERY": TaskType.RETRIEVAL_QUERY,
          "RETRIEVAL_DOCUMENT": TaskType.RETRIEVAL_DOCUMENT,
          "SEMANTIC_SIMILARITY": TaskType.SEMANTIC_SIMILARITY,
          "CLASSIFICATION": TaskType.CLASSIFICATION,
          "CLUSTERING": TaskType.CLUSTERING,
        }
        task_type = task_type_map.get(request.task_type, TaskType.RETRIEVAL_DOCUMENT)
        config = EmbedContentConfig(task_type=task_type, title=request.title)
      elif request.title:
        config = EmbedContentConfig(title=request.title)

    try:
      async with self._timed_request(
        f"embedding:{model}",
        timeout=kwargs.get("timeout", 30.0),
      ):
        # Handle both string and list inputs
        inputs = request.input if isinstance(request.input, list) else [request.input]

        embeddings = []
        for idx, text in enumerate(inputs):
          response = await self.client.aio.models.embed_content(  # type: ignore
            model=model,
            contents=text,
            config=config,
          )

          embedding_values = response.embeddings[0].values if response.embeddings and response.embeddings[0].values else []
          embeddings.append(
            Embedding(
              index=idx,
              embedding=embedding_values,
            )
          )

        # Estimate usage (Gemini doesn't provide token counts for embeddings)
        total_tokens = sum(len(str(inp)) // 4 for inp in inputs)
        usage = Usage(
          input_tokens=total_tokens,
          output_tokens=0,
          total_tokens=total_tokens,
        )

        return EmbeddingResponse(
          data=embeddings,
          model=model,
          usage=usage,
        )

    except Exception as e:
      self.logger.error(f"Gemini embedding generation failed: {e}")
      raise self._handle_gemini_error(e)

  async def health_check(self) -> bool:
    """Check if Gemini service is accessible.

    Returns:
        True if service is healthy
    """
    try:
      # Simple embedding request to check connectivity
      test_request = EmbeddingRequest(input="health check")
      await self.generate_embedding(test_request)
      return True
    except Exception as e:
      self.logger.error(f"Gemini health check failed: {e}")
      return False

  async def close(self):
    """Close the Gemini client and cleanup resources."""
    if self._closed:
      return

    try:
      if hasattr(self, "client") and self.client:
        # Gemini's genai.Client may not have an explicit close method
        # but we can clean up by setting it to None
        self.client = None
        self.logger.debug("Closed Gemini client")
    except Exception as e:
      self.logger.error(f"Error closing Gemini client: {e}")
    finally:
      self._closed = True
