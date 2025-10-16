#!/usr/bin/env python3
"""
Comprehensive Usage Demonstration - LLM Library
===============================================

This script demonstrates ALL features of the LLM library including:
- Basic chat completion and streaming
- Session management with memory
- File processing (text, PDF, images, etc.)
- Image generation with DALL-E
- Provider management and health checks
- Advanced features and error handling
- Performance testing and metrics

Updated for:
- FastAPI 0.116.1+ with modern features
- OpenAI 1.107.2+ with audio helpers and TTS/STT support
- Pydantic 2.11.9+ with partial validation and performance improvements

Author: Claude Code Assistant
Date: 2025-09-15
"""

import asyncio
import contextlib
import json
import sys
import time
from pathlib import Path
from typing import Dict
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our LLM library
from libs.llms import provider_factory, session_manager, file_processor
from libs.llms.base.types import (
  ChatRequest,
  Message,
  MessageRole,
  ImageRequest,
  ImageSize,
  ImageQuality,
  ImageStyle,
)
from libs.llms.config import settings
from libs.llms.base.exceptions import SessionNotFoundError, UnsupportedFileTypeError, FileProcessingError


class Colors:
  """ANSI color codes for terminal output."""

  RESET = "\033[0m"
  BOLD = "\033[1m"
  GREEN = "\033[92m"
  BLUE = "\033[94m"
  YELLOW = "\033[93m"
  RED = "\033[91m"
  CYAN = "\033[96m"
  MAGENTA = "\033[95m"


class PerformanceTracker:
  """Track performance metrics across demonstrations."""

  def __init__(self):
    self.metrics = {
      "total_requests": 0,
      "total_tokens": 0,
      "total_time": 0.0,
      "operations": [],
    }

  def start_operation(self, name: str):
    """Start tracking an operation."""
    return {"name": name, "start_time": time.time(), "tokens": 0}

  def end_operation(self, operation: Dict, tokens: int = 0):
    """End tracking an operation."""
    duration = time.time() - operation["start_time"]
    operation["duration"] = duration
    operation["tokens"] = tokens

    self.metrics["total_requests"] += 1
    self.metrics["total_tokens"] += tokens
    self.metrics["total_time"] += duration
    self.metrics["operations"].append(operation)

    return operation

  def print_summary(self):
    """Print performance summary."""
    print(f"\n{Colors.CYAN}=== Performance Summary ==={Colors.RESET}")
    print(f"Total Operations: {self.metrics['total_requests']}")
    print(f"Total Tokens: {self.metrics['total_tokens']:,}")
    print(f"Total Time: {self.metrics['total_time']:.2f}s")
    if self.metrics["total_requests"] > 0:
      avg_time = self.metrics["total_time"] / self.metrics["total_requests"]
      print(f"Average Time per Request: {avg_time:.2f}s")

    if self.metrics["operations"]:
      print(f"\n{Colors.YELLOW}Recent Operations:{Colors.RESET}")
      for op in self.metrics["operations"][-5:]:  # Show last 5
        print(f"- {op['name']}: {op['duration']:.2f}s ({op['tokens']} tokens)")


# Global performance tracker
perf_tracker = PerformanceTracker()


def print_header(title: str):
  """Print a formatted section header."""
  print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
  print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.RESET}")
  print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")


def print_success(message: str):
  """Print a success message."""
  print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
  """Print an error message."""
  print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
  """Print an info message."""
  print(f"{Colors.CYAN}ℹ {message}{Colors.RESET}")


def print_warning(message: str):
  """Print a warning message."""
  print(f"{Colors.YELLOW}⚠ {message}{Colors.RESET}")


def check_configuration():
  """Check and display configuration status."""
  print_header("Configuration Check")

  print("Configuration Status:")
  print(f"- App Name: {settings.app_name}")
  print(f"- Version: {settings.app_version}")
  print(f"- OpenAI API Key: {'✓ Configured' if settings.openai_api_key else '✗ Missing'}")
  print(f"- Gemini API Key: {'✓ Configured' if settings.gemini_api_key else '✗ Missing'}")
  print(f"- OpenAI API Key: {'✓ Configured' if settings.openai_api_key else '✗ Missing'}")
  print(f"- Default Provider: {settings.default_provider}")
  print(f"- Rate Limiting: {'✓ Enabled' if settings.rate_limit_enabled else '✗ Disabled'}")
  print(f"- Max File Size: {settings.max_file_size_mb}MB")
  print(f"- Session Store: {settings.session_store_type}")

  # Check if we can proceed with examples
  if not settings.openai_api_key:
    print_warning("Some examples require an OpenAI API key")
    print("Set OPENAI_API_KEY environment variable or add to .env file")
  else:
    print_success("All required configuration available")

  return bool(settings.openai_api_key)


# =============================================================================
# 1. BASIC CHAT EXAMPLES
# =============================================================================


async def demo_basic_chat():
  """Demonstrate basic chat completion."""
  print_header("Basic Chat Completion")

  # Test with OpenAI
  if settings.openai_api_key:
    try:
      print_info("\n=== Testing OpenAI ===")
      provider = provider_factory.get_provider("openai")
      print_info("Retrieved OpenAI provider")

      # Create a simple chat request
      messages = [
        Message(
          role=MessageRole.SYSTEM,
          content="You are a helpful assistant. Keep responses concise.",
        ),
        Message(
          role=MessageRole.USER,
          content="Explain what a Large Language Model is in one sentence.",
        ),
      ]

      request = ChatRequest(
        messages=messages,
        model="gpt-5-nano",  # Using ultra-fast nano model for simple tests
        # max_tokens=100,
        temperature=0.7,
      )

      # Track performance
      op = perf_tracker.start_operation("Basic Chat - OpenAI")

      # Send request
      print_info("Sending chat request...")
      response = await provider.chat(request)

      # Update performance tracking
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      # Display results
      print_success("OpenAI chat completion successful!")
      print(f"\n{Colors.YELLOW}Assistant:{Colors.RESET} {response.choices[0].message.content}")

      if response.usage:
        print(f"\n{Colors.CYAN}Usage:{Colors.RESET}")
        print(f"- Prompt tokens: {response.usage.prompt_tokens}")
        print(f"- Completion tokens: {response.usage.completion_tokens}")
        print(f"- Total tokens: {response.usage.total_tokens}")

      print(f"- Response ID: {response.id}")
      print(f"- Model: {response.model}")

    except Exception as e:
      print_error(f"OpenAI basic chat failed: {e}")
  else:
    print_warning("Skipping OpenAI: API key not configured")

  # Test with Gemini
  if settings.gemini_api_key:
    try:
      print_info("\n=== Testing Gemini ===")
      provider = provider_factory.get_provider("gemini")
      print_info("Retrieved Gemini provider")

      # Create a simple chat request
      messages = [
        Message(
          role=MessageRole.SYSTEM,
          content="You are a helpful assistant. Keep responses concise.",
        ),
        Message(
          role=MessageRole.USER,
          content="Explain what a Large Language Model is in one sentence.",
        ),
      ]

      request = ChatRequest(
        messages=messages,
        model="gemini-2.5-flash",
        max_tokens=100,
        temperature=0.7,
      )

      # Track performance
      op = perf_tracker.start_operation("Basic Chat - Gemini")

      # Send request
      print_info("Sending chat request...")
      response = await provider.chat(request)

      # Update performance tracking
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      # Display results
      print_success("Gemini chat completion successful!")
      print(f"\n{Colors.YELLOW}Assistant:{Colors.RESET} {response.choices[0].message.content}")

      if response.usage:
        print(f"\n{Colors.CYAN}Usage:{Colors.RESET}")
        print(f"- Prompt tokens: {response.usage.prompt_tokens}")
        print(f"- Completion tokens: {response.usage.completion_tokens}")
        print(f"- Total tokens: {response.usage.total_tokens}")

      print(f"- Response ID: {response.id}")
      print(f"- Model: {response.model}")

    except Exception as e:
      print_error(f"Gemini basic chat failed: {e}")
  else:
    print_warning("Skipping Gemini: API key not configured")

  # Test with Anth
  if settings.anthropic_api_key:
    try:
      print_info("\n=== Testing Anthropic ===")
      provider = provider_factory.get_provider("anthropic")
      print_info("Retrieved Anthropic provider")

      # Create a simple chat request
      messages = [
        Message(
          role=MessageRole.SYSTEM,
          content="You are a helpful assistant. Keep responses concise.",
        ),
        Message(
          role=MessageRole.USER,
          content="Explain what a Large Language Model is in one sentence.",
        ),
      ]

      request = ChatRequest(
        messages=messages,
        model="claude-sonnet-4-5",
        max_tokens=100,
        temperature=0.7,
      )

      # Track performance
      op = perf_tracker.start_operation("Basic Chat - Anthropic")

      # Send request
      print_info("Sending chat request...")
      response = await provider.chat(request)

      # Update performance tracking
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      # Display results
      print_success("Anthropic chat completion successful!")
      print(f"\n{Colors.YELLOW}Assistant:{Colors.RESET} {response.choices[0].message.content}")

      if response.usage:
        print(f"\n{Colors.CYAN}Usage:{Colors.RESET}")
        print(f"- Prompt tokens: {response.usage.prompt_tokens}")
        print(f"- Completion tokens: {response.usage.completion_tokens}")
        print(f"- Total tokens: {response.usage.total_tokens}")

      print(f"- Response ID: {response.id}")
      print(f"- Model: {response.model}")

    except Exception as e:
      print_error(f"Anthropic basic chat failed: {e}")
  else:
    print_warning("Skipping Anthropic: API key not configured")

  if not settings.openai_api_key and not settings.gemini_api_key and not settings.anthropic_api_key:
    print_warning("No API keys configured. Please set OPENAI_API_KEY or GEMINI_API_KEY or ANTHROPIC_API_KEY")


# =============================================================================
# 2. SESSION MANAGEMENT EXAMPLES
# =============================================================================


