"""
Custom exceptions for the USF P1 Chatbot SDK
"""


class CivieAPIError(Exception):
    """Base exception for all Civie API errors"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class AuthenticationError(CivieAPIError):
    """Raised when authentication fails (401)"""
    pass


class ValidationError(CivieAPIError):
    """Raised when request validation fails (422)"""
    pass


class NotFoundError(CivieAPIError):
    """Raised when resource is not found (404)"""
    pass


class RateLimitError(CivieAPIError):
    """Raised when rate limit is exceeded (429)"""
    pass


class ServerError(CivieAPIError):
    """Raised when server error occurs (5xx)"""
    pass


class ConnectionError(CivieAPIError):
    """Raised when connection to API fails"""
    pass
