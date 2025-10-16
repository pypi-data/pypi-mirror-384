"""Test the new truth-grounded deep research system."""

import asyncio
from definable.llms.research import DeepResearchOrchestrator
from definable.llms.research.types import ResearchConfig
from definable.llms.config import settings


async def test_deep_research():
  """Test the deep research system."""

  print("=" * 80)
  print("🔬 TRUTH-GROUNDED DEEP RESEARCH SYSTEM TEST")
  print("=" * 80)

  # Get API keys from config (loads from .env)
  exa_key = settings.exa_api_key.get_secret_value() if settings.exa_api_key else None

  if not exa_key:
    raise ValueError("EXA_API_KEY not found in environment or .env file")

  # Initialize orchestrator (uses existing Gemini and DeepSeek providers)
  orchestrator = DeepResearchOrchestrator(
    exa_api_key=exa_key,
    config=ResearchConfig(
      min_sources=20,  # Start smaller for testing
      min_iterations=1,
      confidence_threshold=0.75,
    ),
  )

  query = "What are the latest breakthroughs in quantum computing in 2025?"

  print(f"\n📝 Research Query: {query}")
  print("-" * 80)

  try:
    async for event in orchestrator.research(query):
      event_type = event.get("type")
      data = event.get("data", {})

      if event_type == "start":
        print(f"\n🚀 {data.get('message')}")
        print(f"   Expected time: {data.get('estimated_time')}")

      elif event_type == "decomposing":
        print(f"\n🧠 {data.get('message')}")

      elif event_type == "perspective_decomposition":
        print(f"   Found {len(data.get('questions', []))} research questions")

      elif event_type == "searching":
        print(f"\n🔍 {data.get('message')}")

      elif event_type == "sources_collected":
        print(f"   ✅ Collected {data.get('count')} sources from {data.get('unique_domains')} domains")

      elif event_type == "extracting_quotes":
        print(f"\n📄 {data.get('message')}")

      elif event_type == "quotes_extracted":
        print(f"   ✅ Extracted {data.get('count')} direct quotes")

      elif event_type == "verifying_facts":
        print(f"\n✓ {data.get('message')}")

      elif event_type == "facts_verified":
        print(f"   ✅ Verified {data.get('verified_count')} facts")

      elif event_type == "cross_verifying":
        print(f"\n⚡ {data.get('message')}")

      elif event_type == "cross_verified":
        print(f"   ✅ Cross-verified {data.get('claims_found')} claims")
        print(f"   📊 {data.get('multi_source_claims')} claims with 3+ sources")

      elif event_type == "confidence_check":
        conf = data.get("confidence", 0)
        threshold = data.get("threshold", 0)
        passed = data.get("passed", False)
        print(f"\n📈 Confidence Score: {conf:.2%}")
        print(f"   Threshold: {threshold:.2%}")
        print(f"   Status: {'✅ PASSED' if passed else '❌ FAILED'}")

      elif event_type == "synthesizing":
        print(f"\n📝 {data.get('message')}")

      elif event_type == "complete":
        print(f"\n{'=' * 80}")
        print("✅ RESEARCH COMPLETE")
        print("=" * 80)

        metadata = data.get("metadata", {})
        print("\n📊 Statistics:")
        print(f"   Duration: {metadata.get('duration_seconds', 0):.1f} seconds")
        print(f"   Sources: {metadata.get('sources_consulted', 0)}")
        print(f"   Quotes: {metadata.get('quotes_extracted', 0)}")
        print(f"   Verified Facts: {metadata.get('verified_facts', 0)}")
        print(f"   Cross-Verified Claims: {metadata.get('cross_verified_claims', 0)}")
        print(f"   Confidence: {metadata.get('confidence_score', 0):.2%}")

        report = data.get("report", "")
        print("\n📄 REPORT:")
        print("=" * 80)
        print(report)
        print("=" * 80)

  except Exception as e:
    print(f"\n❌ Research failed: {e}")
    import traceback

    traceback.print_exc()


if __name__ == "__main__":
  asyncio.run(test_deep_research())
