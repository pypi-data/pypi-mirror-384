"""Rate limiting utilities for the LLM library."""

import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import structlog


logger = structlog.get_logger()


@dataclass
class TokenBucket:
  """Token bucket for rate limiting."""

  capacity: int
  refill_rate: float  # tokens per second
  tokens: float = field(init=False)
  last_refill: float = field(init=False)

  def __post_init__(self):
    """Initialize the bucket with full capacity."""
    self.tokens = float(self.capacity)
    self.last_refill = time.time()

  def _refill(self):
    """Refill tokens based on elapsed time."""
    now = time.time()
    elapsed = now - self.last_refill
    tokens_to_add = elapsed * self.refill_rate
    self.tokens = min(self.capacity, self.tokens + tokens_to_add)
    self.last_refill = now

  async def acquire(self, tokens: int = 1) -> float:
    """Acquire tokens, waiting if necessary.

    Args:
        tokens: Number of tokens to acquire

    Returns:
        Time waited in seconds
    """
    wait_time = 0.0

    while True:
      self._refill()

      if self.tokens >= tokens:
        self.tokens -= tokens
        return wait_time

      # Calculate time to wait for enough tokens
      tokens_needed = tokens - self.tokens
      time_to_wait = tokens_needed / self.refill_rate

      # Wait for tokens to be available
      await asyncio.sleep(time_to_wait)
      wait_time += time_to_wait

  def try_acquire(self, tokens: int = 1) -> bool:
    """Try to acquire tokens without waiting.

    Args:
        tokens: Number of tokens to acquire

    Returns:
        True if tokens were acquired
    """
    self._refill()

    if self.tokens >= tokens:
      self.tokens -= tokens
      return True

    return False

  @property
  def available_tokens(self) -> int:
    """Get the number of available tokens."""
    self._refill()
    return int(self.tokens)


class RateLimiter:
  """Rate limiter for API requests."""

  def __init__(
    self,
    requests_per_minute: int = 60,
    tokens_per_minute: int = 90000,
    burst_multiplier: float = 1.5,
  ):
    """Initialize the rate limiter.

    Args:
        requests_per_minute: Maximum requests per minute
        tokens_per_minute: Maximum tokens per minute
        burst_multiplier: Multiplier for burst capacity
    """
    self.requests_bucket = TokenBucket(
      capacity=int(requests_per_minute * burst_multiplier),
      refill_rate=requests_per_minute / 60.0,
    )

    self.tokens_bucket = TokenBucket(
      capacity=int(tokens_per_minute * burst_multiplier),
      refill_rate=tokens_per_minute / 60.0,
    )

    self.logger = logger.bind(component="rate_limiter")

  async def acquire_request(self, estimated_tokens: int = 0) -> float:
    """Acquire permission for a request.

    Args:
        estimated_tokens: Estimated tokens for the request

    Returns:
        Total time waited in seconds
    """
    # Acquire request token
    request_wait = await self.requests_bucket.acquire(1)

    # Acquire token tokens if needed
    token_wait = 0.0
    if estimated_tokens > 0:
      token_wait = await self.tokens_bucket.acquire(estimated_tokens)

    total_wait = request_wait + token_wait

    if total_wait > 0:
      self.logger.info(f"Rate limited: waited {total_wait:.2f}s (request: {request_wait:.2f}s, tokens: {token_wait:.2f}s)")

    return total_wait

  def try_acquire_request(self, estimated_tokens: int = 0) -> bool:
    """Try to acquire permission for a request without waiting.

    Args:
        estimated_tokens: Estimated tokens for the request

    Returns:
        True if request can proceed
    """
    # Check request limit
    if not self.requests_bucket.try_acquire(1):
      return False

    # Check token limit if needed
    if estimated_tokens > 0:
      if not self.tokens_bucket.try_acquire(estimated_tokens):
        # Restore request token since we can't proceed
        self.requests_bucket.tokens += 1
        return False

    return True

  def get_status(self) -> Dict[str, Any]:
    """Get the current status of the rate limiter.

    Returns:
        Dictionary with status information
    """
    return {
      "requests": {
        "available": self.requests_bucket.available_tokens,
        "capacity": self.requests_bucket.capacity,
        "refill_rate": self.requests_bucket.refill_rate,
      },
      "tokens": {
        "available": self.tokens_bucket.available_tokens,
        "capacity": self.tokens_bucket.capacity,
        "refill_rate": self.tokens_bucket.refill_rate,
      },
    }


