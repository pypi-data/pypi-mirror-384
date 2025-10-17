# """Cross-verification across multiple sources."""

# from typing import List
# from difflib import SequenceMatcher
# import structlog

# from ..types import VerifiedFact, CrossVerifiedClaim

# logger = structlog.get_logger()


# class CrossVerifier:
#     """Cross-references claims across multiple sources."""

#     def __init__(self, provider, model: str, min_sources_per_claim: int = 3):
#         self.provider = provider
#         self.model = model
#         self.min_sources = min_sources_per_claim

#     async def cross_verify_claims(self, verified_facts: List[VerifiedFact]) -> List[CrossVerifiedClaim]:
#         """Cross-verify claims across multiple sources."""
#         # Cluster similar facts
#         clusters = self.cluster_similar_facts(verified_facts)

#         cross_verified = []
#         for cluster in clusters:
#             if len(cluster) >= self.min_sources:
#                 # Check consistency
#                 consistency = await self.check_consistency(cluster)
#                 if consistency >= 0.9:  # High consistency required
#                     claim = await self._synthesize_claim(cluster)
#                     cross_verified.append(CrossVerifiedClaim(
#                         claim=claim,
#                         supporting_facts=cluster,
#                         source_count=len(cluster),
#                         unique_sources=[f.source_url for f in cluster],
#                         consistency_score=consistency,
#                         strength=min(1.0, (len(cluster) / self.min_sources) * consistency)
#                     ))

#         logger.info(f"Cross-verified {len(cross_verified)} claims from {len(verified_facts)} facts")
#         return cross_verified

#     def cluster_similar_facts(self, facts: List[VerifiedFact]) -> List[List[VerifiedFact]]:
#         """Group semantically similar facts."""
#         clusters = []
#         used = set()

#         for i, fact1 in enumerate(facts):
#             if i in used:
#                 continue

#             cluster = [fact1]
#             used.add(i)

#             for j, fact2 in enumerate(facts[i+1:], i+1):
#                 if j in used:
#                     continue

#                 similarity = SequenceMatcher(None, fact1.quote.lower(), fact2.quote.lower()).ratio()
#                 if similarity >= 0.7:  # Similar enough
#                     cluster.append(fact2)
#                     used.add(j)

#             clusters.append(cluster)

#         return [c for c in clusters if len(c) >= 2]

#     async def check_consistency(self, facts_cluster: List[VerifiedFact]) -> float:
#         """Verify all sources agree on the claim."""
#         quotes = [f.quote for f in facts_cluster]

#         prompt = f"""Analyze if these quotes from different sources are consistent and say the same thing:

# {chr(10).join(f'{i+1}. "{q}"' for i, q in enumerate(quotes))}

# Return JSON:
# {{
#     "consistent": true/false,
#     "consistency_score": 0.0-1.0,
#     "notes": "explanation"
# }}"""

#         try:
#             from ...base.types import ChatRequest, Message, MessageRole
#             import json
#             import structlog

#             logger = structlog.get_logger()

#             response = await self.provider.chat(ChatRequest(
#                 messages=[Message(role=MessageRole.USER, content=prompt)],
#                 model=self.model,
#                 temperature=0.2
#             ), timeout=None)

#             # Clean markdown formatting
#             raw_content = response.choices[0].message.content.strip()
#             if raw_content.startswith("```json"):
#                 raw_content = raw_content[7:]
#             if raw_content.startswith("```"):
#                 raw_content = raw_content[3:]
#             if raw_content.endswith("```"):
#                 raw_content = raw_content[:-3]
#             raw_content = raw_content.strip()

#             data = json.loads(raw_content)
#             return data.get("consistency_score", 0.0)
#         except Exception:
#             # Fallback to simple text similarity
#             avg_similarity = sum(
#                 SequenceMatcher(None, quotes[i].lower(), quotes[j].lower()).ratio()
#                 for i in range(len(quotes))
#                 for j in range(i+1, len(quotes))
#             ) / max(1, (len(quotes) * (len(quotes) - 1)) // 2)
#             return avg_similarity

#     async def _synthesize_claim(self, facts: List[VerifiedFact]) -> str:
#         """Synthesize a single claim from multiple facts."""
#         # Just use the most common phrasing
#         quotes = [f.quote for f in facts]
#         # Return the longest quote as it's likely most complete
#         return max(quotes, key=len)
