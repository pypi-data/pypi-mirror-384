# """Fact verification using independent model."""

# from typing import List
# import structlog

# from ..types import ExtractedQuote, VerifiedFact
# from ..models.deepseek_client import DeepSeekClient

# logger = structlog.get_logger()


# class FactVerifier:
#     """Independent verification of extracted facts."""

#     def __init__(self, deepseek_client: DeepSeekClient, verification_threshold: float = 0.95):
#         self.client = deepseek_client
#         self.threshold = verification_threshold

#     async def batch_verify(self, quotes: List[ExtractedQuote], sources_content: dict) -> List[VerifiedFact]:
#         """Verify multiple facts in batches with DeepSeek."""
#         # Batch quotes together - verify 20 at a time
#         batch_size = 20
#         all_verified = []

#         for i in range(0, len(quotes), batch_size):
#             batch = quotes[i:i+batch_size]

#             # Build batch prompt
#             quotes_text = "\n\n---QUOTE SEPARATOR---\n\n".join([
#                 f"QUOTE #{j+1}\n"
#                 f"Quote: {q.quote}\n"
#                 f"Context Before: {q.context_before}\n"
#                 f"Context After: {q.context_after}\n"
#                 f"Source: {q.source_title}\n"
#                 f"Full Source Content:\n{sources_content.get(q.source_url, '')}"
#                 for j, q in enumerate(batch)
#             ])

#             prompt = f"""Verify these quotes exist in their respective sources:

# {quotes_text}

# For EACH quote, verify:
# 1. Quote exists in source (exact or very similar)
# 2. Context is accurate
# 3. No misrepresentation

# Return JSON:
# {{
#     "verifications": [
#         {{
#             "quote_number": 1,
#             "verified_in_source": true/false,
#             "confidence": 0.0-1.0,
#             "notes": "concerns"
#         }}
#     ]
# }}"""

#             try:
#                 response = await self.client.call_json(prompt)
#                 verifications = response.get("verifications", [])

#                 for v in verifications:
#                     quote_idx = v.get("quote_number", 1) - 1
#                     if 0 <= quote_idx < len(batch):
#                         quote = batch[quote_idx]
#                         if v.get("verified_in_source", False) and v.get("confidence", 0.0) >= self.threshold:
#                             all_verified.append(VerifiedFact(
#                                 quote=quote.quote,
#                                 source_url=quote.source_url,
#                                 source_title=quote.source_title,
#                                 context=f"{quote.context_before} {quote.quote} {quote.context_after}",
#                                 verified_in_source=True,
#                                 verified_by_second_model=True,
#                                 verification_confidence=v.get("confidence", 0.0)
#                             ))

#                 logger.info(f"Batch {i//batch_size + 1}: Verified {len([v for v in verifications if v.get('verified_in_source')])} quotes")

#             except Exception as e:
#                 logger.error(f"Batch verification failed: {e}")
#                 # Skip this batch on error
#                 continue

#         logger.info(f"Total verified: {len(all_verified)}/{len(quotes)} facts")
#         return all_verified
