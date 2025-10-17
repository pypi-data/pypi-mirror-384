# Gushwork RAG Python SDK

A Python client library for the Gushwork RAG (Retrieval-Augmented Generation) API, inspired by Pinecone's SDK design philosophy.

## Features

- 🔐 **API Key Management** - Create and manage API keys with role-based access control
- 📁 **File Management** - Upload and manage documents with S3 integration
- 🗂️ **Namespace Organization** - Organize documents into logical namespaces
- 💬 **AI Chat Completions** - Get intelligent responses using your documents as context
- 🌊 **Streaming Support** - Real-time streaming responses for chat completions
- 📊 **Structured Output** - Get responses in specific JSON formats
- 🎯 **Type Hints** - Full type hint support for better IDE integration
- 🐍 **Pythonic API** - Clean, intuitive interface following Python best practices

## Installation

```bash
pip install gushwork-rag
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from gushwork_rag import GushworkRAG

# Initialize the client
client = GushworkRAG(
    api_key="your-api-key-here",
    base_url="http://localhost:8080"  # or your production URL
)

# Create a namespace
namespace = client.namespaces.create(
    name="my-documents",
    instructions="Answer questions based on the provided documents."
)

# Upload a file
file = client.files.upload(
    file_path="document.pdf",
    namespace="my-documents"
)

# Chat with your documents
response = client.chat.create(
    namespace="my-documents",
    messages=[
        {"role": "user", "content": "What is the main topic of the document?"}
    ],
    model="gpt-3.5-turbo"
)

print(response.content)
```

## Usage Examples

### Context Manager (Recommended)

```python
from gushwork_rag import GushworkRAG

with GushworkRAG(api_key="your-api-key") as client:
    # Your code here
    health = client.health_check()
    print(health["status"])
# Client is automatically closed
```

### Managing Namespaces

```python
# Create a namespace
namespace = client.namespaces.create(
    name="research-papers",
    instructions="Provide scientific and accurate answers based on research papers."
)

# List all namespaces
namespaces = client.namespaces.list()
for ns in namespaces:
    print(f"{ns.name}: {ns.instructions}")

# Get a specific namespace
namespace = client.namespaces.get(namespace_id="ns_123")

# Update a namespace
updated = client.namespaces.update(
    namespace_id="ns_123",
    instructions="New instructions here"
)

# Delete a namespace
client.namespaces.delete(namespace_id="ns_123")
```

### File Operations

```python
# Upload a file
file = client.files.upload(
    file_path="path/to/document.pdf",
    namespace="my-documents",
    mime_type="application/pdf"  # Optional, auto-detected
)
print(f"Uploaded: {file.file_name}")

# List files in a namespace
files = client.files.list_by_namespace(
    namespace="my-documents",
    limit=50,
    skip=0
)
print(f"Total files: {files.total}")
for file in files.files:
    print(f"- {file.file_name} ({file.status})")

# Get file details
file = client.files.get(file_id="file_123")
print(f"Status: {file.status}")
print(f"Uploaded: {file.uploaded_at}")

# Update file status (typically for internal use)
from gushwork_rag import FileStatus

file = client.files.update_status(
    file_id="file_123",
    status=FileStatus.FILE_INDEXED,
    processed_at="2024-01-01T00:00:00Z"
)

# Delete a file
client.files.delete(file_id="file_123")
```

### Chat Completions

#### Simple Chat

```python
response = client.chat.create(
    namespace="my-documents",
    messages=[
        {"role": "user", "content": "What are the key findings?"}
    ],
    model="gpt-3.5-turbo"
)
print(response.content)
```

#### Multi-turn Conversation

```python
from gushwork_rag import Message

messages = [
    Message(role="user", content="What is the document about?"),
    Message(role="assistant", content="The document discusses AI technologies."),
    Message(role="user", content="What are the main benefits mentioned?"),
]

response = client.chat.create(
    namespace="my-documents",
    messages=messages,
    model="gpt-4"
)
print(response.content)
```

#### Streaming Chat

```python
# Stream responses in real-time
for chunk in client.chat.stream(
    namespace="my-documents",
    messages=[{"role": "user", "content": "Summarize the document"}],
    model="gpt-3.5-turbo"
):
    content = chunk.get("content", "")
    print(content, end="", flush=True)
print()  # New line at the end
```

#### Structured Output

```python
# Get responses in a specific JSON format
response = client.chat.create(
    namespace="my-documents",
    messages=[{"role": "user", "content": "Extract key information"}],
    model="gpt-4",
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "document_summary",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_points": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["title", "summary", "key_points"]
            }
        }
    }
)
print(response.content)  # Returns a dictionary matching the schema
```

#### Advanced Retrieval Options

