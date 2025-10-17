"""Retry utilities for the LLM library."""

import asyncio
import random
import time
from typing import TypeVar, Callable, Optional, Tuple, Type, Any, Dict, Awaitable
from functools import wraps
import structlog

from ..base.exceptions import (
  RetryableError,
  NetworkError,
  ProviderRateLimitError,
  ProviderTimeoutError,
  ServiceUnavailableError,
)


logger = structlog.get_logger()

T = TypeVar("T")


class RetryStrategy:
  """Base class for retry strategies."""

  def get_delay(self, attempt: int) -> float:
    """Get the delay for the next retry attempt.

    Args:
        attempt: Current attempt number (1-based)

    Returns:
        Delay in seconds
    """
    raise NotImplementedError


class ExponentialBackoff(RetryStrategy):
  """Exponential backoff retry strategy."""

  def __init__(
    self,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
  ):
    """Initialize exponential backoff strategy.

    Args:
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential calculation
        jitter: Whether to add random jitter
    """
    self.initial_delay = initial_delay
    self.max_delay = max_delay
    self.exponential_base = exponential_base
    self.jitter = jitter

  def get_delay(self, attempt: int) -> float:
    """Get the delay for the next retry attempt.

    Args:
        attempt: Current attempt number (1-based)

    Returns:
        Delay in seconds
    """
    delay = min(
      self.initial_delay * (self.exponential_base ** (attempt - 1)),
      self.max_delay,
    )

    if self.jitter:
      # Add random jitter (0-25% of delay)
      delay = delay * (1 + random.random() * 0.25)

    return delay


class LinearBackoff(RetryStrategy):
  """Linear backoff retry strategy."""

  def __init__(
    self,
    initial_delay: float = 1.0,
    increment: float = 1.0,
    max_delay: float = 60.0,
  ):
    """Initialize linear backoff strategy.

    Args:
        initial_delay: Initial delay in seconds
        increment: Increment for each retry
        max_delay: Maximum delay in seconds
    """
    self.initial_delay = initial_delay
    self.increment = increment
    self.max_delay = max_delay

  def get_delay(self, attempt: int) -> float:
    """Get the delay for the next retry attempt.

    Args:
        attempt: Current attempt number (1-based)

    Returns:
        Delay in seconds
    """
    delay = self.initial_delay + (attempt - 1) * self.increment
    return min(delay, self.max_delay)


class FixedDelay(RetryStrategy):
  """Fixed delay retry strategy."""

  def __init__(self, delay: float = 1.0):
    """Initialize fixed delay strategy.

    Args:
        delay: Fixed delay in seconds
    """
    self.delay = delay

  def get_delay(self, attempt: int) -> float:
    """Get the delay for the next retry attempt.

    Args:
        attempt: Current attempt number (1-based)

    Returns:
        Delay in seconds
    """
    return self.delay


class RetryConfig:
  """Configuration for retry behavior."""

  def __init__(
    self,
    max_attempts: int = 3,
    strategy: Optional[RetryStrategy] = None,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
  ):
    """Initialize retry configuration.

    Args:
        max_attempts: Maximum number of retry attempts
        strategy: Retry strategy to use
        retryable_exceptions: Tuple of exceptions to retry on
        on_retry: Callback function called on each retry
    """
    self.max_attempts = max_attempts
    self.strategy = strategy or ExponentialBackoff()
    self.retryable_exceptions = retryable_exceptions or (
      RetryableError,
      NetworkError,
      ProviderRateLimitError,
      ProviderTimeoutError,
      ServiceUnavailableError,
      asyncio.TimeoutError,
      ConnectionError,
    )
    self.on_retry = on_retry


async def retry_async(func: Callable[..., Awaitable[T]], config: Optional[RetryConfig] = None, *args, **kwargs) -> T:
  """Retry an async function with the specified configuration.

  Args:
      func: Async function to retry
      config: Retry configuration
      *args: Positional arguments for the function
      **kwargs: Keyword arguments for the function

  Returns:
      Result from the function

  Raises:
      The last exception if all retries fail
  """
  config = config or RetryConfig()
  last_exception = None

  for attempt in range(1, config.max_attempts + 1):
    try:
      return await func(*args, **kwargs)

    except config.retryable_exceptions as e:
      last_exception = e

      # Check if this is a rate limit error with retry_after
      if isinstance(e, ProviderRateLimitError) and hasattr(e, "retry_after"):
        delay = e.retry_after
      elif isinstance(e, RetryableError) and hasattr(e, "retry_after"):
        delay = e.retry_after
      else:
        delay = config.strategy.get_delay(attempt)

      if attempt < config.max_attempts:
        logger.warning(f"Retry {attempt}/{config.max_attempts} after {delay:.2f}s: {e}")

        # Call the retry callback if provided
        if config.on_retry:
          config.on_retry(e, attempt)

        await asyncio.sleep(delay)
      else:
        logger.error(f"All {config.max_attempts} retry attempts failed")
        raise

  # This should never be reached, but just in case
  if last_exception:
    raise last_exception
  raise RuntimeError("Unexpected retry logic error")