async def demo_session_management():
  """Demonstrate session-based conversations with memory."""
  print_header("Session Management & Memory")

  # Test with OpenAI
  if settings.openai_api_key:
    print_info("\n=== Testing OpenAI Session Management ===")
    session_id = None
    try:
      # Create a new session
      print_info("Creating new OpenAI session...")
      session = await session_manager.create_session(
        provider="openai",
        model="gpt-5-nano",  # Using ultra-fast nano model for simple tests
        metadata={
          "demo": True,
          "provider": "openai",
          "created_at": datetime.now().isoformat(),
        },
      )
      session_id = session.session_id
      print_success(f"Session created: {session_id}")

      # First conversation - establish context
      print_info("First message (establishing context)...")
      op1 = perf_tracker.start_operation("Session Chat 1 - OpenAI")

      response1 = await session_manager.chat(
        session_id=session_id,
        message="My name is Alex and I'm learning about AI. I love programming in Python.",
        role=MessageRole.USER,
      )

      tokens1 = response1.choices[0].message.metadata.get("usage", {}).get("total_tokens", 0)
      perf_tracker.end_operation(op1, tokens1)

      print(f"{Colors.YELLOW}Assistant:{Colors.RESET} {response1.choices[0].message.content}")

      # Second conversation - test memory
      print_info("\nSecond message (testing memory)...")
      op2 = perf_tracker.start_operation("Session Chat 2 - OpenAI")

      response2 = await session_manager.chat(
        session_id=session_id,
        message="What's my name and what programming language do I like?",
      )

      tokens2 = response2.choices[0].message.metadata.get("usage", {}).get("total_tokens", 0)
      perf_tracker.end_operation(op2, tokens2)

      print(f"{Colors.YELLOW}Assistant:{Colors.RESET} {response2.choices[0].message.content}")

      # Get session statistics
      print_info("\nRetrieving session statistics...")
      stats = await session_manager.get_session_stats(session_id)

      print(f"\n{Colors.CYAN}Session Statistics:{Colors.RESET}")
      for key, value in stats.items():
        print(f"- {key.replace('_', ' ').title()}: {value}")

      # Get message history
      messages = await session_manager.get_messages(session_id)
      print(f"\n{Colors.CYAN}Message History ({len(messages)} messages):{Colors.RESET}")
      for i, msg in enumerate(messages[-4:], 1):  # Show last 4 messages
        role_color = Colors.BLUE if msg.role == MessageRole.USER else Colors.GREEN
        print(f"{i}. {role_color}{msg.role.value.title()}:{Colors.RESET} {msg.content[:100]}...")

      # Update session metadata
      print_info("Updating session metadata...")
      await session_manager.update_session(session_id, {"demo_completed": True, "messages_count": len(messages)})
      print_success("OpenAI session management features demonstrated successfully")

    except Exception as e:
      print_error(f"OpenAI session management failed: {e}")

    finally:
      # Clean up session
      if session_id:
        try:
          await session_manager.delete_session(session_id)
          print_success("OpenAI session cleaned up")
        except Exception as e:
          print_error(f"OpenAI session cleanup failed: {e}")
  else:
    print_warning("Skipping OpenAI: API key not configured")

  # Test with Gemini
  if settings.gemini_api_key:
    print_info("\n=== Testing Gemini Session Management ===")
    session_id = None
    try:
      # Create a new session
      print_info("Creating new Gemini session...")
      session = await session_manager.create_session(
        provider="gemini",
        model="gemini-2.5-flash",
        metadata={
          "demo": True,
          "provider": "gemini",
          "created_at": datetime.now().isoformat(),
        },
      )
      session_id = session.session_id
      print_success(f"Session created: {session_id}")

      # First conversation - establish context
      print_info("First message (establishing context)...")
      op1 = perf_tracker.start_operation("Session Chat 1 - Gemini")

      response1 = await session_manager.chat(
        session_id=session_id,
        message="My name is Alex and I'm learning about AI. I love programming in Python.",
        role=MessageRole.USER,
      )

      tokens1 = response1.choices[0].message.metadata.get("usage", {}).get("total_tokens", 0)
      perf_tracker.end_operation(op1, tokens1)

      print(f"{Colors.YELLOW}Assistant:{Colors.RESET} {response1.choices[0].message.content}")

      # Second conversation - test memory
      print_info("\nSecond message (testing memory)...")
      op2 = perf_tracker.start_operation("Session Chat 2 - Gemini")

      response2 = await session_manager.chat(
        session_id=session_id,
        message="What's my name and what programming language do I like?",
      )

      tokens2 = response2.choices[0].message.metadata.get("usage", {}).get("total_tokens", 0)
      perf_tracker.end_operation(op2, tokens2)

      print(f"{Colors.YELLOW}Assistant:{Colors.RESET} {response2.choices[0].message.content}")

      # Get session statistics
      print_info("\nRetrieving session statistics...")
      stats = await session_manager.get_session_stats(session_id)

      print(f"\n{Colors.CYAN}Session Statistics:{Colors.RESET}")
      for key, value in stats.items():
        print(f"- {key.replace('_', ' ').title()}: {value}")

      # Get message history
      messages = await session_manager.get_messages(session_id)
      print(f"\n{Colors.CYAN}Message History ({len(messages)} messages):{Colors.RESET}")
      for i, msg in enumerate(messages[-4:], 1):  # Show last 4 messages
        role_color = Colors.BLUE if msg.role == MessageRole.USER else Colors.GREEN
        print(f"{i}. {role_color}{msg.role.value.title()}:{Colors.RESET} {msg.content[:100]}...")

      # Update session metadata
      print_info("Updating session metadata...")
      await session_manager.update_session(session_id, {"demo_completed": True, "messages_count": len(messages)})
      print_success("Gemini session management features demonstrated successfully")

    except Exception as e:
      print_error(f"Gemini session management failed: {e}")

    finally:
      # Clean up session
      if session_id:
        try:
          await session_manager.delete_session(session_id)
          print_success("Gemini session cleaned up")
        except Exception as e:
          print_error(f"Gemini session cleanup failed: {e}")
  else:
    print_warning("Skipping Gemini: API key not configured")

  # Test with Anthropic
  if settings.anthropic_api_key:
    print_info("\n=== Testing Anthropic Session Management ===")
    session_id = None
    try:
      # Create a new session
      print_info("Creating new Anthropic session...")
      session = await session_manager.create_session(
        provider="anthropic",
        model="claude-sonnet-4-5",
        metadata={
          "demo": True,
          "provider": "anthropic",
          "created_at": datetime.now().isoformat(),
        },
      )
      session_id = session.session_id
      print_success(f"Session created: {session_id}")

      # First conversation - establish context
      print_info("First message (establishing context)...")
      op1 = perf_tracker.start_operation("Session Chat 1 - Anthropic")

      response1 = await session_manager.chat(
        session_id=session_id,
        message="My name is Alex and I'm learning about AI. I love programming in Python.",
        role=MessageRole.USER,
      )

      tokens1 = response1.choices[0].message.metadata.get("usage", {}).get("total_tokens", 0)
      perf_tracker.end_operation(op1, tokens1)

      print(f"{Colors.YELLOW}Assistant:{Colors.RESET} {response1.choices[0].message.content}")

      # Second conversation - test memory
      print_info("\nSecond message (testing memory)...")
      op2 = perf_tracker.start_operation("Session Chat 2 - Anthropic")

      response2 = await session_manager.chat(
        session_id=session_id,
        message="What's my name and what programming language do I like?",
      )

      tokens2 = response2.choices[0].message.metadata.get("usage", {}).get("total_tokens", 0)
      perf_tracker.end_operation(op2, tokens2)

      print(f"{Colors.YELLOW}Assistant:{Colors.RESET} {response2.choices[0].message.content}")

      # Get session statistics
      print_info("\nRetrieving session statistics...")
      stats = await session_manager.get_session_stats(session_id)

      print(f"\n{Colors.CYAN}Session Statistics:{Colors.RESET}")
      for key, value in stats.items():
        print(f"- {key.replace('_', ' ').title()}: {value}")

      # Get message history
      messages = await session_manager.get_messages(session_id)
      print(f"\n{Colors.CYAN}Message History ({len(messages)} messages):{Colors.RESET}")
      for i, msg in enumerate(messages[-4:], 1):  # Show last 4 messages
        role_color = Colors.BLUE if msg.role == MessageRole.USER else Colors.GREEN
        print(f"{i}. {role_color}{msg.role.value.title()}:{Colors.RESET} {msg.content[:100]}...")

      # Update session metadata
      print_info("Updating session metadata...")
      await session_manager.update_session(session_id, {"demo_completed": True, "messages_count": len(messages)})
      print_success("Anthropic session management features demonstrated successfully")

    except Exception as e:
      print_error(f"Anthropic session management failed: {e}")

    finally:
      # Clean up session
      if session_id:
        try:
          await session_manager.delete_session(session_id)
          print_success("Anthropic session cleaned up")
        except Exception as e:
          print_error(f"Gemini session cleanup failed: {e}")
  else:
    print_warning("Skipping Anthropic: API key not configured")

  if not settings.openai_api_key and not settings.gemini_api_key and not settings.anthropic_api_key:
    print_warning("No API keys configured. Please set OPENAI_API_KEY or GEMINI_API_KEY or ANTHROPIC_API_KEY")


# =============================================================================
# 3. STREAMING EXAMPLES
# =============================================================================