class MultiKeyRateLimiter:
  """Rate limiter that tracks multiple keys (e.g., per user or session)."""

  def __init__(
    self,
    requests_per_minute: int = 60,
    tokens_per_minute: int = 90000,
    burst_multiplier: float = 1.5,
    cleanup_interval: int = 300,  # 5 minutes
  ):
    """Initialize the multi-key rate limiter.

    Args:
        requests_per_minute: Maximum requests per minute per key
        tokens_per_minute: Maximum tokens per minute per key
        burst_multiplier: Multiplier for burst capacity
        cleanup_interval: Interval for cleaning up unused limiters (seconds)
    """
    self.requests_per_minute = requests_per_minute
    self.tokens_per_minute = tokens_per_minute
    self.burst_multiplier = burst_multiplier
    self.limiters: Dict[str, RateLimiter] = {}
    self.last_access: Dict[str, float] = {}
    self.cleanup_interval = cleanup_interval
    self.last_cleanup = time.time()
    self.logger = logger.bind(component="multi_rate_limiter")

  def _get_limiter(self, key: str) -> RateLimiter:
    """Get or create a rate limiter for a key.

    Args:
        key: The key to get a limiter for

    Returns:
        Rate limiter for the key
    """
    # Cleanup old limiters periodically
    if time.time() - self.last_cleanup > self.cleanup_interval:
      self._cleanup()

    if key not in self.limiters:
      self.limiters[key] = RateLimiter(self.requests_per_minute, self.tokens_per_minute, self.burst_multiplier)

    self.last_access[key] = time.time()
    return self.limiters[key]

  def _cleanup(self):
    """Remove rate limiters that haven't been used recently."""
    now = time.time()
    cutoff = now - self.cleanup_interval

    keys_to_remove = [key for key, last_access in self.last_access.items() if last_access < cutoff]

    for key in keys_to_remove:
      del self.limiters[key]
      del self.last_access[key]

    if keys_to_remove:
      self.logger.info(f"Cleaned up {len(keys_to_remove)} unused rate limiters")

    self.last_cleanup = now

  async def acquire_request(self, key: str, estimated_tokens: int = 0) -> float:
    """Acquire permission for a request for a specific key.

    Args:
        key: The key to rate limit
        estimated_tokens: Estimated tokens for the request

    Returns:
        Total time waited in seconds
    """
    limiter = self._get_limiter(key)
    return await limiter.acquire_request(estimated_tokens)

  def try_acquire_request(self, key: str, estimated_tokens: int = 0) -> bool:
    """Try to acquire permission for a request without waiting.

    Args:
        key: The key to rate limit
        estimated_tokens: Estimated tokens for the request

    Returns:
        True if request can proceed
    """
    limiter = self._get_limiter(key)
    return limiter.try_acquire_request(estimated_tokens)

  def get_status(self, key: Optional[str] = None) -> Dict[str, Any]:
    """Get the current status of the rate limiter(s).

    Args:
        key: Optional specific key to get status for

    Returns:
        Dictionary with status information
    """
    if key:
      if key in self.limiters:
        return self.limiters[key].get_status()
      else:
        return {"error": f"No rate limiter found for key: {key}"}

    return {
      "total_keys": len(self.limiters),
      "keys": list(self.limiters.keys()),
      "config": {
        "requests_per_minute": self.requests_per_minute,
        "tokens_per_minute": self.tokens_per_minute,
        "burst_multiplier": self.burst_multiplier,
        "cleanup_interval": self.cleanup_interval,
      },
    }
