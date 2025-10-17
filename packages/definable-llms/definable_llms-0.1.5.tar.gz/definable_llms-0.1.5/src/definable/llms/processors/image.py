"""Image processing for PNG, JPG, GIF, and other image files."""

import base64
import io
from typing import Dict, Any, Tuple, List
import structlog

try:
  from PIL import Image
except ImportError:
  Image = None  # type: ignore

from ..base.types import FileInfo
from ..base.exceptions import FileProcessingError
from .base import BaseProcessor


logger = structlog.get_logger()


class ImageProcessor(BaseProcessor):
  """Image file processor using Pillow."""

  SUPPORTED_FORMATS = {
    ".png": "PNG",
    ".jpg": "JPEG",
    ".jpeg": "JPEG",
    ".gif": "GIF",
    ".bmp": "BMP",
    ".webp": "WEBP",
    ".tiff": "TIFF",
    ".tif": "TIFF",
  }

  SUPPORTED_CONTENT_TYPES = [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/bmp",
    "image/webp",
    "image/tiff",
  ]

  def __init__(
    self,
    max_size: Tuple[int, int] = (2048, 2048),
    quality: int = 85,
    extract_text: bool = False,
  ):
    """Initialize image processor.

    Args:
        max_size: Maximum image dimensions (width, height)
        quality: JPEG quality for compression (1-95)
        extract_text: Whether to extract text using OCR
    """
    super().__init__()
    self.max_size = max_size
    self.quality = quality
    self.extract_text = extract_text

  def can_process(self, file_info: FileInfo) -> bool:
    """Check if file is a supported image."""
    filename_lower = file_info.filename.lower()
    return any(filename_lower.endswith(ext) for ext in self.SUPPORTED_FORMATS.keys()) or file_info.content_type in self.SUPPORTED_CONTENT_TYPES

  async def process(self, file_info: FileInfo) -> FileInfo:
    """Process image file.

    Args:
        file_info: Image file information

    Returns:
        File info with processed image data and optional text
    """
    try:
      from PIL import Image
    except ImportError:
      raise FileProcessingError(
        file_info.filename,
        "Pillow library not available. Install with: pip install Pillow",
      )

    try:
      # Load image
      if file_info.content:
        image = Image.open(io.BytesIO(file_info.content))
      elif file_info.path:
        image = Image.open(file_info.path)
      else:
        raise FileProcessingError(file_info.filename, "No content or path provided")

      # Extract basic image metadata
      metadata: Dict[str, Any] = {
        "format": image.format,
        "mode": image.mode,
        "size": image.size,
        "width": image.width,
        "height": image.height,
        "has_transparency": self._has_transparency(image),
        "color_space": self._get_color_space(image),
      }

      # Add EXIF data if available
      if hasattr(image, "_getexif") and image._getexif():
        try:
          exif = image._getexif()
          metadata["exif"] = {str(k): str(v) for k, v in exif.items() if k is not None and isinstance(v, (str, int, float))}
        except Exception as e:
          self.logger.warning(f"Failed to extract EXIF data: {e}")

      # Resize if too large
      processed_image = image
      if image.size[0] > self.max_size[0] or image.size[1] > self.max_size[1]:
        processed_image = image.copy()  # type: ignore
        processed_image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        metadata["resized"] = True
        metadata["original_size"] = image.size
        self.logger.info(f"Resized image from {image.size} to {processed_image.size}")

      # Convert to base64 for storage/transmission
      output_format = self._get_output_format(processed_image)
      image_bytes = self._image_to_bytes(processed_image, output_format)
      base64_data = base64.b64encode(image_bytes).decode("utf-8")

      # Create data URL
      mime_type = self._format_to_mime_type(output_format)
      data_url = f"data:{mime_type};base64,{base64_data}"

      metadata.update({
        "processed_format": output_format,
        "processed_size": len(image_bytes),
        "base64_length": len(base64_data),
        "data_url": data_url,
      })

      # Extract text using OCR if requested
      extracted_text = ""
      if self.extract_text:
        extracted_text = await self._extract_text_ocr(processed_image)
        if extracted_text:
          metadata["ocr_text_length"] = len(extracted_text)

      # Update file info
      file_info.processed_text = extracted_text or f"[Image: {file_info.filename}]"
      file_info.metadata.update(metadata)

      # For images, we don't create text chunks unless OCR was performed
      if extracted_text:
        from .base import TextChunker

        chunker = TextChunker()
        file_info.chunks = chunker.chunk_text(extracted_text)
      else:
        file_info.chunks = [f"[Image: {file_info.filename} - {image.width}x{image.height} {image.format}]"]

      self.logger.info(f"Processed image: {image.format} {image.size} -> {output_format} {processed_image.size}, OCR: {len(extracted_text)} chars")

      return file_info

    except Exception as e:
      self.logger.error(f"Failed to process image {file_info.filename}: {e}")
      raise FileProcessingError(file_info.filename, f"Image processing failed: {e}")

  def _has_transparency(self, image) -> bool:
    """Check if image has transparency."""
    try:
      return image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info)
    except Exception:
      return False

  def _get_color_space(self, image) -> str:
    """Get image color space information."""
    mode_descriptions = {
      "1": "1-bit pixels, black and white",
      "L": "8-bit pixels, black and white",
      "P": "8-bit pixels, mapped to any other mode",
      "RGB": "3x8-bit pixels, true color",
      "RGBA": "4x8-bit pixels, true color with transparency",
      "CMYK": "4x8-bit pixels, color separation",
      "YCbCr": "3x8-bit pixels, color video format",
      "LAB": "3x8-bit pixels, L*a*b* color space",
      "HSV": "3x8-bit pixels, Hue, Saturation, Value color space",
    }
    return mode_descriptions.get(image.mode, f"Unknown ({image.mode})")

  def _get_output_format(self, image) -> str:
    """Determine the best output format for the image."""
    # Keep PNG for images with transparency
    if self._has_transparency(image):
      return "PNG"

    # Use JPEG for photos (RGB mode)
    if image.mode == "RGB":
      return "JPEG"

    # Default to PNG for other modes
    return "PNG"

  def _image_to_bytes(self, image, image_format: str) -> bytes:
    """Convert PIL Image to bytes."""
    if Image is None:
      raise FileProcessingError("test", "Pillow (PIL) is required for image processing")

    buffer = io.BytesIO()

    if image_format == "JPEG":
      # Convert to RGB if necessary (JPEG doesn't support transparency)
      if image.mode in ("RGBA", "LA", "P"):
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
          image = image.convert("RGBA")
        rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
        image = rgb_image

      image.save(buffer, format=image_format, quality=self.quality, optimize=True)
    else:
      image.save(buffer, format=image_format, optimize=True)

    return buffer.getvalue()

  def _format_to_mime_type(self, image_format: str) -> str:
    """Convert PIL format to MIME type."""
    format_map = {
      "PNG": "image/png",
      "JPEG": "image/jpeg",
      "GIF": "image/gif",
      "BMP": "image/bmp",
      "WEBP": "image/webp",
      "TIFF": "image/tiff",
    }
    return format_map.get(image_format, "image/png")

  async def _extract_text_ocr(self, image) -> str:
    """Extract text from image using OCR.

    Args:
        image: PIL Image object

    Returns:
        Extracted text
    """
    if not self.extract_text:
      return ""

    try:
      import pytesseract
    except ImportError:
      self.logger.warning("pytesseract not available for OCR. Install with: pip install pytesseract")
      return ""

    try:
      # Extract text using Tesseract
      text = pytesseract.image_to_string(image)

      # Clean up the text
      lines = []
      for line in text.split("\n"):
        cleaned_line = line.strip()
        if cleaned_line and len(cleaned_line) > 1:  # Skip single characters and empty lines
          lines.append(cleaned_line)

      extracted_text = "\n".join(lines)

      if extracted_text:
        self.logger.info(f"OCR extracted {len(extracted_text)} characters")

      return extracted_text

    except Exception as e:
      self.logger.warning(f"OCR failed: {e}")
      return ""


