"""Truth-grounded deep research system."""

from .orchestrator.research_orchestrator import DeepResearchOrchestrator
from .types import ResearchConfig, ResearchReport

# Global research manager instance
research_manager = DeepResearchOrchestrator(
  exa_api_key="",  # This should be configured from settings
  config=ResearchConfig(),
)

__all__ = ["DeepResearchOrchestrator", "ResearchConfig", "ResearchReport", "research_manager"]