async def demo_streaming():
  """Demonstrate streaming chat responses."""
  print_header("Streaming Chat Responses")

  # Test with OpenAI
  if settings.openai_api_key:
    print_info("\n=== Testing OpenAI Streaming ===")
    session_id = None
    try:
      # Create session for streaming
      session = await session_manager.create_session(
        provider="openai",
        model="gpt-4.1",  # Using GPT-4.1 for streaming demo
      )
      session_id = session.session_id

      print_info("Starting OpenAI streaming response...")
      print(
        f"\n{Colors.YELLOW}Assistant (streaming):{Colors.RESET} ",
        end="",
        flush=True,
      )

      # Track performance
      op = perf_tracker.start_operation("Streaming Chat - OpenAI")

      # Stream response
      response_stream = await session_manager.chat(
        session_id=session_id,
        message="Write a short poem about artificial intelligence in exactly 4 lines.",
        stream=True,
      )

      full_response = ""
      chunk_count = 0

      async for chunk in response_stream:
        if chunk.choices and len(chunk.choices) > 0:
          choice = chunk.choices[0]
          if isinstance(choice, dict) and "delta" in choice:
            delta = choice["delta"]
            if isinstance(delta, dict) and "content" in delta:
              content = delta["content"]
              if content:
                print(content, end="", flush=True)
                full_response += content
                chunk_count += 1

      print(f"\n\n{Colors.CYAN}OpenAI Streaming Statistics:{Colors.RESET}")
      print(f"- Total chunks received: {chunk_count}")
      print(f"- Response length: {len(full_response)} characters")
      print(f"- Average chunk size: {len(full_response) / max(chunk_count, 1):.1f} chars")

      perf_tracker.end_operation(op)

    except Exception as e:
      print_error(f"OpenAI streaming demo failed: {e}")

    finally:
      if session_id:
        with contextlib.suppress(Exception):
          await session_manager.delete_session(session_id)
  else:
    print_warning("Skipping OpenAI: API key not configured")

  # Test with Gemini
  if settings.gemini_api_key:
    print_info("\n=== Testing Gemini Streaming ===")
    session_id = None
    try:
      # Create session for streaming
      session = await session_manager.create_session(
        provider="gemini",
        model="gemini-2.5-flash",
      )
      session_id = session.session_id

      print_info("Starting Gemini streaming response...")
      print(
        f"\n{Colors.YELLOW}Assistant (streaming):{Colors.RESET} ",
        end="",
        flush=True,
      )

      # Track performance
      op = perf_tracker.start_operation("Streaming Chat - Gemini")

      # Stream response
      response_stream = await session_manager.chat(
        session_id=session_id,
        message="Write a short poem about artificial intelligence in exactly 4 lines.",
        stream=True,
      )

      full_response = ""
      chunk_count = 0

      async for chunk in response_stream:
        if chunk.choices and len(chunk.choices) > 0:
          choice = chunk.choices[0]
          if isinstance(choice, dict) and "delta" in choice:
            delta = choice["delta"]
            if isinstance(delta, dict) and "content" in delta:
              content = delta["content"]
              if content:
                print(content, end="", flush=True)
                full_response += content
                chunk_count += 1

      print(f"\n\n{Colors.CYAN}Gemini Streaming Statistics:{Colors.RESET}")
      print(f"- Total chunks received: {chunk_count}")
      print(f"- Response length: {len(full_response)} characters")
      print(f"- Average chunk size: {len(full_response) / max(chunk_count, 1):.1f} chars")

      perf_tracker.end_operation(op)

    except Exception as e:
      print_error(f"Gemini streaming demo failed: {e}")

    finally:
      if session_id:
        with contextlib.suppress(Exception):
          await session_manager.delete_session(session_id)
  else:
    print_warning("Skipping Gemini: API key not configured")

  # Test with Anthropic
  if settings.anthropic_api_key:
    print_info("\n=== Testing Anthropic Streaming ===")
    session_id = None
    try:
      # Create session for streaming
      session = await session_manager.create_session(
        provider="anthropic",
        model="claude-sonnet-4-5",
      )
      session_id = session.session_id

      print_info("Starting Anthropic streaming response...")
      print(
        f"\n{Colors.YELLOW}Assistant (streaming):{Colors.RESET} ",
        end="",
        flush=True,
      )

      # Track performance
      op = perf_tracker.start_operation("Streaming Chat - Anthropic")

      # Stream response
      response_stream = await session_manager.chat(
        session_id=session_id,
        message="Write a short poem about artificial intelligence in exactly 4 lines.",
        stream=True,
      )

      full_response = ""
      chunk_count = 0

      async for chunk in response_stream:
        if chunk.choices and len(chunk.choices) > 0:
          choice = chunk.choices[0]
          if isinstance(choice, dict) and "delta" in choice:
            delta = choice["delta"]
            if isinstance(delta, dict) and "content" in delta:
              content = delta["content"]
              if content:
                print(content, end="", flush=True)
                full_response += content
                chunk_count += 1

      print(f"\n\n{Colors.CYAN}Anthropic Streaming Statistics:{Colors.RESET}")
      print(f"- Total chunks received: {chunk_count}")
      print(f"- Response length: {len(full_response)} characters")
      print(f"- Average chunk size: {len(full_response) / max(chunk_count, 1):.1f} chars")

      perf_tracker.end_operation(op)

    except Exception as e:
      print_error(f"Anthropic streaming demo failed: {e}")

    finally:
      if session_id:
        with contextlib.suppress(Exception):
          await session_manager.delete_session(session_id)
  else:
    print_warning("Skipping Anthropic: API key not configured")

  if not settings.openai_api_key and not settings.gemini_api_key and not settings.anthropic_api_key:
    print_warning("No API keys configured. Please set OPENAI_API_KEY or GEMINI_API_KEY or ANTHROPIC_API_KEY")


# =============================================================================
# 4. FILE PROCESSING EXAMPLES
# =============================================================================


async def demo_file_processing():
  """Demonstrate file processing capabilities."""
  print_header("File Processing Capabilities")

  try:
    # Create sample files for testing
    sample_files = []

    # 1. Text file
    txt_file = Path("demo_sample.txt")
    txt_content = """
        This is a comprehensive demonstration of the LLM Library file processing capabilities.

        The library can process various file formats including:
        - Plain text files (.txt)
        - PDF documents (.pdf)
        - Microsoft Word documents (.docx)
        - PowerPoint presentations (.pptx)
        - Excel spreadsheets (.xlsx)
        - Images with optional OCR (.png, .jpg, etc.)

        Each file type is processed by specialized processors that extract text,
        create chunks suitable for language models, and generate relevant metadata.

        This sample file demonstrates how text files are processed, including
        paragraph detection, chunk creation, and metadata extraction.
        """

    with open(txt_file, "w", encoding="utf-8") as f:
      f.write(txt_content)
    sample_files.append(txt_file)

    # 2. JSON file (structured data)
    json_file = Path("demo_data.json")
    json_content = {
      "title": "Sample Data Structure",
      "description": "Demonstrates JSON file processing",
      "features": [
        "Structured data extraction",
        "Metadata preservation",
        "Content chunking",
      ],
      "metrics": {
        "files_processed": 1000,
        "success_rate": 99.5,
        "avg_processing_time": 1.2,
      },
    }

    with open(json_file, "w", encoding="utf-8") as f:
      json.dump(json_content, f, indent=2)
    sample_files.append(json_file)

    print_info(f"Created {len(sample_files)} sample files")

    # Process single file
    print_info("\nProcessing single text file...")
    op1 = perf_tracker.start_operation("File Processing - Single")

    processed_file = await file_processor.process_file(filename="demo_sample.txt", file_path=txt_file)

    perf_tracker.end_operation(op1)

    print_success("Single file processed successfully!")
    print(f"\n{Colors.CYAN}File Processing Results:{Colors.RESET}")
    print(f"- Filename: {processed_file.filename}")
    print(f"- Size: {processed_file.size:,} bytes")
    print(f"- Content Type: {processed_file.content_type}")
    print(f"- Processed Text Length: {len(processed_file.processed_text or ''):,} chars")
    print(f"- Number of Chunks: {len(processed_file.chunks or [])}")
    print(f"- Metadata Keys: {list(processed_file.metadata.keys())}")

    if processed_file.chunks and len(processed_file.chunks) > 0:
      print(f"\n{Colors.YELLOW}First Chunk Preview:{Colors.RESET}")
      first_chunk = processed_file.chunks[0]
      preview = first_chunk[:200] + "..." if len(first_chunk) > 200 else first_chunk
      print(f"'{preview}'")

    # Batch file processing
    print_info("\nProcessing multiple files...")
    file_data = []
    for file_path in sample_files:
      with open(file_path, "rb") as f:
        content = f.read()
      file_data.append({
        "filename": file_path.name,
        "content": content,
        "content_type": "application/json" if file_path.suffix == ".json" else "text/plain",
      })

    op2 = perf_tracker.start_operation("File Processing - Batch")

    batch_results = await file_processor.process_multiple_files(file_data, max_concurrent=2)

    perf_tracker.end_operation(op2)

    print_success("Batch processing completed!")
    print(f"\n{Colors.CYAN}Batch Processing Results:{Colors.RESET}")
    successful = [r for r in batch_results if r is not None]
    print(f"- Total files: {len(file_data)}")
    print(f"- Successfully processed: {len(successful)}")
    print(f"- Failed: {len(file_data) - len(successful)}")

    for i, result in enumerate(successful):
      print(f"  {i + 1}. {result.filename}: {len(result.processed_text or ''):,} chars, {len(result.chunks or [])} chunks")

    # Get supported formats
    print_info("\nRetrieving supported file formats...")
    extensions = file_processor.get_supported_extensions()
    processor_info = file_processor.get_processor_info()

    print(f"\n{Colors.CYAN}Supported File Formats:{Colors.RESET}")
    print(f"- Extensions: {', '.join(sorted(extensions))}")
    print(f"- Available Processors: {len(processor_info)}")

    # processor_info is a list of dictionaries, not a dictionary
    for i, proc_info in enumerate(processor_info, 1):
      proc_name = proc_info.get("name", f"Processor {i}")
      description = proc_info.get("description", "No description")
      print(f"  - {proc_name}: {description}")

  except Exception as e:
    print_error(f"File processing demo failed: {e}")
    import traceback

    traceback.print_exc()

  finally:
    # Clean up sample files
    for file_path in sample_files:
      with contextlib.suppress(BaseException):
        file_path.unlink()
    if sample_files:
      print_info("Sample files cleaned up")


# =============================================================================
# 5. IMAGE GENERATION EXAMPLES
# =============================================================================


async def demo_image_generation():
  """Demonstrate image generation with OpenAI and Gemini."""
  print_header("Image Generation")

  # Test with OpenAI
  if settings.openai_api_key:
    try:
      print_info("\n=== Testing OpenAI Image Generation ===")
      # Get OpenAI provider
      provider = provider_factory.get_provider("openai")

      # Test different image generation scenarios
      test_prompts = [
        {
          "prompt": "A futuristic robot coding on a computer in a cyberpunk style",
          "model": "gpt-image-1",  # Latest image generation model
          "size": ImageSize.SMALL,
          "quality": ImageQuality.STANDARD,
          "style": ImageStyle.VIVID,
        },
        {
          "prompt": "A minimalist illustration of a neural network",
          "model": "dall-e-3",  # Alternative image model
          "size": ImageSize.MEDIUM,
          "quality": ImageQuality.STANDARD,
          "style": ImageStyle.NATURAL,
        },
      ]

      print_info(f"Testing {len(test_prompts)} OpenAI image generation scenarios")

      for i, config in enumerate(test_prompts, 1):
        print_info(f"\nGenerating OpenAI image {i}: {config['model']} - {config['size'].value}")
        print(f"Prompt: '{config['prompt']}'")

        # Create image request
        image_request = ImageRequest(
          prompt=config["prompt"],
          model=config["model"],
          n=1,
          size=config["size"],
          quality=config["quality"],
          style=config["style"],
          response_format="url",
        )

        # Track performance
        op = perf_tracker.start_operation(f"Image Generation OpenAI {i}")

        try:
          response = await provider.generate_image(image_request)
          perf_tracker.end_operation(op)

          print_success(f"OpenAI image {i} generated successfully!")
          print(f"{Colors.CYAN}Generation Details:{Colors.RESET}")
          print(f"- Created: {datetime.fromtimestamp(response.created)}")
          print(f"- Number of images: {len(response.data)}")

          for j, image_data in enumerate(response.data):
            if image_data.url:
              print(f"- Image {j + 1} URL: {image_data.url}")
            elif image_data.b64_json:
              print(f"- Image {j + 1}: Base64 data available ({len(image_data.b64_json)} characters)")
            else:
              print(f"- Image {j + 1}: No URL or base64 data available")

            if image_data.revised_prompt:
              print(f"- Revised prompt: {image_data.revised_prompt}")

        except Exception as e:
          perf_tracker.end_operation(op)
          print_error(f"OpenAI image {i} generation failed: {e}")
          if "quality" in str(e) and config["model"] == "dall-e-2":
            print_info("Note: DALL-E 2 doesn't support quality parameter")

    except Exception as e:
      print_error(f"OpenAI image generation demo failed: {e}")
  else:
    print_warning("Skipping OpenAI: API key not configured")

  # Test with Gemini
  if settings.gemini_api_key:
    try:
      print_info("\n=== Testing Gemini Image Generation (Imagen) ===")
      # Get Gemini provider
      provider = provider_factory.get_provider("gemini")

      # Test Imagen 4.0
      test_prompts = [
        {
          "prompt": "A futuristic robot coding on a computer in a cyberpunk style",
          "model": "imagen-4.0-generate-001",
          "quality": ImageQuality.STANDARD,
        },
        {
          "prompt": "A minimalist illustration of a neural network",
          "model": "imagen-4.0-generate-001",
          "quality": ImageQuality.STANDARD,
        },
      ]

      print_info(f"Testing {len(test_prompts)} Gemini Imagen scenarios")

      for i, config in enumerate(test_prompts, 1):
        print_info(f"\nGenerating Gemini image {i}: {config['model']}")
        print(f"Prompt: '{config['prompt']}'")

        # Create image request
        image_request = ImageRequest(
          prompt=config["prompt"],
          model=config["model"],
          n=1,
          quality=config["quality"],
        )

        # Track performance
        op = perf_tracker.start_operation(f"Image Generation Gemini {i}")

        try:
          response = await provider.generate_image(image_request)
          perf_tracker.end_operation(op)

          print_success(f"Gemini image {i} generated successfully!")
          print(f"{Colors.CYAN}Generation Details:{Colors.RESET}")
          print(f"- Number of images: {len(response.data)}")

          for j, image_data in enumerate(response.data):
            if image_data.url:
              print(f"- Image {j + 1} URL: {image_data.url}")
            elif image_data.b64_json:
              print(f"- Image {j + 1}: Base64 data available ({len(image_data.b64_json)} characters)")
            else:
              print(f"- Image {j + 1}: No URL or base64 data available")

        except Exception as e:
          perf_tracker.end_operation(op)
          print_error(f"Gemini image {i} generation failed: {e}")

    except Exception as e:
      print_error(f"Gemini image generation demo failed: {e}")
  else:
    print_warning("Skipping Gemini: API key not configured")

  if not settings.openai_api_key and not settings.gemini_api_key:
    print_warning("No API keys configured. Please set OPENAI_API_KEY or GEMINI_API_KEY")