class ImageAnalyzer:
  """Utility class for analyzing image content."""

  def __init__(self):
    """Initialize image analyzer."""
    self.logger = logger.bind(component="image_analyzer")

  async def analyze_image(self, file_info: FileInfo) -> Dict[str, Any]:
    """Analyze image and provide description.

    Args:
        file_info: Processed file info with image data

    Returns:
        Analysis results
    """
    try:
      from PIL import Image
    except ImportError:
      return {"error": "Pillow not available"}

    try:
      # Get image from file info
      if not file_info.metadata.get("data_url"):
        return {"error": "No image data available"}

      # Extract base64 data
      data_url = file_info.metadata["data_url"]
      base64_data = data_url.split(",")[1]
      image_bytes = base64.b64decode(base64_data)
      image = Image.open(io.BytesIO(image_bytes))

      # Basic analysis
      analysis = {
        "dimensions": f"{image.width}x{image.height}",
        "aspect_ratio": round(image.width / image.height, 2),
        "orientation": self._get_orientation(image),
        "color_analysis": self._analyze_colors(image),
        "complexity": self._estimate_complexity(image),
      }

      # Add dominant colors
      if image.mode == "RGB":
        analysis["dominant_colors"] = self._get_dominant_colors(image)

      return analysis

    except Exception as e:
      self.logger.error(f"Image analysis failed: {e}")
      return {"error": str(e)}

  def _get_orientation(self, image) -> str:
    """Determine image orientation."""
    if image.width > image.height:
      return "landscape"
    elif image.height > image.width:
      return "portrait"
    else:
      return "square"

  def _analyze_colors(self, image) -> Dict[str, Any]:
    """Analyze color properties of the image."""
    try:
      from PIL import ImageStat

      # Convert to RGB for analysis
      if image.mode != "RGB":
        rgb_image = image.convert("RGB")
      else:
        rgb_image = image

      # Get basic color statistics
      stat = ImageStat.Stat(rgb_image)

      return {
        "mean_rgb": [round(x) for x in stat.mean],
        "stddev_rgb": [round(x, 2) for x in stat.stddev],
        "brightness": round(sum(stat.mean) / 3, 2),
        "contrast": round(sum(stat.stddev) / 3, 2),
      }

    except Exception as e:
      self.logger.warning(f"Color analysis failed: {e}")
      return {}

  def _estimate_complexity(self, image) -> str:
    """Estimate image complexity based on color variation."""
    try:
      from PIL import ImageStat

      # Convert to grayscale for complexity analysis
      gray_image = image.convert("L")
      stat = ImageStat.Stat(gray_image)

      # Use standard deviation as complexity measure
      complexity_score = stat.stddev[0]

      if complexity_score < 20:
        return "low"
      elif complexity_score < 50:
        return "medium"
      else:
        return "high"

    except Exception:
      return "unknown"

  def _get_dominant_colors(self, image, num_colors: int = 5) -> List[Dict[str, Any]]:
    """Get dominant colors from the image."""
    try:
      # Resize image for faster processing
      small_image = image.copy()
      small_image.thumbnail((100, 100))

      # Get color histogram
      colors = small_image.getcolors(small_image.width * small_image.height)
      if not colors:
        return []

      # Sort by frequency and get top colors
      colors.sort(key=lambda x: x[0], reverse=True)

      dominant_colors = []
      for count, color in colors[:num_colors]:
        if isinstance(color, tuple) and len(color) == 3:
          dominant_colors.append({
            "rgb": color,
            "hex": f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}",
            "percentage": round(
              (count / (small_image.width * small_image.height)) * 100,
              2,
            ),
          })

      return dominant_colors

    except Exception as e:
      self.logger.warning(f"Dominant color extraction failed: {e}")
      return []
