"""Basic usage examples for the LLM library."""

import asyncio
from pathlib import Path

# Add the src directory to the path so we can import our library
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from definable.llms import provider_factory, session_manager, file_processor
from definable.llms.base.types import ChatRequest, Message, MessageRole
from definable.llms.config import settings


async def example_1_basic_chat():
  """Example 1: Basic chat completion without sessions."""
  print("=== Example 1: Basic Chat Completion ===")

  if not settings.openai_api_key:
    print("Skipping: No OpenAI API key configured")
    return

  try:
    # Get a provider
    provider = provider_factory.get_provider("openai")

    # Create a simple chat request
    messages = [Message(role=MessageRole.USER, content="Hello! Can you tell me a joke?")]

    request = ChatRequest(
      messages=messages,
      model="gpt-3.5-turbo",  # Use cheaper model for examples
      max_tokens=100,
    )

    # Send the request
    response = await provider.chat(request)

    # Print the response
    print(f"Assistant: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}")

  except Exception as e:
    print(f"Error: {e}")


async def example_2_session_chat():
  """Example 2: Session-based conversation with memory."""
  print("\n=== Example 2: Session-Based Chat ===")

  if not settings.openai_api_key:
    print("Skipping: No OpenAI API key configured")
    return

  try:
    # Create a new session
    session = await session_manager.create_session(provider="openai", model="gpt-3.5-turbo")
    print(f"Created session: {session.session_id}")

    # First message
    response1 = await session_manager.chat(
      session_id=session.session_id,
      message="My favorite color is blue. Please remember this.",
    )
    print(f"Assistant: {response1.choices[0].message.content}")

    # Second message that tests memory
    response2 = await session_manager.chat(session_id=session.session_id, message="What's my favorite color?")
    print(f"Assistant: {response2.choices[0].message.content}")

    # Get session stats
    stats = await session_manager.get_session_stats(session.session_id)
    print(f"Session stats: {stats['total_messages']} messages, {stats['total_tokens']} tokens")

    # Clean up
    await session_manager.delete_session(session.session_id)
    print("Session deleted")

  except Exception as e:
    print(f"Error: {e}")


async def example_3_streaming_chat():
  """Example 3: Streaming responses."""
  print("\n=== Example 3: Streaming Chat ===")

  if not settings.openai_api_key:
    print("Skipping: No OpenAI API key configured")
    return

  try:
    # Create session
    session = await session_manager.create_session(provider="openai", model="gpt-3.5-turbo")

    print("Assistant: ", end="")

    # Stream the response
    response_stream = await session_manager.chat(
      session_id=session.session_id,
      message="Tell me a very short story about a robot.",
      stream=True,
    )

    async for chunk in response_stream:
      if chunk.choices and chunk.choices[0].get("delta", {}).get("content"):
        print(chunk.choices[0]["delta"]["content"], end="", flush=True)

    print("\n")  # New line after streaming

    # Clean up
    await session_manager.delete_session(session.session_id)

  except Exception as e:
    print(f"Error: {e}")


async def example_4_file_processing():
  """Example 4: File processing."""
  print("\n=== Example 4: File Processing ===")

  try:
    # Create a sample text file
    sample_file = Path("sample.txt")
    sample_content = """
        This is a sample text file for testing the LLM library.

        It contains multiple paragraphs and should be processed
        into chunks for better handling by language models.

        The file processor can handle various formats including:
        - PDF documents
        - Word documents (DOCX)
        - PowerPoint presentations (PPTX)
        - Excel spreadsheets (XLSX)
        - Plain text files
        - Images (with optional OCR)
        """

    with open(sample_file, "w") as f:
      f.write(sample_content)

    # Process the file
    processed_file = await file_processor.process_file(filename="sample.txt", file_path=sample_file)

    print(f"Processed file: {processed_file.filename}")
    print(f"Original size: {processed_file.size} bytes")
    print(f"Extracted text length: {len(processed_file.processed_text or '')}")
    print(f"Number of chunks: {len(processed_file.chunks or [])}")
    print(f"Metadata: {processed_file.metadata}")

    if processed_file.chunks:
      print("\nFirst chunk:")
      print(processed_file.chunks[0][:200] + "..." if len(processed_file.chunks[0]) > 200 else processed_file.chunks[0])

    # Clean up
    sample_file.unlink()

  except Exception as e:
    print(f"Error: {e}")


async def example_5_provider_info():
  """Example 5: Provider information and capabilities."""
  print("\n=== Example 5: Provider Information ===")

  try:
    # List all available providers
    available_providers = provider_factory.get_available_providers()

    print("Available providers:")
    for provider_info in available_providers:
      print(f"- {provider_info['name']}: {'✓' if provider_info['is_available'] else '✗'}")
      if not provider_info["is_available"]:
        print(f"  Error: {provider_info['error_message']}")

    # Get detailed info for OpenAI if available
    if any(p["name"] == "openai" and p["is_available"] for p in available_providers):
      provider = provider_factory.get_provider("openai")
      capabilities = provider.get_capabilities()

      print("\nOpenAI capabilities:")
      print(f"- Chat: {capabilities.chat}")
      print(f"- Streaming: {capabilities.streaming}")
      print(f"- Function calling: {capabilities.function_calling}")
      print(f"- Vision: {capabilities.vision}")
      print(f"- Image generation: {capabilities.image_generation}")
      print(f"- Max context length: {capabilities.max_context_length}")
      print(f"- Supported models: {len(capabilities.supported_models)} models")

  except Exception as e:
    print(f"Error: {e}")


async def main():
  """Run all examples."""
  print("LLM Library - Basic Usage Examples")
  print("==================================")

  # Check configuration
  print("Configuration:")
  print(f"- OpenAI API Key: {'✓' if settings.openai_api_key else '✗'}")
  print(f"- Default provider: {settings.default_provider}")
  print(f"- Rate limiting: {'✓' if settings.rate_limit_enabled else '✗'}")

  # Run examples
  await example_1_basic_chat()
  await example_2_session_chat()
  await example_3_streaming_chat()
  await example_4_file_processing()
  await example_5_provider_info()

  print("\n=== All Examples Complete ===")


if __name__ == "__main__":
  # Create examples directory if it doesn't exist
  Path("examples").mkdir(exist_ok=True)

  # Run the examples
  asyncio.run(main())
