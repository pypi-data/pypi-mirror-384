"""Chat completion endpoints."""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import structlog

from ...base.types import MessageRole
from ...sessions import session_manager
from ...base.exceptions import (
  SessionNotFoundError,
  SessionExpiredError,
  ProviderError,
  InvalidRequestError,
)


logger = structlog.get_logger()
router = APIRouter()


class ChatRequest(BaseModel):
  """Request model for chat completion."""

  message: str = Field(..., description="Message content")
  session_id: Optional[str] = Field(None, description="Session ID for conversation context")
  provider: Optional[str] = Field(None, description="LLM provider (if no session)")
  model: Optional[str] = Field(None, description="Model name (if no session)")
  stream: bool = Field(False, description="Whether to stream the response")
  temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for generation")
  max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
  role: str = Field("user", description="Message role")
  top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Top-p sampling parameter")
  top_k: Optional[int] = Field(None, gt=0, description="Top-k sampling parameter")
  frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Frequency penalty")
  presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0, description="Presence penalty")
  reasoning_budget_tokens: Optional[int] = Field(None, description="Reasoning budget tokens")
  metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class QuickChatRequest(BaseModel):
  """Request model for quick chat without session."""

  message: str = Field(..., description="Message content")
  provider: str = Field("openai", description="LLM provider")
  model: str = Field("gpt-4-turbo-preview", description="Model name")
  stream: bool = Field(False, description="Whether to stream the response")
  temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Temperature for generation")
  max_tokens: Optional[int] = Field(None, gt=0, description="Maximum tokens to generate")
  system_message: Optional[str] = Field(None, description="Optional system message")


@router.post("/chat")
async def chat_completion(request: ChatRequest):
  """Send a chat message and get completion response."""
  try:
    # If session_id is provided, use session-based chat
    if request.session_id:
      return await _session_chat(request)

    # Otherwise, create a temporary session or use quick chat
    elif request.provider and request.model:
      return await _quick_chat(request)

    else:
      raise HTTPException(
        status_code=400,
        detail="Either session_id or both provider and model must be provided",
      )

  except HTTPException:
    raise
  except SessionNotFoundError:
    raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found")
  except SessionExpiredError:
    raise HTTPException(status_code=410, detail=f"Session '{request.session_id}' has expired")
  except ProviderError as e:
    raise HTTPException(status_code=e.status_code, detail=e.message)
  except InvalidRequestError as e:
    raise HTTPException(status_code=400, detail=e.message)
  except Exception as e:
    logger.error(f"Chat completion failed: {e}")
    raise HTTPException(status_code=500, detail="Chat completion failed")


