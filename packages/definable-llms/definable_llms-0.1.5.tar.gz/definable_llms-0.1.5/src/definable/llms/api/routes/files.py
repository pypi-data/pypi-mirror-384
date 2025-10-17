"""File processing endpoints."""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, File, UploadFile, Query
from pydantic import BaseModel
import structlog

from ...base.types import FileInfo
from ...processors import file_processor
from ...base.exceptions import (
  FileProcessingError,
  UnsupportedFileTypeError,
  FileSizeError,
)


logger = structlog.get_logger()
router = APIRouter()


class FileProcessingResponse(BaseModel):
  """Response model for file processing."""

  filename: str
  size: int
  content_type: str
  processed: bool
  text_length: int
  chunks_count: int
  metadata: Dict[str, Any]
  error: Optional[str] = None


class BatchFileProcessingResponse(BaseModel):
  """Response model for batch file processing."""

  total_files: int
  processed_files: int
  failed_files: int
  results: List[FileProcessingResponse]


@router.post("/files/process", response_model=FileProcessingResponse)
async def process_single_file(file: UploadFile = File(...)):
  """Process a single uploaded file."""
  try:
    # Read file content
    content = await file.read()

    # Process the file
    processed_file = await file_processor.process_file(filename=file.filename or "unknown", content=content, content_type=file.content_type)

    logger.info(f"Processed file: {file.filename or 'unknown'}")

    return FileProcessingResponse(
      filename=processed_file.filename or "unknown",
      size=processed_file.size,
      content_type=processed_file.content_type or "unknown",
      processed=True,
      text_length=len(processed_file.processed_text or ""),
      chunks_count=len(processed_file.chunks or []),
      metadata=processed_file.metadata,
    )

  except (FileProcessingError, UnsupportedFileTypeError, FileSizeError) as e:
    raise HTTPException(status_code=e.status_code, detail=e.to_dict())
  except Exception as e:
    logger.error(f"File processing failed for {file.filename}: {e}")
    raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")


@router.post("/files/process-batch", response_model=BatchFileProcessingResponse)
async def process_multiple_files(
  files: List[UploadFile] = File(...),
  max_concurrent: int = Query(3, ge=1, le=10, description="Maximum concurrent processing"),
):
  """Process multiple uploaded files concurrently."""
  try:
    # Prepare file data for processing
    file_data = []
    for file in files:
      content = await file.read()
      file_data.append({
        "filename": file.filename,
        "content": content,
        "content_type": file.content_type,
      })

    # Process files concurrently
    processed_files = await file_processor.process_multiple_files(file_data, max_concurrent=max_concurrent)

    # Create response
    results = []
    processed_count = 0
    failed_count = 0

    for i, file_dict in enumerate(file_data):
      if i < len(processed_files) and processed_files[i] is not None:
        pfile = processed_files[i]
        results.append(
          FileProcessingResponse(
            filename=pfile.filename,
            size=pfile.size,
            content_type=pfile.content_type,
            processed=True,
            text_length=len(pfile.processed_text or ""),
            chunks_count=len(pfile.chunks or []),
            metadata=pfile.metadata,
          )
        )
        processed_count += 1
      else:
        results.append(
          FileProcessingResponse(
            filename=str(file_dict["filename"]) if file_dict["filename"] else "unknown",
            size=len(file_dict["content"]) if file_dict["content"] else 0,
            content_type=str(file_dict["content_type"]) if file_dict["content_type"] else "unknown",
            processed=False,
            text_length=0,
            chunks_count=0,
            metadata={},
            error="Processing failed",
          )
        )
        failed_count += 1

    logger.info(f"Batch processed: {processed_count} success, {failed_count} failed")

    return BatchFileProcessingResponse(
      total_files=len(files),
      processed_files=processed_count,
      failed_files=failed_count,
      results=results,
    )

  except Exception as e:
    logger.error(f"Batch file processing failed: {e}")
    raise HTTPException(status_code=500, detail=f"Batch file processing failed: {str(e)}")


