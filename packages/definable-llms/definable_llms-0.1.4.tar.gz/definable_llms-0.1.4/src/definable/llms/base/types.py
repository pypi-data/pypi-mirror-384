"""Type definitions for the LLM library."""

from typing import Optional, List, Dict, Any, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from pathlib import Path


class MessageRole(str, Enum):
  """Message roles in a conversation."""

  SYSTEM = "system"
  USER = "user"
  ASSISTANT = "assistant"
  FUNCTION = "function"
  TOOL = "tool"


class ContentType(str, Enum):
  """Content types for messages."""

  TEXT = "text"
  IMAGE = "image"
  AUDIO = "audio"
  VIDEO = "video"
  FILE = "file"


class FinishReason(str, Enum):
  """Reasons for completion finish."""

  STOP = "stop"
  LENGTH = "length"
  FUNCTION_CALL = "function_call"
  TOOL_CALLS = "tool_calls"
  CONTENT_FILTER = "content_filter"
  ERROR = "error"


class ImageSize(str, Enum):
  """Standard image sizes for generation."""

  SMALL = "1024x1024"  # DALL-E 3 square
  MEDIUM = "1024x1792"  # Portrait
  LARGE = "1792x1024"  # Landscape


class ImageStyle(str, Enum):
  """Image generation styles."""

  VIVID = "vivid"
  NATURAL = "natural"


class ImageQuality(str, Enum):
  """Image generation quality."""

  STANDARD = "standard"
  HD = "hd"


class FileInfo(BaseModel):
  """Information about an uploaded file."""

  model_config = ConfigDict(arbitrary_types_allowed=True)

  filename: str
  content_type: str
  size: int
  path: Optional[Path] = None
  content: Optional[bytes] = None
  metadata: Dict[str, Any] = Field(default_factory=dict)
  processed_text: Optional[str] = None
  chunks: Optional[List[str]] = None


class FunctionCall(BaseModel):
  """Function call information."""

  name: str
  arguments: str  # JSON string of arguments


class ToolCall(BaseModel):
  """Tool call information."""

  id: str
  type: Literal["function"]
  function: FunctionCall


class MessageContent(BaseModel):
  """Content of a message, supporting multimodal inputs."""

  type: ContentType
  text: Optional[str] = None
  image_url: Optional[str] = None
  image_base64: Optional[str] = None
  file_path: Optional[str] = None
  file_info: Optional[FileInfo] = None


class Message(BaseModel):
  """A single message in a conversation."""

  role: MessageRole
  content: Union[str, List[MessageContent]]
  name: Optional[str] = None
  function_call: Optional[FunctionCall] = None
  tool_calls: Optional[List[ToolCall]] = None
  reasoning_content: Optional[str] = None  # For models with reasoning/thinking process
  metadata: Dict[str, Any] = Field(default_factory=dict)
  timestamp: datetime = Field(default_factory=datetime.now)


class ChatRequest(BaseModel):
  """Request for chat completion."""

  messages: List[Message]
  model: Optional[str] = None
  temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
  max_tokens: Optional[int] = Field(None, gt=0)
  top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
  top_k: Optional[int] = Field(None, gt=0)  # Gemini-specific parameter
  frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
  presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
  stop: Optional[Union[str, List[str]]] = None
  stream: bool = True  # Streaming will be enabled by default
  reasoning: Optional[bool] = None  # Enable reasoning/extended thinking mode
  reasoning_budget_tokens: Optional[int] = Field(None)
  functions: Optional[List[Dict[str, Any]]] = None
  function_call: Optional[Union[str, Dict[str, str]]] = None
  tools: Optional[List[Dict[str, Any]]] = None
  tool_choice: Optional[Union[str, Dict[str, Any]]] = None
  user: Optional[str] = None
  seed: Optional[int] = None
  response_format: Optional[Dict[str, str]] = None
  logit_bias: Optional[Dict[str, float]] = None
  logprobs: Optional[bool] = None
  top_logprobs: Optional[int] = None
  n: int = 1


class Usage(BaseModel):
  """Token usage information."""

  input_tokens: int
  output_tokens: int
  total_tokens: int
  cached_tokens: Optional[int] = None


class Choice(BaseModel):
  """A single choice in a chat completion."""

  index: int
  message: Message
  finish_reason: Optional[FinishReason] = None
  logprobs: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
  """Response from chat completion."""

  id: str
  object: str = "chat.completion"
  created: int
  model: str
  choices: List[Choice]
  usage: Optional[Usage] = None
  system_fingerprint: Optional[str] = None
  metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
  """A chunk in a streaming response."""

  id: str
  object: str = "chat.completion.chunk"
  created: int
  model: str
  choices: List[Dict[str, Any]]
  usage: Optional[Usage] = None


class ImageRequest(BaseModel):
  """Request for image generation."""

  prompt: str
  model: Optional[str] = None
  n: int = Field(default=1, ge=1, le=10)
  size: Optional[ImageSize] = ImageSize.LARGE
  quality: Optional[ImageQuality] = ImageQuality.STANDARD
  style: Optional[ImageStyle] = ImageStyle.VIVID
  response_format: Literal["url", "b64_json"] = "url"
  user: Optional[str] = None
  stream: bool = False  # Enable streaming for gpt-image-1
  partial_images: Optional[int] = Field(default=5, ge=1, le=5)  # Number of partial images (1-5)
  upload_to_gcp: bool = False  # Upload generated images to GCP Cloud Storage


