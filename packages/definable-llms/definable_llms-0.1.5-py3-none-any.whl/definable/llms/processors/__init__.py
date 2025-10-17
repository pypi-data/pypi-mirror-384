"""File processing pipeline for the LLM library."""

import asyncio
from typing import List, Optional, Union, Dict, Any
from pathlib import Path
import structlog

from ..base.types import FileInfo
from ..base.exceptions import FileProcessingError, UnsupportedFileTypeError
from ..utils.validators import FileValidator
from .base import BaseProcessor, TextChunker
from .document import (
  PDFProcessor,
  DocxProcessor,
  PowerPointProcessor,
  SpreadsheetProcessor,
  PlainTextProcessor,
)
from .image import ImageProcessor, ImageAnalyzer


logger = structlog.get_logger()


class FileProcessingPipeline:
  """Main file processing pipeline that coordinates all processors."""

  def __init__(
    self,
    max_file_size_mb: int = 50,
    allowed_extensions: Optional[List[str]] = None,
    enable_ocr: bool = False,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
  ):
    """Initialize the file processing pipeline.

    Args:
        max_file_size_mb: Maximum file size in MB
        allowed_extensions: List of allowed file extensions
        enable_ocr: Whether to enable OCR for images
        chunk_size: Default chunk size for text processing
        chunk_overlap: Overlap between text chunks
    """
    self.validator = FileValidator(max_file_size_mb, allowed_extensions)
    self.chunker = TextChunker(chunk_size, chunk_overlap)
    self.logger = logger.bind(component="file_pipeline")

    # Initialize processors
    self.processors: List[BaseProcessor] = [
      PDFProcessor(),
      DocxProcessor(),
      PowerPointProcessor(),
      SpreadsheetProcessor(),
      ImageProcessor(extract_text=enable_ocr),
      PlainTextProcessor(),  # Keep this last as it's most permissive
    ]

    # Image analyzer for additional image analysis
    self.image_analyzer = ImageAnalyzer()

  async def process_file(
    self,
    filename: str,
    content: Optional[bytes] = None,
    file_path: Optional[Union[str, Path]] = None,
    content_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
  ) -> FileInfo:
    """Process a single file.

    Args:
        filename: Name of the file
        content: File content as bytes
        file_path: Path to the file (used if content not provided)
        content_type: MIME type of the file
        metadata: Additional metadata

    Returns:
        Processed file information

    Raises:
        FileProcessingError: If processing fails
        UnsupportedFileTypeError: If file type is not supported
    """
    # Create file info object
    file_info = FileInfo(
      filename=filename,
      content_type=content_type or "application/octet-stream",
      size=len(content) if content else 0,
      path=Path(file_path) if file_path else None,
      content=content,
      metadata=metadata or {},
    )

    # Update size if reading from file path
    if not content and file_path:
      path = Path(file_path)
      if path.exists():
        file_info.size = path.stat().st_size
        file_info.content_type = self._guess_content_type(filename)

    # Validate file
    self.validator.validate_file(filename, file_info.size, file_info.content_type)

    # Find appropriate processor
    processor = self._find_processor(file_info)
    if not processor:
      raise UnsupportedFileTypeError(
        filename,
        Path(filename).suffix,
        [
          ".pdf",
          ".docx",
          ".pptx",
          ".xlsx",
          ".csv",
          ".txt",
          ".md",
          ".png",
          ".jpg",
        ],
      )

    # Process the file
    try:
      self.logger.info(f"Processing {filename} with {processor.__class__.__name__}")
      processed_file = await processor.process(file_info)

      # Add image analysis if it's an image
      if isinstance(processor, ImageProcessor):
        analysis = await self.image_analyzer.analyze_image(processed_file)
        processed_file.metadata["image_analysis"] = analysis

      self.logger.info(
        f"Successfully processed {filename}: {len(processed_file.processed_text or '')} chars, {len(processed_file.chunks or [])} chunks"
      )

      return processed_file

    except Exception as e:
      self.logger.error(f"Failed to process {filename}: {e}")
      if isinstance(e, FileProcessingError):
        raise
      raise FileProcessingError(filename, f"Unexpected error: {e}")

  async def process_multiple_files(self, files: List[Dict[str, Any]], max_concurrent: int = 3) -> List[FileInfo]:
    """Process multiple files concurrently.

    Args:
        files: List of file dictionaries with keys: filename, content/file_path, etc.
        max_concurrent: Maximum number of concurrent processing tasks

    Returns:
        List of processed file information
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_single_file(file_dict: Dict[str, Any]) -> Optional[FileInfo]:
      async with semaphore:
        try:
          return await self.process_file(**file_dict)
        except Exception as e:
          self.logger.error(f"Failed to process file {file_dict.get('filename', 'unknown')}: {e}")
          return None

    # Create tasks for all files
    tasks = [process_single_file(file_dict) for file_dict in files]

    # Wait for all tasks to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out None results and exceptions
    processed_files = []
    for result in results:
      if isinstance(result, FileInfo):
        processed_files.append(result)
      elif isinstance(result, Exception):
        self.logger.error(f"File processing exception: {result}")

    self.logger.info(f"Processed {len(processed_files)} out of {len(files)} files")
    return processed_files

  def _find_processor(self, file_info: FileInfo) -> Optional[BaseProcessor]:
    """Find the appropriate processor for a file.

    Args:
        file_info: File information

    Returns:
        Processor that can handle the file, or None
    """
    for processor in self.processors:
      if processor.can_process(file_info):
        return processor
    return None

  def _guess_content_type(self, filename: str) -> str:
    """Guess content type from filename.

    Args:
        filename: Name of the file

    Returns:
        Guessed MIME type
    """
    import mimetypes

    content_type, _ = mimetypes.guess_type(filename)
    return content_type or "application/octet-stream"

  def get_supported_extensions(self) -> List[str]:
    """Get list of all supported file extensions.

    Returns:
        List of supported extensions
    """
    extensions = set()

    # Add extensions from processors
    test_files = [
      ("test.pdf", "application/pdf"),
      (
        "test.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      ),
      (
        "test.pptx",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
      ),
      (
        "test.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      ),
      ("test.csv", "text/csv"),
      ("test.txt", "text/plain"),
      ("test.md", "text/markdown"),
      ("test.png", "image/png"),
      ("test.jpg", "image/jpeg"),
      ("test.gif", "image/gif"),
    ]

    for filename, content_type in test_files:
      test_file_info = FileInfo(filename=filename, content_type=content_type, size=1000)
      if self._find_processor(test_file_info):
        extensions.add(Path(filename).suffix.lower())

    return sorted(list(extensions))

  def get_processor_info(self) -> List[Dict[str, Any]]:
    """Get information about all available processors.

    Returns:
        List of processor information
    """
    info = []
    for processor in self.processors:
      info.append({
        "name": processor.__class__.__name__,
        "description": processor.__doc__ or "No description available",
      })
    return info


# Global file processing pipeline
file_processor = FileProcessingPipeline()


__all__ = [
  # Main pipeline
  "FileProcessingPipeline",
  "file_processor",
  # Base classes
  "BaseProcessor",
  "TextChunker",
  # Document processors
  "PDFProcessor",
  "DocxProcessor",
  "PowerPointProcessor",
  "SpreadsheetProcessor",
  "PlainTextProcessor",
  # Image processing
  "ImageProcessor",
  "ImageAnalyzer",
]