@router.post("/chat/quick")
async def quick_chat(request: QuickChatRequest):
  """Quick chat without creating a persistent session."""
  try:
    # Create temporary session
    temp_session = await session_manager.create_session(
      provider=request.provider or "openai", model=request.model or "gpt-4", metadata={"temporary": True}
    )

    # Add system message if provided
    if request.system_message:
      from ...base.types import Message, MessageRole

      system_message = Message(role=MessageRole.SYSTEM, content=request.system_message)
      await session_manager.add_message(temp_session.session_id, system_message)

    # Send user message and get response
    chat_kwargs = {}
    if request.temperature is not None:
      chat_kwargs["temperature"] = request.temperature
    if request.max_tokens is not None:
      chat_kwargs["max_tokens"] = request.max_tokens

    if request.stream:
      response = await session_manager.chat(
        session_id=temp_session.session_id,
        message=request.message,
        stream=True,
      )

      # Clean up temporary session after streaming
      async def cleanup_after_stream():
        if hasattr(response, "__aiter__"):
          async for chunk in response:  # type: ignore
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"

        # Cleanup
        await session_manager.delete_session(temp_session.session_id)
        yield "data: [DONE]\n\n"

      return StreamingResponse(
        cleanup_after_stream(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"},
      )

    else:
      response = await session_manager.chat(
        session_id=temp_session.session_id,
        message=request.message,
        stream=False,
      )

      # Clean up temporary session
      await session_manager.delete_session(temp_session.session_id)

      return response

  except ProviderError as e:
    raise HTTPException(status_code=e.status_code, detail=e.message)
  except Exception as e:
    logger.error(f"Quick chat failed: {e}")
    raise HTTPException(status_code=500, detail="Quick chat failed")


@router.post("/chat/with-files")
async def chat_with_files(
  message: str = Form(..., description="Chat message"),
  session_id: Optional[str] = Form(None, description="Session ID"),
  provider: Optional[str] = Form(None, description="LLM provider"),
  model: Optional[str] = Form(None, description="Model name"),
  stream: bool = Form(False, description="Stream response"),
  files: List[UploadFile] = File(..., description="Files to process"),
):
  """Chat with file attachments."""
  try:
    # Process uploaded files
    from ...processors import file_processor

    processed_files = []
    for file in files:
      content = await file.read()
      filename = file.filename or "unknown"

      processed_file = await file_processor.process_file(filename=filename, content=content, content_type=file.content_type)
      processed_files.append(processed_file)

    # Create or get session
    if session_id:
      session = await session_manager.get_session(session_id)
    elif provider and model:
      session = await session_manager.create_session(provider=provider, model=model, metadata={"has_files": True})
    else:
      raise HTTPException(
        status_code=400,
        detail="Either session_id or both provider and model must be provided",
      )

    # Create enhanced message with file content
    file_content_parts = []
    for pfile in processed_files:
      file_content_parts.append(f"File: {pfile.filename}")
      if pfile.processed_text:
        file_content_parts.append(pfile.processed_text[:2000])  # Limit content

    enhanced_message = message
    if file_content_parts:
      enhanced_message += "\n\nAttached files:\n" + "\n---\n".join(file_content_parts)

    # Send chat message
    if stream:
      response = await session_manager.chat(session_id=session.session_id, message=enhanced_message, stream=True)

      async def stream_response():
        if hasattr(response, "__aiter__"):
          async for chunk in response:  # type: ignore
            yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        yield "data: [DONE]\n\n"

      return StreamingResponse(
        stream_response(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"},
      )
    else:
      response = await session_manager.chat(session_id=session.session_id, message=enhanced_message, stream=False)

      # Add file metadata to response
      if hasattr(response, "metadata"):
        response.metadata["processed_files"] = [  # type: ignore
          {
            "filename": pfile.filename,
            "size": pfile.size,
            "chunks": len(pfile.chunks or []),
          }
          for pfile in processed_files
        ]

      return response

  except HTTPException:
    raise
  except Exception as e:
    logger.error(f"Chat with files failed: {e}")
    raise HTTPException(status_code=500, detail="Chat with files failed")


async def _session_chat(request: ChatRequest):
  """Handle session-based chat."""
  chat_kwargs = {}
  if request.temperature is not None:
    chat_kwargs["temperature"] = request.temperature
  if request.max_tokens is not None:
    chat_kwargs["max_tokens"] = request.max_tokens

  role = MessageRole(request.role) if request.role != "user" else MessageRole.USER

  if request.stream:
    if not request.session_id:
      raise HTTPException(status_code=400, detail="Session ID required for streaming chat")
    response = await session_manager.chat(
      session_id=request.session_id,
      message=request.message,
      role=role,
      stream=True,
    )

    async def stream_response():
      if hasattr(response, "__aiter__"):
        async for chunk in response:  # type: ignore
          yield f"data: {json.dumps(chunk.model_dump())}\n\n"
      yield "data: [DONE]\n\n"

    return StreamingResponse(
      stream_response(),
      media_type="text/plain",
      headers={"Cache-Control": "no-cache"},
    )
  else:
    if not request.session_id:
      raise HTTPException(status_code=400, detail="Session ID required for chat")
    response = await session_manager.chat(
      session_id=request.session_id,
      message=request.message,
      role=role,
      stream=False,
    )
    return response


async def _quick_chat(request: ChatRequest):
  """Handle quick chat by creating a temporary session."""
  # Create temporary session
  temp_session = await session_manager.create_session(
    provider=request.provider or "openai", model=request.model or "gpt-4", metadata={"temporary": True}
  )

  try:
    # Use session-based chat
    temp_request = ChatRequest(
      message=request.message,
      session_id=temp_session.session_id,
      provider=request.provider,
      model=request.model,
      stream=request.stream,
      temperature=request.temperature,
      max_tokens=request.max_tokens,
      role=request.role,
      top_p=request.top_p,
      top_k=request.top_k,
      frequency_penalty=request.frequency_penalty,
      presence_penalty=request.presence_penalty,
      reasoning_budget_tokens=request.reasoning_budget_tokens,
      metadata={"temporary": True},
    )

    response = await _session_chat(temp_request)

    # If not streaming, clean up immediately
    if not request.stream:
      await session_manager.delete_session(temp_session.session_id)

    return response

  except Exception:
    # Clean up on error
    await session_manager.delete_session(temp_session.session_id)
    raise
