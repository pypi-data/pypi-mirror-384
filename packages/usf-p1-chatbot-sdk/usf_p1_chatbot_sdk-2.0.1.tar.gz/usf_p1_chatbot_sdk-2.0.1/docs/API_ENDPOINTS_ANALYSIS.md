# Civie Chatbot API - Complete Endpoint Analysis
## Total Endpoints: 33

This document provides a comprehensive analysis of all 33 API endpoints with their:
- HTTP Method and Path
- Input Parameters (Path, Query, Body)
- Output Schema
- Authentication Requirements

---

## 1. Health Check (1 endpoint)

### 1.1 GET /health
**Description:** Basic health check endpoint  
**Authentication:** Not Required  
**Input Parameters:** None  
**Output:** JSON object  

---

## 2. Chat Operations (2 endpoints)

### 2.1 POST /api/chat
**Description:** Conversational chat endpoint with RAG capabilities  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (JSON):**
  - `messages` (array, required): List of conversation messages
    - Format 1: `{"role": "user/assistant/system", "content": "..."}`
    - Format 2: `{"user": "...", "assistant": "..."}`
  - `filter_type` (string, optional): "include" or "exclude"
  - `uuids` (array of strings, optional): Document UUIDs to filter
  - `collection_id` (string, optional): Collection ID to restrict retrieval
  - `patient_user_name` (string, optional): Patient username for filtering
  - `ground_truth_chunks` (array, optional): Ground truth chunks for evaluation
    - Each chunk: `{"uuid": "...", "layer": "...", "chunk_id": "..."}`

**Output Schema (ConversationalChatResponse):**
```json
{
  "response": "string",
  "generated_query": "string",
  "retrieved_context": {
    "main_context": "string (XML formatted)",
    "summarized_context": "string (XML formatted)",
    "main_docs": [array of ContextDocument],
    "summary_docs": [array of ContextDocument],
    "total_docs_retrieved": "integer",
    "reranking_applied": "boolean",
    "evaluation_metrics": {
      "precision": "number",
      "recall": "number",
      "retrieved_chunks_count": "integer",
      "ground_truth_chunks_count": "integer",
      "matched_chunks_count": "integer"
    }
  },
  "total_response_time_ms": "number"
}
```

### 2.2 POST /api/chat/stream
**Description:** Streaming conversational chat endpoint with Server-Sent Events (SSE)  
**Authentication:** Required (Bearer Token)  
**Input Parameters:** Same as /api/chat  
**Output:** StreamingResponse (SSE format)  

---

## 3. Async Data Ingestion (3 endpoints)

### 3.1 POST /api/data/async/pdfs
**Description:** Async PDF data ingestion with file validation  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (multipart/form-data):**
  - `files` (array of binary, optional): PDF files (default: [])
  - `collection_id` (string, required): Collection ID
  - `patient_user_name` (string, required): Patient username

**Output Schema (AsyncIngestionResponse):**
```json
{
  "status": "string (default: 'accepted')",
  "message": "string",
  "request_id": "string",
  "estimated_time_minutes": "number or null",
  "total_files": "integer",
  "patient_user_name": "string or null"
}
```

### 3.2 POST /api/data/async/urls
**Description:** Async URL data ingestion with URL validation  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (JSON):**
  - `urls` (array of strings, optional): URLs to ingest (default: [])
  - `collection_id` (string, optional): Collection ID
  - `patient_user_name` (string, optional): Patient username

**Output Schema:** Same as AsyncIngestionResponse

### 3.3 POST /api/data/async
**Description:** Mixed data ingestion (PDFs + URLs)  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (multipart/form-data):**
  - `urls` (string, optional): JSON string of URLs (default: "[]")
  - `collection_id` (string, required): Collection ID
  - `patient_user_name` (string, required): Patient username
  - `files` (array of binary, optional): PDF files

**Output Schema:** Same as AsyncIngestionResponse

---

## 4. Ingestion Status APIs (4 endpoints)

### 4.1 GET /api/data/progress/{request_id}
**Description:** Get ingestion request progress  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `request_id` (string, required): Request ID

**Output Schema (ProgressResponse):**
```json
{
  "request_id": "string",
  "status": "string",
  "progress_percentage": "number",
  "total_files": "integer",
  "processed_files": "integer",
  "successful_files": "integer",
  "failed_files": "integer",
  "created_at": "string or null",
  "started_at": "string or null",
  "completed_at": "string or null",
  "estimated_time_remaining_minutes": "number or null",
  "collection_id": "string or null",
  "files": [array of objects]
}
```

### 4.2 GET /api/data/requests
**Description:** List recent ingestion requests  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Query:**
  - `limit` (integer, optional): Max requests to return (default: 20)