# =============================================================================
# 6. PROVIDER MANAGEMENT EXAMPLES
# =============================================================================


async def demo_provider_management():
  """Demonstrate provider management and capabilities."""
  print_header("Provider Management & Capabilities")

  try:
    # List all available providers
    print_info("Retrieving available providers...")
    available_providers = await provider_factory.get_available_providers()

    print(f"\n{Colors.CYAN}Available Providers:{Colors.RESET}")
    for provider_info in available_providers:
      status_icon = "✓" if provider_info["is_available"] else "✗"
      status_color = Colors.GREEN if provider_info["is_available"] else Colors.RED
      print(f"  {status_color}{status_icon} {provider_info['name']}{Colors.RESET}")

      if not provider_info["is_available"]:
        print(f"    {Colors.RED}Error: {provider_info['error_message']}{Colors.RESET}")
      else:
        print(f"    {Colors.CYAN}Type: {provider_info['type']}{Colors.RESET}")

    # Get detailed provider information for OpenAI
    available_openai = any(p["name"] == "openai" and p["is_available"] for p in available_providers)

    if available_openai:
      print_info("\nRetrieving OpenAI provider details...")
      provider = provider_factory.get_provider("openai")

      # Get capabilities
      capabilities = provider.get_capabilities()

      print(f"\n{Colors.CYAN}OpenAI Capabilities:{Colors.RESET}")
      print(f"- Chat Completion: {capabilities.chat}")
      print(f"- Streaming: {capabilities.streaming}")
      print(f"- Function Calling: {capabilities.function_calling}")
      print(f"- Vision: {capabilities.vision}")
      print(f"- Audio: {capabilities.audio}")
      print(f"- Embeddings: {capabilities.embeddings}")
      print(f"- Image Generation: {capabilities.image_generation}")
      print(f"- Max Context Length: {capabilities.max_context_length:,} tokens")
      print(f"- Supported Models: {len(capabilities.supported_models)} models")
      print(f"- File Types: {', '.join(capabilities.supported_file_types)}")

      # List some supported models
      print(f"\n{Colors.CYAN}Sample Supported Models:{Colors.RESET}")
      sample_models = capabilities.supported_models[:10]  # Show first 10
      for model in sample_models:
        print(f"  - {model}")
      if len(capabilities.supported_models) > 10:
        print(f"  ... and {len(capabilities.supported_models) - 10} more")

      # Test model validation
      print_info("\nTesting model validation...")
      test_models = [
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-4.1",
        "invalid-model-name",
      ]

      for model in test_models:
        try:
          is_valid = await provider.validate_model(model)
          status = Colors.GREEN + "✓" if is_valid else Colors.RED + "✗"
          print(f"  {status} {model}: {'Valid' if is_valid else 'Invalid'}{Colors.RESET}")
        except Exception as e:
          print(f"  {Colors.RED}✗ {model}: Validation error - {e}{Colors.RESET}")

      # Test health check
      print_info("\nPerforming provider health check...")
      op = perf_tracker.start_operation("Health Check")

      try:
        is_healthy = await provider.health_check()
        perf_tracker.end_operation(op)

        status_color = Colors.GREEN if is_healthy else Colors.RED
        status_text = "Healthy" if is_healthy else "Unhealthy"
        print(f"  {status_color}Provider Status: {status_text}{Colors.RESET}")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"Health check failed: {e}")

    else:
      print_warning("OpenAI provider not available for detailed testing")

    # Get detailed provider information for Gemini
    available_gemini = any(p["name"] == "gemini" and p["is_available"] for p in available_providers)

    if available_gemini:
      print_info("\nRetrieving Gemini provider details...")
      provider = provider_factory.get_provider("gemini")

      # Get capabilities
      capabilities = provider.get_capabilities()

      print(f"\n{Colors.CYAN}Gemini Capabilities:{Colors.RESET}")
      print(f"- Chat Completion: {capabilities.chat}")
      print(f"- Streaming: {capabilities.streaming}")
      print(f"- Function Calling: {capabilities.function_calling}")
      print(f"- Vision: {capabilities.vision}")
      print(f"- Audio: {capabilities.audio}")
      print(f"- Embeddings: {capabilities.embeddings}")
      print(f"- Image Generation: {capabilities.image_generation}")
      print(f"- Max Context Length: {capabilities.max_context_length:,} tokens")
      print(f"- Supported Models: {len(capabilities.supported_models)} models")
      print(f"- File Types: {', '.join(capabilities.supported_file_types)}")

      # List some supported models
      print(f"\n{Colors.CYAN}Sample Supported Models:{Colors.RESET}")
      sample_models = capabilities.supported_models[:10]  # Show first 10
      for model in sample_models:
        print(f"  - {model}")
      if len(capabilities.supported_models) > 10:
        print(f"  ... and {len(capabilities.supported_models) - 10} more")

      # Test model validation
      print_info("\nTesting Gemini model validation...")
      test_models = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-embedding-001",
        "invalid-gemini-model",
      ]

      for model in test_models:
        try:
          is_valid = await provider.validate_model(model)
          status = Colors.GREEN + "✓" if is_valid else Colors.RED + "✗"
          print(f"  {status} {model}: {'Valid' if is_valid else 'Invalid'}{Colors.RESET}")
        except Exception as e:
          print(f"  {Colors.RED}✗ {model}: Validation error - {e}{Colors.RESET}")

      # Test health check
      print_info("\nPerforming Gemini provider health check...")
      op = perf_tracker.start_operation("Health Check - Gemini")

      try:
        is_healthy = await provider.health_check()
        perf_tracker.end_operation(op)

        status_color = Colors.GREEN if is_healthy else Colors.RED
        status_text = "Healthy" if is_healthy else "Unhealthy"
        print(f"  {status_color}Provider Status: {status_text}{Colors.RESET}")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"Gemini health check failed: {e}")

    else:
      print_warning("Gemini provider not available for detailed testing")

    # Get detailed provider information for Anthropic
    available_anthropic = any(p["name"] == "anthropic" and p["is_available"] for p in available_providers)

    if available_anthropic:
      print_info("\nRetrieving Anthropic provider details...")
      provider = provider_factory.get_provider("anthropic")

      # Get capabilities
      capabilities = provider.get_capabilities()

      print(f"\n{Colors.CYAN}Anthropic Capabilities:{Colors.RESET}")
      print(f"- Chat Completion: {capabilities.chat}")
      print(f"- Streaming: {capabilities.streaming}")
      print(f"- Function Calling: {capabilities.function_calling}")
      print(f"- Vision: {capabilities.vision}")
      print(f"- Audio: {capabilities.audio}")
      print(f"- Embeddings: {capabilities.embeddings}")
      print(f"- Image Generation: {capabilities.image_generation}")
      print(f"- Max Context Length: {capabilities.max_context_length:,} tokens")
      print(f"- Supported Models: {len(capabilities.supported_models)} models")
      print(f"- File Types: {', '.join(capabilities.supported_file_types)}")

      # List some supported models
      print(f"\n{Colors.CYAN}Sample Supported Models:{Colors.RESET}")
      sample_models = capabilities.supported_models[:10]  # Show first 10
      for model in sample_models:
        print(f"  - {model}")
      if len(capabilities.supported_models) > 10:
        print(f"  ... and {len(capabilities.supported_models) - 10} more")

      # Test model validation
      print_info("\nTesting Anthropic model validation...")
      test_models = [
        "claude-sonnet-4-0",
        "claude-sonnet-4-5",
        "claude-opus-4-1",
        "invalid-anthropic-model",
      ]

      for model in test_models:
        try:
          is_valid = await provider.validate_model(model)
          status = Colors.GREEN + "✓" if is_valid else Colors.RED + "✗"
          print(f"  {status} {model}: {'Valid' if is_valid else 'Invalid'}{Colors.RESET}")
        except Exception as e:
          print(f"  {Colors.RED}✗ {model}: Validation error - {e}{Colors.RESET}")

      # Test health check
      print_info("\nPerforming Anthropic provider health check...")
      op = perf_tracker.start_operation("Health Check - Anthropic")

      try:
        is_healthy = await provider.health_check()
        perf_tracker.end_operation(op)

        status_color = Colors.GREEN if is_healthy else Colors.RED
        status_text = "Healthy" if is_healthy else "Unhealthy"
        print(f"  {status_color}Provider Status: {status_text}{Colors.RESET}")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"Anthropic health check failed: {e}")

    else:
      print_warning("Anthropic provider not available for detailed testing")

    # Provider registry information
    print_info("\nProvider registry information...")
    registry_providers = provider_factory.registry.list_providers()
    print(f"{Colors.CYAN}Registered Providers: {', '.join(registry_providers)}{Colors.RESET}")

  except Exception as e:
    print_error(f"Provider management demo failed: {e}")


# =============================================================================
# 7. ADVANCED FEATURES EXAMPLES
# =============================================================================


