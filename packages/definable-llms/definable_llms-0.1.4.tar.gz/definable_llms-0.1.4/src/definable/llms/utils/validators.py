"""Input validation utilities for the LLM library."""

import re
import mimetypes
from typing import Optional, List, Union
from pathlib import Path
import structlog

from ..base.types import Message, MessageRole, ContentType
from ..base.exceptions import (
  InvalidRequestError,
  FileSizeError,
  UnsupportedFileTypeError,
)


logger = structlog.get_logger()


class MessageValidator:
  """Validator for chat messages."""

  @staticmethod
  def validate_message(message: Message) -> None:
    """Validate a single message.

    Args:
        message: Message to validate

    Raises:
        InvalidRequestError: If message is invalid
    """
    # Validate role
    if message.role not in MessageRole:
      raise InvalidRequestError(f"Invalid message role: {message.role}", field="role")

    # Validate content
    if message.content is None:
      raise InvalidRequestError("Message content cannot be None", field="content")

    if isinstance(message.content, str):
      if not message.content.strip():
        raise InvalidRequestError("Message content cannot be empty", field="content")
    elif isinstance(message.content, list):
      if not message.content:
        raise InvalidRequestError("Message content list cannot be empty", field="content")

      for content in message.content:
        if content.type not in ContentType:
          raise InvalidRequestError(f"Invalid content type: {content.type}", field="content.type")

        # Validate based on content type
        if content.type == ContentType.TEXT:
          if not content.text or not content.text.strip():
            raise InvalidRequestError("Text content cannot be empty", field="content.text")
        elif content.type == ContentType.IMAGE:
          if not content.image_url and not content.image_base64:
            raise InvalidRequestError(
              "Image content must have either URL or base64 data",
              field="content.image",
            )

    # Validate function calls
    if message.function_call and message.tool_calls:
      raise InvalidRequestError(
        "Cannot have both function_call and tool_calls in the same message",
        field="function_call",
      )

  @staticmethod
  def validate_messages(messages: List[Message]) -> None:
    """Validate a list of messages.

    Args:
        messages: List of messages to validate

    Raises:
        InvalidRequestError: If messages are invalid
    """
    if not messages:
      raise InvalidRequestError("Messages list cannot be empty")

    # Validate each message
    for i, message in enumerate(messages):
      try:
        MessageValidator.validate_message(message)
      except InvalidRequestError as e:
        e.details["message_index"] = i
        raise

    # Validate message sequence
    # First message should typically be system or user
    if messages[0].role not in [MessageRole.SYSTEM, MessageRole.USER]:
      logger.warning(f"First message has role '{messages[0].role}', expected 'system' or 'user'")

    # Check for alternating pattern (optional validation)
    # This is lenient as some providers allow consecutive messages
    # from the same role


class FileValidator:
  """Validator for file uploads and processing."""

  def __init__(self, max_size_mb: int = 50, allowed_extensions: Optional[List[str]] = None):
    """Initialize the file validator.

    Args:
        max_size_mb: Maximum file size in MB
        allowed_extensions: List of allowed file extensions
    """
    self.max_size_bytes = max_size_mb * 1024 * 1024
    self.allowed_extensions = allowed_extensions or [
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
    ]

  def validate_file(self, filename: str, size: int, content_type: Optional[str] = None) -> None:
    """Validate a file.

    Args:
        filename: Name of the file
        size: Size of the file in bytes
        content_type: MIME type of the file

    Raises:
        FileSizeError: If file is too large
        UnsupportedFileTypeError: If file type is not supported
    """
    # Check file size
    if size > self.max_size_bytes:
      raise FileSizeError(filename, size, self.max_size_bytes)

    # Check file extension
    file_path = Path(filename)
    extension = file_path.suffix.lower()

    if extension not in self.allowed_extensions:
      raise UnsupportedFileTypeError(filename, extension, self.allowed_extensions)

    # Validate content type if provided
    if content_type:
      expected_type, _ = mimetypes.guess_type(filename)
      if expected_type and content_type != expected_type:
        logger.warning(f"Content type mismatch for {filename}: expected {expected_type}, got {content_type}")

  def validate_file_path(self, file_path: Union[str, Path]) -> None:
    """Validate a file path.

    Args:
        file_path: Path to the file

    Raises:
        InvalidRequestError: If file path is invalid
        FileSizeError: If file is too large
        UnsupportedFileTypeError: If file type is not supported
    """
    path = Path(file_path)

    # Check if file exists
    if not path.exists():
      raise InvalidRequestError(f"File not found: {file_path}")

    # Check if it's a file (not a directory)
    if not path.is_file():
      raise InvalidRequestError(f"Path is not a file: {file_path}")

    # Validate file
    self.validate_file(path.name, path.stat().st_size)