**Output:** Array of objects

### 4.3 GET /api/data/status
**Description:** Get ingestion service status  
**Authentication:** Required (Bearer Token)  
**Input Parameters:** None  
**Output:** Object with service status

### 4.4 DELETE /api/data/request/{request_id}
**Description:** Cancel an ingestion request  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `request_id` (string, required): Request ID

**Output:** Object with cancellation status

---

## 5. Log APIs (8 endpoints)

### 5.1 GET /api/logs/collections
**Description:** Get all available log collections  
**Authentication:** Required (Bearer Token)  
**Input Parameters:** None  
**Output:** Object with log collections

### 5.2 GET /api/logs/stats
**Description:** Get logging statistics  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Query:**
  - `start_date` (string, optional): Start date (ISO format)
  - `end_date` (string, optional): End date (ISO format)
  - `collection_name` (string, optional): Specific collection

**Output:** Object with statistics

### 5.3 GET /api/logs/recent
**Description:** Get recent logs across all collections  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Query:**
  - `minutes` (integer, optional): Minutes to look back (default: 60, max: 1440)
  - `level` (string, optional): Filter by log level
  - `collection` (string, optional): Filter by collection
  - `limit` (integer, optional): Number of logs (default: 50, max: 500)

**Output:** Object with logs

### 5.4 GET /api/logs/{collection_name}
**Description:** Get logs from specific collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_name` (string, required): Collection name
- **Query:**
  - `start_date` (string, optional): Start date (ISO format)
  - `end_date` (string, optional): End date (ISO format)
  - `limit` (integer, optional): Number of logs (default: 100, max: 1000)
  - `offset` (integer, optional): Skip logs (default: 0)

**Output:** Object with logs

### 5.5 DELETE /api/logs/{collection_name}
**Description:** Clear logs from collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_name` (string, required): Collection name
- **Query:**
  - `confirm` (boolean, optional): Confirm deletion (default: false)
  - `older_than_days` (integer, optional): Only delete logs older than N days

**Output:** Object with deletion status

### 5.6 GET /api/logs/patient-recent/{collection_id}/{patient_user_name}
**Description:** Get recent logs for specific patient  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID
  - `patient_user_name` (string, required): Patient username
- **Query:**
  - `minutes` (integer, optional): Minutes to look back (default: 60, max: 1440)
  - `level` (string, optional): Filter by log level
  - `event_type` (string, optional): Filter by event type
  - `limit` (integer, optional): Number of logs (default: 100, max: 500)

**Output:** Object with patient logs

### 5.7 GET /api/logs/patient-from-collection/{collection_id}/{patient_user_name}/{log_collection_name}
**Description:** Get patient logs from specific log collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID
  - `patient_user_name` (string, required): Patient username
  - `log_collection_name` (string, required): Log collection name
- **Query:**
  - `start_date` (string, optional): Start date (ISO format)
  - `end_date` (string, optional): End date (ISO format)
  - `level` (string, optional): Filter by log level
  - `event_type` (string, optional): Filter by event type
  - `limit` (integer, optional): Number of logs (default: 100, max: 1000)
  - `offset` (integer, optional): Skip logs (default: 0)

**Output:** Object with patient logs

### 5.8 GET /api/logs/collection-specific/{collection_id}/{log_collection_name}
**Description:** Get logs by collection and log collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID
  - `log_collection_name` (string, required): Log collection name
- **Query:**
  - `start_date` (string, optional): Start date (ISO format)
  - `end_date` (string, optional): End date (ISO format)
  - `level` (string, optional): Filter by log level
  - `event_type` (string, optional): Filter by event type
  - `limit` (integer, optional): Number of logs (default: 100, max: 1000)
  - `offset` (integer, optional): Skip logs (default: 0)

**Output:** Object with logs

---

## 6. Collection Management (3 endpoints)

### 6.1 GET /api/collections
**Description:** List all collections  
**Authentication:** Required (Bearer Token)  
**Input Parameters:** None  
**Output Schema (ListCollectionsResponse):**
```json
{
  "status": "string",
  "message": "string",
  "collections": [
    {
      "collection_id": "string",
      "collection_name": "string",
      "description": "string",
      "created_at": "datetime",
      "chunk_count": "integer or null",
      "document_count": "integer",
      "qdrant_collection_name": "string",
      "document_uuids": ["array of strings"]
    }
  ],
  "total_count": "integer"
}
```

### 6.2 POST /api/collections
**Description:** Create new collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (JSON):**
  - `collection_name` (string, required): Collection name
  - `description` (string, optional): Collection description (default: "")

