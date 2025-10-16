"""
Demonstration of Model-Specific Capabilities
=============================================
This demo showcases the new model-specific capability architecture.
"""

import asyncio
import time

from definable.llms import provider_factory, session_manager
from definable.llms.base.types import ModelInfo


class Colors:
  """Terminal color codes for better readability."""

  RESET = "\033[0m"
  BOLD = "\033[1m"
  RED = "\033[91m"
  GREEN = "\033[92m"
  YELLOW = "\033[93m"
  BLUE = "\033[94m"
  MAGENTA = "\033[95m"
  CYAN = "\033[96m"


def print_header(text: str):
  """Print a formatted header."""
  print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
  print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
  print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_section(text: str):
  """Print a section header."""
  print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {text}{Colors.RESET}")
  print(f"{Colors.CYAN}{'-' * (len(text) + 2)}{Colors.RESET}")


def print_model_info(model: ModelInfo):
  """Print detailed model information."""
  caps = model.capabilities

  print(f"\n{Colors.GREEN}📦 Model: {model.name}{Colors.RESET}")
  print(f"  {Colors.YELLOW}Display Name:{Colors.RESET} {model.display_name}")
  print(f"  {Colors.YELLOW}Type:{Colors.RESET} {model.model_type}")
  print(f"  {Colors.YELLOW}Description:{Colors.RESET} {model.description}")

  # Context and tokens
  print(f"  {Colors.CYAN}Context Window:{Colors.RESET} {caps.max_context_length:,} tokens")
  if caps.max_output_tokens:
    print(f"  {Colors.CYAN}Max Output:{Colors.RESET} {caps.max_output_tokens:,} tokens")

  # Features
  features = []
  if caps.chat:
    features.append("💬 Chat")
  if caps.vision:
    features.append("👁️ Vision")
  if caps.function_calling:
    features.append("🔧 Functions")
  if caps.streaming:
    features.append("📡 Streaming")
  if caps.embeddings:
    features.append("🔍 Embeddings")
  if caps.image_generation:
    features.append("🎨 Images")

  if features:
    print(f"  {Colors.YELLOW}Features:{Colors.RESET} {' | '.join(features)}")

  # Cost information
  if caps.input_cost_per_token:
    input_cost_1k = caps.input_cost_per_token * 1000
    print(f"  {Colors.MAGENTA}Input Cost:{Colors.RESET} ${input_cost_1k:.6f} per 1K tokens")
  if caps.output_cost_per_token:
    output_cost_1k = caps.output_cost_per_token * 1000
    print(f"  {Colors.MAGENTA}Output Cost:{Colors.RESET} ${output_cost_1k:.6f} per 1K tokens")


