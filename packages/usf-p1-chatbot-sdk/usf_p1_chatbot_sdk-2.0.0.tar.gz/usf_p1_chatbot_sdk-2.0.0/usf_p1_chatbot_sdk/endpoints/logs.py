"""
Log management endpoints for the USF P1 Chatbot SDK
"""
from typing import Dict, Any, Optional, List
from ..base_client import BaseClient


class LogsEndpoints:
    """Log management operations endpoints"""
    
    def __init__(self, client: BaseClient):
        self.client = client
    
    def get_collections(self) -> Dict[str, Any]:
        """
        Get all available log collections
        
        Returns:
            Dict with available log collections
        
        Example:
            >>> collections = client.logs.get_collections()
            >>> print(collections)
        """
        return self.client.get("/api/logs/collections")
    
    def get_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get logging statistics across collections
        
        Args:
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            collection_name: Optional specific collection name
        
        Returns:
            Dict with logging statistics
        
        Example:
            >>> stats = client.logs.get_stats(
            ...     start_date="2025-01-01T00:00:00Z",
            ...     collection_name="logs_chat_interactions"
            ... )
            >>> print(stats)
        """
        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if collection_name:
            params["collection_name"] = collection_name
        
        return self.client.get("/api/logs/stats", params=params if params else None)
    
    def get_recent(
        self,
        minutes: int = 60,
        level: Optional[str] = None,
        collection: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get recent logs across all collections
        
        Args:
            minutes: Minutes to look back (default: 60, max: 1440)
            level: Optional filter by log level
            collection: Optional filter by collection
            limit: Number of logs to return (default: 50, max: 500)
        
        Returns:
            Dict with recent logs
        
        Example:
            >>> logs = client.logs.get_recent(minutes=30, level="ERROR", limit=100)
            >>> print(f"Found {len(logs['logs'])} error logs")
        """
        params = {
            "minutes": minutes,
            "limit": limit
        }
        if level:
            params["level"] = level
        if collection:
            params["collection"] = collection
        
        return self.client.get("/api/logs/recent", params=params)
    
    def get_from_collection(
        self,
        collection_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get logs from a specific collection with filtering
        
        Args:
            collection_name: Name of the log collection
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            limit: Number of logs to return (default: 100, max: 1000)
            offset: Number of logs to skip (default: 0)
        
        Returns:
            Dict with logs from the specified collection
        
        Example:
            >>> logs = client.logs.get_from_collection(
            ...     collection_name="logs_chat_interactions",
            ...     limit=50
            ... )
            >>> print(logs)
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        return self.client.get(f"/api/logs/{collection_name}", params=params)
    
    def clear_collection(
        self,
        collection_name: str,
        confirm: bool = False,
        older_than_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clear logs from a specific collection
        
        Args:
            collection_name: Name of the log collection
            confirm: Set to True to confirm deletion (default: False)
            older_than_days: Optional - only delete logs older than N days
        
        Returns:
            Dict with deletion status
        
        Example:
            >>> result = client.logs.clear_collection(
            ...     collection_name="logs_test",
            ...     confirm=True,
            ...     older_than_days=30
            ... )
            >>> print(result["message"])
        """
        params = {"confirm": confirm}
        if older_than_days is not None:
            params["older_than_days"] = older_than_days
        
        return self.client.delete(f"/api/logs/{collection_name}", params=params)
    
    def get_patient_recent(
        self,
        collection_id: str,
        patient_user_name: str,
        minutes: int = 60,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get recent logs for a specific patient
        
        Args:
            collection_id: Collection ID
            patient_user_name: Patient username
            minutes: Minutes to look back (default: 60, max: 1440)
            level: Optional filter by log level
            event_type: Optional filter by event type
            limit: Number of logs to return (default: 100, max: 500)
        
        Returns:
            Dict with patient logs
        
        Example:
            >>> logs = client.logs.get_patient_recent(
            ...     collection_id="col_123",
            ...     patient_user_name="patient_123",
            ...     minutes=120
            ... )
            >>> print(logs)
        """
        params = {
            "minutes": minutes,
            "limit": limit
        }
        if level:
            params["level"] = level
        if event_type:
            params["event_type"] = event_type
        
        return self.client.get(
            f"/api/logs/patient-recent/{collection_id}/{patient_user_name}",
            params=params
        )
    
    def get_patient_from_collection(
        self,
        collection_id: str,
        patient_user_name: str,
        log_collection_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get patient logs from a specific log collection
        
        Args:
            collection_id: Collection ID
            patient_user_name: Patient username
            log_collection_name: Log collection name
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            level: Optional filter by log level
            event_type: Optional filter by event type
            limit: Number of logs to return (default: 100, max: 1000)
            offset: Number of logs to skip (default: 0)
        
        Returns:
            Dict with patient logs from specific collection
        
        Example:
            >>> logs = client.logs.get_patient_from_collection(
            ...     collection_id="col_123",
            ...     patient_user_name="patient_123",
            ...     log_collection_name="logs_chat_interactions"
            ... )
            >>> print(logs)
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if level:
            params["level"] = level
        if event_type:
            params["event_type"] = event_type
        
        return self.client.get(
            f"/api/logs/patient-from-collection/{collection_id}/{patient_user_name}/{log_collection_name}",
            params=params
        )
    
    def get_by_collection_and_log_collection(
        self,
        collection_id: str,
        log_collection_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        level: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get logs by collection and log collection
        
        Args:
            collection_id: Collection ID
            log_collection_name: Log collection name
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)
            level: Optional filter by log level
            event_type: Optional filter by event type
            limit: Number of logs to return (default: 100, max: 1000)
            offset: Number of logs to skip (default: 0)
        
        Returns:
            Dict with logs for specified collection and log collection
        
        Example:
            >>> logs = client.logs.get_by_collection_and_log_collection(
            ...     collection_id="col_123",
            ...     log_collection_name="logs_data_ingestion",
            ...     level="ERROR"
            ... )
            >>> print(logs)
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if level:
            params["level"] = level
        if event_type:
            params["event_type"] = event_type
        
        return self.client.get(
            f"/api/logs/collection-specific/{collection_id}/{log_collection_name}",
            params=params
        )