def retry_sync(func: Callable[..., T], config: Optional[RetryConfig] = None, *args, **kwargs) -> T:
  """Retry a synchronous function with the specified configuration.

  Args:
      func: Function to retry
      config: Retry configuration
      *args: Positional arguments for the function
      **kwargs: Keyword arguments for the function

  Returns:
      Result from the function

  Raises:
      The last exception if all retries fail
  """
  config = config or RetryConfig()
  last_exception = None

  for attempt in range(1, config.max_attempts + 1):
    try:
      return func(*args, **kwargs)

    except config.retryable_exceptions as e:
      last_exception = e

      # Check if this is a rate limit error with retry_after
      if isinstance(e, ProviderRateLimitError) and hasattr(e, "retry_after"):
        delay = e.retry_after
      elif isinstance(e, RetryableError) and hasattr(e, "retry_after"):
        delay = e.retry_after
      else:
        delay = config.strategy.get_delay(attempt)

      if attempt < config.max_attempts:
        logger.warning(f"Retry {attempt}/{config.max_attempts} after {delay:.2f}s: {e}")

        # Call the retry callback if provided
        if config.on_retry:
          config.on_retry(e, attempt)

        time.sleep(delay)
      else:
        logger.error(f"All {config.max_attempts} retry attempts failed")
        raise

  # This should never be reached, but just in case
  if last_exception:
    raise last_exception
  raise RuntimeError("Unexpected retry logic error")


def with_retry(config: Optional[RetryConfig] = None):
  """Decorator to add retry logic to a function.

  Args:
      config: Retry configuration

  Returns:
      Decorated function
  """

  def decorator(func: Callable[..., T]) -> Callable[..., Any]:
    if asyncio.iscoroutinefunction(func):

      @wraps(func)
      async def async_wrapper(*args, **kwargs) -> T:
        # Type ignore because func is actually Callable[..., Awaitable[T]]
        return await retry_async(func, config, *args, **kwargs)  # type: ignore

      return async_wrapper
    else:

      @wraps(func)
      def sync_wrapper(*args, **kwargs) -> T:
        return retry_sync(func, config, *args, **kwargs)

      return sync_wrapper

  return decorator


class CircuitBreaker:
  """Circuit breaker pattern for handling failures."""

  def __init__(
    self,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Optional[Type[Exception]] = None,
  ):
    """Initialize circuit breaker.

    Args:
        failure_threshold: Number of failures before opening
        recovery_timeout: Time to wait before attempting recovery
        expected_exception: Exception type to catch
    """
    self.failure_threshold = failure_threshold
    self.recovery_timeout = recovery_timeout
    self.expected_exception = expected_exception or Exception

    self.failure_count = 0
    self.last_failure_time = 0.0
    self.state = "closed"  # closed, open, half-open

    self.logger = logger.bind(component="circuit_breaker")

  def call(self, func: Callable[..., T], *args, **kwargs) -> T:
    """Call a function with circuit breaker protection.

    Args:
        func: Function to call
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Result from the function

    Raises:
        ServiceUnavailableError: If circuit is open
        Original exception: If function fails
    """
    # Check circuit state
    if self.state == "open":
      if time.time() - self.last_failure_time >= self.recovery_timeout:
        self.state = "half-open"
        self.logger.info("Circuit breaker entering half-open state")
      else:
        raise ServiceUnavailableError("circuit_breaker", "Circuit breaker is open")

    try:
      result = func(*args, **kwargs)

      # Reset on success
      if self.state == "half-open":
        self.state = "closed"
        self.failure_count = 0
        self.logger.info("Circuit breaker closed after successful recovery")

      return result

    except self.expected_exception:
      self.failure_count += 1
      self.last_failure_time = time.time()

      if self.failure_count >= self.failure_threshold:
        self.state = "open"
        self.logger.error(f"Circuit breaker opened after {self.failure_count} failures")

      raise

  async def call_async(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
    """Call an async function with circuit breaker protection.

    Args:
        func: Async function to call
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Result from the function

    Raises:
        ServiceUnavailableError: If circuit is open
        Original exception: If function fails
    """
    # Check circuit state
    if self.state == "open":
      if time.time() - self.last_failure_time >= self.recovery_timeout:
        self.state = "half-open"
        self.logger.info("Circuit breaker entering half-open state")
      else:
        raise ServiceUnavailableError("circuit_breaker", "Circuit breaker is open")

    try:
      result = await func(*args, **kwargs)

      # Reset on success
      if self.state == "half-open":
        self.state = "closed"
        self.failure_count = 0
        self.logger.info("Circuit breaker closed after successful recovery")

      return result

    except self.expected_exception:
      self.failure_count += 1
      self.last_failure_time = time.time()

      if self.failure_count >= self.failure_threshold:
        self.state = "open"
        self.logger.error(f"Circuit breaker opened after {self.failure_count} failures")

      raise

  def reset(self):
    """Reset the circuit breaker."""
    self.failure_count = 0
    self.last_failure_time = 0.0
    self.state = "closed"
    self.logger.info("Circuit breaker reset")

  def get_state(self) -> Dict[str, Any]:
    """Get the current state of the circuit breaker.

    Returns:
        Dictionary with state information
    """
    return {
      "state": self.state,
      "failure_count": self.failure_count,
      "failure_threshold": self.failure_threshold,
      "recovery_timeout": self.recovery_timeout,
      "time_since_last_failure": (time.time() - self.last_failure_time if self.last_failure_time > 0 else None),
    }
