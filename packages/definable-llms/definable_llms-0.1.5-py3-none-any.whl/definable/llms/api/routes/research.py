"""Research endpoints with streaming support."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import structlog

from ...base.types import ResearchRequest
from ...research import research_manager

logger = structlog.get_logger()
router = APIRouter()


@router.post("/research/stream")
async def conduct_research_streaming(request: ResearchRequest):
  """Conduct deep research with SSE progress streaming."""
  try:

    async def event_generator():
      try:
        async for event in research_manager.research(str(request.topic)):
          yield f"data: {json.dumps(event)}\n\n"
      except Exception as e:
        logger.error(f"Research failed: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
      event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    )
  except Exception as e:
    logger.error(f"Failed to start research: {e}")
    raise HTTPException(status_code=500, detail=str(e))


@router.post("/research")
async def conduct_research(request: ResearchRequest):
  """Conduct deep research (non-streaming)."""
  try:
    result = None
    async for event in research_manager.research(str(request.topic)):
      if event.get("type") == "complete":
        result = event.get("result")
        break

    if result:
      return result
    else:
      raise HTTPException(status_code=500, detail="No result returned")
  except Exception as e:
    logger.error(f"Research failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
