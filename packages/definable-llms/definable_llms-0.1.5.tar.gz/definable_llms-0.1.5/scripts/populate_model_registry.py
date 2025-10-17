#!/usr/bin/env python3
"""Script to populate ModelRegistry table with OpenAI model capabilities."""

import asyncio
import sys
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from definable.llms.database import init_database, get_db_session
from definable.llms.database.schema import ModelRegistry
from definable.llms.config import settings

# OpenAI model data with descriptions
OPENAI_MODELS = [
  # Deep Research Models
  {
    "model_name": "o4-mini-deep-research",
    "provider": "openai",
    "capability": "chat",
    "description": "Deep research model with extended thinking for comprehensive synthesis",
    "display_name": "o4 Mini Deep Research",
    "input_cost_per_token": Decimal("0.000003"),  # $3.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000012"),  # $12.00 per 1M tokens
    "max_context_length": 128000,
    "max_output_tokens": 16000,
    "supports_streaming": True,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
  # Chat Models
  {
    "model_name": "gpt-5",
    "provider": "openai",
    "capability": "chat",
    "description": "Latest flagship model with advanced reasoning, 45% fewer errors, 80% fewer hallucinations",
    "display_name": "GPT-5",
    "input_cost_per_token": Decimal("0.00000125"),  # $1.25 per 1M tokens
    "output_cost_per_token": Decimal("0.00001"),  # $10.00 per 1M tokens
    "max_context_length": 128000,
    "max_output_tokens": 4096,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "gpt-5-mini",
    "provider": "openai",
    "capability": "chat",
    "description": "Fast and cost-efficient version of GPT-5 for defined tasks",
    "display_name": "GPT-5 Mini",
    "input_cost_per_token": Decimal("0.00000025"),  # $0.25 per 1M tokens
    "output_cost_per_token": Decimal("0.000002"),  # $2.00 per 1M tokens
    "max_context_length": 128000,
    "max_output_tokens": 4096,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "gpt-5-nano",
    "provider": "openai",
    "capability": "chat",
    "description": "Ultra-compact speed demon for low-latency needs",
    "display_name": "GPT-5 Nano",
    "input_cost_per_token": Decimal("0.00000005"),  # $0.05 per 1M tokens
    "output_cost_per_token": Decimal("0.0000004"),  # $0.40 per 1M tokens
    "max_context_length": 128000,
    "max_output_tokens": 4096,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "gpt-4.1",
    "provider": "openai",
    "capability": "chat",
    "description": "Enhanced coding model with 1M token context, 21.4% improvement in coding benchmarks",
    "display_name": "GPT-4.1",
    "input_cost_per_token": Decimal("0.000002"),  # $2.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000008"),  # $8.00 per 1M tokens
    "max_context_length": 1000000,  # 1M tokens context window
    "max_output_tokens": 4096,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": False,
  },
  # Embedding Models
  {
    "model_name": "text-embedding-3-large",
    "provider": "openai",
    "capability": "embedding",
    "description": "Highest performance embedding model with up to 3072 dimensions",
    "display_name": "Text Embedding 3 Large",
    "input_cost_per_token": Decimal("0.00000013"),  # $0.13 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),  # No output cost for embeddings
    "max_context_length": 8191,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
  {
    "model_name": "text-embedding-3-small",
    "provider": "openai",
    "capability": "embedding",
    "description": "Cost-effective embedding model with 1536 dimensions",
    "display_name": "Text Embedding 3 Small",
    "input_cost_per_token": Decimal("0.00000002"),  # $0.02 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),  # No output cost for embeddings
    "max_context_length": 8191,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
  # Image Generation Models (special pricing structure)
  {
    "model_name": "gpt-image-1",
    "provider": "openai",
    "capability": "image_gen",
    "description": "Latest multimodal image generation with advanced text rendering and C2PA watermarking",
    "display_name": "GPT Image 1",
    "input_cost_per_token": Decimal("0.040"),  # $0.04 per image (1024x1024)
    "output_cost_per_token": Decimal("0.0"),  # No output tokens for images
    "max_context_length": 4000,  # prompt length limit
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
  {
    "model_name": "dall-e-3",
    "provider": "openai",
    "capability": "image_gen",
    "description": "Advanced image generation model with style control and HD quality options",
    "display_name": "DALL-E 3",
    "input_cost_per_token": Decimal("0.080"),  # $0.08 per image (1024x1024)
    "output_cost_per_token": Decimal("0.0"),  # No output tokens for images
    "max_context_length": 4000,  # prompt length limit
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
]

# Gemini model data
GEMINI_MODELS = [
  # Chat Models - Gemini 2.5 Series (Latest)
  {
    "model_name": "gemini-2.5-pro",
    "provider": "gemini",
    "capability": "chat",
    "description": "State-of-the-art thinking model for complex reasoning in code, math, and STEM",
    "display_name": "Gemini 2.5 Pro",
    "input_cost_per_token": Decimal("0.00000125"),  # Approximate pricing
    "output_cost_per_token": Decimal("0.000005"),
    "max_context_length": 1000000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "gemini-2.5-flash",
    "provider": "gemini",
    "capability": "chat",
    "description": "Best price-performance model for large scale processing and agentic use cases",
    "display_name": "Gemini 2.5 Flash",
    "input_cost_per_token": Decimal("0.0000001"),  # Very low cost
    "output_cost_per_token": Decimal("0.0000004"),
    "max_context_length": 1000000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "gemini-2.5-flash-lite",
    "provider": "gemini",
    "capability": "chat",
    "description": "Fastest flash model optimized for cost-efficiency and high throughput",
    "display_name": "Gemini 2.5 Flash-Lite",
    "input_cost_per_token": Decimal("0.00000005"),  # Most cost-efficient
    "output_cost_per_token": Decimal("0.0000002"),
    "max_context_length": 1000000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  # Chat Models - Gemini 2.0 Series
  {
    "model_name": "gemini-2.0-flash-thinking-exp-1219",
    "provider": "gemini",
    "capability": "chat",
    "description": "Experimental Gemini 2.0 Flash model with built-in thinking capabilities",
    "display_name": "Gemini 2.0 Flash Thinking (Exp)",
    "input_cost_per_token": Decimal("0.0000001"),
    "output_cost_per_token": Decimal("0.0000004"),
    "max_context_length": 2000000,  # 2M context for thinking model
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "gemini-2.0-flash",
    "provider": "gemini",
    "capability": "chat",
    "description": "Second generation workhorse model with 1M token context",
    "display_name": "Gemini 2.0 Flash",
    "input_cost_per_token": Decimal("0.0000001"),
    "output_cost_per_token": Decimal("0.0000004"),
    "max_context_length": 1000000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": False,
  },
  {
    "model_name": "gemini-2.0-flash-lite",
    "provider": "gemini",
    "capability": "chat",
    "description": "Second generation small workhorse model with 1M token context",
    "display_name": "Gemini 2.0 Flash-Lite",
    "input_cost_per_token": Decimal("0.00000005"),
    "output_cost_per_token": Decimal("0.0000002"),
    "max_context_length": 1000000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": False,
  },
  # Embedding Models
  {
    "model_name": "gemini-embedding-001",
    "provider": "gemini",
    "capability": "embedding",
    "description": "High-quality text embeddings model",
    "display_name": "Gemini Embedding 001",
    "input_cost_per_token": Decimal("0.00000001"),
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 2048,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
  # Image Generation
  {
    "model_name": "imagen-4.0-generate-001",
    "provider": "gemini",
    "capability": "image_gen",
    "description": "Advanced image generation model (Imagen 4.0)",
    "display_name": "Imagen 4.0",
    "input_cost_per_token": Decimal("0.040"),
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 4000,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
  # Video Generation
  {
    "model_name": "veo-3.0-generate-001",
    "provider": "gemini",
    "capability": "video_gen",
    "description": "Video generation model (Veo 3.0)",
    "display_name": "Veo 3.0",
    "input_cost_per_token": Decimal("0.100"),  # Approximate pricing for video
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 4000,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
]

ANTHROPIC_MODELS = [
  # Claude 4 Series - Latest Models
  {
    "model_name": "claude-opus-4-1",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Enhanced Claude Opus 4.1 with improved performance and reasoning",
    "display_name": "Claude Opus 4.1",
    "input_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000075"),  # $75.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 32000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-opus-4-1-20250805",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude Opus 4.1 (dated version) with extended thinking",
    "display_name": "Claude Opus 4.1 (20250805)",
    "input_cost_per_token": Decimal("0.000015"),
    "output_cost_per_token": Decimal("0.000075"),
    "max_context_length": 200000,
    "max_output_tokens": 32000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-opus-4-0",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Most capable Claude model with extended thinking for complex tasks",
    "display_name": "Claude Opus 4",
    "input_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000075"),  # $75.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 32000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-opus-4-20250514",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude Opus 4 (dated version) with extended thinking",
    "display_name": "Claude Opus 4 (20250514)",
    "input_cost_per_token": Decimal("0.000015"),
    "output_cost_per_token": Decimal("0.000075"),
    "max_context_length": 200000,
    "max_output_tokens": 32000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-sonnet-4-5",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Latest Claude Sonnet 4.5 - smartest model, efficient for everyday use",
    "display_name": "Claude Sonnet 4.5",
    "input_cost_per_token": Decimal("0.000003"),  # $3.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 64000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-sonnet-4-5-20250929",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude Sonnet 4.5 (dated version) with extended thinking",
    "display_name": "Claude Sonnet 4.5 (20250929)",
    "input_cost_per_token": Decimal("0.000003"),
    "output_cost_per_token": Decimal("0.000015"),
    "max_context_length": 200000,
    "max_output_tokens": 64000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-sonnet-4-0",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Balanced Claude Sonnet 4 for everyday use with strong performance",
    "display_name": "Claude Sonnet 4",
    "input_cost_per_token": Decimal("0.000003"),  # $3.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 64000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-sonnet-4-20250514",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude Sonnet 4 (dated version) with extended thinking",
    "display_name": "Claude Sonnet 4 (20250514)",
    "input_cost_per_token": Decimal("0.000003"),
    "output_cost_per_token": Decimal("0.000015"),
    "max_context_length": 200000,
    "max_output_tokens": 64000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  # Claude 3 Series - Legacy Models
  {
    "model_name": "claude-3-7-sonnet-latest",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Enhanced 3-series model featuring extended-thinking mode",
    "display_name": "Claude 3.7 Sonnet",
    "input_cost_per_token": Decimal("0.000003"),  # $3.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 64000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-3-7-sonnet-20250219",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude 3.7 Sonnet (dated version) with extended thinking support",
    "display_name": "Claude 3.7 Sonnet (20250219)",
    "input_cost_per_token": Decimal("0.000003"),  # $3.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 64000,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": True,
  },
  {
    "model_name": "claude-3-5-haiku-latest",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Fast and cost-effective Claude 3.5 Haiku for high-volume tasks",
    "display_name": "Claude 3.5 Haiku",
    "input_cost_per_token": Decimal("0.0000008"),  # $0.80 per 1M tokens
    "output_cost_per_token": Decimal("0.000004"),  # $4.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": False,
  },
  {
    "model_name": "claude-3-opus-latest",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude 3 Opus flagship model with top-tier performance",
    "display_name": "Claude 3 Opus",
    "input_cost_per_token": Decimal("0.000015"),  # $15.00 per 1M tokens
    "output_cost_per_token": Decimal("0.000075"),  # $75.00 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 4096,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": True,
    "is_active": True,
    "supports_reasoning": False,
  },
  {
    "model_name": "claude-3-haiku-latest",
    "provider": "anthropic",
    "capability": "chat",
    "description": "Claude 3 Haiku fast model for quick responses and high throughput",
    "display_name": "Claude 3 Haiku",
    "input_cost_per_token": Decimal("0.00000025"),  # $0.25 per 1M tokens
    "output_cost_per_token": Decimal("0.00000125"),  # $1.25 per 1M tokens
    "max_context_length": 200000,
    "max_output_tokens": 4096,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": False,
    "is_active": True,
    "supports_reasoning": False,
  },
]

# DeepSeek model data
DEEPSEEK_MODELS = [
  {
    "model_name": "deepseek-chat",
    "provider": "deepseek",
    "capability": "chat",
    "description": "DeepSeek V3 flagship chat model with 671B parameters, competitive with GPT-4o and Claude 3.5 Sonnet",
    "display_name": "DeepSeek Chat",
    "input_cost_per_token": Decimal("0.00000014"),  # $0.14 per 1M tokens (cache miss)
    "output_cost_per_token": Decimal("0.00000028"),  # $0.28 per 1M tokens
    "max_context_length": 64000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": True,
    "supports_vision": False,
    "is_active": True,
  },
  {
    "model_name": "deepseek-reasoner",
    "provider": "deepseek",
    "capability": "chat",
    "description": "DeepSeek R1 reasoning model with extended thinking process, competitive with OpenAI o1",
    "display_name": "DeepSeek Reasoner",
    "input_cost_per_token": Decimal("0.00000055"),  # $0.55 per 1M tokens (cache miss)
    "output_cost_per_token": Decimal("0.0000022"),  # $2.20 per 1M tokens
    "max_context_length": 64000,
    "max_output_tokens": 8192,
    "supports_streaming": True,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
]

# Voyage AI model data (to be added later)
VOYAGE_MODELS = [
  # Embedding Models
  {
    "model_name": "voyage-3-large",
    "provider": "voyage-ai",
    "capability": "embedding",
    "description": "Latest and greatest embedding model from Voyage AI.",
    "display_name": "Voyage 3 Large",
    "input_cost_per_token": Decimal("0.00000018"),  # $0.18 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 16384,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
  {
    "model_name": "voyage-3.5",
    "provider": "voyage-ai",
    "capability": "embedding",
    "description": "Cheaper and faster than voyage-3-large.",
    "display_name": "Voyage 3.5",
    "input_cost_per_token": Decimal("0.00000015"),  # $0.15 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 16384,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
  {
    "model_name": "voyage-3.5-lite",
    "provider": "voyage-ai",
    "capability": "embedding",
    "description": "Lite version of voyage-3.5.",
    "display_name": "Voyage 3.5 Lite",
    "input_cost_per_token": Decimal("0.00000010"),  # $0.10 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 16384,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
  {
    "model_name": "voyage-code-3",
    "provider": "voyage-ai",
    "capability": "embedding",
    "description": "Specialized for code embeddings.",
    "display_name": "Voyage Code 3",
    "input_cost_per_token": Decimal("0.00000018"),  # $0.18 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 16384,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
  {
    "model_name": "voyage-finance-2",
    "provider": "voyage-ai",
    "capability": "embedding",
    "description": "Specialized for finance embeddings.",
    "display_name": "Voyage Finance 2",
    "input_cost_per_token": Decimal("0.00000018"),  # $0.18 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 16384,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
  {
    "model_name": "voyage-law-2",
    "provider": "voyage-ai",
    "capability": "embedding",
    "description": "Specialized for law embeddings.",
    "display_name": "Voyage Law 2",
    "input_cost_per_token": Decimal("0.00000018"),  # $0.18 per 1M tokens
    "output_cost_per_token": Decimal("0.0"),
    "max_context_length": 16384,
    "max_output_tokens": None,
    "supports_streaming": False,
    "supports_functions": False,
    "supports_vision": False,
    "is_active": True,
  },
]


async def populate_model_registry():
  """Populate ModelRegistry table with OpenAI, Gemini, and Anthropic model data."""
  print("Starting ModelRegistry population...")

  # Initialize database connection
  database_url = settings.db_url

  try:
    await init_database(database_url)
    print("Database initialized successfully")
  except Exception as e:
    print(f"Database initialization failed: {e}")
    return False

  # Get database session
  try:
    async with get_db_session() as db:
      # Clear existing OpenAI models
      print("Clearing existing OpenAI models...")
      from sqlalchemy import delete

      result = await db.execute(delete(ModelRegistry).where(ModelRegistry.provider == "openai"))
      await db.commit()
      print(f"Removed {result.rowcount} existing OpenAI models")

      # Clear existing Gemini models
      print("Clearing existing Gemini models...")
      result = await db.execute(delete(ModelRegistry).where(ModelRegistry.provider == "gemini"))
      await db.commit()
      print(f"Removed {result.rowcount} existing Gemini models")

      # Clear existing Anthropic models
      print("Clearing existing Anthropic models...")
      result = await db.execute(delete(ModelRegistry).where(ModelRegistry.provider == "anthropic"))
      await db.commit()
      print(f"Removed {result.rowcount} existing Anthropic models")

      # Clear existing DeepSeek models
      print("Clearing existing DeepSeek models...")
      result = await db.execute(delete(ModelRegistry).where(ModelRegistry.provider == "deepseek"))
      await db.commit()
      print(f"Removed {result.rowcount} existing DeepSeek models")

      # Insert new model data
      print("\nInserting OpenAI models...")
      inserted_count = 0

      for model_data in OPENAI_MODELS:
        model = ModelRegistry(**model_data, last_updated=datetime.now())
        db.add(model)
        inserted_count += 1
        print(f"  Added {model_data['model_name']} ({model_data['capability']})")

      print(f"Successfully inserted {inserted_count} OpenAI models!")

      # Insert Gemini models
      print("\nInserting Gemini models...")
      gemini_count = 0

      for model_data in GEMINI_MODELS:
        model = ModelRegistry(**model_data, last_updated=datetime.now())
        db.add(model)
        gemini_count += 1
        print(f"  Added {model_data['model_name']} ({model_data['capability']})")

      await db.commit()
      print(f"Successfully inserted {gemini_count} Gemini models!")

      # Insert Anthropic models
      print("\nInserting Anthropic models...")
      anthropic_count = 0

      for model_data in ANTHROPIC_MODELS:
        model = ModelRegistry(**model_data, last_updated=datetime.now())
        db.add(model)
        anthropic_count += 1
        print(f"  Added {model_data['model_name']} ({model_data['capability']})")

      await db.commit()
      print(f"Successfully inserted {anthropic_count} Anthropic models!")

      # Insert DeepSeek models
      print("\nInserting DeepSeek models...")
      deepseek_count = 0

      for model_data in DEEPSEEK_MODELS:
        model = ModelRegistry(**model_data, last_updated=datetime.now())
        db.add(model)
        deepseek_count += 1
        print(f"  Added {model_data['model_name']} ({model_data['capability']})")

      await db.commit()
      print(f"Successfully inserted {deepseek_count} DeepSeek models!")

      # Verify insertion
      print("\nVerifying inserted data...")
      from sqlalchemy import select

      # Show OpenAI models
      result = await db.execute(
        select(
          ModelRegistry.model_name,
          ModelRegistry.capability,
          ModelRegistry.input_cost_per_token,
          ModelRegistry.supports_streaming,
        )
        .where(ModelRegistry.provider == "openai")
        .order_by(ModelRegistry.capability, ModelRegistry.model_name)
      )
      rows = result.fetchall()

      print(f"\n[OpenAI] Found {len(rows)} models:")
      print("   Model Name               | Capability | Cost/Token   | Streaming")
      print("   " + "-" * 70)
      for row in rows:
        streaming = "Yes" if row[3] else "No"
        print(f"   {row[0]:<23} | {row[1]:<10} | ${row[2]:<10} | {streaming}")

      # Show Gemini models
      result = await db.execute(
        select(
          ModelRegistry.model_name,
          ModelRegistry.capability,
          ModelRegistry.input_cost_per_token,
          ModelRegistry.supports_streaming,
        )
        .where(ModelRegistry.provider == "gemini")
        .order_by(ModelRegistry.capability, ModelRegistry.model_name)
      )
      rows = result.fetchall()

      print(f"\n[Gemini] Found {len(rows)} models:")
      print("   Model Name               | Capability | Cost/Token   | Streaming")
      print("   " + "-" * 70)
      for row in rows:
        streaming = "Yes" if row[3] else "No"
        print(f"   {row[0]:<23} | {row[1]:<10} | ${row[2]:<10} | {streaming}")

      # Show Anthropic models
      result = await db.execute(
        select(
          ModelRegistry.model_name,
          ModelRegistry.capability,
          ModelRegistry.input_cost_per_token,
          ModelRegistry.supports_streaming,
        )
        .where(ModelRegistry.provider == "anthropic")
        .order_by(ModelRegistry.capability, ModelRegistry.model_name)
      )
      rows = result.fetchall()

      print(f"\n[Anthropic] Found {len(rows)} models:")
      print("   Model Name               | Capability | Cost/Token   | Streaming")
      print("   " + "-" * 70)
      for row in rows:
        streaming = "Yes" if row[3] else "No"
        print(f"   {row[0]:<23} | {row[1]:<10} | ${row[2]:<10} | {streaming}")

      return True

  except Exception as e:
    print(f"Error during population: {e}")
    return False


async def main():
  """Main entry point."""
  print("Model Registry Population Script (OpenAI, Gemini, and Anthropic)")
  print("=" * 50)

  success = await populate_model_registry()

  if success:
    print("\nModelRegistry population completed successfully!")
  else:
    print("\nModelRegistry population failed!")
    print("Check the database connection and try again")
    return 1

  return 0


if __name__ == "__main__":
  exit_code = asyncio.run(main())
  sys.exit(exit_code)
