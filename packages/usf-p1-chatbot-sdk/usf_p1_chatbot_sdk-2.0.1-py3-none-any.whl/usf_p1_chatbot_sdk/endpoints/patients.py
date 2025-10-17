"""
Patient management endpoints for the USF P1 Chatbot SDK
"""
from typing import Dict, Any, Optional, List
from ..base_client import BaseClient


class PatientsEndpoints:
    """Patient management operations endpoints"""
    
    def __init__(self, client: BaseClient):
        self.client = client
    
    def register(
        self,
        patient_user_name: str,
        collection_id: str,
        patient_id: Optional[str] = None,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Register a new patient
        
        Args:
            patient_user_name: Unique username (3-50 chars, alphanumeric + underscore)
            collection_id: Collection ID to register patient in
            patient_id: Optional patient ID (auto-generated if not provided)
            full_name: Optional full name (max 100 chars)
            email: Optional email address
            metadata: Optional additional metadata
        
        Returns:
            Dict containing:
                - status: Registration status
                - message: Status message
                - patient_user_name: Registered patient username
                - patient_id: Generated or provided patient ID
                - created_at: Registration timestamp
        
        Example:
            >>> response = client.patients.register(
            ...     patient_user_name="john_doe",
            ...     collection_id="col_123",
            ...     full_name="John Doe",
            ...     email="john@example.com"
            ... )
            >>> print(response["patient_id"])
        """
        payload = {
            "patient_user_name": patient_user_name,
            "collection_id": collection_id
        }
        
        if patient_id is not None:
            payload["patient_id"] = patient_id
        if full_name is not None:
            payload["full_name"] = full_name
        if email is not None:
            payload["email"] = email
        if metadata is not None:
            payload["metadata"] = metadata
        
        return self.client.post("/api/patient/register", json_data=payload)
    
    def validate(self, patient_user_name: str, collection_id: str) -> Dict[str, Any]:
        """
        Validate if a patient exists
        
        Args:
            patient_user_name: Patient username (3-50 chars)
            collection_id: Collection ID to validate patient in
        
        Returns:
            Dict containing:
                - exists: Whether patient exists
                - patient_user_name: Validated patient username
                - patient_id: Patient ID if exists (null otherwise)
                - message: Validation message
        
        Example:
            >>> response = client.patients.validate(
            ...     patient_user_name="john_doe",
            ...     collection_id="col_123"
            ... )
            >>> if response["exists"]:
            ...     print(f"Patient ID: {response['patient_id']}")
        """
        payload = {
            "patient_user_name": patient_user_name,
            "collection_id": collection_id
        }
        return self.client.post("/api/patient/validate", json_data=payload)
    
    def get(self, patient_user_name: str, collection_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a patient
        
        Args:
            patient_user_name: Patient username
            collection_id: Collection ID where patient is registered
        
        Returns:
            Dict containing:
                - patient_user_name: Patient username
                - patient_id: Patient ID
                - full_name: Full name (if available)
                - email: Email (if available)
                - created_at: Registration timestamp
                - updated_at: Last update timestamp
                - data_count: Number of data entries
                - metadata: Patient metadata
        
        Example:
            >>> info = client.patients.get(
            ...     patient_user_name="john_doe",
            ...     collection_id="col_123"
            ... )
            >>> print(f"{info['full_name']}: {info['data_count']} records")
        """
        return self.client.get(
            f"/api/patient/{patient_user_name}",
            params={"collection_id": collection_id}
        )
    
    def delete(
        self,
        patient_user_name: str,
        collection_id: str,
        delete_patient_record: bool = True
    ) -> Dict[str, Any]:
        """
        Delete a patient and all their associated data
        
        Args:
            patient_user_name: Patient username
            collection_id: Collection ID where patient is registered
            delete_patient_record: Whether to delete patient record (default: True)
        
        Returns:
            Dict with deletion status including:
                - Documents deleted from MongoDB, Qdrant, and S3
                - Collections affected
                - Patient record deletion status
        
        Example:
            >>> result = client.patients.delete(
            ...     patient_user_name="john_doe",
            ...     collection_id="col_123",
            ...     delete_patient_record=True
            ... )
            >>> print(result["message"])
        """
        return self.client.delete(
            f"/api/patient/{patient_user_name}",
            params={
                "collection_id": collection_id,
                "delete_patient_record": delete_patient_record
            }
        )
    
    def list(self, limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
        """
        List all patients with basic information
        
        Args:
            limit: Maximum number of patients to return (default: 50, max: 100)
            skip: Number of patients to skip for pagination (default: 0)
        
        Returns:
            List of patient objects
        
        Example:
            >>> patients = client.patients.list(limit=20)
            >>> for patient in patients:
            ...     print(f"{patient['patient_user_name']}: {patient['patient_id']}")
        """
        return self.client.get(
            "/api/patients",
            params={"limit": limit, "skip": skip}
        )
    
    def list_by_collection(
        self,
        collection_id: str,
        limit: int = 50,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List all patients within a specific collection
        
        Args:
            collection_id: Collection ID to list patients from
            limit: Maximum number of patients to return (default: 50, max: 100)
            skip: Number of patients to skip for pagination (default: 0)
        
        Returns:
            List of patient objects with data counts
        
        Example:
            >>> patients = client.patients.list_by_collection(
            ...     collection_id="col_123",
            ...     limit=20
            ... )
            >>> for patient in patients:
            ...     print(f"{patient['patient_user_name']}: {patient['data_count']} records")
        """
        return self.client.get(
            f"/api/patients/collection/{collection_id}",
            params={"limit": limit, "skip": skip}
        )
    
    def get_data_summary(self, patient_user_name: str, collection_id: str) -> Dict[str, Any]:
        """
        Get a summary of data entries for a specific patient
        
        Args:
            patient_user_name: Patient username
            collection_id: Collection ID where patient is registered
        
        Returns:
            Dict with patient data summary and statistics
        
        Example:
            >>> summary = client.patients.get_data_summary(
            ...     patient_user_name="john_doe",
            ...     collection_id="col_123"
            ... )
            >>> print(f"Total data entries: {summary['total_entries']}")
        """
        return self.client.get(
            f"/api/patient/{patient_user_name}/data",
            params={"collection_id": collection_id}
        )
