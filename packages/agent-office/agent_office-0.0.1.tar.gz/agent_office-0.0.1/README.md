# Agent Office Python SDK

Python SDK for the Agent Office API - AI-powered document editing for agentic workflows.

## Installation

```bash
pip install agent-office
```

## Quick Start

```python
from agent_office import AgentOffice
from uuid import uuid4

# Initialize the client
client = AgentOffice(api_key="sk_ao_your_api_key")  # Get your key from https://agentoffice.dev

# Upload a document
doc = client.documents.create(
    file="document.docx",
    return_markdown=True
)
print(f"Uploaded: {doc.doc_id}")

# Edit the document
edit = client.edit(
    doc_id=doc.doc_id,
    edit_uid=str(uuid4()),
    edit_instructions="Change the title to 'My New Title'",
    tracked_changes=False
)
print(f"Edit applied: {edit.edit_applied}")

# Download the edited document
result = client.documents.download(doc_id=doc.doc_id)
print(f"Download URL: {result.download_url}")

# You can then download the file using requests
import requests
response = requests.get(result.download_url)
with open(f"edited_{doc.name}", "wb") as f:
    f.write(response.content)
```

## Features

- 📝 Upload and convert documents (DOCX, PDF, etc.)
- ✏️ AI-powered document editing
- 📖 Read document content as Markdown
- 💾 Download edited documents
- 🔄 Track changes support

## API Reference

### Client Initialization

```python
client = AgentOffice(
    api_key="sk_ao_your_api_key",  # Required: Your API key
    base_url="https://api.agentoffice.dev",  # Optional: API base URL
    timeout=60  # Optional: Request timeout in seconds
)
```

### Documents

#### Create Document

```python
doc = client.documents.create(
    file="path/to/document.docx",  # File path or file-like object
    return_markdown=True,  # Return markdown content
    ttl_seconds=3600  # Time to live in seconds (300-21600)
)
```

#### Create Document from URL

```python
doc = client.documents.create_from_url(
    file_url="https://example.com/document.docx",
    ttl_seconds=3600
)
```

#### Download Document

```python
result = client.documents.download(
    doc_id="doc-id",
    expires_in=3600  # Presigned URL expiration in seconds
)
print(result.download_url)
```

#### Check Document Exists

```python
result = client.documents.exists(doc_id="doc-id")
if result.exists:
    print(f"Document exists: {result.document.name}")
```

### Edit Document

```python
edit = client.edit(
    doc_id="doc-id",
    edit_uid=str(uuid4()),  # Unique identifier for the edit
    edit_instructions="Change the title to 'My New Title'",  # Natural language instructions
    lookup_text="Section 1",  # Optional: Text to locate edit position
    tracked_changes=False,  # Enable track changes
    use_large_model=False  # Use larger AI model
)
```

### Read Document

```python
result = client.read(doc_id="doc-id")
print(result.markdown)
```

## Error Handling

The SDK provides specific exception types for different error conditions:

```python
from agent_office import (
    AgentOffice,
    AgentOfficeError,
    AuthenticationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
)

client = AgentOffice(api_key="sk_ao_your_api_key")

try:
    doc = client.documents.create("document.docx")
except AuthenticationError:
    print("Invalid API key")
except NotFoundError:
    print("Document not found")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except RateLimitError:
    print("Rate limit exceeded")
except ServerError:
    print("Server error")
except AgentOfficeError as e:
    print(f"General error: {e.message}")
```

## Development

### Install from source

```bash
git clone https://github.com/agentoffice/python-sdk.git
cd python-sdk
pip install -e .
```

### Install development dependencies

```bash
pip install -e ".[dev]"
```

## License

MIT

## Support

- Website: https://agentoffice.dev
- Documentation: https://docs.agentoffice.dev
- Email: support@agentoffice.dev
