"""
Chat endpoints for the USF P1 Chatbot SDK
"""
from typing import List, Dict, Any, Optional, Iterator
from ..base_client import BaseClient


class ChatEndpoints:
    """Chat operations endpoints"""
    
    def __init__(self, client: BaseClient):
        self.client = client
    
    def send_message(
        self,
        messages: List[Dict[str, str]],
        collection_id: Optional[str] = None,
        patient_user_name: Optional[str] = None,
        filter_type: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        ground_truth_chunks: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Send a conversational chat message
        
        Args:
            messages: List of conversation messages
                Format 1: [{"role": "user/assistant/system", "content": "..."}]
                Format 2: [{"user": "...", "assistant": "..."}]
            collection_id: Optional collection ID to restrict retrieval
            patient_user_name: Optional patient username for filtering
            filter_type: Optional filter type ("include" or "exclude")
            uuids: Optional list of document UUIDs to filter
            ground_truth_chunks: Optional ground truth chunks for evaluation
                Each chunk: {"uuid": "...", "layer": "...", "chunk_id": "..."}
        
        Returns:
            Dict containing:
                - response: The generated response
                - generated_query: The query generated from conversation context
                - retrieved_context: Full context retrieved from Qdrant
                - total_response_time_ms: Total response time in milliseconds
        
        Example:
            >>> response = client.chat.send_message(
            ...     messages=[{"user": "What is my diagnosis?"}],
            ...     collection_id="col_123",
            ...     patient_user_name="patient_123"
            ... )
            >>> print(response["response"])
        """
        payload = {"messages": messages}
        
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if patient_user_name is not None:
            payload["patient_user_name"] = patient_user_name
        if filter_type is not None:
            payload["filter_type"] = filter_type
        if uuids is not None:
            payload["uuids"] = uuids
        if ground_truth_chunks is not None:
            payload["ground_truth_chunks"] = ground_truth_chunks
        
        return self.client.post("/api/chat", json_data=payload)
    
    def send_message_stream(
        self,
        messages: List[Dict[str, str]],
        collection_id: Optional[str] = None,
        patient_user_name: Optional[str] = None,
        filter_type: Optional[str] = None,
        uuids: Optional[List[str]] = None,
        ground_truth_chunks: Optional[List[Dict[str, str]]] = None
    ) -> Iterator[str]:
        """
        Send a conversational chat message with streaming response (SSE)
        
        Args:
            messages: List of conversation messages
            collection_id: Optional collection ID to restrict retrieval
            patient_user_name: Optional patient username for filtering
            filter_type: Optional filter type ("include" or "exclude")
            uuids: Optional list of document UUIDs to filter
            ground_truth_chunks: Optional ground truth chunks for evaluation
        
        Yields:
            Streaming response chunks
        
        Example:
            >>> for chunk in client.chat.send_message_stream(
            ...     messages=[{"user": "Tell me about my condition"}],
            ...     collection_id="col_123"
            ... ):
            ...     print(chunk, end='', flush=True)
        """
        payload = {"messages": messages}
        
        if collection_id is not None:
            payload["collection_id"] = collection_id
        if patient_user_name is not None:
            payload["patient_user_name"] = patient_user_name
        if filter_type is not None:
            payload["filter_type"] = filter_type
        if uuids is not None:
            payload["uuids"] = uuids
        if ground_truth_chunks is not None:
            payload["ground_truth_chunks"] = ground_truth_chunks
        
        response = self.client.post_stream("/api/chat/stream", json_data=payload)
        
        # Stream SSE events
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    yield decoded_line[6:]  # Remove 'data: ' prefix
