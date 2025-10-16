# USF P1 Chatbot SDK v2.0.0

[![PyPI version](https://badge.fury.io/py/usf-p1-chatbot-sdk.svg)](https://badge.fury.io/py/usf-p1-chatbot-sdk)
[![Python](https://img.shields.io/pypi/pyversions/usf-p1-chatbot-sdk.svg)](https://pypi.org/project/usf-p1-chatbot-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Python SDK for the **Civie Chatbot API v2.0.0**, providing complete coverage of all 33 API endpoints across 8 categories.

## 🎯 Complete API Coverage

This SDK provides **100% coverage** of all 33 endpoints across 8 categories:

| Category | Endpoints | Description |
|----------|-----------|-------------|
| **Health Check** | 1 | API health monitoring |
| **Chat Operations** | 2 | Conversational & streaming chat |
| **Async Data Ingestion** | 3 | PDF, URL, and mixed document ingestion |
| **Ingestion Status** | 4 | Progress tracking & request management |
| **Log Management** | 8 | Comprehensive logging & analytics |
| **Collection Management** | 3 | Collection CRUD operations |
| **File Operations** | 5 | Database & S3 file management |
| **Patient Management** | 7 | Complete patient lifecycle management |

## ✨ Key Features

- 🔒 **Production Ready**: Bearer token authentication with comprehensive error handling
- 📦 **Easy to Use**: Intuitive API with organized endpoint groups
- 🎯 **Type Hints**: Full type hint support for better IDE integration
- 📝 **Well Documented**: Detailed docstrings and examples for every method
- ⚡ **Async Support**: Streaming responses for real-time chat
- 🔄 **Auto Content-Type**: Automatic multipart/form-data handling for file uploads
- 🚀 **Context Manager**: Automatic resource cleanup with context managers

## Installation

```bash
pip install usf-p1-chatbot-sdk
```

## Quick Start

```python
from usf_p1_chatbot_sdk import CivieClient

# Initialize the client
client = CivieClient(
    api_key="your-bearer-token",
    base_url="https://api-civie.us.inc"
)

# Check API health
health = client.health()
print(health)

# Send a chat message
response = client.chat.send_message(
    messages=[{"user": "What medications am I on?"}],
    collection_id="medical_records",
    patient_user_name="patient_123"
)
print(response["response"])

# Close client when done
client.close()
```

## 📚 Comprehensive Documentation

### 1. Health Check (1 endpoint)

```python
# Basic health check
health = client.health()
print(health["status"])
```

### 2. Chat Operations (2 endpoints)

#### Standard Chat with RAG
```python
response = client.chat.send_message(
    messages=[
        {"user": "What is my latest diagnosis?"},
        {"assistant": "I'll check your records."},
        {"user": "Also, what medications am I currently taking?"}
    ],
    collection_id="col_123",
    patient_user_name="patient_123",
    filter_type="include",  # Optional: "include" or "exclude" 
    uuids=["doc_uuid_1", "doc_uuid_2"],  # Optional: filter specific documents
    ground_truth_chunks=[  # Optional: for evaluation
        {"uuid": "doc1", "layer": "L1", "chunk_id": "C1"}
    ]
)

print(response["response"])
print(f"Generated Query: {response['generated_query']}")
print(f"Response Time: {response['total_response_time_ms']}ms")
```

#### Streaming Chat (SSE)
```python
# Get real-time streaming responses
for chunk in client.chat.send_message_stream(
    messages=[{"user": "Explain my treatment plan in detail"}],
    collection_id="col_123",
    patient_user_name="patient_123"
):
    print(chunk, end='', flush=True)
```

### 3. Async Data Ingestion (3 endpoints)

#### Ingest PDF Files
```python
# Upload PDF files for async processing
# Note: Content-Type is automatically set to multipart/form-data
result = client.ingestion.ingest_pdfs(
    pdf_files=["report1.pdf", "lab_results.pdf"],
    collection_id="col_123",
    patient_user_name="patient_123"
)

print(f"Request ID: {result['request_id']}")
print(f"Estimated Time: {result['estimated_time_minutes']} minutes")
```

#### Ingest URLs
```python
# Ingest documents from URLs
result = client.ingestion.ingest_urls(
    urls=[
        "https://example.com/medical-doc.pdf",
        "https://example.com/guidelines.html"
    ],
    collection_id="col_123",
    patient_user_name="patient_123"
)
```

#### Mixed Ingestion (PDFs + URLs)
```python
# Ingest both PDFs and URLs in single request
result = client.ingestion.ingest_mixed(
    collection_id="col_123",
    patient_user_name="patient_123",
    pdf_files=["local_report.pdf"],
    urls=["https://example.com/remote_doc.pdf"]
)
```

### 4. Ingestion Status (4 endpoints)

```python
# Get ingestion progress
progress = client.ingestion.get_progress("request_id_123")
print(f"Progress: {progress['progress_percentage']}%")
print(f"Status: {progress['status']}")
print(f"Processed: {progress['processed_files']}/{progress['total_files']}")

# List recent ingestion requests
requests = client.ingestion.list_recent_requests(limit=10)

# Get ingestion service status
status = client.ingestion.get_service_status()

# Cancel a pending request
result = client.ingestion.cancel_request("request_id_123")
```

### 5. Log Management (8 endpoints)

```python
# Get all log collections
collections = client.logs.get_collections()

# Get logging statistics
stats = client.logs.get_stats(
    start_date="2025-01-01T00:00:00Z",
    end_date="2025-01-31T23:59:59Z",
    collection_name="logs_chat_interactions"
)

# Get recent logs across all collections
logs = client.logs.get_recent(
    minutes=60,
    level="ERROR",
    limit=100
)

# Get logs from specific collection
logs = client.logs.get_from_collection(
    collection_name="logs_chat_interactions",
    start_date="2025-01-01T00:00:00Z",
    limit=50
)

# Clear logs from collection
result = client.logs.clear_collection(
    collection_name="logs_test",
    confirm=True,
    older_than_days=30
)

# Get recent logs for specific patient
patient_logs = client.logs.get_patient_recent(
    collection_id="col_123",
    patient_user_name="patient_123",
    minutes=120,
    event_type="chat_interaction"
)

# Get patient logs from specific log collection
logs = client.logs.get_patient_from_collection(
    collection_id="col_123",
    patient_user_name="patient_123",
    log_collection_name="logs_chat_interactions",
    level="INFO",
    limit=100
)

# Get logs by collection and log collection
logs = client.logs.get_by_collection_and_log_collection(
    collection_id="col_123",
    log_collection_name="logs_data_ingestion",
    level="ERROR"
)
```

### 6. Collection Management (3 endpoints)

```python
# List all collections
response = client.collections.list()
print(f"Total: {response['total_count']}")
for col in response["collections"]:
    print(f"{col['collection_name']}: {col['document_count']} docs")

# Create new collection
response = client.collections.create(
    collection_name="medical_records_2025",
    description="Patient records for 2025"
)
collection_id = response["collection_info"]["collection_id"]

# Delete collection
result = client.collections.delete("col_123")
```

### 7. File Operations (5 endpoints)

```python
# List all database files
db_files = client.files.list_db_files()

# List database files by collection
files = client.files.list_db_files_by_collection("col_123")

# List all S3 files
s3_files = client.files.list_s3_files()

# List S3 files by collection
files = client.files.list_s3_files_by_collection("col_123")

# Delete document by UUID
result = client.files.delete_document("doc_uuid_123")
```

### 8. Patient Management (7 endpoints)

```python
# Register new patient
response = client.patients.register(
    patient_user_name="john_doe",
    collection_id="col_123",
    patient_id="P12345",  # Optional, auto-generated if not provided
    full_name="John Doe",
    email="john@example.com",
    metadata={"age": 45, "condition": "diabetes"}
)

# Validate patient existence
result = client.patients.validate(
    patient_user_name="john_doe",
    collection_id="col_123"
)

# Get patient information
info = client.patients.get(
    patient_user_name="john_doe",
    collection_id="col_123"
)

# Delete patient and all data
result = client.patients.delete(
    patient_user_name="john_doe",
    collection_id="col_123",
    delete_patient_record=True
)

# List all patients
patients = client.patients.list(limit=50, skip=0)

# List patients by collection
patients = client.patients.list_by_collection(
    collection_id="col_123",
    limit=50
)

# Get patient data summary
summary = client.patients.get_data_summary(
    patient_user_name="john_doe",
    collection_id="col_123"
)
```

## Context Manager Usage

Use context managers for automatic resource cleanup:

```python
from usf_p1_chatbot_sdk import CivieClient

with CivieClient(api_key="your-token") as client:
    response = client.chat.send_message(
        messages=[{"user": "Hello"}],
        collection_id="col_123",
        patient_user_name="patient_123"
    )
    print(response["response"])
# Client automatically closed
```

## Error Handling

```python
from usf_p1_chatbot_sdk import (
    CivieClient,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    CivieAPIError
)

try:
    client = CivieClient(api_key="your-token")
    response = client.chat.send_message(
        messages=[{"user": "Hello"}],
        collection_id="col_123",
        patient_user_name="patient_123"
    )
except AuthenticationError:
    print("Invalid API key")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except NotFoundError:
    print("Resource not found")
except RateLimitError:
    print("Rate limit exceeded")
except ServerError:
    print("Server error")
except CivieAPIError as e:
    print(f"API error: {e.message}")
finally:
    client.close()
```

## Advanced Configuration

```python
# Custom timeout
client = CivieClient(
    api_key="your-token",
    base_url="https://api-civie.us.inc",
    timeout=120  # 120 seconds
)

# Custom base URL for different environments
client = CivieClient(
    api_key="your-token",
    base_url="https://staging-api.example.com"
)
```

## Requirements

- Python 3.8+
- requests >= 2.31.0

## Development

### Install for Development

```bash
git clone https://github.com/ultrasafe/usf-p1-chatbot-sdk.git
cd usf-p1-chatbot-sdk
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v --cov=usf_p1_chatbot_sdk
```

## Building and Publishing

### Build Package

```bash
python -m build
```

### Upload to PyPI

```bash
python -m twine upload dist/*
```

## Complete Endpoint Reference

See [API_ENDPOINTS_ANALYSIS.md](docs/API_ENDPOINTS_ANALYSIS.md) for detailed documentation of all 33 endpoints with:
- HTTP methods and paths
- Input parameters (required/optional)
- Output schemas
- Authentication requirements

## Changelog

### Version 2.0.0 (Current)

- ✨ **Complete Rewrite**: All 33 endpoints across 8 categories
- 🔒 **Enhanced Security**: Improved authentication and error handling
- 📦 **Better Organization**: Endpoints grouped by category
- 🎯 **Type Hints**: Full type hint coverage
- 📝 **Documentation**: Comprehensive docs with examples
- 🔄 **Auto Content-Type**: Automatic multipart/form-data for file uploads
- 🚀 **Production Ready**: Proper parameter validation and error messages
- 📊 **Enhanced Logging**: Complete log management suite (8 endpoints)
- 👥 **Patient Management**: Full patient lifecycle (7 endpoints)
- 📁 **File Operations**: Complete file management (5 endpoints)

### Version 1.x

- Initial release with basic functionality

## License

MIT License - see [LICENSE](LICENSE) file

## Support

- **API Docs**: [https://api-civie.us.inc/docs](https://api-civie.us.inc/docs)
- **Issues**: [GitHub Issues](https://github.com/ultrasafe/usf-p1-chatbot-sdk/issues)
- **PyPI**: [https://pypi.org/project/usf-p1-chatbot-sdk/](https://pypi.org/project/usf-p1-chatbot-sdk/)

## Contributing

Contributions welcome! Please submit Pull Requests.

---

**Developed by USF Team** | [API Documentation](https://api-civie.us.inc/docs)
