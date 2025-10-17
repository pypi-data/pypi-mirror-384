"""Session management for LLM conversations."""

import asyncio
import contextlib
import structlog
import uuid

from datetime import datetime
from typing import Optional, List, Dict, Any, Union, AsyncGenerator

from ..base.types import (
  Message,
  SessionInfo,
  ChatRequest,
  ChatResponse,
  StreamChunk,
  MessageRole,
)
from ..base.exceptions import (
  InvalidRequestError,
)
from ..config import Settings
from ..providers import provider_factory
from .store import SessionStore, MemorySessionStore, RedisSessionStore


logger = structlog.get_logger()


class SessionManager:
  """Manages LLM conversation sessions."""

  def __init__(self, store: Optional[SessionStore] = None, config: Optional[Settings] = None):
    """Initialize session manager.

    Args:
        store: Session storage implementation
        config: Configuration settings
    """
    self.config = config or Settings()
    self.store = store or self._create_default_store()
    self.logger = logger.bind(component="session_manager")

    # Background cleanup task
    self._cleanup_task: Optional[asyncio.Task[Any]] = None
    self._cleanup_started = False

  def _create_default_store(self) -> SessionStore:
    """Create default session store based on configuration."""
    if self.config.session_store_type == "redis" and self.config.redis_url:
      return RedisSessionStore(
        redis_url=self.config.redis_url,
        default_ttl_seconds=self.config.session_ttl_seconds,
      )
    else:
      return MemorySessionStore(default_ttl_seconds=self.config.session_ttl_seconds)

  def _start_cleanup_task(self):
    """Start the background cleanup task if not already started."""
    if not self._cleanup_started and hasattr(self.store, "cleanup_expired_sessions"):
      try:
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        self._cleanup_started = True
      except RuntimeError:
        # No event loop running, cleanup will start when first method is called
        pass

  async def _cleanup_loop(self):
    """Background task for cleaning up expired sessions."""
    while True:
      try:
        await asyncio.sleep(300)  # Run every 5 minutes
        cleaned = await self.store.cleanup_expired_sessions()
        if cleaned > 0:
          self.logger.info(f"Cleaned up {cleaned} expired sessions")
      except Exception as e:
        self.logger.error(f"Error in cleanup loop: {e}")
        await asyncio.sleep(60)  # Wait a minute before retrying

  async def create_session(
    self,
    provider: str,
    model: str,
    session_id: Optional[str] = None,
    session_title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
  ) -> SessionInfo:
    """Create a new conversation session.

    Args:
        provider: LLM provider name
        model: Model name
        session_id: Optional custom session ID
        session_title: Optional session title (auto-generated if not provided)
        metadata: Optional session metadata

    Returns:
        Session information
    """
    # Start cleanup task if not already started
    self._start_cleanup_task()

    if session_id is None:
      session_id = str(uuid.uuid4())

    # Validate provider and model
    try:
      provider_instance = provider_factory.get_provider(provider)

      # Validate model exists
      if not await provider_instance.validate_model(model):
        raise InvalidRequestError(f"Model '{model}' is not supported by provider '{provider}'")

      # Get model capabilities for validation and metadata
      try:
        model_capabilities = await provider_instance.get_model_capabilities(model)
        model_info = await provider_instance.get_model_info(model)

        # Add model capabilities to metadata
        if metadata is None:
          metadata = {}
        metadata.update({
          "model_capabilities": model_capabilities.model_dump(),
          "model_info": {
            "display_name": model_info.display_name,
            "description": model_info.description,
            "model_type": model_info.model_type,
            "max_context_length": model_capabilities.max_context_length,
            "supports_streaming": model_capabilities.streaming,
            "supports_function_calling": model_capabilities.function_calling,
            "supports_vision": model_capabilities.vision,
          },
        })

        self.logger.info(
          f"Model {model} validated with capabilities: chat={model_capabilities.chat}, "
          f"vision={model_capabilities.vision}, functions={model_capabilities.function_calling}"
        )

      except ValueError as e:
        raise InvalidRequestError(f"Failed to get capabilities for model '{model}': {e}")

    except Exception as e:
      if isinstance(e, InvalidRequestError):
        raise
      self.logger.error(f"Could not validate provider {provider}: {e}")
      raise InvalidRequestError(f"Provider '{provider}' is not available or misconfigured")

    session_info = await self.store.create_session(
      session_id=session_id,
      provider=provider,
      model=model,
      session_title=session_title,  # Pass title to store
      ttl_seconds=self.config.session_ttl_seconds,
      metadata=metadata,
    )

    self.logger.info(f"Created session {session_id} with {provider}:{model} - {session_info.session_title}")
    return session_info

  async def get_session(self, session_id: str) -> SessionInfo:
    """Get session information.

    Args:
        session_id: Session identifier

    Returns:
        Session information
    """
    return await self.store.get_session(session_id)

  async def update_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
    """Update session metadata.

    Args:
        session_id: Session identifier
        metadata: Updated metadata

    Returns:
        Updated session information
    """
    return await self.store.update_session(session_id, metadata)

  async def delete_session(self, session_id: str) -> bool:
    """Delete a session and all its data.

    Args:
        session_id: Session identifier

    Returns:
        True if session was deleted
    """
    deleted = await self.store.delete_session(session_id)
    if deleted:
      self.logger.info(f"Deleted session {session_id}")
    return deleted

  async def chat(
    self,
    session_id: str,
    message: str,
    role: MessageRole = MessageRole.USER,
    files: Optional[List[Any]] = None,
    stream: bool = False,
    **kwargs,
  ) -> Union[ChatResponse, AsyncGenerator[StreamChunk, None]]:
    """Send a chat message in a session.

    Args:
        session_id: Session identifier
        message: Message content
        role: Message role (default: user)
        files: Optional file attachments
        stream: Whether to stream the response
        **kwargs: Additional chat parameters (temperature, max_tokens, reasoning, etc.)

    Returns:
        Chat response or stream generator
    """
    # Get session info
    session_info = await self.get_session(session_id)

    # Create message object
    user_message = Message(role=role, content=message, timestamp=datetime.now())

    # Add user message to history
    await self.store.add_message(session_id, user_message)

    # Get conversation history
    history = await self.get_messages(session_id, limit=self.config.session_max_history)

    # Create chat request - kwargs now includes reasoning if provided
    chat_request = ChatRequest(messages=history, model=session_info.model, stream=stream, **kwargs)

    # Get provider and make request
    provider = provider_factory.get_provider(session_info.provider)

    try:
      response = await provider.chat(chat_request)

      if stream:
        # response is AsyncGenerator for streaming
        return self._handle_streaming_response(session_id, response)  # type: ignore
      else:
        # response is ChatResponse for non-streaming
        return await self._handle_chat_response(session_id, response)  # type: ignore

    except Exception as e:
      self.logger.error(f"Chat failed for session {session_id}: {e}")
      raise

  async def _handle_chat_response(self, session_id: str, response: ChatResponse) -> ChatResponse:
    """Handle non-streaming chat response.

    Args:
        session_id: Session identifier
        response: Chat response

    Returns:
        The same response after processing
    """
    # Add assistant message to history
    if response.choices:
      assistant_message = response.choices[0].message
      assistant_message.timestamp = datetime.now()
      await self.store.add_message(session_id, assistant_message)

      # Update session token count
      if response.usage:
        session_info = await self.get_session(session_id)
        session_info.total_tokens += response.usage.total_tokens
        await self.update_session(session_id, {"total_tokens": session_info.total_tokens})

    return response

  async def _handle_streaming_response(self, session_id: str, response: AsyncGenerator[StreamChunk, None]) -> AsyncGenerator[StreamChunk, None]:
    """Handle streaming chat response.

    Args:
        session_id: Session identifier
        response: Streaming response generator

    Yields:
        Stream chunks
    """
    accumulated_content = ""
    accumulated_reasoning = ""
    total_tokens = 0

    async for chunk in response:
      # Accumulate content and reasoning from chunks
      if chunk.choices:
        choice = chunk.choices[0]

        # Check if this is a thinking/reasoning chunk
        if choice.get("type") == "thinking":
          accumulated_reasoning += choice["delta"]["content"]
        # Regular content chunk
        elif "delta" in choice and "content" in choice["delta"]:
          accumulated_content += choice["delta"]["content"]

      # Track token usage
      if chunk.usage and hasattr(chunk.usage, "get"):
        total_tokens = chunk.usage.get("total_tokens", 0)

      yield chunk

    # Save the complete assistant message
    if accumulated_content or accumulated_reasoning:
      assistant_message = Message(
        role=MessageRole.ASSISTANT,
        content=accumulated_content,
        reasoning_content=accumulated_reasoning or None,
        timestamp=datetime.now(),
      )
      await self.store.add_message(session_id, assistant_message)

    # Update session token count
    if total_tokens > 0:
      session_info = await self.get_session(session_id)
      session_info.total_tokens += total_tokens
      await self.update_session(session_id, {"total_tokens": session_info.total_tokens})

  async def generate_title(self, message: str) -> str:
    """Generate session title from a message.

    Args:
        message: Last user message content

    Returns:
        Generated title
    """
    try:
      # Determine whether it is a greeting message
      if message.startswith("Hello") or message.startswith("Hi") or message.startswith("Hey"):
        # Generate title
        new_title = "Greetings from the user"
        return new_title

      else:
        # Use a fast, cost-effective model for title generation
        title_generation_provider = "gemini" if self.config.gemini_api_key else "openai"
        title_generation_model = "gemini-2.5-flash" if self.config.gemini_api_key else "gpt-5-nano"

        provider = provider_factory.get_provider(title_generation_provider)

        system_prompt = """
          You are a title generator. Create a concise, descriptive title
          for the conversation. The title should be 3-8 words maximum,
          with no quotes, no punctuation at the end, and capture the main topic.
          The title should be in the same language as the conversation,
          The response should only be the title, no other text
        """

        user_prompt = f"Generate a brief title for this conversation:\n\n{message}\n\n"

        request = ChatRequest(
          messages=[
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=user_prompt),
          ],
          model=title_generation_model,
          max_tokens=300,
          temperature=0.7,
          top_p=None,
          top_k=None,
          frequency_penalty=None,
          presence_penalty=None,
          stream=False,
          reasoning_budget_tokens=None,
        )

        response = await provider.chat(request)

        if hasattr(response, "choices") and response.choices:
          title_content = response.choices[0].message.content
          if not isinstance(title_content, str):
            self.logger.warning(f"Title generation returned non-string content: {type(title_content)}")
            title = "New Session"
          else:
            title = title_content

          await provider.close()
          return title
        else:
          await provider.close()
          return "New Session"

    except Exception as e:
      # Don't fail the chat if title generation fails
      self.logger.warning(f"Failed to generate title for message {message}: {e}")
      await provider.close()
      return "New Session"

  async def add_message(self, session_id: str, message: Message) -> None:
    """Add a message to session history.

    Args:
        session_id: Session identifier
        message: Message to add
    """
    await self.store.add_message(session_id, message)

  async def get_messages(self, session_id: str, limit: Optional[int] = None, offset: int = 0) -> List[Message]:
    """Get messages from session history.

    Args:
        session_id: Session identifier
        limit: Maximum number of messages
        offset: Number of messages to skip

    Returns:
        List of messages
    """
    return await self.store.get_messages(session_id, limit, offset)

  async def clear_messages(self, session_id: str) -> None:
    """Clear all messages from a session.

    Args:
        session_id: Session identifier
    """
    await self.store.clear_messages(session_id)
    self.logger.info(f"Cleared messages for session {session_id}")

  async def switch_provider(self, session_id: str, provider: str, model: str) -> SessionInfo:
    """Switch provider for an existing session.

    Args:
        session_id: Session identifier
        provider: New provider name
        model: New model name

    Returns:
        Updated session information
    """
    # Validate provider exists
    try:
      provider_instance = provider_factory.get_provider(provider)
      if not await provider_instance.validate_model(model):
        self.logger.warning(f"Model {model} may not be supported by {provider}")
    except Exception as e:
      raise InvalidRequestError(f"Invalid provider {provider}: {e}")

    # Update session
    session_info = await self.get_session(session_id)
    session_info.provider = provider
    session_info.model = model
    session_info.updated_at = datetime.now()

    # Save updated session
    updated_session = await self.update_session(
      session_id,
      {
        "provider": provider,
        "model": model,
      },
    )

    self.logger.info(f"Switched session {session_id} to {provider}:{model}")
    return updated_session

  async def list_sessions(self, limit: Optional[int] = None, offset: int = 0) -> List[SessionInfo]:
    """List all sessions.

    Args:
        limit: Maximum number of sessions
        offset: Number of sessions to skip

    Returns:
        List of session information
    """
    return await self.store.list_sessions(limit, offset)

  async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
    """Get statistics for a session.

    Args:
        session_id: Session identifier

    Returns:
        Dictionary with session statistics
    """
    session_info = await self.get_session(session_id)
    messages = await self.get_messages(session_id)

    # Calculate basic stats
    user_messages = sum(1 for msg in messages if msg.role == MessageRole.USER)
    assistant_messages = sum(1 for msg in messages if msg.role == MessageRole.ASSISTANT)
    system_messages = sum(1 for msg in messages if msg.role == MessageRole.SYSTEM)

    # Calculate session duration
    duration_minutes = 0.0
    if messages:
      start_time = min(msg.timestamp for msg in messages)
      end_time = max(msg.timestamp for msg in messages)
      duration_minutes = (end_time - start_time).total_seconds() / 60

    return {
      "session_id": session_id,
      "provider": session_info.provider,
      "model": session_info.model,
      "created_at": session_info.created_at,
      "updated_at": session_info.updated_at,
      "total_messages": len(messages),
      "user_messages": user_messages,
      "assistant_messages": assistant_messages,
      "system_messages": system_messages,
      "total_tokens": session_info.total_tokens,
      "duration_minutes": round(duration_minutes, 2),
      "metadata": session_info.metadata,
    }

  async def close(self):
    """Close the session manager and cleanup resources."""
    if self._cleanup_task:
      self._cleanup_task.cancel()
      with contextlib.suppress(asyncio.CancelledError):
        await self._cleanup_task

    if hasattr(self.store, "close"):
      await self.store.close()

    self.logger.info("Session manager closed")


# Global session manager instance
session_manager = SessionManager()