```python
from gushwork_rag import RetrievalType

response = client.chat.create(
    namespace="my-documents",
    messages=[{"role": "user", "content": "What are the conclusions?"}],
    model="gpt-3.5-turbo",
    retrieval_type=RetrievalType.GEMINI,  # or RetrievalType.SIMPLE
    top_k=10,  # Number of top results to retrieve
    top_n=5,   # Number of top chunks to return
    top_p=0.9  # Top-p sampling parameter
)
```

### API Key Management (Requires ADMIN Access)

```python
from gushwork_rag import APIAccess

# Create a new API key
api_key = client.auth.create_api_key(
    key_name="production-key",
    access=APIAccess.READ_WRITE
)
print(f"New API Key: {api_key.api_key}")
# Save this key securely!

# List all API keys
keys = client.auth.list_api_keys()
for key in keys:
    print(f"{key.key_name}: {key.access} (Last used: {key.last_used})")

# Delete an API key
client.auth.delete_api_key(api_key_id="key_123")
```

## API Reference

### GushworkRAG

Main client class for interacting with the API.

**Methods:**
- `health_check()` - Check API health
- `close()` - Close the HTTP session
- Properties: `namespaces`, `files`, `chat`, `auth`

### NamespacesClient

Manage document namespaces.

**Methods:**
- `create(name, instructions)` - Create a namespace
- `list()` - List all namespaces
- `get(namespace_id)` - Get a namespace by ID
- `update(namespace_id, instructions)` - Update a namespace
- `delete(namespace_id)` - Delete a namespace

### FilesClient

Manage files and documents.

**Methods:**
- `upload(file_path, namespace, mime_type)` - Upload a file
- `get(file_id)` - Get file details
- `list_by_namespace(namespace, limit, skip)` - List files in a namespace
- `update_status(file_id, status, ...)` - Update file status
- `delete(file_id)` - Delete a file

### ChatClient

Chat completions with RAG.

**Methods:**
- `create(namespace, messages, model, **kwargs)` - Get a chat completion
- `stream(namespace, messages, model, **kwargs)` - Stream a chat completion
- `completions(namespace, messages, model, **kwargs)` - Generic completion method

### AuthClient

Manage API keys (requires ADMIN access).

**Methods:**
- `create_api_key(key_name, access)` - Create a new API key
- `list_api_keys()` - List all API keys
- `delete_api_key(api_key_id)` - Delete an API key

## Models

### Enums

- `FileStatus` - File processing status (UPLOAD_URL_CREATED, UPLOADED, PROCESSING, etc.)
- `APIAccess` - Access levels (ADMIN, READ_WRITE, READ)
- `RetrievalType` - Retrieval types (SIMPLE, GEMINI)

### Data Classes

- `Namespace` - Namespace information
- `File` - File metadata
- `APIKey` - API key information
- `Message` - Chat message
- `ChatCompletionResponse` - Chat response

## Error Handling

```python
from gushwork_rag import (
    GushworkError,
    AuthenticationError,
    NotFoundError,
    BadRequestError,
    ForbiddenError,
    ServerError,
)

try:
    namespace = client.namespaces.create(name="test", instructions="test")
except AuthenticationError:
    print("Invalid API key")
except BadRequestError as e:
    print(f"Bad request: {e.message}")
except NotFoundError:
    print("Resource not found")
except ForbiddenError:
    print("Access forbidden")
except ServerError:
    print("Server error")
except GushworkError as e:
    print(f"API error: {e.message} (status: {e.status_code})")
```

## Access Levels

- **ADMIN** - Can create API keys and manage all resources
- **READ_WRITE** - Can upload, update, and delete files
- **READ** - Can read files and use chat completions

## Supported File Types

- PDF (`.pdf`)
- Text files (`.txt`)
- Markdown (`.md`)
- Word documents (`.doc`, `.docx`)

Max file size: 10MB (configurable on server)

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/gushwork/gw-rag.git
cd gw-rag/sdk/python

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Format code
black gushwork_rag/

# Sort imports
isort gushwork_rag/

# Type checking
mypy gushwork_rag/

# Linting
flake8 gushwork_rag/
```


## Examples

See the [examples](./examples) directory for complete working examples:

- `basic_usage.py` - Basic CRUD operations
- `chat_examples.py` - Various chat completion examples
- `streaming_chat.py` - Streaming responses
- `structured_output.py` - JSON schema responses
- `file_management.py` - File upload and management

## Support

- **Documentation**: [GitHub Repository](https://github.com/gushwork/gw-rag)
- **Issues**: [GitHub Issues](https://github.com/gushwork/gw-rag/issues)
- **Email**: support@gushwork.com

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

### 0.1.0 (2024-01-01)

- Initial release
- Support for namespaces, files, chat completions, and API key management
- Streaming support
- Structured output support
- Full type hints
- Comprehensive error handling

