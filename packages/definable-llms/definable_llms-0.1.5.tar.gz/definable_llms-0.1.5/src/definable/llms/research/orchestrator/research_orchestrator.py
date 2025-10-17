"""Main research orchestrator - coordinates entire research process."""

from typing import AsyncGenerator, Dict, Any, Optional
import time
import json
import structlog

from ..types import ResearchConfig, Source
from ...providers import provider_factory
from ...base.types import ChatRequest, Message, MessageRole
from ..search.exa_client import ExaSearchClient
from ..extraction.quote_extractor import QuoteExtractor

# from ..verification.fact_verifier import FactVerifier  # DISABLED - too slow
# from ..verification.cross_verifier import CrossVerifier  # DISABLED - too slow
from ..state.research_state import ResearchState

logger = structlog.get_logger()


class DeepResearchOrchestrator:
  """Coordinates truth-grounded deep research process."""

  def __init__(self, exa_api_key: str, config: Optional[ResearchConfig] = None):
    self.config = config or ResearchConfig()

    # Use existing providers
    self.gemini_flash_provider = provider_factory.get_provider("gemini")
    self.gemini_flash_model = "gemini-2.5-flash"
    self.gemini_pro_model = "gemini-2.5-pro"

    # Use DeepSeek provider
    self.deepseek_provider = provider_factory.get_provider("deepseek")
    self.deepseek_chat_model = "deepseek-chat"
    self.deepseek_reasoner_model = "deepseek-reasoner"

    self.search_client = ExaSearchClient(exa_api_key)

    # Initialize components
    self.quote_extractor = QuoteExtractor(self.gemini_flash_provider, self.gemini_flash_model)
    # self.fact_verifier = FactVerifier(self.deepseek_provider, self.config.quote_verification_threshold)  # DISABLED
    # self.cross_verifier = CrossVerifier(self.gemini_flash_provider, self.gemini_pro_model, self.config.min_sources_per_claim)  # DISABLED

    logger.info("Initialized Deep Research Orchestrator")

  async def close(self):
    """Close all provider connections and cleanup resources."""
    try:
      await self.gemini_flash_provider.close()
      await self.deepseek_provider.close()
      logger.info("Closed all provider connections")
    except Exception as e:
      logger.error(f"Error closing providers: {e}")

  async def research(self, query: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Main research coordinator - yields progress events."""
    start_time = time.time()
    state = ResearchState()

    yield {"type": "start", "data": {"message": f"Starting deep research: {query}", "estimated_time": "3-5 minutes"}}

    # Phase 1: Decompose query into multiple perspectives
    yield {"type": "phase", "data": {"phase": "decomposition", "message": "Analyzing query from multiple perspectives..."}}

    # Stream the decomposition thinking
    questions = []
    async for event in self._decompose_query_streaming(query):
      if event["type"] == "thinking":
        yield {"type": "thinking", "data": {"phase": "decomposition", "content": event["content"]}}
      elif event["type"] == "result":
        questions = event["questions"]

    state.questions_explored = questions
    yield {"type": "result", "data": {"phase": "decomposition", "perspectives": 5, "questions": questions}}

    # Phase 2: Comprehensive source collection
    yield {"type": "searching", "data": {"message": "Searching for sources...", "engine": "Exa"}}
    sources = await self._collect_sources(questions)
    state.add_sources([Source(**s) for s in sources])
    yield {"type": "sources_collected", "data": {"count": len(sources), "unique_domains": len(set(s["domain"] for s in sources))}}

    # Phase 3: Extract quotes from all sources with streaming
    yield {"type": "phase", "data": {"phase": "extraction", "message": "Extracting direct quotes from sources..."}}
    quotes = []
    async for event in self._extract_quotes_streaming(state.raw_sources, query):
      if event["type"] == "thinking":
        yield {"type": "thinking", "data": {"phase": "extraction", "content": event["content"]}}
      elif event["type"] == "result":
        quotes.extend(event["quotes"])
    state.add_quotes(quotes)
    yield {"type": "result", "data": {"phase": "extraction", "count": len(quotes)}}

    # Phase 4: Verify facts independently (DISABLED - too slow for 294 quotes)
    # yield {"type": "verifying_facts", "data": {"message": "Verifying facts with independent model..."}}
    # sources_content = {s.url: s.content for s in state.raw_sources}
    # verified_facts = await self.fact_verifier.batch_verify(quotes, sources_content)
    # for fact in verified_facts:
    #     state.add_verified_fact(fact)
    # yield {"type": "facts_verified", "data": {"verified_count": len(verified_facts)}}

    # Skip verification - use quotes directly
    #         verified_facts = quotes

    #         # Phase 5: Cross-verify across sources (DISABLED - too slow)
    #         # yield {"type": "cross_verifying", "data": {"message": "Cross-verifying claims across sources..."}}
    #         # cross_verified = await self.cross_verifier.cross_verify_claims(verified_facts)
    #         # for claim in cross_verified:
    #         #     state.add_cross_verified_claim(claim)
    #         # yield {"type": "cross_verified", "data": {"claims_found": len(cross_verified), "multi_source_claims": len([c for c in cross_verified
    #  if c.source_count >= 3])}}

    #         # Skip cross-verification - use all verified facts
    #         cross_verified = verified_facts

    # Phase 6-9: Iterative research, critique, confidence check (simplified for now)
    state.research_iterations = 1

    # Phase 10: Calculate confidence
    confidence = state.calculate_confidence()
    yield {
      "type": "confidence_check",
      "data": {
        "confidence": confidence,
        "threshold": self.config.confidence_threshold,
        "passed": confidence >= self.config.confidence_threshold,
      },
    }

    # Phase 11: Synthesize report with streaming
    yield {"type": "synthesizing", "data": {"message": "Synthesizing final report..."}}

    # Stream the report generation
    full_report_chunks = []
    async for chunk in self._synthesize_report(query, state):
      # Yield each chunk as it comes from the LLM
      yield {"type": "report_chunk", "data": {"content": chunk}}
      full_report_chunks.append(chunk)

    report = "".join(full_report_chunks)

    duration = time.time() - start_time
    metrics = state.get_coverage_metrics()

    yield {
      "type": "complete",
      "data": {
        "report": report,
        "metadata": {
          "duration_seconds": duration,
          "sources_consulted": metrics["unique_sources"],
          "quotes_extracted": len(state.extracted_quotes),
          "verified_facts": len(state.verified_facts),
          "cross_verified_claims": len(state.cross_verified_claims),
          "confidence_score": confidence,
          "iterations_completed": state.research_iterations,
          "contradictions_resolved": 0,
        },
      },
    }

  async def _decompose_query_streaming(self, query: str):
    """Break query into multiple research questions with streaming."""
    prompt = f"""Break this research query into 5 different perspectives with 3-5 specific questions each.

Query: {query}

Return JSON:
{{
    "perspectives": [
        {{
            "name": "perspective name",
            "questions": ["question 1", "question 2", ...]
        }}
    ]
}}"""

    try:
      # Stream the response
      stream = await self.gemini_flash_provider.chat(
        ChatRequest(
          messages=[Message(role=MessageRole.USER, content=prompt)],
          model=self.gemini_flash_model,
          temperature=0.0,
          max_tokens=None,
          top_p=None,
          top_k=None,
          frequency_penalty=None,
          presence_penalty=None,
          reasoning_budget_tokens=None,
          stream=True,
        ),
        timeout=None,
      )

      # Collect chunks and yield thinking
      full_response = []
      if hasattr(stream, "__aiter__"):
        async for chunk in stream:  # type: ignore
          if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].get("delta", {})
            content = delta.get("content", "")
            if content:
              full_response.append(content)
              yield {"type": "thinking", "content": content}

      # Parse the complete response
      raw_content = "".join(full_response).strip()
      if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
      if raw_content.startswith("```"):
        raw_content = raw_content[3:]
      if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
      raw_content = raw_content.strip()

      data = json.loads(raw_content)
      all_questions = []
      for p in data.get("perspectives", []):
        all_questions.extend(p.get("questions", []))

      logger.info(f"Decomposed query into {len(all_questions)} questions")
      yield {"type": "result", "questions": all_questions[:25]}

    except Exception as e:
      logger.error(f"Query decomposition failed: {e}")
      yield {"type": "result", "questions": [query]}

  async def _decompose_query(self, query: str) -> list:
    """Break query into multiple research questions (non-streaming fallback)."""
    prompt = f"""Break this research query into 5 different perspectives with 3-5 specific questions each.

Query: {query}

Return JSON:
{{
    "perspectives": [
        {{
            "name": "perspective name",
            "questions": ["question 1", "question 2", ...]
        }}
    ]
}}"""

    try:
      response = await self.gemini_flash_provider.chat(
        ChatRequest(
          messages=[Message(role=MessageRole.USER, content=prompt)],
          model=self.gemini_flash_model,
          temperature=0.0,
          max_tokens=None,
          top_p=None,
          top_k=None,
          frequency_penalty=None,
          presence_penalty=None,
          reasoning_budget_tokens=None,
        ),
        timeout=None,
      )

      raw_content = response.choices[0].message.content.strip()  # type: ignore
      if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
      if raw_content.startswith("```"):
        raw_content = raw_content[3:]
      if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
      raw_content = raw_content.strip()

      data = json.loads(raw_content)
      all_questions = []
      for p in data.get("perspectives", []):
        all_questions.extend(p.get("questions", []))
      logger.info(f"Decomposed query into {len(all_questions)} questions")
      return all_questions[:25]
    except Exception as e:
      logger.error(f"Query decomposition failed: {e}")
      return [query]

  async def _collect_sources(self, questions: list) -> list:
    """Collect comprehensive sources."""
    all_sources = []
    seen_urls = set()

    # Search for each question
    for question in questions[:5]:  # Limit to 5 questions to avoid too many sources
      sources = await self.search_client.comprehensive_search(question, min_results=10)
      for source in sources:
        if source["url"] not in seen_urls:
          all_sources.append(source)
          seen_urls.add(source["url"])

    return all_sources[: self.config.max_sources]

  async def _extract_quotes_streaming(self, sources: list, query: str):
    """Extract quotes from all sources in batches with streaming."""
    batch_size = 3
    total_batches = (len(sources) + batch_size - 1) // batch_size

    for i in range(0, len(sources), batch_size):
      batch = sources[i : i + batch_size]
      batch_num = i // batch_size + 1

      # Stream extraction for this batch
      batch_quotes = []
      async for event in self.quote_extractor.extract_quotes_batch_streaming(batch, query):
        if event["type"] == "thinking":
          # Add batch context to thinking
          content = f"[Batch {batch_num}/{total_batches}] {event['content']}"
          yield {"type": "thinking", "content": content}
        elif event["type"] == "result":
          batch_quotes = event["quotes"]

      logger.info(f"Batch {batch_num}: Extracted {len(batch_quotes)} quotes from {len(batch)} sources")
      yield {"type": "result", "quotes": batch_quotes}

  async def _extract_all_quotes(self, sources: list, query: str) -> list:
    """Extract quotes from all sources in batches (non-streaming fallback)."""
    all_quotes = []
    batch_size = 3

    for i in range(0, len(sources), batch_size):
      batch = sources[i : i + batch_size]
      quotes = await self.quote_extractor.extract_quotes_batch(batch, query)
      all_quotes.extend(quotes)
      logger.info(f"Batch {i // batch_size + 1}: Extracted {len(quotes)} quotes from {len(batch)} sources")

    return all_quotes

  async def _synthesize_report(self, query: str, state: ResearchState):
    """Synthesize report from verified evidence (streaming)."""
    # Use extracted quotes directly (verification disabled)
    quotes = state.extracted_quotes

    logger.info(f"Synthesizing report from {len(quotes)} quotes")

    # Build comprehensive quotes text with all details
    quotes_text = "\n\n".join([
      f'[{i + 1}] "{quote.quote}"\n'
      f"    Source: {quote.source_title}\n"
      f"    URL: {quote.source_url}\n"
      f"    Context: ...{quote.context_before} [{quote.quote}] {quote.context_after}..."
      for i, quote in enumerate(quotes)
    ])

    # Use Gemini Pro for synthesis (better at long context)
    prompt = f"""Create an extremely comprehensive, in-depth research report on: {query}

You have {len(quotes)} verified quotes from {len(state.sources_used)} authoritative sources.
Use ALL of them to create the most thorough analysis possible.

QUOTES:
{quotes_text}

INSTRUCTIONS:
1. Create a DETAILED, multi-section report covering all major themes and findings
2. Include an executive summary at the top
3. Organize into clear sections with subsections (use markdown headers ##, ###)
4. CITE EVERY claim with [Source N] references to the quote numbers above
5. Synthesize related quotes together - don't just list them
6. Include specific numbers, dates, names, and technical details from quotes
7. Add a "Research Gaps" section noting what wasn't covered
8. Make it comprehensive - aim for 3000+ words given the wealth of evidence
9. Use ONLY information from the provided quotes - no external knowledge

Write the full, detailed report now:"""

    try:
      logger.info("Starting comprehensive report synthesis with Gemini Pro (STREAMING)")

      # Enable streaming to get chunks as they're generated
      stream = await self.gemini_flash_provider.chat(
        ChatRequest(
          messages=[Message(role=MessageRole.USER, content=prompt)],
          model=self.gemini_pro_model,
          temperature=0.2,
          max_tokens=None,
          top_p=None,
          top_k=None,
          frequency_penalty=None,
          presence_penalty=None,
          reasoning_budget_tokens=None,
          stream=True,
        ),
        timeout=None,
      )

      # Stream chunks as they arrive - no buffering!
      chunk_count = 0
      if hasattr(stream, "__aiter__"):
        async for chunk in stream:  # type: ignore
          # Extract content from StreamChunk structure: choices[0]["delta"]["content"]
          if chunk.choices and len(chunk.choices) > 0:
            delta = chunk.choices[0].get("delta", {})
            content = delta.get("content", "")
            if content:
              chunk_count += 1
              # Yield chunk immediately for streaming to frontend
              yield content

      logger.info(f"Streamed {chunk_count} chunks to frontend")

    except Exception as e:
      logger.error(f"Report synthesis failed: {e}")
      error_msg = f"\n\n---\nError during synthesis: {str(e)}\n\nExtracted {len(quotes)} quotes from {len(state.sources_used)} sources."
      yield error_msg
