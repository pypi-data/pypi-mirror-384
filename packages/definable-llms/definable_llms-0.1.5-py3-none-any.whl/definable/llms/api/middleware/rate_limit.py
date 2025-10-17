"""Rate limiting middleware for the API."""

import time
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ...config import settings
from ...utils.rate_limiter import MultiKeyRateLimiter


logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
  """Middleware for rate limiting API requests."""

  def __init__(self, app):
    """Initialize rate limiting middleware."""
    super().__init__(app)
    self.limiter = MultiKeyRateLimiter(
      requests_per_minute=settings.rate_limit_requests_per_minute,
      tokens_per_minute=settings.rate_limit_tokens_per_minute,
    )
    self.logger = logger.bind(middleware="rate_limit")

  async def dispatch(self, request: Request, call_next):
    """Process request and apply rate limiting."""

    # Get client identifier
    client_id = self._get_client_id(request)

    # Estimate tokens for the request (simplified)
    estimated_tokens = self._estimate_request_tokens(request)

    # Check rate limit
    if not self.limiter.try_acquire_request(client_id, estimated_tokens):
      self.logger.warning(f"Rate limit exceeded for client: {client_id}")
      return self._rate_limit_error(client_id)

    # Process request
    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()

    # Add rate limit headers to response
    self._add_rate_limit_headers(response, client_id)

    # Log request
    self.logger.info(
      "Request processed",
      client_id=client_id,
      method=request.method,
      path=request.url.path,
      duration=round(end_time - start_time, 3),
      status_code=response.status_code,
      estimated_tokens=estimated_tokens,
    )

    return response

  def _get_client_id(self, request: Request) -> str:
    """Get client identifier for rate limiting."""
    # Use API key if available (from auth middleware)
    if hasattr(request.state, "api_key") and request.state.api_key:
      return f"api_key:{request.state.api_key}"

    # Use client IP address
    client_host = request.client.host if request.client else "unknown"

    # Check for forwarded IP headers (when behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
      # Take the first IP if multiple are present
      client_host = forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
      client_host = real_ip

    return f"ip:{client_host}"

  def _estimate_request_tokens(self, request: Request) -> int:
    """Estimate token count for a request."""
    # This is a simplified estimation
    # In a real implementation, you might want to parse the request body
    # and estimate tokens based on the content

    path = request.url.path

    # Different endpoints have different token requirements
    if "/chat" in path:
      # Chat endpoints typically use more tokens
      return 100
    elif "/embeddings" in path:
      # Embeddings might use fewer tokens
      return 50
    elif "/images" in path:
      # Image generation has different token requirements
      return 200
    else:
      # Default estimation
      return 10

  def _rate_limit_error(self, client_id: str) -> JSONResponse:
    """Return rate limit error response."""
    # Get current status (for potential future use)
    self.limiter.get_status(client_id)

    return JSONResponse(
      status_code=429,
      content={
        "error": "RateLimitExceeded",
        "message": "Rate limit exceeded. Please try again later.",
        "details": {
          "client_id": client_id,
          "rate_limit": {
            "requests_per_minute": settings.rate_limit_requests_per_minute,
            "tokens_per_minute": settings.rate_limit_tokens_per_minute,
          },
          "retry_after": 60,  # Suggest waiting 60 seconds
        },
        "status_code": 429,
      },
      headers={
        "Retry-After": "60",
        "X-RateLimit-Limit-Requests": str(settings.rate_limit_requests_per_minute),
        "X-RateLimit-Limit-Tokens": str(settings.rate_limit_tokens_per_minute),
        "X-RateLimit-Remaining-Requests": "0",
        "X-RateLimit-Remaining-Tokens": "0",
      },
    )

  def _add_rate_limit_headers(self, response, client_id: str):
    """Add rate limit headers to response."""
    try:
      status = self.limiter.get_status(client_id)

      if "error" not in status:
        # Add rate limit headers
        response.headers["X-RateLimit-Limit-Requests"] = str(settings.rate_limit_requests_per_minute)
        response.headers["X-RateLimit-Limit-Tokens"] = str(settings.rate_limit_tokens_per_minute)

        # Add remaining counts if available
        if "requests" in status:
          response.headers["X-RateLimit-Remaining-Requests"] = str(status["requests"].get("available", 0))

        if "tokens" in status:
          response.headers["X-RateLimit-Remaining-Tokens"] = str(status["tokens"].get("available", 0))

    except Exception as e:
      self.logger.warning(f"Failed to add rate limit headers: {e}")