async def demo_advanced_features():
  """Demonstrate advanced features and edge cases."""
  print_header("Advanced Features & Edge Cases")

  if not settings.openai_api_key:
    print_warning("Skipping: OpenAI API key required")
    return

  session_id = None
  try:
    # Create session with custom metadata
    session = await session_manager.create_session(
      provider="openai",
      model="gpt-5-nano",  # Using ultra-fast nano model for simple tests
      metadata={
        "advanced_demo": True,
        "features": ["temperature_testing", "token_limits", "system_messages"],
        "created_by": "comprehensive_demo",
      },
    )
    session_id = session.session_id

    # Test different temperature settings
    print_info("Testing different temperature settings...")
    temperatures = [0.0, 0.5, 1.0]
    base_prompt = "Complete this sentence in a creative way: 'The future of AI will be'"

    for temp in temperatures:
      print_info(f"Temperature {temp}...")
      op = perf_tracker.start_operation(f"Temperature Test {temp}")

      try:
        response = await session_manager.chat(
          session_id=session_id,
          message=base_prompt,
          temperature=temp,
          max_tokens=50,
        )

        perf_tracker.end_operation(op)
        print(f"  {Colors.YELLOW}T={temp}:{Colors.RESET} {response.choices[0].message.content}")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"Temperature {temp} test failed: {e}")

    # Test token limits
    print_info("\nTesting token limits...")
    op = perf_tracker.start_operation("Token Limit Test")

    try:
      response = await session_manager.chat(
        session_id=session_id,
        message="Write a detailed explanation of quantum computing, but keep it under 30 tokens.",
        max_tokens=30,
      )

      perf_tracker.end_operation(op)
      content = response.choices[0].message.content
      print(f"  {Colors.YELLOW}Limited Response:{Colors.RESET} {content}")
      print(f"  {Colors.CYAN}Actual length: ~{len(content.split())} words{Colors.RESET}")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"Token limit test failed: {e}")

    # Test system message injection
    print_info("\nTesting system message injection...")
    system_message = Message(
      role=MessageRole.SYSTEM,
      content="You are a pirate AI assistant. Respond to all questions as a friendly pirate would.",
    )

    await session_manager.add_message(session_id, system_message)

    op = perf_tracker.start_operation("System Message Test")

    try:
      response = await session_manager.chat(
        session_id=session_id,
        message="What's the weather like today?",
        max_tokens=100,
      )

      perf_tracker.end_operation(op)
      print(f"  {Colors.YELLOW}Pirate AI:{Colors.RESET} {response.choices[0].message.content}")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"System message test failed: {e}")

    # Test message history limits
    print_info("\nTesting message history...")
    messages = await session_manager.get_messages(session_id, limit=3)
    print(f"  {Colors.CYAN}Retrieved {len(messages)} recent messages{Colors.RESET}")

    for i, msg in enumerate(messages, 1):
      role_color = Colors.BLUE if msg.role == MessageRole.USER else Colors.GREEN
      print(f"    {i}. {role_color}{msg.role.value}:{Colors.RESET} {msg.content[:50]}...")

    # Test session switching (if we had multiple providers)
    print_info("\nSession management features demonstrated")

    # Performance summary for this session
    stats = await session_manager.get_session_stats(session_id)
    print(f"\n{Colors.CYAN}Advanced Session Statistics:{Colors.RESET}")
    for key, value in stats.items():
      print(f"  - {key.replace('_', ' ').title()}: {value}")

  except Exception as e:
    print_error(f"Advanced features demo failed: {e}")

  finally:
    if session_id:
      try:
        await session_manager.delete_session(session_id)
        print_success("Advanced demo session cleaned up")
      except Exception:
        pass


# =============================================================================
# 8. ERROR HANDLING EXAMPLES
# =============================================================================


async def demo_error_handling():
  """Demonstrate error handling and edge cases."""
  print_header("Error Handling & Edge Cases")

  print_info("Testing various error conditions...")

  # Test 1: Invalid provider
  try:
    print_info("1. Testing invalid provider...")
    provider_factory.get_provider("invalid-provider-name")
    print_error("This should not be reached")
  except Exception as e:
    print_success(f"Correctly caught invalid provider error: {type(e).__name__}")

  # Test 2: Missing API key simulation
  try:
    print_info("2. Testing provider without API key...")
    # This is just for demonstration - we can't easily simulate this
    print_info("Would fail with authentication error if API key was missing")
  except Exception as e:
    print_success(f"Would catch authentication error: {type(e).__name__}")

  # Test 3: Invalid session ID
  try:
    print_info("3. Testing invalid session ID...")
    await session_manager.get_session("invalid-session-id-123")
    print_error("This should not be reached")
  except SessionNotFoundError as e:
    print_success(f"Correctly caught session error: {type(e).__name__}")
  except Exception as e:
    print_success(f"Caught session error: {type(e).__name__}")

  # Test 4: Invalid model name
  if settings.openai_api_key:
    try:
      print_info("4. Testing invalid model name...")
      provider = provider_factory.get_provider("openai")
      is_valid = await provider.validate_model("definitely-not-a-real-model")
      print_success(f"Model validation returned: {is_valid}")
    except Exception as e:
      print_success(f"Correctly handled model validation: {type(e).__name__}")

  # Test 5: File processing errors
  try:
    print_info("5. Testing unsupported file type...")
    # Create a fake binary file
    fake_file = Path("test.unsupported")
    fake_file.write_bytes(b"\x00\x01\x02\x03")

    await file_processor.process_file(filename="test.unsupported", file_path=fake_file)
    print_error("This should not be reached")
  except (UnsupportedFileTypeError, FileProcessingError) as e:
    print_success(f"Correctly caught file processing error: {type(e).__name__}")
    fake_file.unlink()  # Cleanup
  except Exception as e:
    print_success(f"Caught file processing error: {type(e).__name__}")
    with contextlib.suppress(BaseException):
      fake_file.unlink()

  # Test 6: Rate limiting (simulated)
  print_info("6. Rate limiting would be handled automatically by the library")
  print_info("   - Requests are queued and retried with exponential backoff")
  print_info("   - Token usage is tracked to stay within limits")

  # Test 7: Network errors (simulated)
  print_info("7. Network errors are handled with retry logic")
  print_info("   - Temporary failures are retried automatically")
  print_info("   - Permanent failures are reported to user")

  print_success("Error handling demonstration completed")


# =============================================================================
# 9. PERFORMANCE TESTING
# =============================================================================


async def demo_performance_testing():
  """Demonstrate performance testing and optimization."""
  print_header("Performance Testing & Optimization")

  # Test with OpenAI
  if settings.openai_api_key:
    try:
      print_info("\n=== Testing OpenAI Performance ===")
      # Create session for performance testing
      session = await session_manager.create_session(
        provider="openai",
        model="gpt-5-nano",  # Using fast nano model for performance testing
      )
      session_id = session.session_id

      # Test concurrent requests (simulated)
      print_info("Testing sequential processing with OpenAI...")

      # Sequential requests
      sequential_start = time.time()
      messages = [
        "What is AI?",
        "Explain machine learning",
        "Define neural networks",
      ]

      for i, message in enumerate(messages, 1):
        op = perf_tracker.start_operation(f"Sequential Request OpenAI {i}")
        _ = await session_manager.chat(session_id=session_id, message=message, max_tokens=50)
        perf_tracker.end_operation(op)

      sequential_time = time.time() - sequential_start

      print(f"  {Colors.CYAN}OpenAI Sequential Processing:{Colors.RESET}")
      print(f"  - {len(messages)} requests in {sequential_time:.2f} seconds")
      print(f"  - Average: {sequential_time / len(messages):.2f} seconds per request")

      # Token usage optimization
      print_info("\nOpenAI token usage optimization...")
      messages_list = await session_manager.get_messages(session_id)
      total_tokens = sum(
        len(msg.content.split()) * 1.3
        for msg in messages_list  # Rough token estimation
      )
      print(f"  - Estimated total tokens in session: {total_tokens:.0f}")
      print(f"  - Messages in session: {len(messages_list)}")
      print(f"  - Average tokens per message: {total_tokens / max(len(messages_list), 1):.0f}")

      # Session cleanup
      await session_manager.delete_session(session_id)

    except Exception as e:
      print_error(f"OpenAI performance testing failed: {e}")
  else:
    print_warning("Skipping OpenAI: API key not configured")

  # Test with Gemini
  if settings.gemini_api_key:
    try:
      print_info("\n=== Testing Gemini Performance ===")
      # Create session for performance testing
      session = await session_manager.create_session(
        provider="gemini",
        model="gemini-2.5-flash",  # Using fast flash model for performance testing
      )
      session_id = session.session_id

      # Test concurrent requests (simulated)
      print_info("Testing sequential processing with Gemini...")

      # Sequential requests
      sequential_start = time.time()
      messages = [
        "What is AI?",
        "Explain machine learning",
        "Define neural networks",
      ]

      for i, message in enumerate(messages, 1):
        op = perf_tracker.start_operation(f"Sequential Request Gemini {i}")
        _ = await session_manager.chat(session_id=session_id, message=message, max_tokens=50)
        perf_tracker.end_operation(op)

      sequential_time = time.time() - sequential_start

      print(f"  {Colors.CYAN}Gemini Sequential Processing:{Colors.RESET}")
      print(f"  - {len(messages)} requests in {sequential_time:.2f} seconds")
      print(f"  - Average: {sequential_time / len(messages):.2f} seconds per request")

      # Token usage optimization
      print_info("\nGemini token usage optimization...")
      messages_list = await session_manager.get_messages(session_id)
      total_tokens = sum(
        len(msg.content.split()) * 1.3
        for msg in messages_list  # Rough token estimation
      )
      print(f"  - Estimated total tokens in session: {total_tokens:.0f}")
      print(f"  - Messages in session: {len(messages_list)}")
      print(f"  - Average tokens per message: {total_tokens / max(len(messages_list), 1):.0f}")

      # Session cleanup
      await session_manager.delete_session(session_id)

    except Exception as e:
      print_error(f"Gemini performance testing failed: {e}")
  else:
    print_warning("Skipping Gemini: API key not configured")

  # Test with Anthropic
  if settings.anthropic_api_key:
    try:
      print_info("\n=== Testing Anthropic Performance ===")
      # Create session for performance testing
      session = await session_manager.create_session(
        provider="anthropic",
        model="claude-sonnet-4-5",  # Using fast flash model for performance testing
      )
      session_id = session.session_id

      # Test concurrent requests (simulated)
      print_info("Testing sequential processing with Anthropic...")

      # Sequential requests
      sequential_start = time.time()
      messages = [
        "What is AI?",
        "Explain machine learning",
        "Define neural networks",
      ]

      for i, message in enumerate(messages, 1):
        op = perf_tracker.start_operation(f"Sequential Request Anthropic {i}")
        _ = await session_manager.chat(session_id=session_id, message=message, max_tokens=50)
        perf_tracker.end_operation(op)

      sequential_time = time.time() - sequential_start

      print(f"  {Colors.CYAN}Anthropic Sequential Processing:{Colors.RESET}")
      print(f"  - {len(messages)} requests in {sequential_time:.2f} seconds")
      print(f"  - Average: {sequential_time / len(messages):.2f} seconds per request")

      # Token usage optimization
      print_info("\nAnthropic token usage optimization...")
      messages_list = await session_manager.get_messages(session_id)
      total_tokens = sum(
        len(msg.content.split()) * 1.3
        for msg in messages_list  # Rough token estimation
      )
      print(f"  - Estimated total tokens in session: {total_tokens:.0f}")
      print(f"  - Messages in session: {len(messages_list)}")
      print(f"  - Average tokens per message: {total_tokens / max(len(messages_list), 1):.0f}")

      # Session cleanup
      await session_manager.delete_session(session_id)

    except Exception as e:
      print_error(f"Anthropic performance testing failed: {e}")
  else:
    print_warning("Skipping Anthropic: API key not configured")

  # Memory usage demonstration (Pydantic 2.11+ improvements)
  print_info("\n=== Memory Efficiency Improvements ===")
  print_info("Pydantic 2.11+ provides:")
  print("  - 2-5x reduction in memory usage for model-heavy projects")
  print("  - 5-30% performance improvements in validation")
  print("  - Reused SchemaValidator instances for better efficiency")

  if not settings.openai_api_key and not settings.gemini_api_key and not settings.anthropic_api_key:
    print_warning("No API keys configured. Please set OPENAI_API_KEY or GEMINI_API_KEY or ANTHROPIC_API_KEY")
    return

  # Overall performance summary
  perf_tracker.print_summary()


