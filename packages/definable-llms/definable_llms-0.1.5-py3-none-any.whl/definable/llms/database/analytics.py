"""Analytics manager for session analytics."""

import time
from decimal import Decimal
from typing import Optional

from .operations import DatabaseOperations
from .models import SessionAnalyticsModel


class AnalyticsManager:
  """Manages analytics for session analytics requirements."""

  def __init__(self, db_ops: DatabaseOperations):
    self.db_ops = db_ops

  async def start_session_analytics(self, session_id: str) -> SessionAnalyticsModel:
    """Initialize analytics for a new session."""
    return await self.db_ops.create_session_analytics(session_id)

  async def record_chat_completion(
    self,
    session_id: str,
    model: str,
    provider: str,
    response_time: float,
    tokens_used: int,
    cost: Decimal,
  ):
    """Record chat completion analytics."""
    # Record individual request
    await self.db_ops.record_request_event(
      session_id=session_id,
      request_type="chat",
      model_used=model,
      provider_used=provider,
      response_time=response_time,
      tokens_used=tokens_used,
      cost=cost,
    )

    # Update session aggregates
    await self.db_ops.update_session_metrics(
      session_id=session_id,
      tokens=tokens_used,
      cost=cost,
      response_time=response_time,
      model=model,
      request_type="chat",
    )

  async def get_session_analytics(self, session_id: str) -> Optional[SessionAnalyticsModel]:
    """Get comprehensive analytics (session analytics requirements)."""
    return await self.db_ops.get_session_analytics(session_id)


class RequestTimer:
  """Helper for timing requests."""

  def __init__(self):
    self.start_time = time.time()

  def elapsed(self) -> float:
    """Get elapsed time in seconds."""
    return time.time() - self.start_time
