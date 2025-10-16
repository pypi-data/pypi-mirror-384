"""Abstract session storage interface and implementations."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime, timedelta
import json
import structlog

from ..base.types import Message, SessionInfo
from ..base.exceptions import SessionNotFoundError, SessionExpiredError

if TYPE_CHECKING:
  from redis.asyncio import Redis


logger = structlog.get_logger()


class SessionStore(ABC):
  """Abstract base class for session storage."""

  @abstractmethod
  async def create_session(
    self,
    session_id: str,
    provider: str,
    model: str,
    session_title: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
  ) -> SessionInfo:
    """Create a new session.

    Args:
        session_id: Unique session identifier
        provider: LLM provider name
        model: Model name
        session_title: Optional session title (generated if not provided)
        ttl_seconds: Time to live in seconds
        metadata: Optional session metadata

    Returns:
        Session information
    """
    pass

  @abstractmethod
  async def get_session(self, session_id: str) -> SessionInfo:
    """Get session information.

    Args:
        session_id: Session identifier

    Returns:
        Session information

    Raises:
        SessionNotFoundError: If session doesn't exist
        SessionExpiredError: If session has expired
    """
    pass

  @abstractmethod
  async def update_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
    """Update session metadata.

    Args:
        session_id: Session identifier
        metadata: Updated metadata

    Returns:
        Updated session information
    """
    pass

  @abstractmethod
  async def delete_session(self, session_id: str) -> bool:
    """Delete a session.

    Args:
        session_id: Session identifier

    Returns:
        True if session was deleted
    """
    pass

  @abstractmethod
  async def add_message(self, session_id: str, message: Message) -> None:
    """Add a message to session history.

    Args:
        session_id: Session identifier
        message: Message to add

    Raises:
        SessionNotFoundError: If session doesn't exist
    """
    pass

  @abstractmethod
  async def get_messages(self, session_id: str, limit: Optional[int] = None, offset: int = 0) -> List[Message]:
    """Get messages from session history.

    Args:
        session_id: Session identifier
        limit: Maximum number of messages
        offset: Number of messages to skip

    Returns:
        List of messages

    Raises:
        SessionNotFoundError: If session doesn't exist
    """
    pass

  @abstractmethod
  async def clear_messages(self, session_id: str) -> None:
    """Clear all messages from a session.

    Args:
        session_id: Session identifier
    """
    pass

  @abstractmethod
  async def list_sessions(self, limit: Optional[int] = None, offset: int = 0) -> List[SessionInfo]:
    """List all sessions.

    Args:
        limit: Maximum number of sessions
        offset: Number of sessions to skip

    Returns:
        List of session information
    """
    pass

  @abstractmethod
  async def cleanup_expired_sessions(self) -> int:
    """Clean up expired sessions.

    Returns:
        Number of sessions cleaned up
    """
    pass


class MemorySessionStore(SessionStore):
  """In-memory session storage implementation."""

  def __init__(self, default_ttl_seconds: int = 3600):
    """Initialize memory session store.

    Args:
        default_ttl_seconds: Default TTL for sessions
    """
    self.default_ttl_seconds = default_ttl_seconds
    self._sessions: Dict[str, SessionInfo] = {}
    self._messages: Dict[str, List[Message]] = {}
    self._expiry: Dict[str, datetime] = {}
    self.logger = logger.bind(store="memory")

  async def create_session(
    self,
    session_id: str,
    provider: str,
    model: str,
    session_title: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
  ) -> SessionInfo:
    """Create a new session."""
    now = datetime.now()
    ttl = ttl_seconds or self.default_ttl_seconds

    # Generate default title if not provided
    if not session_title:
      session_title = f"Chat {now.strftime('%b %d, %H:%M')}"

    session_info = SessionInfo(
      session_id=session_id,
      session_title=session_title,
      provider=provider,
      model=model,
      created_at=now,
      updated_at=now,
      message_count=0,
      total_tokens=0,
      metadata=metadata or {},
    )

    self._sessions[session_id] = session_info
    self._messages[session_id] = []
    self._expiry[session_id] = now + timedelta(seconds=ttl)

    self.logger.info(f"Created session: {session_id} - {session_title}")
    return session_info

  async def get_session(self, session_id: str) -> SessionInfo:
    """Get session information."""
    if session_id not in self._sessions:
      raise SessionNotFoundError(session_id)

    # Check expiry
    if datetime.now() > self._expiry[session_id]:
      await self.delete_session(session_id)
      raise SessionExpiredError(session_id)

    return self._sessions[session_id]

  async def update_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
    """Update session metadata."""
    session_info = await self.get_session(session_id)

    if metadata:
      session_info.metadata.update(metadata)

    session_info.updated_at = datetime.now()
    self._sessions[session_id] = session_info

    return session_info

  async def delete_session(self, session_id: str) -> bool:
    """Delete a session."""
    if session_id in self._sessions:
      del self._sessions[session_id]
      del self._messages[session_id]
      del self._expiry[session_id]
      self.logger.info(f"Deleted session: {session_id}")
      return True
    return False

  async def add_message(self, session_id: str, message: Message) -> None:
    """Add a message to session history."""
    session_info = await self.get_session(session_id)

    self._messages[session_id].append(message)
    session_info.message_count = len(self._messages[session_id])
    session_info.updated_at = datetime.now()

    self._sessions[session_id] = session_info

  async def get_messages(self, session_id: str, limit: Optional[int] = None, offset: int = 0) -> List[Message]:
    """Get messages from session history."""
    await self.get_session(session_id)  # Check if session exists

    messages = self._messages[session_id]

    if offset > 0:
      messages = messages[offset:]

    if limit is not None:
      messages = messages[:limit]

    return messages

  async def clear_messages(self, session_id: str) -> None:
    """Clear all messages from a session."""
    session_info = await self.get_session(session_id)

    self._messages[session_id] = []
    session_info.message_count = 0
    session_info.total_tokens = 0
    session_info.updated_at = datetime.now()

    self._sessions[session_id] = session_info

  async def list_sessions(self, limit: Optional[int] = None, offset: int = 0) -> List[SessionInfo]:
    """List all sessions."""
    # Clean up expired sessions first
    await self.cleanup_expired_sessions()

    sessions = list(self._sessions.values())

    if offset > 0:
      sessions = sessions[offset:]

    if limit is not None:
      sessions = sessions[:limit]

    return sessions

  async def cleanup_expired_sessions(self) -> int:
    """Clean up expired sessions."""
    now = datetime.now()
    expired_sessions = []

    for session_id, expiry_time in self._expiry.items():
      if now > expiry_time:
        expired_sessions.append(session_id)

    for session_id in expired_sessions:
      await self.delete_session(session_id)

    if expired_sessions:
      self.logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

    return len(expired_sessions)


class RedisSessionStore(SessionStore):
  """Redis-based session storage implementation."""

  def __init__(
    self,
    redis_url: str,
    default_ttl_seconds: int = 3600,
    key_prefix: str = "llm_session",
  ):
    """Initialize Redis session store.

    Args:
        redis_url: Redis connection URL
        default_ttl_seconds: Default TTL for sessions
        key_prefix: Prefix for Redis keys
    """
    self.redis_url = redis_url
    self.default_ttl_seconds = default_ttl_seconds
    self.key_prefix = key_prefix
    self._redis: Optional["Redis"] = None  # type: ignore[type-arg]
    self.logger = logger.bind(store="redis")

  async def _get_redis(self):
    """Get or create Redis connection."""
    if self._redis is None:
      import redis.asyncio as aioredis

      self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
    return self._redis

  def _session_key(self, session_id: str) -> str:
    """Get Redis key for session info."""
    return f"{self.key_prefix}:info:{session_id}"

  def _messages_key(self, session_id: str) -> str:
    """Get Redis key for session messages."""
    return f"{self.key_prefix}:messages:{session_id}"

  async def create_session(
    self,
    session_id: str,
    provider: str,
    model: str,
    session_title: Optional[str] = None,
    ttl_seconds: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None,
  ) -> SessionInfo:
    """Create a new session."""
    redis = await self._get_redis()
    now = datetime.now()
    ttl = ttl_seconds or self.default_ttl_seconds

    # Generate default title if not provided
    if not session_title:
      session_title = f"Chat {now.strftime('%b %d, %H:%M')}"

    session_info = SessionInfo(
      session_id=session_id,
      session_title=session_title,
      provider=provider,
      model=model,
      created_at=now,
      updated_at=now,
      message_count=0,
      total_tokens=0,
      metadata=metadata or {},
    )

    # Store session info
    session_data = session_info.model_dump()
    # Convert datetime objects to strings for JSON serialization
    session_data["created_at"] = session_data["created_at"].isoformat()
    session_data["updated_at"] = session_data["updated_at"].isoformat()

    await redis.setex(self._session_key(session_id), ttl, json.dumps(session_data))

    # Initialize empty message list
    await redis.delete(self._messages_key(session_id))
    await redis.expire(self._messages_key(session_id), ttl)

    self.logger.info(f"Created session: {session_id} - {session_title}")
    return session_info

  async def get_session(self, session_id: str) -> SessionInfo:
    """Get session information."""
    redis = await self._get_redis()

    session_data = await redis.get(self._session_key(session_id))
    if not session_data:
      raise SessionNotFoundError(session_id)

    # Parse session data
    data = json.loads(session_data)
    data["created_at"] = datetime.fromisoformat(data["created_at"])
    data["updated_at"] = datetime.fromisoformat(data["updated_at"])

    return SessionInfo(**data)

  async def update_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> SessionInfo:
    """Update session metadata."""
    session_info = await self.get_session(session_id)

    if metadata:
      session_info.metadata.update(metadata)

    session_info.updated_at = datetime.now()

    # Update in Redis
    redis = await self._get_redis()
    session_data = session_info.model_dump()
    session_data["created_at"] = session_data["created_at"].isoformat()
    session_data["updated_at"] = session_data["updated_at"].isoformat()

    # Preserve TTL
    ttl = await redis.ttl(self._session_key(session_id))
    if ttl > 0:
      await redis.setex(self._session_key(session_id), ttl, json.dumps(session_data))

    return session_info

  async def delete_session(self, session_id: str) -> bool:
    """Delete a session."""
    redis = await self._get_redis()

    session_key = self._session_key(session_id)
    messages_key = self._messages_key(session_id)

    deleted_count = await redis.delete(session_key, messages_key)

    if deleted_count > 0:
      self.logger.info(f"Deleted session: {session_id}")
      return True
    return False

  async def add_message(self, session_id: str, message: Message) -> None:
    """Add a message to session history."""
    session_info = await self.get_session(session_id)
    redis = await self._get_redis()

    # Serialize message
    message_data = message.model_dump()
    message_data["timestamp"] = message_data["timestamp"].isoformat()

    # Add to Redis list
    await redis.lpush(self._messages_key(session_id), json.dumps(message_data))

    # Update session info
    session_info.message_count = await redis.llen(self._messages_key(session_id))
    session_info.updated_at = datetime.now()

    # Update session
    await self.update_session(session_id, session_info.metadata)

  async def get_messages(self, session_id: str, limit: Optional[int] = None, offset: int = 0) -> List[Message]:
    """Get messages from session history."""
    await self.get_session(session_id)  # Check if session exists
    redis = await self._get_redis()

    # Get messages from Redis list (most recent first)
    end_index = offset + (limit or -1) - 1 if limit else -1
    message_data_list = await redis.lrange(self._messages_key(session_id), offset, end_index)

    # Parse messages
    messages = []
    for message_data in reversed(message_data_list):  # Reverse to get chronological order
      data = json.loads(message_data)
      data["timestamp"] = datetime.fromisoformat(data["timestamp"])
      messages.append(Message(**data))

    return messages

  async def clear_messages(self, session_id: str) -> None:
    """Clear all messages from a session."""
    session_info = await self.get_session(session_id)
    redis = await self._get_redis()

    await redis.delete(self._messages_key(session_id))

    session_info.message_count = 0
    session_info.total_tokens = 0
    session_info.updated_at = datetime.now()

    await self.update_session(session_id, session_info.metadata)

  async def list_sessions(self, limit: Optional[int] = None, offset: int = 0) -> List[SessionInfo]:
    """List all sessions."""
    redis = await self._get_redis()

    # Get all session keys
    pattern = f"{self.key_prefix}:info:*"
    keys = await redis.keys(pattern)

    sessions = []
    for key in keys[offset : offset + (limit or len(keys))]:
      try:
        session_data = await redis.get(key)
        if session_data:
          data = json.loads(session_data)
          data["created_at"] = datetime.fromisoformat(data["created_at"])
          data["updated_at"] = datetime.fromisoformat(data["updated_at"])
          sessions.append(SessionInfo(**data))
      except Exception as e:
        self.logger.warning(f"Failed to parse session from key {key}: {e}")

    return sessions

  async def cleanup_expired_sessions(self) -> int:
    """Clean up expired sessions."""
    # Redis handles TTL automatically, so no cleanup needed
    return 0

  async def close(self):
    """Close Redis connection."""
    if self._redis:
      await self._redis.close()
      self._redis = None  # Clear reference after closing
