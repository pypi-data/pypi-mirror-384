"""FastAPI application for the LLM library."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import structlog

from ..config import settings
from ..base.exceptions import LLMException
from ..utils.logger import configure_logging
from .routes import chat, sessions, files, health, providers
from .middleware.rate_limit import RateLimitMiddleware
from .middleware.auth import AuthMiddleware


logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
  """Application lifespan manager."""
  # Startup
  configure_logging(settings.log_level.value, json_logs=not settings.debug)
  logger.info("Starting LLM Library API", version=settings.app_version)

  # Startup health checks could go here

  yield

  # Shutdown
  logger.info("Shutting down LLM Library API")


def create_app() -> FastAPI:
  """Create and configure the FastAPI application."""

  app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Scalable multi-provider LLM library for definable.ai",
    debug=settings.debug,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
  )

  # Add CORS middleware
  if settings.cors_enabled:
    app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.cors_origins,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
    )

  # Add authentication middleware
  if settings.require_api_key:
    app.add_middleware(AuthMiddleware)

  # Add rate limiting middleware
  if settings.rate_limit_enabled:
    app.add_middleware(RateLimitMiddleware)

  # Exception handler for LLM exceptions
  @app.exception_handler(LLMException)
  async def llm_exception_handler(request: Request, exc: LLMException):
    """Handle LLM library exceptions."""
    logger.error(
      f"LLM Exception: {exc.error_code}",
      message=exc.message,
      details=exc.details,
      status_code=exc.status_code,
    )

    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())

  # General exception handler
  @app.exception_handler(Exception)
  async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    return JSONResponse(
      status_code=500,
      content={
        "error": "InternalServerError",
        "message": "An unexpected error occurred",
        "details": {"error": str(exc)} if settings.debug else {},
        "status_code": 500,
      },
    )

  # Include routers
  app.include_router(health.router, prefix=settings.api_prefix, tags=["Health"])

  app.include_router(providers.router, prefix=settings.api_prefix, tags=["Providers"])

  app.include_router(sessions.router, prefix=settings.api_prefix, tags=["Sessions"])

  app.include_router(chat.router, prefix=settings.api_prefix, tags=["Chat"])

  app.include_router(files.router, prefix=settings.api_prefix, tags=["Files"])

  from .routes import research

  app.include_router(research.router, prefix=settings.api_prefix, tags=["Research"])

  # Root endpoint
  @app.get("/")
  async def root():
    """Root endpoint with API information."""
    return {
      "name": settings.app_name,
      "version": settings.app_version,
      "description": "Scalable multi-provider LLM library for definable.ai",
      "docs_url": "/docs" if settings.debug else None,
      "api_prefix": settings.api_prefix,
    }

  return app


# Create the app instance
app = create_app()


def run_server(host: Optional[str] = None, port: Optional[int] = None, reload: Optional[bool] = None, workers: int = 1):
  """Run the FastAPI server.

  Args:
      host: Host to bind to
      port: Port to bind to
      reload: Enable auto-reload
      workers: Number of worker processes
  """
  uvicorn.run(
    app,  # Use the app instance directly
    host=host or settings.api_host,
    port=port or settings.api_port,
    reload=False,  # Disable reload to avoid import warnings
    workers=workers,
    log_level=settings.log_level.value.lower(),
  )