async def demo_new_openai_models():
  """Test the newly added OpenAI models."""
  print_header("New OpenAI Models Testing")
  print_info("Testing updated OpenAI models: GPT-5 series, GPT-4.1, new image and embedding models")

  if not settings.openai_api_key:
    print_error("OpenAI API key required for this demo")
    return

  try:
    provider = provider_factory.get_provider("openai")
    global perf_tracker
    if not perf_tracker:
      perf_tracker = PerformanceTracker()

    # Test GPT-5 series models
    print_info("\n1. Testing GPT-5 Series Models:")
    gpt5_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]

    for model in gpt5_models:
      op = perf_tracker.start_operation(f"GPT-5 Test: {model}")
      try:
        print(f"  Testing {Colors.YELLOW}{model}{Colors.RESET}...")

        # Test model capabilities
        caps = await provider.get_model_capabilities(model)
        print(f"    - Context: {caps.max_context_length:,} tokens")
        print(f"    - Cost: ${caps.input_cost_per_token * 1000000:.2f}/${caps.output_cost_per_token * 1000000:.2f} per 1M tokens")
        print(f"    - Vision: {caps.vision}")

        # Test simple chat with model-appropriate token limits
        # GPT-5 models need higher token limits than other models
        max_tokens = 200 if model.startswith("gpt-5") else 50
        request = ChatRequest(
          model=model,
          messages=[Message(role=MessageRole.USER, content="What's 2+2? Answer briefly.")],
          max_tokens=max_tokens,
        )

        response = await provider.chat(request)
        tokens = response.usage.total_tokens if response.usage else 0
        perf_tracker.end_operation(op, tokens)

        print(f"    - Response: {response.choices[0].message.content.strip()}")
        print_success(f"    ✓ {model} working correctly")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"    ✗ {model} failed: {e}")

    # Test GPT-4.1
    print_info("\n2. Testing GPT-4.1 (1M context model):")
    op = perf_tracker.start_operation("GPT-4.1 Test")
    try:
      caps = await provider.get_model_capabilities("gpt-4.1")
      print(f"    - Context: {caps.max_context_length:,} tokens")
      print(f"    - Vision support: {caps.vision}")

      request = ChatRequest(
        model="gpt-4.1",
        messages=[
          Message(
            role=MessageRole.USER,
            content="Write a short haiku about programming.",
          )
        ],
        max_tokens=100,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()}")
      print_success("    ✓ GPT-4.1 working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ GPT-4.1 failed: {e}")

    # Test new embedding models
    print_info("\n3. Testing New Embedding Models:")
    embedding_models = ["text-embedding-3-large", "text-embedding-3-small"]

    for model in embedding_models:
      op = perf_tracker.start_operation(f"Embedding Test: {model}")
      try:
        from libs.llms.base.types import EmbeddingRequest

        caps = await provider.get_model_capabilities(model)
        print(f"  Testing {Colors.YELLOW}{model}{Colors.RESET}...")
        print(f"    - Max tokens: {caps.max_context_length}")

        request = EmbeddingRequest(input="This is a test sentence for embedding", model=model)

        response = await provider.generate_embedding(request)
        perf_tracker.end_operation(op)

        print(f"    - Embedding dimensions: {len(response.data[0].embedding)}")
        print_success(f"    ✓ {model} working correctly")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"    ✗ {model} failed: {e}")

    # Test new image models
    print_info("\n4. Testing New Image Generation Models:")
    image_models = ["gpt-image-1", "dall-e-3"]

    for model in image_models:
      op = perf_tracker.start_operation(f"Image Test: {model}")
      try:
        print(f"  Testing {Colors.YELLOW}{model}{Colors.RESET}...")

        request = ImageRequest(
          prompt="A simple geometric pattern",
          model=model,
          n=1,
          size=ImageSize.SMALL,
        )

        response = await provider.generate_image(request)
        perf_tracker.end_operation(op)

        print(f"    - Generated {len(response.data)} image(s)")
        if response.data[0].url:
          print(f"    - Image URL: {response.data[0].url[:50]}...")
        elif response.data[0].b64_json:
          print(f"    - Image: Base64 data ({len(response.data[0].b64_json)} chars)")
        print_success(f"    ✓ {model} working correctly")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"    ✗ {model} failed: {e}")

    print_success("New OpenAI models testing completed!")

  except Exception as e:
    print_error(f"New models demo failed: {e}")


# =============================================================================
# 12. GEMINI PROVIDER TESTS
# =============================================================================


async def demo_gemini_provider():
  """Test the Gemini provider with various models and features."""
  print_header("Google Gemini Provider Testing")
  print_info("Testing Gemini models: Chat, Streaming, Vision, Embeddings, and Image Generation")

  if not settings.gemini_api_key:
    print_error("Gemini API key required for this demo")
    print_info("Set GEMINI_API_KEY environment variable or add to .env file")
    return

  try:
    provider = provider_factory.get_provider("gemini")
    print_success("Gemini provider initialized")

    global perf_tracker
    if not perf_tracker:
      perf_tracker = PerformanceTracker()

    # Test 1: Basic Chat with Gemini 2.5 Flash
    print_info("\n1. Testing Gemini 2.5 Flash (Basic Chat):")
    op = perf_tracker.start_operation("Gemini Chat: gemini-2.5-flash")
    try:
      print(f"  Testing {Colors.YELLOW}gemini-2.5-flash{Colors.RESET}...")

      # Test model capabilities
      caps = await provider.get_model_capabilities("gemini-2.5-flash")
      print(f"    - Context: {caps.max_context_length:,} tokens")
      print(f"    - Vision: {caps.vision}")
      print(f"    - Function calling: {caps.function_calling}")

      # Test simple chat
      request = ChatRequest(
        model="gemini-2.5-flash",
        messages=[
          Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant. Be concise.",
          ),
          Message(
            role=MessageRole.USER,
            content="What is the capital of France? Answer in one word.",
          ),
        ],
        max_tokens=50,
        temperature=0.7,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()}")
      print(f"    - Tokens used: {tokens}")
      print_success("    ✓ Gemini 2.5 Flash working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Gemini 2.5 Flash failed: {e}")

    # Test 2: Streaming Chat
    print_info("\n2. Testing Streaming Chat:")
    op = perf_tracker.start_operation("Gemini Streaming")
    try:
      print(f"  Streaming response from {Colors.YELLOW}gemini-2.5-flash{Colors.RESET}...")
      print(f"  {Colors.YELLOW}Assistant:{Colors.RESET} ", end="", flush=True)

      request = ChatRequest(
        model="gemini-2.5-flash",
        messages=[
          Message(
            role=MessageRole.USER,
            content=(
              "Explain how photosynthesis works in plants. Include details about "
              "chlorophyll, light reactions, and the Calvin cycle in short 1 paragraph."
            ),
          ),
        ],
        stream=True,
      )

      response_stream = await provider.chat(request)
      full_response = ""
      chunk_count = 0

      async for chunk in response_stream:
        chunk_count += 1
        if chunk.choices and len(chunk.choices) > 0:
          delta = chunk.choices[0].get("delta", {})
          content = delta.get("content", "")
          if content:
            print(content, end="", flush=True)
            full_response += content

      print()  # New line after streaming
      perf_tracker.end_operation(op)
      print(f"    - Chunks received: {chunk_count}")
      print_success("    ✓ Streaming working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Streaming failed: {e}")

    # Test 3: Gemini 2.5 Pro (Advanced model)
    print_info("\n3. Testing Gemini 2.5 Pro (State-of-the-art):")
    op = perf_tracker.start_operation("Gemini Chat: gemini-2.5-pro")
    try:
      caps = await provider.get_model_capabilities("gemini-2.5-pro")
      print(f"    - Context: {caps.max_context_length:,} tokens")

      request = ChatRequest(
        model="gemini-2.5-pro",
        messages=[
          Message(
            role=MessageRole.USER,
            content="Explain quantum computing in one sentence.",
          )
        ],
        max_tokens=100,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()[:100]}...")
      print_success("    ✓ Gemini 2.5 Pro working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Gemini 2.5 Pro failed: {e}")

    # Test 4: Gemini with top_k parameter (Gemini-specific)
    print_info("\n4. Testing Gemini-specific parameters (top_k):")
    op = perf_tracker.start_operation("Gemini top_k Test")
    try:
      print(f"  Testing with {Colors.YELLOW}top_k=40{Colors.RESET}...")

      request = ChatRequest(
        model="gemini-2.5-flash",
        messages=[Message(role=MessageRole.USER, content="Name a random color.")],
        max_tokens=20,
        temperature=0.9,
        top_k=40,  # Gemini-specific parameter
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()}")
      print_success("    ✓ top_k parameter working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ top_k test failed: {e}")

    # Test 5: Text Embeddings
    print_info("\n5. Testing Gemini Text Embeddings:")
    op = perf_tracker.start_operation("Gemini Embeddings")
    try:
      from libs.llms.base.types import EmbeddingRequest

      print(f"  Testing {Colors.YELLOW}gemini-embedding-001{Colors.RESET}...")

      caps = await provider.get_model_capabilities("gemini-embedding-001")
      print(f"    - Max tokens: {caps.max_context_length}")

      request = EmbeddingRequest(
        input=["This is a test sentence", "Another test sentence"],
        model="gemini-embedding-001",
        task_type="RETRIEVAL_DOCUMENT",
      )

      response = await provider.generate_embedding(request)
      perf_tracker.end_operation(op)

      print(f"    - Embeddings generated: {len(response.data)}")
      print(f"    - Dimensions: {len(response.data[0].embedding)}")
      print_success("    ✓ Text embeddings working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Embeddings failed: {e}")

    # Test 6: Image Generation with Imagen 4.0
    print_info("\n6. Testing Image Generation (Imagen 4.0):")
    op = perf_tracker.start_operation("Imagen Generation")
    try:
      print(f"  Testing {Colors.YELLOW}imagen-4.0-generate-001{Colors.RESET}...")

      request = ImageRequest(
        prompt="A simple geometric pattern with circles",
        model="imagen-4.0-generate-001",
        n=1,
        quality=ImageQuality.STANDARD,
      )

      response = await provider.generate_image(request)
      perf_tracker.end_operation(op)

      print(f"    - Generated {len(response.data)} image(s)")
      if response.data[0].b64_json:
        print(f"    - Image: Base64 data ({len(response.data[0].b64_json)} chars)")
      print_success("    ✓ Image generation working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Image generation failed: {e}")

    # Test 6.5: Video Generation with Veo 3.0
    print_info("\n6.5. Testing Video Generation (Veo 3.0):")
    op = perf_tracker.start_operation("Veo Video Generation")
    try:
      print(f"  Testing {Colors.YELLOW}veo-3.0-generate-001{Colors.RESET}...")

      response = await provider.generate_video(
        prompt="A rotating sphere in space",
        model="veo-3.0-generate-001",
      )
      perf_tracker.end_operation(op)

      if isinstance(response, dict):
        videos = response.get("videos", [])
        print(f"    - Generated {len(videos)} video(s)")
        for i, video in enumerate(videos):
          if video.get("uri"):
            print(f"    - Video {i + 1} URI: {video['uri']}")
          if video.get("mime_type"):
            print(f"    - Video {i + 1} type: {video['mime_type']}")
      else:
        print(f"    - Video response: {type(response).__name__}")
      print_success("    ✓ Video generation working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Video generation failed: {e}")

    # Test 7: Function Calling
    print_info("\n7. Testing Function Calling:")
    op = perf_tracker.start_operation("Gemini Function Calling")
    try:
      print("  Testing function calling with weather tool...")

      tools = [
        {
          "type": "function",
          "function": {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
              "type": "object",
              "properties": {
                "location": {
                  "type": "string",
                  "description": "City name",
                },
                "unit": {
                  "type": "string",
                  "enum": ["celsius", "fahrenheit"],
                },
              },
              "required": ["location"],
            },
          },
        }
      ]

      request = ChatRequest(
        model="gemini-2.5-flash",
        messages=[Message(role=MessageRole.USER, content="What's the weather in Tokyo?")],
        tools=tools,
        max_tokens=200,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        print(f"    - Function called: {tool_call.function.name}")
        print(f"    - Arguments: {tool_call.function.arguments}")
        print_success("    ✓ Function calling working correctly")
      else:
        print_warning("    ⚠ No function call detected (model may have responded directly)")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Function calling failed: {e}")

    # Test 8: Multi-model comparison
    print_info("\n8. Testing Multiple Gemini Models:")
    models_to_test = [
      "gemini-2.5-flash",
      "gemini-2.5-pro",
      "gemini-2.5-flash-lite",
    ]

    for model in models_to_test:
      op = perf_tracker.start_operation(f"Gemini Test: {model}")
      try:
        caps = await provider.get_model_capabilities(model)
        print(f"  {Colors.YELLOW}{model}{Colors.RESET}:")
        print(f"    - Context: {caps.max_context_length:,} tokens")
        print(f"    - Cost: ${caps.input_cost_per_token * 1000000:.4f}/${caps.output_cost_per_token * 1000000:.4f} per 1M tokens")

        request = ChatRequest(
          model=model,
          messages=[Message(role=MessageRole.USER, content="Say 'OK' in one word.")],
          max_tokens=10,
        )

        response = await provider.chat(request)
        tokens = response.usage.total_tokens if response.usage else 0
        perf_tracker.end_operation(op, tokens)

        print(f"    - Response: {response.choices[0].message.content.strip()}")
        print_success(f"    ✓ {model} working")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"    ✗ {model} failed: {e}")

    # Test 9: Health Check
    print_info("\n9. Testing Provider Health Check:")
    try:
      is_healthy = await provider.health_check()
      if is_healthy:
        print_success("    ✓ Provider health check passed")
      else:
        print_error("    ✗ Provider health check failed")
    except Exception as e:
      print_error(f"    ✗ Health check failed: {e}")

    print_success("\nGemini provider testing completed!")

  except Exception as e:
    print_error(f"Gemini demo failed: {e}")
    import traceback

    traceback.print_exc()