**Output Schema (CollectionResponse):**
```json
{
  "status": "string",
  "message": "string",
  "collection_info": {
    "collection_id": "string",
    "collection_name": "string",
    "description": "string",
    "created_at": "datetime",
    "chunk_count": "integer or null",
    "document_count": "integer",
    "qdrant_collection_name": "string",
    "document_uuids": ["array of strings"]
  }
}
```

### 6.3 DELETE /api/collections/{collection_id}
**Description:** Delete collection and all data  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID

**Output:** Object with deletion status

---

## 7. File Operations (6 endpoints)

### 7.1 GET /api/db/files
**Description:** List all files in database  
**Authentication:** Required (Bearer Token)  
**Input Parameters:** None  
**Output:** Array of file objects

### 7.2 GET /api/db/files/{collection_id}
**Description:** List database files by collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID

**Output:** Array of file objects

### 7.3 GET /api/s3/files
**Description:** List all files in S3  
**Authentication:** Required (Bearer Token)  
**Input Parameters:** None  
**Output:** Object with S3 files

### 7.4 GET /api/s3/files/{collection_id}
**Description:** List S3 files by collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID

**Output:** Object with S3 files

### 7.5 DELETE /api/document/{document_uuid}
**Description:** Delete document by UUID  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `document_uuid` (string, required): Document UUID

**Output:** Object with deletion status

---

## 8. Patient Management (9 endpoints)

### 8.1 POST /api/patient/register
**Description:** Register new patient  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (JSON):**
  - `patient_user_name` (string, required): Unique username (3-50 chars, alphanumeric + underscore)
  - `collection_id` (string, required): Collection ID
  - `patient_id` (string, optional): Patient ID (auto-generated if not provided)
  - `full_name` (string, optional): Full name (max 100 chars)
  - `email` (string, optional): Email address
  - `metadata` (object, optional): Additional metadata

**Output Schema (PatientRegistrationResponse):**
```json
{
  "status": "string",
  "message": "string",
  "patient_user_name": "string",
  "patient_id": "string",
  "created_at": "datetime"
}
```

### 8.2 POST /api/patient/validate
**Description:** Validate if patient exists  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Body (JSON):**
  - `patient_user_name` (string, required): Username (3-50 chars)
  - `collection_id` (string, required): Collection ID

**Output Schema (PatientValidationResponse):**
```json
{
  "exists": "boolean",
  "patient_user_name": "string",
  "patient_id": "string or null",
  "message": "string"
}
```

### 8.3 GET /api/patient/{patient_user_name}
**Description:** Get patient information  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `patient_user_name` (string, required): Patient username
- **Query:**
  - `collection_id` (string, required): Collection ID

**Output Schema (PatientInfoResponse):**
```json
{
  "patient_user_name": "string",
  "patient_id": "string",
  "full_name": "string or null",
  "email": "string or null",
  "created_at": "datetime",
  "updated_at": "datetime or null",
  "data_count": "integer (default: 0)",
  "metadata": "object or null"
}
```

### 8.4 DELETE /api/patient/{patient_user_name}
**Description:** Delete patient and all associated data  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `patient_user_name` (string, required): Patient username
- **Query:**
  - `collection_id` (string, required): Collection ID
  - `delete_patient_record` (boolean, optional): Delete patient record (default: true)

**Output:** Object with deletion status

### 8.5 GET /api/patients
**Description:** List all patients  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Query:**
  - `limit` (integer, optional): Max patients (default: 50, max: 100)
  - `skip` (integer, optional): Skip patients (default: 0)

**Output:** Array of patient objects

### 8.6 GET /api/patients/collection/{collection_id}
**Description:** List patients by collection  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `collection_id` (string, required): Collection ID
- **Query:**
  - `limit` (integer, optional): Max patients (default: 50, max: 100)
  - `skip` (integer, optional): Skip patients (default: 0)

**Output:** Array of patient objects

### 8.7 GET /api/patient/{patient_user_name}/data
**Description:** Get patient data summary  
**Authentication:** Required (Bearer Token)  
**Input Parameters:**
- **Path:**
  - `patient_user_name` (string, required): Patient username
- **Query:**
  - `collection_id` (string, required): Collection ID

**Output:** Object with patient data summary

---

## Summary

**Total Endpoints: 33**
- Health Check: 1
- Chat Operations: 2
- Async Data Ingestion: 3
- Ingestion Status: 4
- Log APIs: 8
- Collection Management: 3
- File Operations: 6
- Patient Management: 9

**Authentication:**
- 32 endpoints require Bearer Token authentication
- 1 endpoint (/health) does not require authentication

**HTTP Methods:**
- GET: 22 endpoints
- POST: 7 endpoints
- DELETE: 4 endpoints