class ImageData(BaseModel):
  """Generated image data."""

  url: Optional[str] = None  # GCP signed URL (if uploaded) or None
  b64_json: Optional[str] = None
  revised_prompt: Optional[str] = None


class ImageResponse(BaseModel):
  """Response from image generation."""

  created: int
  data: List[ImageData]


class ImageStreamChunk(BaseModel):
  """A chunk in a streaming image generation response."""

  type: str  # "image_generation.partial_image" or "image_generation.complete"
  partial_image_index: Optional[int] = None
  b64_json: Optional[str] = None
  url: Optional[str] = None  # GCP URL for uploaded images
  data: Optional[List[ImageData]] = None  # For complete event


class EmbeddingRequest(BaseModel):
  """Request for text embeddings."""

  input: Union[str, List[str]]
  model: Optional[str] = None
  encoding_format: Literal["float", "base64"] = "float"
  dimensions: Optional[int] = None
  user: Optional[str] = None
  # Gemini-specific fields
  task_type: Optional[str] = None  # e.g., "RETRIEVAL_QUERY", "RETRIEVAL_DOCUMENT"
  title: Optional[str] = None  # Optional title for the text (Gemini)


class Embedding(BaseModel):
  """A single embedding."""

  index: int
  embedding: Union[List[float], str]  # float list or base64 string
  object: str = "embedding"


class EmbeddingResponse(BaseModel):
  """Response from embedding generation."""

  object: str = "list"
  data: List[Embedding]
  model: str
  usage: Usage


class SessionInfo(BaseModel):
  """Information about a chat session."""

  session_id: str
  session_title: str
  provider: str
  model: str
  created_at: datetime
  updated_at: datetime
  message_count: int
  total_tokens: int
  metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseQuery(BaseModel):
  """Query for knowledge base search."""

  query: str
  kb_ids: List[str]
  top_k: int = Field(default=5, ge=1, le=100)
  min_score: float = Field(default=0.7, ge=0.0, le=1.0)
  filters: Optional[Dict[str, Any]] = None


class KnowledgeResult(BaseModel):
  """Result from knowledge base search."""

  id: str
  content: str
  score: float
  metadata: Dict[str, Any]
  source: Optional[str] = None


class KnowledgeResponse(BaseModel):
  """Response from knowledge base query."""

  query: str
  results: List[KnowledgeResult]
  total_results: int
  processing_time: float


class ResearchRequest(BaseModel):
  """Request for deep research."""

  topic: str
  depth: Literal["quick", "standard", "comprehensive"] = "standard"
  sources: Optional[List[str]] = None
  max_sources: int = Field(default=10, ge=1, le=50)
  include_citations: bool = True


class ResearchSection(BaseModel):
  """A section in research results."""

  title: str
  content: str
  citations: Optional[List[str]] = None
  confidence: float = Field(ge=0.0, le=1.0)


class ResearchResponse(BaseModel):
  """Response from deep research."""

  topic: str
  summary: str
  sections: List[ResearchSection]
  sources: List[str]
  total_sources_analyzed: int
  processing_time: float
  metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelCapabilities(BaseModel):
  """Capabilities of a specific model."""

  chat: bool = True
  streaming: bool = False
  function_calling: bool = False
  vision: bool = False
  audio: bool = False
  embeddings: bool = False
  image_generation: bool = False
  reasoning: bool = False  # Supports extended reasoning/thinking mode
  max_context_length: int = 4096
  max_output_tokens: Optional[int] = None
  supported_file_types: List[str] = Field(default_factory=list)
  input_cost_per_token: Optional[float] = None  # Cost per input token in USD
  output_cost_per_token: Optional[float] = None  # Cost per output token in USD
  supports_system_messages: bool = True
  supports_tool_calls: bool = False
  supports_parallel_tool_calls: bool = False


class ModelInfo(BaseModel):
  """Information about a specific model."""

  name: str
  display_name: Optional[str] = None
  description: Optional[str] = None
  capabilities: ModelCapabilities
  provider: str
  model_type: Literal["chat", "embedding", "image", "audio"] = "chat"
  version: Optional[str] = None
  release_date: Optional[str] = None
  is_deprecated: bool = False
  deprecation_message: Optional[str] = None


class ProviderCapabilities(BaseModel):
  """Capabilities of a provider (aggregated from all models)."""

  chat: bool = True
  streaming: bool = False
  function_calling: bool = False
  vision: bool = False
  audio: bool = False
  embeddings: bool = False
  image_generation: bool = False
  max_context_length: int = 4096
  supported_models: List[str] = Field(default_factory=list)
  supported_file_types: List[str] = Field(default_factory=list)


class ProviderInfo(BaseModel):
  """Information about a provider."""

  name: str
  type: str
  version: str
  capabilities: ProviderCapabilities
  models: List[ModelInfo] = Field(default_factory=list)
  is_available: bool
  error_message: Optional[str] = None


class HealthCheck(BaseModel):
  """Health check response."""

  status: Literal["healthy", "degraded", "unhealthy"]
  timestamp: datetime
  version: str
  providers: List[ProviderInfo]
  checks: Dict[str, bool]
  errors: List[str] = Field(default_factory=list)