async def demo_model_discovery():
  """Demonstrate model discovery and capabilities."""
  print_header("MODEL DISCOVERY & CAPABILITIES")

  try:
    provider = provider_factory.get_provider("openai")

    # Get all supported models
    all_models = provider.get_supported_models()

    print(f"{Colors.BOLD}Found {len(all_models)} models from OpenAI{Colors.RESET}")

    # Group by type
    chat_models = [m for m in all_models if m.model_type == "chat"]
    embedding_models = [m for m in all_models if m.model_type == "embedding"]
    image_models = [m for m in all_models if m.model_type == "image"]

    print(f"  • {Colors.CYAN}Chat Models:{Colors.RESET} {len(chat_models)}")
    print(f"  • {Colors.CYAN}Embedding Models:{Colors.RESET} {len(embedding_models)}")
    print(f"  • {Colors.CYAN}Image Models:{Colors.RESET} {len(image_models)}")

    # Show detailed info for select models
    print_section("Featured Chat Models")

    featured = ["gpt-4-turbo", "gpt-3.5-turbo", "gpt-4-vision-preview"]
    for model_name in featured:
      model_info = provider.get_model_info(model_name)
      print_model_info(model_info)

    print_section("Embedding Models")
    for model in embedding_models:
      print_model_info(model)

    print_section("Image Generation Models")
    for model in image_models:
      print_model_info(model)

  except Exception as e:
    print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def demo_capability_comparison():
  """Compare capabilities across models."""
  print_header("MODEL CAPABILITY COMPARISON")

  try:
    provider = provider_factory.get_provider("openai")

    print_section("Vision Capability Comparison")

    vision_tests = [
      "gpt-4-turbo",
      "gpt-4-vision-preview",
      "gpt-3.5-turbo",
      "gpt-4",
    ]

    print(f"\n{'Model':<25} {'Vision':<10} {'Context':<15} {'Cost/1K Input':<15}")
    print("-" * 65)

    for model_name in vision_tests:
      try:
        caps = provider.get_model_capabilities(model_name)
        vision = "✅ Yes" if caps.vision else "❌ No"
        context = f"{caps.max_context_length:,}"
        cost = f"${caps.input_cost_per_token * 1000:.4f}" if caps.input_cost_per_token else "N/A"

        print(f"{model_name:<25} {vision:<10} {context:<15} {cost:<15}")
      except Exception as e:
        print(f"{model_name:<25} {'Error':<10} {str(e)[:40]}")

    print_section("Context Length Comparison")

    context_models = [
      "gpt-4-turbo",
      "gpt-4",
      "gpt-3.5-turbo",
      "gpt-3.5-turbo-16k",
    ]

    for model_name in context_models:
      try:
        caps = provider.get_model_capabilities(model_name)
        bar_length = int(caps.max_context_length / 2000)  # Scale for display
        bar = "█" * min(bar_length, 50)

        print(f"{model_name:<20} {caps.max_context_length:>7,} tokens {Colors.CYAN}{bar}{Colors.RESET}")
      except Exception:
        pass

    print_section("Cost Efficiency Analysis")

    print(f"\n{'Model':<25} {'Input $/1M':<15} {'Output $/1M':<15} {'Ratio':<10}")
    print("-" * 65)

    cost_models = ["gpt-4-turbo", "gpt-4", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]

    for model_name in cost_models:
      try:
        caps = provider.get_model_capabilities(model_name)
        if caps.input_cost_per_token and caps.output_cost_per_token:
          input_per_m = caps.input_cost_per_token * 1_000_000
          output_per_m = caps.output_cost_per_token * 1_000_000
          ratio = output_per_m / input_per_m if input_per_m > 0 else 0

          print(f"{model_name:<25} ${input_per_m:<14.2f} ${output_per_m:<14.2f} {ratio:<10.1f}x")
      except Exception:
        pass

  except Exception as e:
    print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def demo_model_validation():
  """Demonstrate model validation and session creation."""
  print_header("MODEL VALIDATION & SESSION CREATION")

  try:
    print_section("Testing Model Validation")

    test_cases = [
      ("gpt-4-turbo", True, "Latest GPT-4 with vision"),
      ("gpt-3.5-turbo", True, "Fast and efficient"),
      ("claude-3-opus", False, "Different provider"),
      ("gpt-5", False, "Future model"),
      ("dall-e-3", True, "Image generation"),
    ]

    provider = provider_factory.get_provider("openai")

    for model_name, expected, description in test_cases:
      try:
        is_valid = await provider.validate_model(model_name)
        status = f"{Colors.GREEN}✅ Valid{Colors.RESET}" if is_valid else f"{Colors.RED}❌ Invalid{Colors.RESET}"
        match = "✓" if is_valid == expected else "✗"
        print(f"  {model_name:<20} {status:<20} {description:<30} {match}")
      except Exception as e:
        print(f"  {model_name:<20} {Colors.RED}Error{Colors.RESET} {str(e)[:50]}")

    print_section("Creating Sessions with Model Validation")

    # Test creating session with valid model
    print(f"\n{Colors.YELLOW}Creating session with GPT-4 Turbo...{Colors.RESET}")
    session = await session_manager.create_session(provider="openai", model="gpt-4-turbo")

    print(f"  {Colors.GREEN}✅ Session created:{Colors.RESET} {session.session_id[:8]}...")

    # Check metadata
    if "model_capabilities" in session.metadata:
      model_caps = session.metadata["model_info"]
      print(f"  {Colors.CYAN}Model Info in Session:{Colors.RESET}")
      print(f"    - Display Name: {model_caps.get('display_name')}")
      print(f"    - Max Context: {model_caps.get('max_context_length'):,} tokens")
      print(f"    - Supports Vision: {model_caps.get('supports_vision')}")
      print(f"    - Supports Functions: {model_caps.get('supports_function_calling')}")

    await session_manager.delete_session(session.session_id)
    print(f"  {Colors.GREEN}✅ Session cleaned up{Colors.RESET}")

    # Test creating session with invalid model
    print(f"\n{Colors.YELLOW}Attempting to create session with invalid model...{Colors.RESET}")
    try:
      await session_manager.create_session(provider="openai", model="gpt-99-ultra")
      print(f"  {Colors.RED}❌ Should have failed!{Colors.RESET}")
    except Exception as e:
      print(f"  {Colors.GREEN}✅ Correctly rejected:{Colors.RESET} {type(e).__name__}")
      print(f"    Message: {str(e)}")

  except Exception as e:
    print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def demo_use_case_selection():
  """Demonstrate selecting the right model for different use cases."""
  print_header("INTELLIGENT MODEL SELECTION")

  try:
    provider = provider_factory.get_provider("openai")

    print_section("Use Case: Need Vision Support")

    all_models = provider.get_supported_models()
    vision_models = [m for m in all_models if m.model_type == "chat" and m.capabilities.vision]

    print(f"Found {len(vision_models)} models with vision support:")
    for model in vision_models:
      caps = model.capabilities
      cost = caps.input_cost_per_token * 1000 if caps.input_cost_per_token else 0
      print(f"  • {Colors.GREEN}{model.name}{Colors.RESET}")
      print(f"    Context: {caps.max_context_length:,} tokens | Cost: ${cost:.4f}/1K")

    print_section("Use Case: Cost-Optimized for High Volume")

    chat_models = [m for m in all_models if m.model_type == "chat"]
    sorted_by_cost = sorted(
      chat_models,
      key=lambda m: m.capabilities.input_cost_per_token or float("inf"),
    )

    print("Most cost-effective models:")
    for model in sorted_by_cost[:3]:
      caps = model.capabilities
      cost = caps.input_cost_per_token * 1000 if caps.input_cost_per_token else 0
      print(f"  • {Colors.GREEN}{model.name}{Colors.RESET}")
      print(f"    ${cost:.6f}/1K tokens | Context: {caps.max_context_length:,}")

    print_section("Use Case: Maximum Context Window")

    sorted_by_context = sorted(chat_models, key=lambda m: m.capabilities.max_context_length, reverse=True)

    print("Largest context windows:")
    for model in sorted_by_context[:3]:
      caps = model.capabilities
      print(f"  • {Colors.GREEN}{model.name}{Colors.RESET}")
      print(f"    {caps.max_context_length:,} tokens")
      if caps.vision:
        print(f"    {Colors.YELLOW}+ Vision support{Colors.RESET}")

    print_section("Use Case: Embeddings Generation")

    embedding_models = [m for m in all_models if m.model_type == "embedding"]

    print("Available embedding models:")
    for model in embedding_models:
      caps = model.capabilities
      cost = caps.input_cost_per_token * 1_000_000 if caps.input_cost_per_token else 0
      print(f"  • {Colors.GREEN}{model.name}{Colors.RESET}")
      print(f"    ${cost:.2f} per million tokens")

  except Exception as e:
    print(f"{Colors.RED}Error: {e}{Colors.RESET}")


