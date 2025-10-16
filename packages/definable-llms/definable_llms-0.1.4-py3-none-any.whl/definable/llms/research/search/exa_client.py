"""Exa search client for comprehensive source collection."""

from typing import List, Dict, Any
from exa_py import Exa
import structlog

logger = structlog.get_logger()


class ExaSearchClient:
  """Client for Exa API search."""

  def __init__(self, api_key: str):
    self.client = Exa(api_key)
    logger.info("Initialized Exa search client")

  async def comprehensive_search(self, query: str, min_results: int = 50, search_type: str = "neural") -> List[Dict[str, Any]]:
    """Perform comprehensive search with query variations to reach target source count."""
    logger.info(f"Starting comprehensive search for: {query}")

    all_results = []
    seen_urls = set()

    # Base query search
    results = await self._search_single(query, num_results=min(10, min_results), search_type=search_type)
    for result in results:
      if result["url"] not in seen_urls:
        all_results.append(result)
        seen_urls.add(result["url"])

    logger.info(f"Base search found {len(all_results)} sources")

    # If we need more, search with variants
    if len(all_results) < min_results:
      variants = self._generate_query_variants(query)
      for variant in variants:
        if len(all_results) >= min_results:
          break

        results = await self._search_single(variant, num_results=10, search_type=search_type)
        for result in results:
          if result["url"] not in seen_urls:
            all_results.append(result)
            seen_urls.add(result["url"])

        logger.info(f"After variant '{variant[:50]}...': {len(all_results)} total sources")

    logger.info(f"Comprehensive search complete: {len(all_results)} unique sources")
    return all_results[: min(len(all_results), min_results * 2)]  # Cap at 2x min

  async def _search_single(self, query: str, num_results: int = 10, search_type: str = "neural") -> List[Dict[str, Any]]:
    """Perform a single search query."""
    try:
      response = self.client.search_and_contents(
        query,
        type=search_type,
        num_results=num_results,
        text=True,
        highlights=True,
      )

      results = []
      for result in response.results:
        results.append({
          "url": result.url,
          "title": result.title,
          "content": result.text or "",
          "published_date": getattr(result, "published_date", None),
          "domain": self._extract_domain(result.url),
          "author": getattr(result, "author", None),
        })

      return results
    except Exception as e:
      logger.error(f"Search failed for query '{query}': {e}")
      return []

  def _generate_query_variants(self, query: str) -> List[str]:
    """Generate query variations to find more sources."""
    variants = [
      f"research on {query}",
      f"studies about {query}",
      f"analysis of {query}",
      f"recent developments in {query}",
      f"expert opinion on {query}",
    ]
    return variants

  def _extract_domain(self, url: str) -> str:
    """Extract domain from URL."""
    try:
      from urllib.parse import urlparse

      parsed = urlparse(url)
      return parsed.netloc
    except Exception:
      return "unknown"

  def deduplicate_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate sources by URL."""
    seen = set()
    unique = []
    for source in sources:
      if source["url"] not in seen:
        seen.add(source["url"])
        unique.append(source)
    return unique
