"""Data structures for deep research system."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import uuid4


class Source(BaseModel):
  """Source document."""

  url: str
  title: str
  content: str
  published_date: Optional[str] = None
  domain: str
  author: Optional[str] = None


class ExtractedQuote(BaseModel):
  """Direct quote extracted from source."""

  id: str = Field(default_factory=lambda: str(uuid4()))
  quote: str
  context_before: str
  context_after: str
  source_url: str
  source_title: str
  location: str
  extraction_confidence: float


class VerifiedFact(BaseModel):
  """Fact verified to exist in source."""

  id: str = Field(default_factory=lambda: str(uuid4()))
  quote: str
  source_url: str
  source_title: str
  context: str
  verified_in_source: bool
  verified_by_second_model: bool
  verification_confidence: float
  timestamp: datetime = Field(default_factory=datetime.now)


class CrossVerifiedClaim(BaseModel):
  """Claim verified across multiple sources."""

  id: str = Field(default_factory=lambda: str(uuid4()))
  claim: str
  supporting_facts: List[VerifiedFact]
  source_count: int
  unique_sources: List[str]
  consistency_score: float
  strength: float
  contradictions: Optional[List[Dict[str, Any]]] = None


class ResearchReport(BaseModel):
  """Final research report."""

  query: str
  report_text: str
  citations: List[Dict[str, Any]]
  metadata: Dict[str, Any]
  verified_facts: List[CrossVerifiedClaim]
  timestamp: datetime = Field(default_factory=datetime.now)


class ResearchConfig(BaseModel):
  """Configuration for research session."""

  min_sources: int = 50
  max_sources: int = 100
  min_sources_per_claim: int = 3
  min_iterations: int = 3
  confidence_threshold: float = 0.85
  quote_verification_threshold: float = 0.95
  consistency_threshold: float = 0.90
