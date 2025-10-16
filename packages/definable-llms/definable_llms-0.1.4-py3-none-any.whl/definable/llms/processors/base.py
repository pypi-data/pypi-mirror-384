"""Base classes for file processing."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path
import structlog

from ..base.types import FileInfo
from ..base.exceptions import FileProcessingError


logger = structlog.get_logger()


class BaseProcessor(ABC):
  """Abstract base class for file processors."""

  def __init__(self):
    """Initialize the processor."""
    self.logger = logger.bind(processor=self.__class__.__name__)

  @abstractmethod
  def can_process(self, file_info: FileInfo) -> bool:
    """Check if this processor can handle the file.

    Args:
        file_info: File information

    Returns:
        True if processor can handle the file
    """
    pass

  @abstractmethod
  async def process(self, file_info: FileInfo) -> FileInfo:
    """Process a file and extract content.

    Args:
        file_info: File information with content

    Returns:
        Updated file information with processed text

    Raises:
        FileProcessingError: If processing fails
    """
    pass

  def _extract_metadata(self, file_path: Path) -> Dict[str, Any]:
    """Extract basic file metadata.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file metadata
    """
    try:
      stat = file_path.stat()
      return {
        "size": stat.st_size,
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "extension": file_path.suffix.lower(),
        "stem": file_path.stem,
      }
    except Exception as e:
      self.logger.warning(f"Failed to extract metadata for {file_path}: {e}")
      return {}

  def _safe_decode(self, content: bytes, encodings: Optional[List[str]] = None) -> str:
    """Safely decode bytes to string.

    Args:
        content: Raw bytes content
        encodings: List of encodings to try

    Returns:
        Decoded string

    Raises:
        FileProcessingError: If decoding fails
    """
    if encodings is None:
      encodings = ["utf-8", "utf-16", "latin-1", "cp1252"]

    for encoding in encodings:
      try:
        return content.decode(encoding)
      except UnicodeDecodeError:
        continue

    # Final fallback with error handling - this should be reachable if all encodings fail
    try:
      return content.decode("utf-8", errors="replace")
    except Exception as e:
      raise FileProcessingError("unknown", f"Failed to decode file content: {e}")


class TextChunker:
  """Utility class for chunking text content."""

  def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separator: str = "\n"):
    """Initialize text chunker.

    Args:
        chunk_size: Maximum chunk size in characters
        chunk_overlap: Overlap between chunks
        separator: Text separator for splitting
    """
    self.chunk_size = chunk_size
    self.chunk_overlap = chunk_overlap
    self.separator = separator
    self.logger = logger.bind(component="text_chunker")

  def chunk_text(self, text: str) -> List[str]:
    """Split text into chunks with overlap.

    Args:
        text: Text to chunk

    Returns:
        List of text chunks
    """
    if not text or len(text) <= self.chunk_size:
      return [text] if text else []

    chunks = []

    # First try to split by separator
    if self.separator in text:
      chunks = self._chunk_by_separator(text)
    else:
      # Fall back to character-based chunking
      chunks = self._chunk_by_characters(text)

    self.logger.debug(f"Created {len(chunks)} chunks from {len(text)} characters")
    return chunks

  def _chunk_by_separator(self, text: str) -> List[str]:
    """Chunk text by separator with overlap.

    Args:
        text: Text to chunk

    Returns:
        List of chunks
    """
    chunks = []
    paragraphs = text.split(self.separator)

    current_chunk = ""
    for paragraph in paragraphs:
      # If adding this paragraph would exceed chunk size
      if len(current_chunk) + len(paragraph) + 1 > self.chunk_size:
        if current_chunk:
          chunks.append(current_chunk.strip())

          # Start new chunk with overlap
          if self.chunk_overlap > 0:
            overlap_text = self._get_overlap_text(current_chunk)
            current_chunk = overlap_text + self.separator + paragraph if overlap_text else paragraph
          else:
            current_chunk = paragraph
        else:
          # Single paragraph is too large, split by characters
          if len(paragraph) > self.chunk_size:
            para_chunks = self._chunk_by_characters(paragraph)
            chunks.extend(para_chunks[:-1])
            current_chunk = para_chunks[-1] if para_chunks else ""
          else:
            current_chunk = paragraph
      else:
        if current_chunk:
          current_chunk += self.separator + paragraph
        else:
          current_chunk = paragraph

    if current_chunk:
      chunks.append(current_chunk.strip())

    return chunks

  def _chunk_by_characters(self, text: str) -> List[str]:
    """Chunk text by character count with overlap.

    Args:
        text: Text to chunk

    Returns:
        List of chunks
    """
    chunks = []
    start = 0

    while start < len(text):
      end = start + self.chunk_size

      # Try to find a good break point
      if end < len(text):
        # Look for whitespace to break on
        for i in range(end, max(start + self.chunk_size // 2, end - 100), -1):
          if text[i].isspace():
            end = i
            break

      chunk = text[start:end].strip()
      if chunk:
        chunks.append(chunk)

      # Calculate next start position with overlap
      if end >= len(text):
        break

      start = max(start + 1, end - self.chunk_overlap)

    return chunks

  def _get_overlap_text(self, text: str) -> str:
    """Get overlap text from the end of current chunk.

    Args:
        text: Current chunk text

    Returns:
        Overlap text
    """
    if len(text) <= self.chunk_overlap:
      return text

    overlap_start = len(text) - self.chunk_overlap

    # Try to find a good break point
    for i in range(overlap_start, overlap_start + 100):
      if i >= len(text):
        break
      if text[i].isspace():
        overlap_start = i + 1
        break

    return text[overlap_start:].strip()
