"""
Collection management endpoints for the USF P1 Chatbot SDK
"""
from typing import Dict, Any, Optional
from ..base_client import BaseClient


class CollectionsEndpoints:
    """Collection management operations endpoints"""
    
    def __init__(self, client: BaseClient):
        self.client = client
    
    def list(self) -> Dict[str, Any]:
        """
        List all collections with their metadata and document counts
        
        Returns:
            Dict containing:
                - status: Operation status
                - message: Status message
                - collections: List of collection objects
                - total_count: Total number of collections
        
        Example:
            >>> response = client.collections.list()
            >>> for col in response["collections"]:
            ...     print(f"{col['collection_name']}: {col['document_count']} documents")
        """
        return self.client.get("/api/collections")
    
    def create(self, collection_name: str, description: str = "") -> Dict[str, Any]:
        """
        Create a new collection for document storage
        
        Args:
            collection_name: Name of the collection to create
            description: Optional description for the collection (default: "")
        
        Returns:
            Dict containing:
                - status: Operation status
                - message: Status message
                - collection_info: Created collection details
        
        Example:
            >>> response = client.collections.create(
            ...     collection_name="medical_records",
            ...     description="Patient medical records collection"
            ... )
            >>> print(response["collection_info"]["collection_id"])
        """
        payload = {
            "collection_name": collection_name,
            "description": description
        }
        return self.client.post("/api/collections", json_data=payload)
    
    def delete(self, collection_id: str) -> Dict[str, Any]:
        """
        Delete a collection and all its associated data
        
        Args:
            collection_id: Collection ID to delete
        
        Returns:
            Dict with deletion status
        
        Example:
            >>> result = client.collections.delete("col_123")
            >>> print(result["message"])
        """
        return self.client.delete(f"/api/collections/{collection_id}")
