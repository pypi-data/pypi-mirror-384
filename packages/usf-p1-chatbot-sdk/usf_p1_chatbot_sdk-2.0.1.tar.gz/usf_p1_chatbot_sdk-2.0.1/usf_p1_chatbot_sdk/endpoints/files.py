"""
File operations endpoints for the USF P1 Chatbot SDK
"""
from typing import Dict, Any, List
from ..base_client import BaseClient


class FilesEndpoints:
    """File operations endpoints"""
    
    def __init__(self, client: BaseClient):
        self.client = client
    
    def list_db_files(self) -> List[Dict[str, str]]:
        """
        List all files in database
        
        Returns:
            List of file objects from database
        
        Example:
            >>> files = client.files.list_db_files()
            >>> for file in files:
            ...     print(f"{file['name']}: {file['uuid']}")
        """
        return self.client.get("/api/db/files")
    
    def list_db_files_by_collection(self, collection_id: str) -> List[Dict[str, str]]:
        """
        List database files by collection
        
        Args:
            collection_id: Collection ID to filter files
        
        Returns:
            List of file objects from database for the specified collection
        
        Example:
            >>> files = client.files.list_db_files_by_collection("col_123")
            >>> print(f"Found {len(files)} files")
        """
        return self.client.get(f"/api/db/files/{collection_id}")
    
    def list_s3_files(self) -> Dict[str, Any]:
        """
        List all files in S3
        
        Returns:
            Dict with S3 files information
        
        Example:
            >>> files = client.files.list_s3_files()
            >>> print(files)
        """
        return self.client.get("/api/s3/files")
    
    def list_s3_files_by_collection(self, collection_id: str) -> Dict[str, Any]:
        """
        List S3 files by collection
        
        Args:
            collection_id: Collection ID to filter files
        
        Returns:
            Dict with S3 files for the specified collection
        
        Example:
            >>> files = client.files.list_s3_files_by_collection("col_123")
            >>> print(files)
        """
        return self.client.get(f"/api/s3/files/{collection_id}")
    
    def delete_document(self, document_uuid: str) -> Dict[str, Any]:
        """
        Delete document by UUID
        
        Args:
            document_uuid: UUID of the document to delete
        
        Returns:
            Dict with deletion status
        
        Example:
            >>> result = client.files.delete_document("uuid_123")
            >>> print(result["message"])
        """
        return self.client.delete(f"/api/document/{document_uuid}")
