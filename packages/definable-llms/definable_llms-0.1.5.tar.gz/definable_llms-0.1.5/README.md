# LLM Library - Scalable Multi-Provider LLM Library

A production-ready, scalable multi-provider Large Language Model (LLM) library designed for **definable.ai**. This library provides a unified interface for multiple LLM providers including OpenAI, Gemini, and Anthropic, with support for chat completions, image generation, file processing, and advanced capabilities.

## ✨ Features

### Core Capabilities
- **Multi-Provider Support**: OpenAI, Gemini, Anthropic (extensible architecture)
- **Unified Interface**: Consistent API across all providers
- **Session Management**: Persistent conversation sessions with context
- **File Processing**: Support for PDF, DOCX, PPTX, XLSX, images, and text files
- **Streaming Responses**: Real-time streaming for chat completions
- **Rate Limiting**: Built-in token bucket rate limiting
- **Retry Logic**: Exponential backoff with circuit breaker patterns
- **FastAPI Integration**: Production-ready REST API

### Advanced Features
- **Provider Switching**: Change providers mid-conversation
- **Image Processing**: OCR, analysis, and multimodal support
- **Chunking**: Smart text chunking for large documents
- **Error Handling**: Comprehensive exception hierarchy
- **Configuration**: Environment-based configuration management
- **Monitoring**: Structured logging and health checks

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd llms_lib

# Install dependencies using uv
uv sync

# Or with pip
pip install -e .
```

## ⚙️ Configuration

Create a `.env` file in your project root:

```env
# API Keys
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Provider Settings
DEFAULT_PROVIDER=openai
OPENAI_DEFAULT_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=90000

# Session Management
SESSION_STORE_TYPE=memory  # or redis
SESSION_TTL_SECONDS=3600
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ENABLED=true
```

## 🚀 Quick Start

### 1. Basic Chat Completion

```python
import asyncio
from definable.llms import provider_factory

async def basic_chat():
    # Get an OpenAI provider
    provider = provider_factory.get_provider("openai")
    
    # Create a chat request
    from definable.llms.base.types import ChatRequest, Message, MessageRole
    
    messages = [
        Message(role=MessageRole.USER, content="Hello, how are you?")
    ]
    
    request = ChatRequest(messages=messages, model="gpt-4-turbo-preview")
    response = await provider.chat(request)
    
    print(response.choices[0].message.content)

# Run the example
asyncio.run(basic_chat())
```

### 2. Session-Based Conversation

```python
import asyncio
from definable.llms import session_manager

async def session_chat():
    # Create a new session
    session = await session_manager.create_session(
        provider="openai",
        model="gpt-4-turbo-preview"
    )
    
    # Send messages in the session
    response1 = await session_manager.chat(
        session_id=session.session_id,
        message="My name is Alice. Please remember this."
    )
    print("Assistant:", response1.choices[0].message.content)
    
    response2 = await session_manager.chat(
        session_id=session.session_id,
        message="What's my name?"
    )
    print("Assistant:", response2.choices[0].message.content)

asyncio.run(session_chat())
```

### 3. File Processing

```python
import asyncio
from definable.llms import file_processor

async def process_document():
    # Process a PDF file
    processed_file = await file_processor.process_file(
        filename="document.pdf",
        file_path="/path/to/document.pdf"
    )
    
    print(f"Extracted text length: {len(processed_file.processed_text)}")
    print(f"Number of chunks: {len(processed_file.chunks)}")
    print(f"Metadata: {processed_file.metadata}")

asyncio.run(process_document())
```

### 4. Streaming Responses

```python
import asyncio
from definable.llms import session_manager

async def streaming_chat():
    session = await session_manager.create_session(
        provider="openai",
        model="gpt-4-turbo-preview"
    )
    
    response_stream = await session_manager.chat(
        session_id=session.session_id,
        message="Tell me a story about AI",
        stream=True
    )
    
    async for chunk in response_stream:
        if chunk.choices and chunk.choices[0].get("delta", {}).get("content"):
            print(chunk.choices[0]["delta"]["content"], end="")

