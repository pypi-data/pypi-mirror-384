"""LLM provider implementations."""

from .factory import ProviderFactory, ProviderRegistry, provider_factory
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider

# Optional providers
try:
  from .gemini import GeminiProvider

  _gemini_available = True
except ImportError:
  GeminiProvider = None
  _gemini_available = False

try:
  from .deepseek import DeepSeekProvider

  _deepseek_available = True
except ImportError:
  DeepSeekProvider = None
  _deepseek_available = False

__all__ = [
  "ProviderFactory",
  "ProviderRegistry",
  "provider_factory",
  "OpenAIProvider",
  "AnthropicProvider",
]

if _gemini_available:
  __all__.append("GeminiProvider")

if _deepseek_available:
  __all__.append("DeepSeekProvider")
