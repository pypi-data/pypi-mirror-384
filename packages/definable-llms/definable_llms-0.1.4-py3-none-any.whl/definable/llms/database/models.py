"""Pydantic models for database operations."""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class SessionAnalyticsModel(BaseModel):
  """Pydantic model for SessionAnalytics (session analytics requirements)."""

  session_id: UUID

  # Core Analytics
  total_tokens: int = 0
  total_cost: Decimal = Field(default=Decimal("0"), decimal_places=6)
  request_count: int = 0
  avg_response_time: float = 0.0

  # Usage Breakdown
  model_usage: Dict[str, Any] = Field(default_factory=dict)
  capability_usage: Dict[str, int] = Field(default_factory=dict)

  # Extended Analytics
  function_calls: int = 0
  files_processed: int = 0
  embeddings_generated: int = 0
  images_generated: int = 0

  # Performance Metrics
  fastest_response: Optional[float] = None
  slowest_response: Optional[float] = None
  success_rate: float = 1.0

  # Timestamps
  created_at: datetime
  updated_at: datetime


class RequestEventModel(BaseModel):
  """Individual request tracking model."""

  id: UUID
  session_id: UUID
  request_type: str
  model_used: str
  provider_used: str
  response_time: float
  tokens_used: int = 0
  cost: Decimal = Field(default=Decimal("0"), decimal_places=6)
  success: bool = True
  error_message: Optional[str] = None
  timestamp: datetime


class ModelRegistryModel(BaseModel):
  """Model registry for dynamic pricing and capabilities."""

  model_name: str
  provider: str
  capability: str
  description: Optional[str] = None
  display_name: Optional[str] = None
  input_cost_per_token: Decimal = Field(decimal_places=10)
  output_cost_per_token: Decimal = Field(decimal_places=10)
  max_context_length: int
  max_output_tokens: Optional[int] = None
  supports_streaming: bool = False
  supports_functions: bool = False
  supports_vision: bool = False
  supports_reasoning: bool = False
  is_active: bool = True
  last_updated: datetime


class CostBreakdown(BaseModel):
  """Detailed cost analysis for a session."""

  session_id: UUID
  total_cost: Decimal

  # Cost by Capability
  chat_cost: Decimal = Decimal("0")
  image_cost: Decimal = Decimal("0")
  embedding_cost: Decimal = Decimal("0")
  function_cost: Decimal = Decimal("0")

  # Cost by Model
  cost_by_model: Dict[str, Decimal] = Field(default_factory=dict)

  # Optimization Insights
  most_expensive_model: Optional[str] = None
  cost_per_token_avg: Decimal = Decimal("0")
  estimated_next_hour_cost: Decimal = Decimal("0")
