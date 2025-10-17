"""Custom exceptions for Freddy SDK"""

from typing import Any, Dict, Optional


class FreddyError(Exception):
    """Base exception for Freddy SDK"""

    pass


class APIError(FreddyError):
    """API returned an error"""

    def __init__(self, message: str, status_code: int, response: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.response = response or {}
        super().__init__(message)


class AuthenticationError(APIError):
    """401 authentication errors"""

    pass


class RateLimitError(APIError):
    """429 rate limit errors"""

    pass


class ValidationError(FreddyError):
    """Request validation errors"""

    pass
