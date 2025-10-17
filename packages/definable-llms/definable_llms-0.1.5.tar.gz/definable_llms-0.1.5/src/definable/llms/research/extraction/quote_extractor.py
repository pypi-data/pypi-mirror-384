"""Quote extraction from sources."""

from typing import List
from difflib import SequenceMatcher
import structlog
import json
import re

from ..types import ExtractedQuote, Source
from ...base.types import ChatRequest, Message, MessageRole

logger = structlog.get_logger()


class QuoteExtractor:
  """Extracts direct quotes from sources without paraphrasing."""

  def __init__(self, provider, model: str):
    self.provider = provider
    self.model = model

  async def extract_quotes_batch_streaming(self, sources: List[Source], context_query: str):
    """Extract quotes from multiple sources with streaming."""
    sources_text = "\n\n---SOURCE SEPARATOR---\n\n".join([
      f"SOURCE #{i + 1}\nTitle: {s.title}\nURL: {s.url}\nContent:\n{s.content}" for i, s in enumerate(sources)
    ])

    prompt = f"""Extract DIRECT QUOTES from these sources that are relevant to: {context_query}

{sources_text}

Instructions:
1. Extract ONLY direct quotes - copy exact text from the sources
2. Do NOT paraphrase or rephrase anything
3. Include context before and after each quote
4. Extract 8-12 key quotes from EACH source (important: extract from ALL sources equally)
5. Make sure to cover ALL sources thoroughly, not just the beginning ones

Return JSON format:
{{
    "quotes": [
        {{
            "source_number": 1,
            "quote": "exact text from source",
            "context_before": "text immediately before",
            "context_after": "text immediately after",
            "confidence": 0.0-1.0
        }}
    ]
}}"""

    try:
      # Stream the response
      stream = await self.provider.chat(
        ChatRequest(
          messages=[Message(role=MessageRole.USER, content=prompt)],
          model=self.model,
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
      async for chunk in stream:
        if chunk.choices and len(chunk.choices) > 0:
          delta = chunk.choices[0].get("delta", {})
          content = delta.get("content", "")
          if content:
            full_response.append(content)
            yield {"type": "thinking", "content": content}

      # Parse the complete response
      raw_content = "".join(full_response)
      if not raw_content:
        logger.error("Empty response from LLM")
        yield {"type": "result", "quotes": []}
        return

      raw_content = raw_content.strip()
      if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
      if raw_content.startswith("```"):
        raw_content = raw_content[3:]
      if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
      raw_content = raw_content.strip()

      if not raw_content:
        logger.error("Empty response after cleaning markdown")
        yield {"type": "result", "quotes": []}
        return

      # Fix invalid escape sequences
      def fix_escapes(match):
        char = match.group(1)
        if char in ['"', "\\", "/", "b", "f", "n", "r", "t", "u"]:
          return match.group(0)
        return char

      raw_content = re.sub(r"\\(.)", fix_escapes, raw_content)
      data = json.loads(raw_content)
      all_quotes = []

      for q in data.get("quotes", []):
        source_idx = q.get("source_number", 1) - 1
        if 0 <= source_idx < len(sources):
          source = sources[source_idx]
          if self.verify_quote_exists(q["quote"], source.content):
            all_quotes.append(
              ExtractedQuote(
                quote=q["quote"],
                context_before=q.get("context_before", ""),
                context_after=q.get("context_after", ""),
                source_url=source.url,
                source_title=source.title,
                location="middle",
                extraction_confidence=q.get("confidence", 0.8),
              )
            )

      logger.info(f"Extracted {len(all_quotes)} quotes from {len(sources)} sources")
      yield {"type": "result", "quotes": all_quotes}

    except Exception as e:
      logger.error(f"Quote extraction failed: {e}")
      yield {"type": "result", "quotes": []}

  async def extract_quotes_batch(self, sources: List[Source], context_query: str) -> List[ExtractedQuote]:
    """Extract quotes from multiple sources in one API call (non-streaming fallback)."""
    sources_text = "\n\n---SOURCE SEPARATOR---\n\n".join([
      f"SOURCE #{i + 1}\nTitle: {s.title}\nURL: {s.url}\nContent:\n{s.content}" for i, s in enumerate(sources)
    ])

    prompt = f"""Extract DIRECT QUOTES from these sources that are relevant to: {context_query}

{sources_text}

Instructions:
1. Extract ONLY direct quotes - copy exact text from the sources
2. Do NOT paraphrase or rephrase anything
3. Include context before and after each quote
4. Extract 8-12 key quotes from EACH source (important: extract from ALL sources equally)
5. Make sure to cover ALL sources thoroughly, not just the beginning ones

Return JSON format:
{{
    "quotes": [
        {{
            "source_number": 1,
            "quote": "exact text from source",
            "context_before": "text immediately before",
            "context_after": "text immediately after",
            "confidence": 0.0-1.0
        }}
    ]
}}"""

    try:
      response = await self.provider.chat(
        ChatRequest(
          messages=[Message(role=MessageRole.USER, content=prompt)],
          model=self.model,
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

      # Clean markdown formatting
      raw_content = response.choices[0].message.content

      if not raw_content:
        logger.error("Empty response from LLM")
        return []

      raw_content = raw_content.strip()

      if raw_content.startswith("```json"):
        raw_content = raw_content[7:]
      if raw_content.startswith("```"):
        raw_content = raw_content[3:]
      if raw_content.endswith("```"):
        raw_content = raw_content[:-3]
      raw_content = raw_content.strip()

      if not raw_content:
        logger.error("Empty response after cleaning markdown")
        return []

      # Fix invalid escape sequences from markdown formatting
      # JSON only allows: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
      # Replace invalid escapes like \_, \*, \a, \c, etc. with just the character
      # But preserve valid JSON escapes
      def fix_escapes(match):
        char = match.group(1)
        if char in ['"', "\\", "/", "b", "f", "n", "r", "t", "u"]:
          return match.group(0)  # Keep valid escapes
        return char  # Remove backslash from invalid escapes

      raw_content = re.sub(r"\\(.)", fix_escapes, raw_content)

      data = json.loads(raw_content)
      all_quotes = []

      for q in data.get("quotes", []):
        source_idx = q.get("source_number", 1) - 1
        if 0 <= source_idx < len(sources):
          source = sources[source_idx]
          if self.verify_quote_exists(q["quote"], source.content):
            all_quotes.append(
              ExtractedQuote(
                quote=q["quote"],
                context_before=q.get("context_before", ""),
                context_after=q.get("context_after", ""),
                source_url=source.url,
                source_title=source.title,
                location="middle",
                extraction_confidence=q.get("confidence", 0.8),
              )
            )

      logger.info(f"Extracted {len(all_quotes)} verified quotes from {len(sources)} sources")
      return all_quotes

    except Exception as e:
      logger.error(f"Batch quote extraction failed: {e}")
      return []

  def verify_quote_exists(self, quote: str, source_content: str, threshold: float = 0.95) -> bool:
    """Verify quote exists in source using fuzzy matching."""
    quote_lower = quote.lower().strip()
    source_lower = source_content.lower()

    # Check exact match first
    if quote_lower in source_lower:
      return True

    # Fuzzy match for slight variations
    words = quote_lower.split()
    if len(words) < 5:
      return False  # Too short for fuzzy matching

    # Check overlapping windows
    quote_length = len(quote)
    for i in range(len(source_content) - quote_length + 1):
      window = source_content[i : i + quote_length].lower()
      similarity = SequenceMatcher(None, quote_lower, window).ratio()
      if similarity >= threshold:
        return True

    return False