class ParameterValidator:
  """Validator for request parameters."""

  @staticmethod
  def validate_temperature(temperature: Optional[float]) -> None:
    """Validate temperature parameter.

    Args:
        temperature: Temperature value

    Raises:
        InvalidRequestError: If temperature is invalid
    """
    if temperature is not None:
      if not 0.0 <= temperature <= 2.0:
        raise InvalidRequestError(
          f"Temperature must be between 0.0 and 2.0, got {temperature}",
          field="temperature",
        )

  @staticmethod
  def validate_max_tokens(max_tokens: Optional[int], max_limit: int = 128000) -> None:
    """Validate max_tokens parameter.

    Args:
        max_tokens: Maximum tokens value
        max_limit: Maximum allowed limit

    Raises:
        InvalidRequestError: If max_tokens is invalid
    """
    if max_tokens is not None:
      if max_tokens <= 0:
        raise InvalidRequestError(f"max_tokens must be positive, got {max_tokens}", field="max_tokens")
      if max_tokens > max_limit:
        raise InvalidRequestError(
          f"max_tokens exceeds limit of {max_limit}, got {max_tokens}",
          field="max_tokens",
        )

  @staticmethod
  def validate_top_p(top_p: Optional[float]) -> None:
    """Validate top_p parameter.

    Args:
        top_p: Top-p value

    Raises:
        InvalidRequestError: If top_p is invalid
    """
    if top_p is not None:
      if not 0.0 <= top_p <= 1.0:
        raise InvalidRequestError(f"top_p must be between 0.0 and 1.0, got {top_p}", field="top_p")

  @staticmethod
  def validate_frequency_penalty(frequency_penalty: Optional[float]) -> None:
    """Validate frequency_penalty parameter.

    Args:
        frequency_penalty: Frequency penalty value

    Raises:
        InvalidRequestError: If frequency_penalty is invalid
    """
    if frequency_penalty is not None:
      if not -2.0 <= frequency_penalty <= 2.0:
        raise InvalidRequestError(
          f"frequency_penalty must be between -2.0 and 2.0, got {frequency_penalty}",
          field="frequency_penalty",
        )

  @staticmethod
  def validate_presence_penalty(presence_penalty: Optional[float]) -> None:
    """Validate presence_penalty parameter.

    Args:
        presence_penalty: Presence penalty value

    Raises:
        InvalidRequestError: If presence_penalty is invalid
    """
    if presence_penalty is not None:
      if not -2.0 <= presence_penalty <= 2.0:
        raise InvalidRequestError(
          f"presence_penalty must be between -2.0 and 2.0, got {presence_penalty}",
          field="presence_penalty",
        )

  @staticmethod
  def validate_n(n: Optional[int]) -> None:
    """Validate n parameter (number of completions).

    Args:
        n: Number of completions

    Raises:
        InvalidRequestError: If n is invalid
    """
    if n is not None:
      if n <= 0:
        raise InvalidRequestError(f"n must be positive, got {n}", field="n")
      if n > 10:
        raise InvalidRequestError(f"n cannot exceed 10, got {n}", field="n")


class URLValidator:
  """Validator for URLs."""

  # URL regex pattern
  URL_PATTERN = re.compile(
    r"^https?://"  # http:// or https://
    r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
    r"localhost|"  # localhost...
    r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
    r"(?::\d+)?"  # optional port
    r"(?:/?|[/?]\S+)$",
    re.IGNORECASE,
  )

  @classmethod
  def validate_url(cls, url: str) -> None:
    """Validate a URL.

    Args:
        url: URL to validate

    Raises:
        InvalidRequestError: If URL is invalid
    """
    if not url:
      raise InvalidRequestError("URL cannot be empty")

    if not cls.URL_PATTERN.match(url):
      raise InvalidRequestError(f"Invalid URL format: {url}")

  @classmethod
  def validate_mcp_url(cls, url: str) -> None:
    """Validate an MCP URL.

    Args:
        url: MCP URL to validate

    Raises:
        InvalidRequestError: If MCP URL is invalid
    """
    if not url:
      raise InvalidRequestError("MCP URL cannot be empty")

    # MCP URLs should start with mcp:// or be a valid HTTP(S) URL
    if not (url.startswith("mcp://") or cls.URL_PATTERN.match(url)):
      raise InvalidRequestError(f"Invalid MCP URL format: {url}")


class ModelValidator:
  """Validator for model names."""

  # Common model patterns
  OPENAI_MODELS = [
    "gpt-4",
    "gpt-4-turbo",
    "gpt-4-turbo-preview",
    "gpt-3.5-turbo",
    "gpt-3.5-turbo-16k",
    "text-embedding-ada-002",
    "text-embedding-3-small",
    "text-embedding-3-large",
    "dall-e-2",
    "dall-e-3",
  ]

  ANTHROPIC_MODELS = [
    "claude-3-opus",
    "claude-3-sonnet",
    "claude-3-haiku",
    "claude-2.1",
    "claude-2.0",
    "claude-instant-1.2",
  ]

  GEMINI_MODELS = ["gemini-pro", "gemini-pro-vision", "gemini-ultra"]

  @classmethod
  def validate_model_name(cls, model: str, provider: Optional[str] = None) -> None:
    """Validate a model name.

    Args:
        model: Model name to validate
        provider: Optional provider name for provider-specific validation

    Raises:
        InvalidRequestError: If model name is invalid
    """
    if not model:
      raise InvalidRequestError("Model name cannot be empty")

    # Basic validation - ensure it's a reasonable model name
    if not re.match(r"^[a-zA-Z0-9_.-]+$", model):
      raise InvalidRequestError(f"Invalid model name format: {model}", field="model")

    # Provider-specific validation (optional, just warnings)
    if provider:
      provider_lower = provider.lower()

      if provider_lower == "openai":
        if not any(model.startswith(prefix) for prefix in cls.OPENAI_MODELS):
          logger.warning(f"Unusual OpenAI model name: {model}")

      elif provider_lower == "anthropic":
        if not any(model.startswith(prefix) for prefix in cls.ANTHROPIC_MODELS):
          logger.warning(f"Unusual Anthropic model name: {model}")

      elif provider_lower == "gemini":
        if not any(model.startswith(prefix) for prefix in cls.GEMINI_MODELS):
          logger.warning(f"Unusual Gemini model name: {model}")
