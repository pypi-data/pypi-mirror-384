"""
Data ingestion endpoints for the USF P1 Chatbot SDK
"""
from typing import List, Dict, Any, Optional, BinaryIO, Union
import json
from ..base_client import BaseClient


class IngestionEndpoints:
    """Data ingestion operations endpoints"""
    
    def __init__(self, client: BaseClient):
        self.client = client
    
    def ingest_pdfs(
        self,
        pdf_files: List[Union[str, BinaryIO]],
        collection_id: str,
        patient_user_name: str
    ) -> Dict[str, Any]:
        """
        Async PDF data ingestion with file validation
        
        Args:
            pdf_files: List of PDF file paths or file objects
            collection_id: Collection ID for document storage
            patient_user_name: Patient username
        
        Returns:
            Dict containing:
                - status: Ingestion status (default: "accepted")
                - message: Status message
                - request_id: Request ID for progress tracking
                - estimated_time_minutes: Estimated processing time
                - total_files: Number of files submitted
                - patient_user_name: Patient username
        
        Example:
            >>> response = client.ingestion.ingest_pdfs(
            ...     pdf_files=["file1.pdf", "file2.pdf"],
            ...     collection_id="col_123",
            ...     patient_user_name="patient_123"
            ... )
            >>> print(response["request_id"])
        """
        files = []
        for pdf_file in pdf_files:
            if isinstance(pdf_file, str):
                files.append(('files', open(pdf_file, 'rb')))
            else:
                files.append(('files', pdf_file))
        
        data = {
            'collection_id': collection_id,
            'patient_user_name': patient_user_name
        }
        
        try:
            return self.client.post("/api/data/async/pdfs", files=files, data=data)
        finally:
            # Close any files we opened
            for file_tuple in files:
                if isinstance(pdf_files[files.index(file_tuple)], str):
                    file_tuple[1].close()
    
    def ingest_urls(
        self,
        urls: List[str],
        collection_id: Optional[str] = None,
        patient_user_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Async URL data ingestion with URL validation
        
        Args:
            urls: List of URLs to ingest
            collection_id: Optional collection ID for document storage
            patient_user_name: Optional patient username
        
        Returns:
            Dict containing:
                - status: Ingestion status (default: "accepted")
                - message: Status message
                - request_id: Request ID for progress tracking
                - estimated_time_minutes: Estimated processing time
                - total_files: Number of URLs submitted
                - patient_user_name: Patient username
        
        Example:
            >>> response = client.ingestion.ingest_urls(
            ...     urls=["https://example.com/doc1", "https://example.com/doc2"],
            ...     collection_id="col_123",
            ...     patient_user_name="patient_123"
            ... )
            >>> print(response["request_id"])
        """
        payload = {"urls": urls}
        
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if patient_user_name is not None:
            payload["patient_user_name"] = patient_user_name
        
        return self.client.post("/api/data/async/urls", json_data=payload)
    
    def ingest_mixed(
        self,
        collection_id: str,
        patient_user_name: str,
        pdf_files: Optional[List[Union[str, BinaryIO]]] = None,
        urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Mixed data ingestion (PDFs + URLs)
        
        Args:
            collection_id: Collection ID for document storage
            patient_user_name: Patient username
            pdf_files: Optional list of PDF file paths or file objects
            urls: Optional list of URLs to ingest
        
        Returns:
            Dict containing:
                - status: Ingestion status (default: "accepted")
                - message: Status message
                - request_id: Request ID for progress tracking
                - estimated_time_minutes: Estimated processing time
                - total_files: Total number of files and URLs submitted
                - patient_user_name: Patient username
        
        Example:
            >>> response = client.ingestion.ingest_mixed(
            ...     collection_id="col_123",
            ...     patient_user_name="patient_123",
            ...     pdf_files=["file1.pdf"],
            ...     urls=["https://example.com/doc1"]
            ... )
            >>> print(response["request_id"])
        """
        files = []
        if pdf_files:
            for pdf_file in pdf_files:
                if isinstance(pdf_file, str):
                    files.append(('files', open(pdf_file, 'rb')))
                else:
                    files.append(('files', pdf_file))
        
        data = {
            'collection_id': collection_id,
            'patient_user_name': patient_user_name,
            'urls': json.dumps(urls if urls else [])
        }
        
        try:
            return self.client.post("/api/data/async", files=files if files else None, data=data)
        finally:
            # Close any files we opened
            if pdf_files:
                for idx, file_tuple in enumerate(files):
                    if isinstance(pdf_files[idx], str):
                        file_tuple[1].close()
    
    def get_progress(self, request_id: str) -> Dict[str, Any]:
        """
        Get the current progress of an ingestion request
        
        Args:
            request_id: Request ID from ingestion response
        
        Returns:
            Dict containing:
                - request_id: Request ID
                - status: Current status
                - progress_percentage: Progress percentage (0-100)
                - total_files: Total files to process
                - processed_files: Files processed so far
                - successful_files: Successfully processed files
                - failed_files: Failed files
                - created_at: Request creation time
                - started_at: Processing start time
                - completed_at: Processing completion time
                - estimated_time_remaining_minutes: Estimated time remaining
                - collection_id: Collection ID
                - files: Detailed file information
        
        Example:
            >>> progress = client.ingestion.get_progress("req_123")
            >>> print(f"Progress: {progress['progress_percentage']}%")
        """
        return self.client.get(f"/api/data/progress/{request_id}")
    
    def list_recent_requests(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List recent ingestion requests
        
        Args:
            limit: Maximum number of requests to return (default: 20)
        
        Returns:
            List of recent ingestion request objects
        
        Example:
            >>> requests = client.ingestion.list_recent_requests(limit=10)
            >>> for req in requests:
            ...     print(req["request_id"], req["status"])
        """
        return self.client.get("/api/data/requests", params={"limit": limit})
    
    def get_service_status(self) -> Dict[str, Any]:
        """
        Get the current status of the ingestion service
        
        Returns:
            Dict with service status information
        
        Example:
            >>> status = client.ingestion.get_service_status()
            >>> print(status)
        """
        return self.client.get("/api/data/status")
    
    def cancel_request(self, request_id: str) -> Dict[str, Any]:
        """
        Cancel an ingestion request (only works if pending/queued)
        
        Args:
            request_id: Request ID to cancel
        
        Returns:
            Dict with cancellation status
        
        Example:
            >>> result = client.ingestion.cancel_request("req_123")
            >>> print(result["message"])
        """
        return self.client.delete(f"/api/data/request/{request_id}")
