"""
Custom exceptions for AnotiAI PII Masker API client.
"""


class APIError(Exception):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    
    def __init__(self, message: str = "Authentication failed. Please check your API key."):
        super().__init__(message, status_code=401)


class NetworkError(APIError):
    """Raised when network connectivity issues occur."""
    
    def __init__(self, message: str = "Network error. Please check your internet connection."):
        super().__init__(message)


class ValidationError(APIError):
    """Raised when input validation fails."""
    
    def __init__(self, message: str = "Input validation failed."):
        super().__init__(message, status_code=400)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded. Please try again later."):
        super().__init__(message, status_code=429)


class ServerError(APIError):
    """Raised when server-side errors occur."""
    
    def __init__(self, message: str = "Server error. Please try again later."):
        super().__init__(message, status_code=500)
