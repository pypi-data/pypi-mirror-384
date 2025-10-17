"""Gemini provider module."""

try:
  from .client import GeminiProvider

  __all__ = ["GeminiProvider"]
except ImportError:
  # Gemini provider is not available due to missing dependencies
  import warnings

  warnings.warn("Gemini provider is not available. Install google-generativeai to enable it.", ImportWarning)

  # Create a stub class to prevent import errors
  class GeminiProvider:  # type: ignore[no-redef]
    def __init__(self, *args, **kwargs):
      raise ImportError("Gemini provider requires google-generativeai. Install with: pip install google-generativeai")

  __all__ = ["GeminiProvider"]