async def main():
  """Run all demonstrations."""
  print(f"\n{Colors.BOLD}{Colors.MAGENTA}")
  print("=" * 80)
  print("MODEL-SPECIFIC CAPABILITIES DEMONSTRATION".center(80))
  print("Showcasing the new architecture improvements".center(80))
  print("=" * 80)
  print(f"{Colors.RESET}\n")

  start_time = time.time()

  # Run all demos
  await demo_model_discovery()
  await demo_capability_comparison()
  await demo_model_validation()
  await demo_use_case_selection()

  # Summary
  elapsed = time.time() - start_time
  print_header("DEMONSTRATION COMPLETE")

  print(f"{Colors.GREEN}✅ All demonstrations completed successfully!{Colors.RESET}")
  print(f"{Colors.CYAN}Total time: {elapsed:.2f} seconds{Colors.RESET}")

  print(f"\n{Colors.BOLD}Key Takeaways:{Colors.RESET}")
  print("• Models now have individual capability definitions")
  print("• Accurate representation of vision, context, and cost")
  print("• Intelligent model selection based on requirements")
  print("• Enhanced validation prevents feature misuse")
  print("• Session management includes capability metadata")

  print(f"\n{Colors.YELLOW}The architecture now accurately represents that:{Colors.RESET}")
  print("• GPT-4 Turbo has vision, GPT-3.5 doesn't")
  print("• Different models have different context windows")
  print("• Costs vary significantly between models")
  print("• Not all models support all features")


if __name__ == "__main__":
  asyncio.run(main())