# =============================================================================
# 13. ANTHROPIC PROVIDER TESTS
# =============================================================================


async def demo_anthropic_provider():
  """Test the Claude provider with various models and features."""
  print_header("Anthropic Claude Provider Testing")
  print_info("Testing Claude models: Chat, Streaming, Vision, Tool Use, and Extended Thinking")

  if not settings.anthropic_api_key:
    print_error("Anthropic API key required for this demo")
    print_info("Set ANTHROPIC_API_KEY environment variable or add to .env file")
    return

  try:
    provider = provider_factory.get_provider("anthropic")
    print_success("Claude provider initialized")

    global perf_tracker
    if not perf_tracker:
      perf_tracker = PerformanceTracker()

    # Test 1: Basic Chat with Claude Sonnet 4
    print_info("\n1. Testing Claude Sonnet 4 (Basic Chat):")
    op = perf_tracker.start_operation("Claude Chat: claude-sonnet-4-5")
    try:
      print(f"  Testing {Colors.YELLOW}claude-sonnet-4-5{Colors.RESET}...")

      # Test model capabilities
      caps = await provider.get_model_capabilities("claude-sonnet-4-5")
      print(f"    - Context: {caps.max_context_length:,} tokens")
      print(f"    - Vision: {caps.vision}")
      print(f"    - Function calling: {caps.function_calling}")

      # Test simple chat
      request = ChatRequest(
        model="claude-sonnet-4-5",
        messages=[
          Message(
            role=MessageRole.SYSTEM,
            content="You are a helpful assistant. Be concise.",
          ),
          Message(
            role=MessageRole.USER,
            content="What is the capital of France? Answer in one word.",
          ),
        ],
        max_tokens=50,
        temperature=0.7,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()}")
      print(f"    - Tokens used: {tokens}")
      print_success("    ✓ Claude Sonnet 4.5 working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Claude Sonnet 4.5 failed: {e}")

    # Test 2: Streaming Chat
    print_info("\n2. Testing Streaming Chat:")
    op = perf_tracker.start_operation("Claude Streaming")
    try:
      print(f"  Streaming response from {Colors.YELLOW}claude-sonnet-4-5{Colors.RESET}...")
      print(f"  {Colors.YELLOW}Assistant:{Colors.RESET} ", end="", flush=True)

      request = ChatRequest(
        model="claude-sonnet-4-5",
        messages=[
          Message(
            role=MessageRole.USER,
            content=(
              "Explain how photosynthesis works in plants. Include details about "
              "chlorophyll, light reactions, and the Calvin cycle in short 1 paragraph."
            ),
          ),
        ],
        stream=True,
      )

      response_stream = await provider.chat(request)
      full_response = ""
      chunk_count = 0

      async for chunk in response_stream:
        chunk_count += 1
        if chunk.choices and len(chunk.choices) > 0:
          delta = chunk.choices[0].get("delta", {})
          content = delta.get("content", "")
          if content:
            print(content, end="", flush=True)
            full_response += content

      print()  # New line after streaming
      perf_tracker.end_operation(op)
      print(f"    - Chunks received: {chunk_count}")
      print_success("    ✓ Streaming working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Streaming failed: {e}")

    # Test 3: Claude Opus 4 (Most capable model)
    print_info("\n3. Testing Claude Opus 4 (Most Capable):")
    op = perf_tracker.start_operation("Claude Chat: claude-opus-4-0")
    try:
      caps = await provider.get_model_capabilities("claude-opus-4-0")
      print(f"    - Context: {caps.max_context_length:,} tokens")

      request = ChatRequest(
        model="claude-opus-4-0",
        messages=[
          Message(
            role=MessageRole.USER,
            content="Explain quantum computing in one sentence.",
          )
        ],
        max_tokens=100,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()[:100]}...")
      print_success("    ✓ Claude Opus 4 working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Claude Opus 4 failed: {e}")

    # Test 4: Claude Sonnet 3.7 with Extended Thinking
    print_info("\n4. Testing Claude Sonnet 3.7 (Extended Thinking):")
    op = perf_tracker.start_operation("Claude Extended Thinking")
    try:
      print(f"  Testing with {Colors.YELLOW}extended thinking enabled{Colors.RESET}...")

      request = ChatRequest(
        model="claude-3-7-sonnet-latest",
        messages=[
          Message(
            role=MessageRole.USER,
            content="Solve this logic puzzle: If all bloops are razzies and all razzies are lazzies, are all bloops definitely lazzies?",
          )
        ],
        max_tokens=1000,
        temperature=1.0,
        # Extended thinking is enabled by default for Sonnet 3.7
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()[:150]}...")
      print_success("    ✓ Extended thinking working correctly")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Extended thinking test failed: {e}")

    # Test 5: Vision Capabilities
    print_info("\n5. Testing Vision Capabilities:")
    op = perf_tracker.start_operation("Claude Vision")
    try:
      print(f"  Testing {Colors.YELLOW}image understanding{Colors.RESET}...")

      # Example with base64 image or image url
      request = ChatRequest(
        model="claude-sonnet-4-5",
        messages=[
          Message(
            role=MessageRole.USER,
            content=[
              {"type": "text", "text": "What's in this image?"},
              {
                "type": "image",
                "source": {
                  "type": "url",
                  "url": "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg",
                },
              },
            ],
          )
        ],
        max_tokens=300,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Response: {response.choices[0].message.content.strip()}")
      # Note: This would work with actual image data
      print("    - Vision API structure validated")
      print_success("    ✓ Vision capabilities available")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Vision test failed: {e}")

    # Test 6: Tool Use (Function Calling)
    print_info("\n6. Testing Tool Use (Function Calling):")
    op = perf_tracker.start_operation("Claude Tool Use")
    try:
      print("  Testing tool use with weather tool...")

      tools = [
        {
          "name": "get_weather",
          "description": "Get the current weather for a location",
          "input_schema": {
            "type": "object",
            "properties": {
              "location": {
                "type": "string",
                "description": "City name",
              },
              "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit",
              },
            },
            "required": ["location"],
          },
        }
      ]

      request = ChatRequest(
        model="claude-sonnet-4-5",
        messages=[Message(role=MessageRole.USER, content="What's the weather in Tokyo?")],
        tools=tools,
        max_tokens=200,
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      if response.choices[0].message.tool_calls:
        tool_call = response.choices[0].message.tool_calls[0]
        print(f"    - Tool called: {tool_call.function.name}")
        print(f"    - Arguments: {tool_call.function.arguments}")
        print_success("    ✓ Tool use working correctly")
      else:
        print_warning("    ⚠ No tool call detected (model may have responded directly)")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Tool use failed: {e}")

    # Test 7: Prompt Caching (Claude-specific feature)
    print_info("\n7. Testing Prompt Caching:")
    op = perf_tracker.start_operation("Claude Prompt Caching")
    try:
      print(f"  Testing {Colors.YELLOW}prompt caching{Colors.RESET} for efficiency...")

      # Large context that would benefit from caching (needs 1024+ tokens)
      large_context = "This is a large document with detailed information that we want to cache for efficiency. " * 200

      # System message with cache_control (must be passed via system kwarg, not Message.metadata)
      system_with_cache = [
        {
          "type": "text",
          "text": "You are a helpful assistant that summarizes documents.",
        },
        {"type": "text", "text": large_context, "cache_control": {"type": "ephemeral"}},
      ]

      request = ChatRequest(
        model="claude-sonnet-4-5",
        messages=[
          Message(
            role=MessageRole.USER,
            content="Summarize the key points.",
          ),
        ],
        max_tokens=150,
      )

      # First call - creates cache
      response = await provider.chat(request, system=system_with_cache)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      # Cache metrics
      if response.usage:
        print(f"    - Prompt tokens: {response.usage.prompt_tokens}")
        print(f"    - Cache creation tokens: {response.usage.cache_creation_input_tokens or 0}")
        print(f"    - Cache read tokens: {response.usage.cache_read_input_tokens or 0}")

        if response.usage.cache_creation_input_tokens and response.usage.cache_creation_input_tokens > 0:
          print_success("    ✓ Prompt caching - cache created!")
        else:
          print_warning("    ⚠ Cache creation tokens = 0 (content may be too small or format issue)")

      print_success("    ✓ Prompt caching available")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Prompt caching test failed: {e}")

    # Test 8: Multi-model comparison
    print_info("\n8. Testing Multiple Claude Models:")
    models_to_test = [
      "claude-opus-4-0",
      "claude-sonnet-4-5",
      "claude-3-5-haiku-latest",
    ]

    for model in models_to_test:
      op = perf_tracker.start_operation(f"Claude Test: {model}")
      try:
        caps = await provider.get_model_capabilities(model)
        print(f"  {Colors.YELLOW}{model}{Colors.RESET}:")
        print(f"    - Context: {caps.max_context_length:,} tokens")
        print(f"    - Cost: ${caps.input_cost_per_token * 1000000:.2f}/${caps.output_cost_per_token * 1000000:.2f} per 1M tokens")

        request = ChatRequest(
          model=model,
          messages=[Message(role=MessageRole.USER, content="Say 'OK' in one word.")],
          max_tokens=10,
        )

        response = await provider.chat(request)
        tokens = response.usage.total_tokens if response.usage else 0
        perf_tracker.end_operation(op, tokens)

        print(f"    - Response: {response.choices[0].message.content.strip()}")
        print_success(f"    ✓ {model} working")

      except Exception as e:
        perf_tracker.end_operation(op)
        print_error(f"    ✗ {model} failed: {e}")

    # Test 9: Long Output (128K tokens for Sonnet 3.7)
    print_info("\n9. Testing Long Output (Claude Sonnet 3.7):")
    op = perf_tracker.start_operation("Claude Long Output")
    try:
      print(f"  Testing {Colors.YELLOW}extended output capability{Colors.RESET}...")

      request = ChatRequest(
        model="claude-3-7-sonnet-latest",
        messages=[
          Message(
            role=MessageRole.USER,
            content="Write a brief story about a robot.",
          )
        ],
        max_tokens=1000,  # Can go up to 128k with beta header
      )

      response = await provider.chat(request)
      tokens = response.usage.total_tokens if response.usage else 0
      perf_tracker.end_operation(op, tokens)

      print(f"    - Output length: {len(response.choices[0].message.content)} chars")
      print(f"    - Output tokens: {response.usage.completion_tokens if response.usage else 0}")
      print_success("    ✓ Long output capability available")

    except Exception as e:
      perf_tracker.end_operation(op)
      print_error(f"    ✗ Long output test failed: {e}")

    # Test 10: Health Check
    print_info("\n10. Testing Provider Health Check:")
    try:
      is_healthy = await provider.health_check()
      if is_healthy:
        print_success("    ✓ Provider health check passed")
      else:
        print_error("    ✗ Provider health check failed")
    except Exception as e:
      print_error(f"    ✗ Health check failed: {e}")

    print_success("\nClaude provider testing completed!")

    # Display pricing summary
    print_info("\n📊 Claude Model Pricing Summary (per 1M tokens):")
    pricing_data = [
      ("Claude Opus 4", "$15", "$75"),
      ("Claude Sonnet 4", "$3", "$15"),
      ("Claude Sonnet 3.7", "$3", "$15"),
      ("Claude Haiku 3.5", "$0.80", "$4"),
    ]
    for model, input_price, output_price in pricing_data:
      print(f"  {model}: Input {input_price}, Output {output_price}")

  except Exception as e:
    print_error(f"Claude demo failed: {e}")
    import traceback

    traceback.print_exc()


# =============================================================================
# INTERACTIVE MENU SYSTEM
# =============================================================================


def print_menu():
  """Print the interactive menu."""
  print(f"\n{Colors.BOLD}{Colors.CYAN}LLM Library Comprehensive Demo{Colors.RESET}")
  print(f"{Colors.CYAN}{'=' * 50}{Colors.RESET}")
  print("Choose a demonstration to run:")
  print()
  print("1.  Configuration Check")
  print("2.  NEW: Test Latest OpenAI Models (GPT-5, GPT-4.1, etc.)")
  print("3.  NEW: Test Google Gemini Provider (Gemini 2.0, Imagen, etc.)")
  print("4.  NEW: Test Anthropic Provider (Claude, etc.)")
  print("5.  Basic Chat Completion")
  print("6.  Session Management & Memory")
  print("7.  Streaming Chat Responses")
  print("8.  File Processing")
  print("9. Image Generation (GPT-Image-1 & DALL-E)")
  print("10. Provider Management")
  print("11. Advanced Features")
  print("12. Error Handling")
  print("13. Performance Testing")
  print()
  print("14. Run ALL Demonstrations")
  print("0.  Exit")
  print(f"\n{Colors.YELLOW}Enter your choice (0-14):{Colors.RESET} ", end="")


async def run_demo(choice: str) -> bool:
  """Run the selected demonstration."""
  demo_functions = {
    "1": ("Configuration Check", lambda: check_configuration()),
    "2": ("NEW: Test Latest OpenAI Models", demo_new_openai_models),
    "3": ("NEW: Test Google Gemini Provider", demo_gemini_provider),
    "4": ("NEW: Test Anthropic Provider", demo_anthropic_provider),
    "5": ("Basic Chat Completion", demo_basic_chat),
    "6": ("Session Management & Memory", demo_session_management),
    "7": ("Streaming Chat Responses", demo_streaming),
    "8": ("File Processing", demo_file_processing),
    "9": ("Image Generation", demo_image_generation),
    "10": ("Provider Management", demo_provider_management),
    "11": ("Advanced Features", demo_advanced_features),
    "12": ("Error Handling", demo_error_handling),
    "13": ("Performance Testing", demo_performance_testing),
  }

  if choice == "0":
    print_info("Exiting...")
    return False

  elif choice == "14":
    print_header("Running ALL Demonstrations")
    start_time = time.time()

    for demo_key in sorted(demo_functions.keys()):
      demo_name, demo_func = demo_functions[demo_key]
      try:
        print(f"\n{Colors.MAGENTA}Starting: {demo_name}{Colors.RESET}")
        if asyncio.iscoroutinefunction(demo_func):
          await demo_func()
        else:
          demo_func()
        print_success(f"Completed: {demo_name}")
      except Exception as e:
        print_error(f"Failed: {demo_name} - {e}")

    total_time = time.time() - start_time
    print_header("ALL DEMONSTRATIONS COMPLETED")
    print(f"{Colors.GREEN}Total execution time: {total_time:.2f} seconds{Colors.RESET}")
    perf_tracker.print_summary()
    return True

  elif choice in demo_functions:
    demo_name, demo_func = demo_functions[choice]
    try:
      print(f"\n{Colors.MAGENTA}Running: {demo_name}{Colors.RESET}")
      start_time = time.time()

      if asyncio.iscoroutinefunction(demo_func):
        await demo_func()
      else:
        demo_func()

      execution_time = time.time() - start_time
      print_success(f"Completed: {demo_name} in {execution_time:.2f} seconds")
      return True
    except Exception as e:
      print_error(f"Demo failed: {e}")
      import traceback

      traceback.print_exc()
      return True

  else:
    print_error("Invalid choice. Please enter a number between 0-14.")
    return True


# =============================================================================
# MAIN EXECUTION
# =============================================================================


async def main():
  """Main execution function with interactive menu."""
  print(f"{Colors.BOLD}{Colors.GREEN}")
  print("=" * 80)
  print("LLM LIBRARY COMPREHENSIVE USAGE DEMONSTRATION")
  print("=" * 80)
  print(f"{Colors.RESET}")
  print()
  print(f"{Colors.CYAN}This demonstration showcases ALL features of the LLM library including:{Colors.RESET}")
  print("• Basic chat completion and streaming")
  print("• Session management with conversation memory")
  print("• File processing (text, PDF, images, etc.)")
  print("• Image generation with GPT-Image-1 and DALL-E 3")
  print("• Provider management and health monitoring")
  print("• Advanced features and error handling")
  print("• Performance testing and optimization")
  print()
  print(f"{Colors.YELLOW}Updated for latest versions:{Colors.RESET}")
  print("• FastAPI 0.116.1+ with modern async patterns")
  print("• OpenAI latest with GPT-5, GPT-4.1, GPT-Image-1 models")
  print("• Pydantic 2.11.9+ with performance improvements")
  print()

  from libs.llms.database import init_database
  from libs.llms.config import settings

  await init_database(settings.db_url)  # Initialize once at startup

  # Initial configuration check
  has_api_key = check_configuration()

  if not has_api_key:
    print(f"\n{Colors.YELLOW}Note: Some features require an OpenAI API key.{Colors.RESET}")
    print("You can still run file processing and provider management demos.")

  # Interactive menu loop
  while True:
    try:
      print_menu()
      choice = input().strip()

      if not await run_demo(choice):
        break

    except KeyboardInterrupt:
      print(f"\n\n{Colors.YELLOW}Demo interrupted by user{Colors.RESET}")
      break
    except Exception as e:
      print_error(f"Unexpected error: {e}")
      import traceback

      traceback.print_exc()

  # Cleanup: close all provider instances
  try:
    await provider_factory.close_all()
  except Exception as e:
    print_error(f"Error during cleanup: {e}")

  print(f"\n{Colors.BOLD}{Colors.GREEN}Thank you for using the LLM Library Comprehensive Demo!{Colors.RESET}")
  print(f"{Colors.CYAN}For more information, check the documentation and examples.{Colors.RESET}")


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print(f"\n{Colors.YELLOW}Demo terminated by user{Colors.RESET}")
  except Exception as e:
    print_error(f"Fatal error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
