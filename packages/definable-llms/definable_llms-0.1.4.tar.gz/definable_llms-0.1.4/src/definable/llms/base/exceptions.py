"""Custom exceptions for the LLM library."""

from typing import Optional, Dict, Any


class LLMException(Exception):
  """Base exception for all LLM library errors."""

  def __init__(
    self,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500,
  ):
    super().__init__(message)
    self.message = message
    self.error_code = error_code or self.__class__.__name__
    self.details = details or {}
    self.status_code = status_code

  def to_dict(self) -> Dict[str, Any]:
    """Convert exception to dictionary for API responses."""
    return {
      "error": self.error_code,
      "message": self.message,
      "details": self.details,
      "status_code": self.status_code,
    }


class ConfigurationError(LLMException):
  """Raised when there's a configuration issue."""

  def __init__(self, message: str, **kwargs):
    super().__init__(message, status_code=500, **kwargs)


class ProviderError(LLMException):
  """Base exception for provider-related errors."""

  def __init__(self, provider: str, message: str, **kwargs):
    super().__init__(message, **kwargs)
    self.provider = provider
    self.details["provider"] = provider


class ProviderNotFoundError(ProviderError):
  """Raised when a provider is not found or not configured."""

  def __init__(self, provider: str):
    super().__init__(
      provider,
      f"Provider '{provider}' not found or not configured",
      status_code=404,
    )


class ProviderAuthenticationError(ProviderError):
  """Raised when provider authentication fails."""

  def __init__(self, provider: str, message: Optional[str] = None):
    super().__init__(
      provider,
      message or f"Authentication failed for provider '{provider}'",
      status_code=401,
    )


class ProviderRateLimitError(ProviderError):
  """Raised when provider rate limit is exceeded."""

  def __init__(
    self,
    provider: str,
    retry_after: Optional[int] = None,
    message: Optional[str] = None,
  ):
    super().__init__(
      provider,
      message or f"Rate limit exceeded for provider '{provider}'",
      status_code=429,
    )
    if retry_after:
      self.details["retry_after"] = retry_after


class ProviderQuotaExceededError(ProviderError):
  """Raised when provider quota is exceeded."""

  def __init__(self, provider: str, message: Optional[str] = None):
    super().__init__(
      provider,
      message or f"Quota exceeded for provider '{provider}'",
      status_code=402,
    )


class ProviderTimeoutError(ProviderError):
  """Raised when provider request times out."""

  def __init__(self, provider: str, timeout: Optional[float] = None):
    message = f"Request to provider '{provider}' timed out"
    if timeout:
      message += f" after {timeout} seconds"
    super().__init__(provider, message, status_code=504)
    if timeout:
      self.details["timeout"] = timeout


class ModelNotFoundError(ProviderError):
  """Raised when a model is not found or not supported."""

  def __init__(self, provider: str, model: str):
    super().__init__(
      provider,
      f"Model '{model}' not found or not supported by provider '{provider}'",
      status_code=404,
    )
    self.details["model"] = model


class InvalidRequestError(LLMException):
  """Raised when request validation fails."""

  def __init__(self, message: str, field: Optional[str] = None, **kwargs):
    super().__init__(message, status_code=400, **kwargs)
    if field:
      self.details["field"] = field


class SessionError(LLMException):
  """Base exception for session-related errors."""

  def __init__(self, session_id: str, message: str, **kwargs):
    super().__init__(message, **kwargs)
    self.session_id = session_id
    self.details["session_id"] = session_id


class SessionNotFoundError(SessionError):
  """Raised when a session is not found."""

  def __init__(self, session_id: str):
    super().__init__(session_id, f"Session '{session_id}' not found", status_code=404)


class SessionExpiredError(SessionError):
  """Raised when a session has expired."""

  def __init__(self, session_id: str):
    super().__init__(session_id, f"Session '{session_id}' has expired", status_code=410)


class FileProcessingError(LLMException):
  """Raised when file processing fails."""

  def __init__(self, filename: str, message: str, file_type: Optional[str] = None, **kwargs):
    super().__init__(message, status_code=422, **kwargs)
    self.filename = filename
    self.details["filename"] = filename
    if file_type:
      self.details["file_type"] = file_type


class FileSizeError(FileProcessingError):
  """Raised when file size exceeds limits."""

  def __init__(self, filename: str, size: int, max_size: int):
    super().__init__(
      filename,
      f"File '{filename}' size ({size} bytes) exceeds maximum allowed size ({max_size} bytes)",
    )
    self.details.update({"size": size, "max_size": max_size})


class UnsupportedFileTypeError(FileProcessingError):
  """Raised when file type is not supported."""

  def __init__(self, filename: str, file_type: str, supported_types: list):
    super().__init__(filename, f"File type '{file_type}' is not supported", file_type=file_type)
    self.details["supported_types"] = supported_types


class ContentFilterError(LLMException):
  """Raised when content is filtered for safety reasons."""

  def __init__(
    self,
    message: str = "Content was filtered due to safety concerns",
    category: Optional[str] = None,
    **kwargs,
  ):
    super().__init__(message, status_code=451, **kwargs)
    if category:
      self.details["category"] = category


class TokenLimitError(LLMException):
  """Raised when token limit is exceeded."""

  def __init__(self, message: str, used_tokens: int, max_tokens: int, **kwargs):
    super().__init__(message, status_code=413, **kwargs)
    self.details.update({"used_tokens": used_tokens, "max_tokens": max_tokens})


class StreamingError(LLMException):
  """Raised when streaming fails."""

  def __init__(self, message: str, **kwargs):
    super().__init__(message, status_code=500, **kwargs)


class EmbeddingError(LLMException):
  """Raised when embedding generation fails."""

  def __init__(self, message: str, **kwargs):
    super().__init__(message, status_code=500, **kwargs)


class KnowledgeBaseError(LLMException):
  """Raised when knowledge base operations fail."""

  def __init__(self, message: str, kb_id: Optional[str] = None, **kwargs):
    super().__init__(message, status_code=500, **kwargs)
    if kb_id:
      self.details["kb_id"] = kb_id


class MCPError(LLMException):
  """Raised when MCP operations fail."""

  def __init__(self, message: str, url: Optional[str] = None, **kwargs):
    super().__init__(message, status_code=500, **kwargs)
    if url:
      self.details["mcp_url"] = url


class RetryableError(LLMException):
  """Base class for errors that can be retried."""

  def __init__(self, message: str, retry_after: Optional[float] = None, **kwargs):
    super().__init__(message, **kwargs)
    self.retry_after = retry_after
    if retry_after:
      self.details["retry_after"] = retry_after


class NetworkError(RetryableError):
  """Raised when network operations fail."""

  def __init__(self, message: str = "Network error occurred", **kwargs):
    super().__init__(message, status_code=503, **kwargs)


class ServiceUnavailableError(RetryableError):
  """Raised when service is temporarily unavailable."""

  def __init__(self, service: str, message: Optional[str] = None, **kwargs):
    super().__init__(
      message or f"Service '{service}' is temporarily unavailable",
      status_code=503,
      **kwargs,
    )
    self.details["service"] = service
