"""Logging configuration for the LLM library."""

import sys
import structlog
from typing import Optional
from pathlib import Path
import logging


def configure_logging(log_level: str = "INFO", log_file: Optional[Path] = None, json_logs: bool = False) -> None:
  """Configure structured logging for the library.

  Args:
      log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
      log_file: Optional path to log file
      json_logs: Whether to output logs in JSON format
  """
  # Configure standard library logging
  logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=getattr(logging, log_level.upper()),
  )

  # Configure structlog processors
  from typing import Any

  processors: list[Any] = [
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
  ]

  if json_logs:
    processors.append(structlog.processors.JSONRenderer())
  else:
    processors.append(structlog.dev.ConsoleRenderer())

  # Configure structlog
  structlog.configure(
    processors=processors,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
  )

  # Add file handler if specified
  if log_file:
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level.upper()))

    if json_logs:
      formatter: Any = structlog.stdlib.ProcessorFormatter(processor=structlog.processors.JSONRenderer())
    else:
      formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler.setFormatter(formatter)
    logging.getLogger().addHandler(file_handler)


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
  """Get a configured logger instance.

  Args:
      name: Optional logger name

  Returns:
      Configured logger instance
  """
  return structlog.get_logger(name)


class LogContext:
  """Context manager for temporary logging context."""

  def __init__(self, **kwargs):
    """Initialize log context with key-value pairs."""
    self.context = kwargs
    self.logger = None

  def __enter__(self):
    """Enter the context."""
    self.logger = structlog.get_logger()
    return self.logger.bind(**self.context)

  def __exit__(self, exc_type, exc_val, exc_tb):
    """Exit the context."""
    if exc_type is not None and self.logger:
      self.logger.error(
        "Error in context",
        exc_type=exc_type.__name__,
        exc_value=str(exc_val),
        **self.context,
      )
    return False
