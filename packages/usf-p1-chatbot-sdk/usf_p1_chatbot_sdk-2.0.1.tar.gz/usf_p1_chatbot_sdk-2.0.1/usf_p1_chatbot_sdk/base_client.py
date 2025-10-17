"""
Base HTTP client for the USF P1 Chatbot SDK
"""
import requests
from typing import Optional, Dict, Any, Union
from .exceptions import (
    CivieAPIError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ConnectionError
)


class BaseClient:
    """Base HTTP client with authentication and error handling"""
    
    def __init__(self, api_key: str, base_url: str = "https://api-civie.us.inc", timeout: int = 60):
        """
        Initialize the base client
        
        Args:
            api_key: Bearer token for authentication
            base_url: Base URL for the API (default: https://api-civie.us.inc)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'USF-P1-Chatbot-SDK/2.0.0'
        })
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        stream: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], requests.Response]:
        """
        Make an HTTP request to the API
        
        Args:
            method: HTTP method (GET, POST, DELETE, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body data
            files: Files for multipart upload
            data: Form data
            stream: Whether to return streaming response
            **kwargs: Additional arguments passed to requests
        
        Returns:
            Response data as dict or Response object if streaming
        
        Raises:
            CivieAPIError: For various API errors
        """
        url = f"{self.base_url}{endpoint}"
        
        # Note: When files are provided, do NOT set Content-Type header
        # The requests library will automatically set it to multipart/form-data 
        # with proper boundary
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                files=files,
                data=data,
                timeout=self.timeout,
                stream=stream,
                **kwargs
            )
            
            # Return streaming response directly
            if stream:
                return response
            
            # Handle error responses
            if not response.ok:
                self._handle_error_response(response)
            
            # Return JSON response
            if response.content:
                return response.json()
            return {}
            
        except requests.exceptions.Timeout:
            raise ConnectionError("Request timed out")
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Failed to connect to API")
        except requests.exceptions.RequestException as e:
            raise CivieAPIError(f"Request failed: {str(e)}")
    
    def _handle_error_response(self, response: requests.Response):
        """Handle error responses from the API"""
        try:
            error_data = response.json()
            error_message = error_data.get('detail', error_data.get('message', 'Unknown error'))
        except:
            error_message = response.text or f"HTTP {response.status_code} error"
        
        if response.status_code == 401:
            raise AuthenticationError(
                f"Authentication failed: {error_message}",
                status_code=401,
                response=error_data if 'error_data' in locals() else None
            )
        elif response.status_code == 404:
            raise NotFoundError(
                f"Resource not found: {error_message}",
                status_code=404,
                response=error_data if 'error_data' in locals() else None
            )
        elif response.status_code == 422:
            raise ValidationError(
                f"Validation error: {error_message}",
                status_code=422,
                response=error_data if 'error_data' in locals() else None
            )
        elif response.status_code == 429:
            raise RateLimitError(
                f"Rate limit exceeded: {error_message}",
                status_code=429,
                response=error_data if 'error_data' in locals() else None
            )
        elif response.status_code >= 500:
            raise ServerError(
                f"Server error: {error_message}",
                status_code=response.status_code,
                response=error_data if 'error_data' in locals() else None
            )
        else:
            raise CivieAPIError(
                f"API error: {error_message}",
                status_code=response.status_code,
                response=error_data if 'error_data' in locals() else None
            )
    
    def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Make a GET request"""
        return self._make_request('GET', endpoint, params=params, **kwargs)
    
    def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, 
             files: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, 
             **kwargs) -> Dict[str, Any]:
        """Make a POST request"""
        return self._make_request('POST', endpoint, json_data=json_data, files=files, data=data, **kwargs)
    
    def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """Make a DELETE request"""
        return self._make_request('DELETE', endpoint, params=params, **kwargs)
    
    def post_stream(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, **kwargs) -> requests.Response:
        """Make a streaming POST request"""
        return self._make_request('POST', endpoint, json_data=json_data, stream=True, **kwargs)
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
