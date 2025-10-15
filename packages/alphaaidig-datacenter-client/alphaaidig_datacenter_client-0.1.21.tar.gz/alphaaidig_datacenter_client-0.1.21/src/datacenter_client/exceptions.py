"""
Custom exceptions for the Datacenter API client.
"""

from typing import Optional

class APIError(Exception):
    """Base class for all API-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.status_code = status_code
        super().__init__(f"API Error (Status: {status_code}): {message}")

class AuthenticationError(APIError):
    """Raised for authentication errors (401, 403)."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)

class NotFoundError(APIError):
    """Raised when a resource is not found (404)."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class InvalidRequestError(APIError):
    """Raised for client-side errors (400)."""
    def __init__(self, message: str):
        super().__init__(message, status_code=400)