"""Freddy AI Assistant Python SDK"""

from .client import FreddyClient
from .async_client import AsyncFreddyClient
from .exceptions import (
    FreddyError,
    APIError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
)

__version__ = "0.1.0"
__all__ = [
    "FreddyClient",
    "AsyncFreddyClient",
    "FreddyError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
]

