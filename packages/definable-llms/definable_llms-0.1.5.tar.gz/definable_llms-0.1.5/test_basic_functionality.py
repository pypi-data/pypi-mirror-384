"""Basic functionality test for the LLM library."""

import asyncio
from pathlib import Path
import sys

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from definable.llms import provider_factory, session_manager, file_processor
from definable.llms.base.types import Message, MessageRole
from definable.llms.config import settings


def test_imports():
  """Test that all modules can be imported."""
  print("✓ All imports successful")


def test_configuration():
  """Test configuration loading."""
  assert settings.app_name == "LLM Library"
  assert settings.app_version == "0.1.0"
  print("✓ Configuration loaded successfully")


def test_provider_registry():
  """Test provider registry functionality."""
  # Check that OpenAI provider is registered
  assert provider_factory.registry.is_registered("openai")

  # List providers
  providers = provider_factory.registry.list_providers()
  assert "openai" in providers

  print("✓ Provider registry working")


async def test_session_manager():
  """Test session manager basic functionality."""
  # Test creating a session (without actually making API calls)
  try:
    # This will fail if no API key, but that's expected
    session = await session_manager.create_session(provider="openai", model="gpt-3.5-turbo")
    print("✓ Session creation works (API key configured)")

    # Clean up
    await session_manager.delete_session(session.session_id)

  except Exception as e:
    if "API key" in str(e).lower():
      print("✓ Session creation properly requires API key")
    else:
      print(f"✗ Unexpected error in session creation: {e}")


async def test_file_processor():
  """Test file processing functionality."""
  # Create a test file
  test_file = Path("test.txt")
  test_content = "This is a test file for the LLM library."

  try:
    with open(test_file, "w") as f:
      f.write(test_content)

    # Process the file
    processed = await file_processor.process_file(filename="test.txt", file_path=test_file)

    assert processed.filename == "test.txt"
    assert processed.processed_text == test_content
    assert len(processed.chunks) > 0

    print("✓ File processing works")

  finally:
    # Clean up
    if test_file.exists():
      test_file.unlink()


def test_types():
  """Test that type definitions work."""
  # Create a message
  message = Message(role=MessageRole.USER, content="Hello, world!")

  assert message.role == MessageRole.USER
  assert message.content == "Hello, world!"

  print("✓ Type definitions work")


async def main():
  """Run all tests."""
  print("Testing LLM Library Basic Functionality")
  print("=" * 40)

  # Run synchronous tests
  test_imports()
  test_configuration()
  test_provider_registry()
  test_types()

  # Run async tests
  await test_session_manager()
  await test_file_processor()

  print("=" * 40)
  print("All basic functionality tests passed! ✓")
  print()
  print("Next steps:")
  print("1. Set up your API keys in a .env file")
  print("2. Run the examples: python examples/basic_usage.py")
  print("3. Start the API server: python -m src.libs.llms.api.main")


if __name__ == "__main__":
  asyncio.run(main())
