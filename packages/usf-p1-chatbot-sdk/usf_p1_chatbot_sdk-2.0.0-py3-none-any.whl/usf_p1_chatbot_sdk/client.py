"""
Main client for the USF P1 Chatbot SDK
"""
from typing import Dict, Any
from .base_client import BaseClient
from .endpoints import (
    ChatEndpoints,
    IngestionEndpoints,
    LogsEndpoints,
    CollectionsEndpoints,
    FilesEndpoints,
    PatientsEndpoints
)


class CivieClient:
    """
    Main client for interacting with the Civie Chatbot API
    
    This client provides access to all API endpoints through organized endpoint groups:
    - chat: Chat operations (conversational and streaming)
    - ingestion: Document ingestion (PDFs, URLs, mixed)
    - logs: Log management and retrieval
    - collections: Collection management
    - files: File operations
    - patients: Patient management
    
    Example:
        >>> from usf_p1_chatbot_sdk import CivieClient
        >>> client = CivieClient(
        ...     api_key="your-api-key",
        ...     base_url="https://api-civie.us.inc"
        ... )
        >>> 
        >>> # Check health
        >>> health = client.health()
        >>> print(health)
        >>> 
        >>> # Send a chat message
        >>> response = client.chat.send_message(
        ...     messages=[{"user": "Hello!"}],
        ...     collection_id="col_123",
        ...     patient_user_name="patient_123"
        ... )
        >>> print(response["response"])
        >>> 
        >>> # Ingest documents
        >>> result = client.ingestion.ingest_pdfs(
        ...     pdf_files=["document.pdf"],
        ...     collection_id="col_123",
        ...     patient_user_name="patient_123"
        ... )
        >>> print(result["request_id"])
        >>> 
        >>> # List collections
        >>> collections = client.collections.list()
        >>> print(collections["total_count"])
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api-civie.us.inc",
        timeout: int = 60
    ):
        """
        Initialize the Civie API client
        
        Args:
            api_key: Bearer token for authentication
            base_url: Base URL for the API (default: https://api-civie.us.inc)
            timeout: Request timeout in seconds (default: 60)
        
        Example:
            >>> client = CivieClient(api_key="your-token")
            >>> # Or with custom base URL
            >>> client = CivieClient(
            ...     api_key="your-token",
            ...     base_url="https://custom-api.example.com",
            ...     timeout=120
            ... )
        """
        self._base_client = BaseClient(api_key, base_url, timeout)
        
        # Initialize endpoint groups
        self.chat = ChatEndpoints(self._base_client)
        self.ingestion = IngestionEndpoints(self._base_client)
        self.logs = LogsEndpoints(self._base_client)
        self.collections = CollectionsEndpoints(self._base_client)
        self.files = FilesEndpoints(self._base_client)
        self.patients = PatientsEndpoints(self._base_client)
    
    def health(self) -> Dict[str, Any]:
        """
        Basic health check endpoint
        
        Returns:
            Dict with health status
        
        Example:
            >>> health = client.health()
            >>> print(health["status"])
        """
        # Health endpoint doesn't require authentication
        session = self._base_client.session
        response = session.get(
            f"{self._base_client.base_url}/health",
            timeout=self._base_client.timeout
        )
        if response.content:
            return response.json()
        return {"status": "ok"}
    
    def close(self):
        """
        Close the client session
        
        Example:
            >>> client.close()
        """
        self._base_client.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __repr__(self):
        return f"CivieClient(base_url='{self._base_client.base_url}')"
