"""SQLAlchemy database schema for analytics."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import (
  Column,
  DateTime,
  Integer,
  String,
  Text,
  Boolean,
  DECIMAL,
  JSON,
  ForeignKey,
  Index,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base: Any = declarative_base()


class SessionAnalytics(Base):
  """Main analytics table for session analytics requirements."""

  __tablename__ = "session_analytics"

  # Primary identification
  session_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)

  # Session Details
  session_title = Column(String(200), nullable=False)

  # Core Analytics
  total_tokens: Column[int] = Column(Integer, default=0, nullable=False)
  total_cost: Column[Decimal] = Column(DECIMAL(10, 6), default=Decimal("0"), nullable=False)
  request_count: Column[int] = Column(Integer, default=0, nullable=False)
  avg_response_time: Column[Decimal] = Column(DECIMAL(8, 3), default=Decimal("0"), nullable=False)

  # Usage Breakdown
  model_usage: Column[dict] = Column(JSON, default=dict, nullable=False)  # {"gpt-5": {"tokens": 1500, "requests": 8}}
  capability_usage: Column[dict] = Column(JSON, default=dict, nullable=False)  # {"chat": 15, "images": 2}

  # Extended Analytics
  function_calls: Column[int] = Column(Integer, default=0, nullable=False)
  files_processed: Column[int] = Column(Integer, default=0, nullable=False)
  embeddings_generated: Column[int] = Column(Integer, default=0, nullable=False)
  images_generated: Column[int] = Column(Integer, default=0, nullable=False)

  # Performance Metrics
  fastest_response: Column[Decimal] = Column(DECIMAL(8, 3), nullable=True)
  slowest_response: Column[Decimal] = Column(DECIMAL(8, 3), nullable=True)
  success_rate: Column[Decimal] = Column(DECIMAL(5, 4), default=Decimal("1.0"), nullable=False)

  # Lifecycle
  created_at = Column(DateTime, default=datetime.now, nullable=False)
  updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

  # Relationships
  requests = relationship("RequestEvent", back_populates="session", cascade="all, delete-orphan")


class RequestEvent(Base):
  """Individual request tracking for detailed analytics."""

  __tablename__ = "request_events"

  # Primary identification
  id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
  session_id = Column(
    PG_UUID(as_uuid=True),
    ForeignKey("session_analytics.session_id"),
    nullable=False,
  )

  # Request Details
  request_type: Column[str] = Column(String(50), nullable=False)  # "chat", "image", "embedding", "function"
  session_title: Column[str] = Column(String(200), nullable=False)
  model_used: Column[str] = Column(String(100), nullable=False)
  provider_used: Column[str] = Column(String(50), nullable=False)

  # Performance Metrics
  response_time: Column[Decimal] = Column(DECIMAL(8, 3), nullable=False)
  tokens_used: Column[int] = Column(Integer, default=0, nullable=False)
  cost: Column[Decimal] = Column(DECIMAL(8, 6), default=Decimal("0"), nullable=False)

  # Status
  success: Column[bool] = Column(Boolean, default=True, nullable=False)
  error_message: Column[str] = Column(Text, nullable=True)

  # Request Context
  request_size: Column[int] = Column(Integer, nullable=True)  # Characters in request
  response_size: Column[int] = Column(Integer, nullable=True)  # Characters in response

  # Timestamp
  timestamp: Column[datetime] = Column(DateTime, default=datetime.now, nullable=False)

  # Relationships
  session = relationship("SessionAnalytics", back_populates="requests")


class ModelRegistry(Base):
  """Model registry with real-time pricing."""

  __tablename__ = "model_registry"

  # Primary identification
  model_name: Column[str] = Column(String(100), primary_key=True)
  provider: Column[str] = Column(String(50), nullable=False)
  capability: Column[str] = Column(String(50), nullable=False)  # "chat", "embedding", "image_gen"

  # Model Information
  description: Column[str] = Column(Text, nullable=True)  # Model description for UI/docs
  display_name: Column[str] = Column(String(200), nullable=True)  # Human-readable name

  # Cost Information
  input_cost_per_token: Column[Decimal] = Column(DECIMAL(12, 10), nullable=False)
  output_cost_per_token: Column[Decimal] = Column(DECIMAL(12, 10), nullable=False)

  # Capabilities
  max_context_length: Column[int] = Column(Integer, nullable=False)
  max_output_tokens: Column[int] = Column(Integer, nullable=True)
  supports_streaming: Column[bool] = Column(Boolean, default=False, nullable=False)
  supports_functions: Column[bool] = Column(Boolean, default=False, nullable=False)
  supports_vision: Column[bool] = Column(Boolean, default=False, nullable=False)
  supports_reasoning: Column[bool] = Column(Boolean, default=False, nullable=False)

  # Status
  is_active: Column[bool] = Column(Boolean, default=True, nullable=False)
  last_updated: Column[datetime] = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)


# Indexes for Performance
Index("idx_session_analytics_created_at", SessionAnalytics.created_at)
Index("idx_request_events_session_id", RequestEvent.session_id)
Index("idx_request_events_timestamp", RequestEvent.timestamp)
Index(
  "idx_model_registry_provider_capability",
  ModelRegistry.provider,
  ModelRegistry.capability,
)
