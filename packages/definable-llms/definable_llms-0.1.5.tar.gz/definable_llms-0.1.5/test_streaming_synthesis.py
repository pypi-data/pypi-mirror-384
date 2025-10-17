"""Test streaming report synthesis to see real-time chunks."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from definable.llms.research.orchestrator.research_orchestrator import DeepResearchOrchestrator
from definable.llms.research.state.research_state import ResearchState
from definable.llms.research.types import ExtractedQuote
from definable.llms.config import settings


async def test_streaming_synthesis():
  """Test the streaming synthesis function."""

  print("=" * 80)
  print("🧪 TESTING STREAMING REPORT SYNTHESIS")
  print("=" * 80)

  # Get API key
  exa_key = settings.exa_api_key.get_secret_value() if settings.exa_api_key else None

  if not exa_key:
    raise ValueError("EXA_API_KEY not found")

  # Initialize orchestrator
  orchestrator = DeepResearchOrchestrator(exa_api_key=exa_key)

  # Create mock research state with sample quotes
  state = ResearchState()

  # Add some fake quotes for testing
  sample_quotes = [
    ExtractedQuote(
      quote="Quantum computing represents a fundamental shift in computing paradigm",
      context_before="In recent developments,",
      context_after="researchers have made significant progress.",
      source_url="https://example.com/quantum1",
      source_title="Quantum Computing Advances",
      location="middle",
      extraction_confidence=0.95,
    ),
    ExtractedQuote(
      quote="Error rates have decreased by 45% in the latest superconducting qubits",
      context_before="According to the latest benchmarks,",
      context_after="which marks a major milestone.",
      source_url="https://example.com/quantum2",
      source_title="Qubit Error Reduction",
      location="middle",
      extraction_confidence=0.92,
    ),
    ExtractedQuote(
      quote="Google's Willow processor achieved quantum error correction below threshold",
      context_before="In a groundbreaking demonstration,",
      context_after="paving the way for fault-tolerant quantum computing.",
      source_url="https://example.com/quantum3",
      source_title="Google Quantum Breakthrough",
      location="middle",
      extraction_confidence=0.98,
    ),
  ]

  state.add_quotes(sample_quotes)

  query = "What are the latest breakthroughs in quantum computing?"

  print(f"\n📝 Query: {query}")
  print(f"📊 State: {len(sample_quotes)} sample quotes loaded")
  print("-" * 80)
  print("\n🔄 Starting streaming synthesis...\n")
  print("=" * 80)

  # Stream the synthesis
  chunk_count = 0
  total_chars = 0

  try:
    async for chunk in orchestrator._synthesize_report(query, state):
      chunk_count += 1
      total_chars += len(chunk)

      # Print chunk with visual separator
      print(f"[CHUNK {chunk_count}] ", end="", flush=True)
      print(chunk, end="", flush=True)

      # Small delay to simulate real-time feel (optional)
      await asyncio.sleep(0.01)

    print("\n" + "=" * 80)
    print("\n✅ Streaming complete!")
    print(f"   Total chunks: {chunk_count}")
    print(f"   Total characters: {total_chars}")
    print(f"   Average chunk size: {total_chars // chunk_count if chunk_count > 0 else 0} chars")

  except Exception as e:
    print(f"\n❌ Error during streaming: {e}")
    import traceback

    traceback.print_exc()


if __name__ == "__main__":
  asyncio.run(test_streaming_synthesis())