asyncio.run(streaming_chat())
```

## 🌐 FastAPI Server

### Running the Server

```python
from definable.llms.api import run_server

# Run with default settings
run_server()

# Or with custom settings
run_server(host="0.0.0.0", port=8080, reload=True)
```

### API Endpoints

The FastAPI server provides the following endpoints:

- **Health**: `GET /api/v1/health` - System health check
- **Providers**: `GET /api/v1/providers` - List available providers
- **Sessions**: `POST /api/v1/sessions` - Create conversation session
- **Chat**: `POST /api/v1/chat` - Send chat messages
- **Files**: `POST /api/v1/files/process` - Process uploaded files

### Example API Usage

```bash
# Create a session
curl -X POST "http://localhost:8000/api/v1/sessions" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4-turbo-preview"
  }'

# Send a chat message
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, world!",
    "session_id": "your-session-id"
  }'

# Process a file
curl -X POST "http://localhost:8000/api/v1/files/process" \
  -F "file=@document.pdf"
```

## 🔌 Adding New Providers

The library is designed for easy extension. Here's how to add a new provider:

```python
from definable.llms.base import BaseProvider, ProviderCapabilities
from definable.llms.base.types import ChatRequest, ChatResponse

class CustomProvider(BaseProvider):
    def _initialize(self, **kwargs):
        # Initialize your provider
        pass
    
    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            chat=True,
            streaming=False,
            # ... other capabilities
        )
    
    async def chat(self, request: ChatRequest) -> ChatResponse:
        # Implement chat functionality
        pass
    
    async def validate_model(self, model: str) -> bool:
        # Validate model support
        pass

# Register the provider
from definable.llms import provider_factory
provider_factory.register_provider("custom", CustomProvider)
```

## 🏗️ Architecture

The library follows a modular, plugin-based architecture:

```
src/libs/llms/
├── base/              # Base classes and types
├── providers/         # Provider implementations
├── sessions/          # Session management
├── processors/        # File processing
├── utils/             # Utilities (rate limiting, retry, etc.)
├── api/               # FastAPI integration
└── config.py          # Configuration management
```

### Key Components

- **BaseProvider**: Abstract base class for all providers
- **SessionManager**: Manages conversation sessions
- **FileProcessor**: Handles document processing
- **RateLimiter**: Token bucket rate limiting
- **RetryStrategy**: Exponential backoff retry logic

## 🧪 Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src/libs/llms

# Run specific test category
python -m pytest tests/unit/
python -m pytest tests/integration/
```

## 📊 Monitoring and Observability

The library includes comprehensive logging and monitoring:

```python
# Configure structured logging
from definable.llms.utils import configure_logging
configure_logging(log_level="INFO", json_logs=True)

# Health checks
from definable.llms.api.routes.health import health_check
health_status = await health_check()
```

## 🔒 Security Considerations

- **API Keys**: Stored securely in environment variables
- **Rate Limiting**: Prevents abuse and quota exhaustion
- **Input Validation**: All inputs are validated and sanitized
- **Error Handling**: Sensitive information is not exposed in errors

## 🚢 Production Deployment

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . .
RUN pip install uv && uv sync

EXPOSE 8000
CMD ["python", "-m", "definable.llms.api.main"]
```

### Environment Configuration

For production, ensure you set:
- `DEBUG=false`
- `LOG_LEVEL=INFO`
- Appropriate rate limits
- Redis for session storage
- Proper CORS origins

## 📚 Documentation

- **API Documentation**: Available at `/docs` when running the server
- **Provider Guide**: See `docs/providers.md`
- **Configuration Reference**: See `docs/configuration.md`
- **Deployment Guide**: See `docs/deployment.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is proprietary to definable.ai.

## 💬 Support

For support and questions, please contact the definable.ai team.

---

Built with ❤️ for scalable AI applications.
