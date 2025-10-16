"""Session management endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import structlog

from ...base.types import SessionInfo, Message
from ...sessions import session_manager
from ...base.exceptions import SessionNotFoundError, SessionExpiredError


logger = structlog.get_logger()
router = APIRouter()


class CreateSessionRequest(BaseModel):
  """Request model for creating a new session."""

  provider: str = Field(..., description="LLM provider name")
  model: str = Field(..., description="Model name")
  session_id: Optional[str] = Field(None, description="Optional custom session ID")
  metadata: Optional[Dict[str, Any]] = Field(None, description="Optional session metadata")


class UpdateSessionRequest(BaseModel):
  """Request model for updating session metadata."""

  metadata: Dict[str, Any] = Field(..., description="Session metadata to update")


class SwitchProviderRequest(BaseModel):
  """Request model for switching provider in a session."""

  provider: str = Field(..., description="New provider name")
  model: str = Field(..., description="New model name")


class AddMessageRequest(BaseModel):
  """Request model for adding a message to session."""

  role: str = Field(..., description="Message role (user, assistant, system)")
  content: str = Field(..., description="Message content")
  metadata: Optional[Dict[str, Any]] = Field(None, description="Optional message metadata")


@router.post("/sessions", response_model=SessionInfo)
async def create_session(request: CreateSessionRequest):
  """Create a new conversation session."""
  try:
    session = await session_manager.create_session(
      provider=request.provider,
      model=request.model,
      session_id=request.session_id,
      metadata=request.metadata,
    )

    logger.info(f"Created session {session.session_id}")
    return session

  except Exception as e:
    logger.error(f"Failed to create session: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(
  limit: Optional[int] = Query(None, description="Maximum number of sessions to return"),
  offset: int = Query(0, description="Number of sessions to skip"),
):
  """List all conversation sessions."""
  try:
    sessions = await session_manager.list_sessions(limit=limit, offset=offset)
    return sessions

  except Exception as e:
    logger.error(f"Failed to list sessions: {e}")
    raise HTTPException(status_code=500, detail="Failed to retrieve sessions")


@router.get("/sessions/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
  """Get information about a specific session."""
  try:
    session = await session_manager.get_session(session_id)
    return session

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except SessionExpiredError:
    raise HTTPException(status_code=410, detail=f"Session '{session_id}' has expired")
  except Exception as e:
    logger.error(f"Failed to get session {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to retrieve session '{session_id}'")


@router.put("/sessions/{session_id}", response_model=SessionInfo)
async def update_session(session_id: str, request: UpdateSessionRequest):
  """Update session metadata."""
  try:
    session = await session_manager.update_session(session_id, request.metadata)
    logger.info(f"Updated session {session_id}")
    return session

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except Exception as e:
    logger.error(f"Failed to update session {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to update session '{session_id}'")


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
  """Delete a conversation session."""
  try:
    deleted = await session_manager.delete_session(session_id)

    if not deleted:
      raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    logger.info(f"Deleted session {session_id}")
    return {"message": f"Session '{session_id}' deleted successfully"}

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Failed to delete session {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to delete session '{session_id}'")


@router.post("/sessions/{session_id}/switch-provider", response_model=SessionInfo)
async def switch_provider(session_id: str, request: SwitchProviderRequest):
  """Switch the provider for an existing session."""
  try:
    session = await session_manager.switch_provider(session_id=session_id, provider=request.provider, model=request.model)

    logger.info(f"Switched session {session_id} to {request.provider}:{request.model}")
    return session

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except Exception as e:
    logger.error(f"Failed to switch provider for session {session_id}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to switch provider for session '{session_id}'",
    )


@router.get("/sessions/{session_id}/messages", response_model=List[Message])
async def get_session_messages(
  session_id: str,
  limit: Optional[int] = Query(None, description="Maximum number of messages to return"),
  offset: int = Query(0, description="Number of messages to skip"),
):
  """Get messages from a conversation session."""
  try:
    messages = await session_manager.get_messages(session_id=session_id, limit=limit, offset=offset)
    return messages

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except Exception as e:
    logger.error(f"Failed to get messages for session {session_id}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to retrieve messages for session '{session_id}'",
    )


@router.post("/sessions/{session_id}/messages")
async def add_message(session_id: str, request: AddMessageRequest):
  """Add a message to a conversation session."""
  try:
    from ...base.types import MessageRole

    message = Message(
      role=MessageRole(request.role),
      content=request.content,
      metadata=request.metadata or {},
    )

    await session_manager.add_message(session_id, message)

    logger.info(f"Added message to session {session_id}")
    return {"message": "Message added successfully"}

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except ValueError:
    raise HTTPException(status_code=400, detail=f"Invalid message role: {request.role}")
  except Exception as e:
    logger.error(f"Failed to add message to session {session_id}: {e}")
    raise HTTPException(status_code=500, detail=f"Failed to add message to session '{session_id}'")


@router.delete("/sessions/{session_id}/messages")
async def clear_session_messages(session_id: str):
  """Clear all messages from a conversation session."""
  try:
    await session_manager.clear_messages(session_id)

    logger.info(f"Cleared messages for session {session_id}")
    return {"message": f"Messages cleared for session '{session_id}'"}

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except Exception as e:
    logger.error(f"Failed to clear messages for session {session_id}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to clear messages for session '{session_id}'",
    )


@router.get("/sessions/{session_id}/stats")
async def get_session_stats(session_id: str):
  """Get statistics for a conversation session."""
  try:
    stats = await session_manager.get_session_stats(session_id)
    return stats

  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
  except Exception as e:
    logger.error(f"Failed to get stats for session {session_id}: {e}")
    raise HTTPException(
      status_code=500,
      detail=f"Failed to get statistics for session '{session_id}'",
    )