@router.get("/files/supported-formats")
async def get_supported_formats():
  """Get list of supported file formats."""
  try:
    extensions = file_processor.get_supported_extensions()
    processor_info = file_processor.get_processor_info()

    return {
      "supported_extensions": extensions,
      "processors": processor_info,
      "max_file_size_mb": file_processor.validator.max_size_bytes // (1024 * 1024),
      "features": {
        "text_extraction": True,
        "chunking": True,
        "metadata_extraction": True,
        "image_processing": True,
        "ocr": False,  # Depends on optional dependencies
      },
    }

  except Exception as e:
    logger.error(f"Failed to get supported formats: {e}")
    raise HTTPException(status_code=500, detail="Failed to retrieve supported formats")


@router.post("/files/analyze-content")
async def analyze_file_content(file: UploadFile = File(...)):
  """Analyze file content without full processing (quick preview)."""
  try:
    # Read file content
    content = await file.read()

    # Create basic file info
    file_info = FileInfo(
      filename=file.filename or "unknown",
      content_type=file.content_type or "unknown",
      size=len(content),
      content=content,
    )

    # Basic analysis without full processing
    filename = file.filename or "unknown"
    analysis = {
      "filename": filename,
      "size": len(content),
      "content_type": file.content_type,
      "extension": filename.split(".")[-1].lower() if "." in filename else None,
      "is_supported": file_processor._find_processor(file_info) is not None,
    }

    # Try to detect file type if unknown
    if not file.content_type or file.content_type == "application/octet-stream":
      import mimetypes

      guessed_type, _ = mimetypes.guess_type(filename)
      if guessed_type:
        analysis["guessed_content_type"] = guessed_type

    # Quick text preview for text files
    if file.content_type and file.content_type.startswith("text/"):
      try:
        text_content = content.decode("utf-8")[:500]  # First 500 chars
        analysis["text_preview"] = text_content
        analysis["estimated_lines"] = len(text_content.splitlines())
      except UnicodeDecodeError:
        analysis["text_preview"] = "Binary content (not text)"

    return analysis

  except Exception as e:
    logger.error(f"File analysis failed for {file.filename}: {e}")
    raise HTTPException(status_code=500, detail=f"File analysis failed: {str(e)}")


@router.post("/files/extract-text")
async def extract_text_only(
  file: UploadFile = File(...),
  chunk: bool = Query(True, description="Whether to chunk the extracted text"),
):
  """Extract text content from a file without full processing."""
  try:
    # Read file content
    content = await file.read()
    filename = file.filename or "unknown"

    # Process the file
    processed_file = await file_processor.process_file(filename=filename, content=content, content_type=file.content_type)

    response = {
      "filename": filename,
      "extracted_text": processed_file.processed_text or "",
      "text_length": len(processed_file.processed_text or ""),
    }

    if chunk and processed_file.chunks:
      response["chunks"] = processed_file.chunks  # type: ignore
      response["chunks_count"] = len(processed_file.chunks)

    return response

  except (FileProcessingError, UnsupportedFileTypeError, FileSizeError) as e:
    raise HTTPException(status_code=e.status_code, detail=e.to_dict())
  except Exception as e:
    logger.error(f"Text extraction failed for {file.filename}: {e}")
    raise HTTPException(status_code=500, detail=f"Text extraction failed: {str(e)}")


@router.post("/files/validate")
async def validate_file(file: UploadFile = File(...)):
  """Validate a file without processing it."""
  try:
    # Read file content to get size
    content = await file.read()
    filename = file.filename or "unknown"

    # Validate using file validator
    file_processor.validator.validate_file(filename=filename, size=len(content), content_type=file.content_type)

    return {
      "filename": file.filename,
      "size": len(content),
      "content_type": file.content_type,
      "valid": True,
      "message": "File passed validation",
    }

  except (UnsupportedFileTypeError, FileSizeError) as e:
    return {
      "filename": file.filename,
      "size": len(content) if "content" in locals() else 0,
      "content_type": file.content_type,
      "valid": False,
      "error": e.message,
      "details": e.details,
    }
  except Exception as e:
    logger.error(f"File validation failed for {file.filename}: {e}")
    raise HTTPException(status_code=500, detail=f"File validation failed: {str(e)}")
