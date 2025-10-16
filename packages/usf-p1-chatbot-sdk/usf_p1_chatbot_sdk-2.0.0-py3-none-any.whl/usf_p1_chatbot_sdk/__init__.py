"""
USF P1 Chatbot SDK
==================

A Python SDK for the Civie Chatbot API v2.0.0

This SDK provides a simple and intuitive interface to interact with the
Civie Chatbot API, including:
- Chat operations (conversational and streaming)
- Document ingestion (PDFs and URLs)
- Patient management
- Collection management
- Log management
- File operations

Example:
    >>> from usf_p1_chatbot_sdk import CivieClient
    >>> client = CivieClient(api_key="your-api-key", base_url="https://api-civie.us.inc")
    >>> response = client.chat.send_message(
    ...     messages=[{"user": "Hello, how can I help?"}],
    ...     collection_id="my-collection",
    ...     patient_user_name="patient123"
    ... )
    >>> print(response["response"])
"""

from .client import CivieClient
from .exceptions import (
    CivieAPIError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError
)

__version__ = "2.0.0"
__author__ = "USF Team"
__all__ = [
    "CivieClient",
    "CivieAPIError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
]
