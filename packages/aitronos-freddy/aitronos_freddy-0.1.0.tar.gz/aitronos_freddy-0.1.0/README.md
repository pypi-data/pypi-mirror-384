# Freddy Python SDK

[![PyPI version](https://badge.fury.io/py/aitronos-freddy.svg)](https://badge.fury.io/py/aitronos-freddy)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [Freddy AI Assistant API](https://freddy-api.aitronos.com)

## Features

- **AI Responses**: Generate text, structured outputs, and tool-augmented responses
- **File Management**: Upload, list, retrieve, and delete files
- **Vector Stores**: Create and manage knowledge bases for RAG
- **Image Generation**: Generate, upscale, and manipulate images with DALL-E and ClipDrop
- **Sync & Async**: Full support for both synchronous and asynchronous operations
- **Type Hints**: Comprehensive type annotations for better IDE support
- **Production Ready**: Error handling, timeouts, and context managers

## Installation

```bash
pip install aitronos-freddy
```

## Quick Start

```python
import os
from freddy import FreddyClient

# Initialize client
client = FreddyClient(api_key=os.getenv("FREDDY_API_KEY"))

# Create AI response
response = client.responses.create(
    model="gpt-4.1",
    inputs=[
        {"role": "user", "texts": [{"text": "Hello, Freddy!"}]}
    ],
    organization_id="your-org-id"
)

print(response.output[0].content[0].text)
client.close()
```

### Using Context Managers (Recommended)

```python
with FreddyClient(api_key="your-api-key") as client:
    response = client.responses.create(
        model="gpt-4.1",
        inputs=[{"role": "user", "texts": [{"text": "Hello!"}]}]
    )
    print(response.output[0].content[0].text)
```

### Async Usage

```python
import asyncio
from freddy import AsyncFreddyClient

async def main():
    async with AsyncFreddyClient(api_key="your-api-key") as client:
        response = await client.responses.create(
            model="gpt-4.1",
            inputs=[{"role": "user", "texts": [{"text": "Hello!"}]}]
        )
        print(response.output[0].content[0].text)

asyncio.run(main())
```

## Core Features

### AI Responses

```python
# Basic text generation
response = client.responses.create(
    model="gpt-4.1",
    inputs=[{"role": "user", "texts": [{"text": "Explain quantum computing"}]}],
    temperature=0.7,
    max_tokens=500
)

# With conversation context
response = client.responses.create(
    model="claude-3-5-sonnet",
    inputs=[
        {"role": "user", "texts": [{"text": "What is Python?"}]},
        {"role": "assistant", "texts": [{"text": "Python is a programming language..."}]},
        {"role": "user", "texts": [{"text": "Show me an example"}]}
    ],
    thread_id="thread_abc123"
)
```

### File Management

```python
# Upload file
file = client.files.upload(
    organization_id="org_123",
    file="document.pdf",
    purpose="vector_store"
)

# List files
files = client.files.list(
    organization_id="org_123",
    page=1,
    page_size=20
)

# Get file details
file = client.files.retrieve("org_123", "file_abc")

# Delete file
client.files.delete("org_123", "file_abc")
```

### Vector Stores

```python
# Create vector store
store = client.vector_stores.create(
    organization_id="org_123",
    name="Company Knowledge Base",
    description="Internal documentation",
    access_mode="organization"
)

# Add file to vector store
client.vector_stores.add_file("org_123", store.id, "file_abc")

# List vector stores
stores = client.vector_stores.list("org_123")

# Query with RAG
response = client.responses.create(
    model="gpt-4.1",
    inputs=[{"role": "user", "texts": [{"text": "What is our return policy?"}]}],
    tools=[{
        "type": "file_search",
        "vectorStoreIds": [store.id]
    }]
)
```

### Image Generation

```python
# Generate images
result = client.images.generate(
    organization_id="org_123",
    prompt="A serene mountain landscape at sunset",
    model="dall-e-3",
    size="1024x1024"
)

# Save to disk
result.save_all("./images", prefix="mountain")

# Upscale image
upscaled = client.images.upscale(
    organization_id="org_123",
    image="photo.jpg",
    target_width=2048,
    target_height=2048
)

# Remove background
no_bg = client.images.remove_background(
    organization_id="org_123",
    image="photo.jpg"
)

# Replace background
new_bg = client.images.replace_background(
    organization_id="org_123",
    image="photo.jpg",
    prompt="tropical beach with palm trees"
)
```

## Configuration

### Custom Base URL

```python
client = FreddyClient(
    api_key="your-key",
    base_url="https://custom-api.example.com"
)
```

### Custom Timeout

```python
client = FreddyClient(
    api_key="your-key",
    timeout=60.0  # 60 seconds
)
```

## Error Handling

```python
from freddy import FreddyClient
from freddy.exceptions import (
    AuthenticationError,
    RateLimitError,
    APIError
)

try:
    with FreddyClient(api_key="invalid-key") as client:
        response = client.responses.create(...)
except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e.message}")
except APIError as e:
    print(f"API error {e.status_code}: {e.message}")
```

## Examples

See the [examples/](examples/) directory for more complete examples:

- [basic_usage.py](examples/basic_usage.py) - Simple AI response generation
- [file_upload.py](examples/file_upload.py) - File management operations
- [vector_stores.py](examples/vector_stores.py) - Knowledge base creation
- [image_generation.py](examples/image_generation.py) - Image operations
- [async_usage.py](examples/async_usage.py) - Async client usage

## Documentation

- [API Reference](https://freddy-api.aitronos.com/docs)
- [OpenAPI Specification](https://freddy-api.aitronos.com/openapi.json)

## Development

```bash
# Clone repository
git clone https://github.com/aitronos/freddy-python.git
cd freddy-python

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run unit tests
poetry run pytest

# Run integration tests (requires API credentials)
# Option 1: Use .env file (recommended)
cp env.example .env
# Edit .env with your credentials

# Option 2: Export variables
export FREDDY_API_KEY=your-key
export FREDDY_ORG_ID=your-org-id

# Run tests
poetry run pytest tests/integration/ --integration --env=staging

# Format code
poetry run black freddy tests examples
poetry run ruff check freddy tests examples
```

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## Requirements

- Python 3.11+
- httpx >= 0.25.0
- pydantic >= 2.9.0

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- Documentation: https://freddy-api.aitronos.com/docs
- Issues: https://github.com/aitronos/freddy-python/issues
- Email: phillip.loacker@aitronos.com

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.
