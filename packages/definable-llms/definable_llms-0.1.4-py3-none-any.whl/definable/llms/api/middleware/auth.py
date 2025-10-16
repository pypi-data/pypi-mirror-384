"""Authentication middleware for the API."""

from typing import Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

from ...config import settings


logger = structlog.get_logger()


class AuthMiddleware(BaseHTTPMiddleware):
  """Middleware for API key authentication."""

  # Paths that don't require authentication
  EXEMPT_PATHS = [
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
  ]

  def __init__(self, app):
    """Initialize auth middleware."""
    super().__init__(app)
    self.api_keys = set(settings.api_keys) if settings.api_keys else set()
    self.header_name = settings.api_key_header
    self.logger = logger.bind(middleware="auth")

  async def dispatch(self, request: Request, call_next):
    """Process request and check authentication."""

    # Skip authentication for exempt paths
    if self._is_exempt_path(request.url.path):
      return await call_next(request)

    # Skip if no API keys are configured
    if not self.api_keys:
      self.logger.warning("API key authentication enabled but no keys configured")
      return await call_next(request)

    # Extract API key from header
    api_key = self._extract_api_key(request)

    if not api_key:
      return self._auth_error("API key required")

    # Validate API key
    if api_key not in self.api_keys:
      client_host = request.client.host if request.client else "unknown"
      self.logger.warning(f"Invalid API key attempt from {client_host}")
      return self._auth_error("Invalid API key")

    # Add authenticated user info to request state
    request.state.authenticated = True
    request.state.api_key = api_key

    return await call_next(request)

  def _is_exempt_path(self, path: str) -> bool:
    """Check if path is exempt from authentication."""
    for exempt_path in self.EXEMPT_PATHS:
      if path.startswith(exempt_path):
        return True

    # Also check if path starts with API prefix for health endpoint
    health_path = f"{settings.api_prefix}/health"
    if path.startswith(health_path):
      return True

    return False

  def _extract_api_key(self, request: Request) -> Optional[str]:
    """Extract API key from request headers."""
    # Check custom header
    api_key = request.headers.get(self.header_name)

    # Fallback to Authorization header (Bearer token)
    if not api_key:
      auth_header = request.headers.get("Authorization", "")
      if auth_header.startswith("Bearer "):
        api_key = auth_header[7:]  # Remove "Bearer " prefix

    return api_key

  def _auth_error(self, message: str) -> JSONResponse:
    """Return authentication error response."""
    return JSONResponse(
      status_code=status.HTTP_401_UNAUTHORIZED,
      content={
        "error": "AuthenticationError",
        "message": message,
        "details": {
          "header": self.header_name,
          "alternative": "Authorization: Bearer <token>",
        },
        "status_code": 401,
      },
    )
