"""Research state tracking."""

from typing import List, Set, Dict, Any
from ..types import Source, ExtractedQuote, VerifiedFact, CrossVerifiedClaim
import structlog

logger = structlog.get_logger()


class ResearchState:
  """Tracks all research progress and findings."""

  def __init__(self):
    self.raw_sources: List[Source] = []
    self.extracted_quotes: List[ExtractedQuote] = []
    self.verified_facts: List[VerifiedFact] = []
    self.cross_verified_claims: List[CrossVerifiedClaim] = []
    self.contradictions: List[Dict[str, Any]] = []
    self.research_iterations: int = 0
    self.questions_explored: List[str] = []
    self.sources_used: Set[str] = set()

  def add_sources(self, sources: List[Source]):
    """Add sources to state."""
    self.raw_sources.extend(sources)
    for source in sources:
      self.sources_used.add(source.url)
    logger.info(f"Added {len(sources)} sources. Total: {len(self.raw_sources)}")

  def add_quotes(self, quotes: List[ExtractedQuote]):
    """Add extracted quotes."""
    self.extracted_quotes.extend(quotes)
    logger.info(f"Added {len(quotes)} quotes. Total: {len(self.extracted_quotes)}")

  def add_verified_fact(self, fact: VerifiedFact):
    """Add a verified fact."""
    self.verified_facts.append(fact)

  def add_cross_verified_claim(self, claim: CrossVerifiedClaim):
    """Add a cross-verified claim."""
    self.cross_verified_claims.append(claim)

  def add_contradiction(self, contradiction: Dict[str, Any]):
    """Add a detected contradiction."""
    self.contradictions.append(contradiction)

  def get_all_findings(self) -> Dict[str, Any]:
    """Get all findings."""
    return {
      "sources_count": len(self.raw_sources),
      "quotes_count": len(self.extracted_quotes),
      "verified_facts_count": len(self.verified_facts),
      "cross_verified_claims_count": len(self.cross_verified_claims),
      "contradictions_count": len(self.contradictions),
    }

  def get_contradictions(self) -> List[Dict[str, Any]]:
    """Get all contradictions."""
    return self.contradictions

  def calculate_confidence(self) -> float:
    """Calculate overall confidence score."""
    if not self.cross_verified_claims:
      return 0.0

    # Average strength of all claims
    strengths = [claim.strength for claim in self.cross_verified_claims]
    avg_strength = sum(strengths) / len(strengths)

    # Penalty for unresolved contradictions
    contradiction_penalty = len(self.contradictions) * 0.05

    confidence = max(0.0, min(1.0, avg_strength - contradiction_penalty))
    return confidence

  def get_coverage_metrics(self) -> Dict[str, Any]:
    """Get research coverage metrics."""
    return {
      "unique_sources": len(self.sources_used),
      "unique_domains": len(set(s.domain for s in self.raw_sources)),
      "questions_explored": len(self.questions_explored),
      "iterations_completed": self.research_iterations,
      "avg_sources_per_claim": (
        sum(c.source_count for c in self.cross_verified_claims) / len(self.cross_verified_claims) if self.cross_verified_claims else 0
      ),
    }
