"""Database CRUD operations for session analytics."""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func

from .schema import SessionAnalytics, RequestEvent
from .models import SessionAnalyticsModel, RequestEventModel


class DatabaseOperations:
  """Database operations for session analytics."""

  def __init__(self, db_session: AsyncSession):
    self.db = db_session

  async def create_session_analytics(self, session_id: str) -> SessionAnalyticsModel:
    """Create new session analytics record."""
    analytics = SessionAnalytics(session_id=session_id)
    self.db.add(analytics)
    await self.db.commit()
    await self.db.refresh(analytics)
    return SessionAnalyticsModel.model_validate(analytics, from_attributes=True)

  async def get_session_analytics(self, session_id: str) -> Optional[SessionAnalyticsModel]:
    """Get session analytics"""
    result = await self.db.execute(select(SessionAnalytics).where(SessionAnalytics.session_id == session_id))
    analytics = result.scalar_one_or_none()
    return SessionAnalyticsModel.model_validate(analytics, from_attributes=True) if analytics else None

  async def update_session_metrics(
    self,
    session_id: str,
    tokens: int,
    cost: Decimal,
    response_time: float,
    model: str,
    request_type: str,
  ):
    """Update session analytics with new request data."""
    # Get current analytics
    result = await self.db.execute(select(SessionAnalytics).where(SessionAnalytics.session_id == session_id))
    analytics = result.scalar_one_or_none()

    if analytics:
      # Calculate new averages
      new_count = analytics.request_count + 1
      new_avg_time = ((float(analytics.avg_response_time) * analytics.request_count) + response_time) / new_count

      # Update model usage
      model_usage: Dict[str, Any] = dict(analytics.model_usage) if analytics.model_usage else {}
      if model not in model_usage:
        model_usage[model] = {"tokens": 0, "requests": 0, "cost": 0}
      model_usage[model]["tokens"] += tokens
      model_usage[model]["requests"] += 1
      model_usage[model]["cost"] = float(model_usage[model]["cost"]) + float(cost)

      # Update capability usage
      capability_usage: Dict[str, int] = dict(analytics.capability_usage) if analytics.capability_usage else {}
      capability_usage[request_type] = capability_usage.get(request_type, 0) + 1

      # Update analytics
      await self.db.execute(
        update(SessionAnalytics)
        .where(SessionAnalytics.session_id == session_id)
        .values(
          total_tokens=analytics.total_tokens + tokens,
          total_cost=analytics.total_cost + cost,
          request_count=new_count,
          avg_response_time=new_avg_time,
          model_usage=model_usage,
          capability_usage=capability_usage,
          fastest_response=func.coalesce(
            func.least(analytics.fastest_response, response_time),
            response_time,
          ),
          slowest_response=func.greatest(analytics.slowest_response, response_time),
          updated_at=datetime.now(),
        )
      )
      await self.db.commit()

  async def record_request_event(
    self,
    session_id: str,
    request_type: str,
    model_used: str,
    provider_used: str,
    response_time: float,
    tokens_used: int,
    cost: Decimal,
    success: bool = True,
    error_message: Optional[str] = None,
  ):
    """Record detailed request event."""
    event = RequestEvent(
      session_id=session_id,
      request_type=request_type,
      model_used=model_used,
      provider_used=provider_used,
      response_time=response_time,
      tokens_used=tokens_used,
      cost=cost,
      success=success,
      error_message=error_message,
    )

    self.db.add(event)
    await self.db.commit()
    return RequestEventModel.model_validate(event, from_attributes=True)
