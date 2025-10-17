"""Base client functionality shared between sync and async clients"""

from typing import Any, Dict, Optional
import httpx
from .exceptions import APIError, AuthenticationError, RateLimitError


def _parse_error_response(response: httpx.Response) -> Dict[str, Any]:
    """Parse error response from API"""
    try:
        error_data = response.json()
        if isinstance(error_data, dict) and "error" in error_data:
            return error_data["error"]
        return error_data
    except Exception:
        return {"message": response.text or "Unknown error", "type": "unknown_error"}


def _raise_for_status(response: httpx.Response) -> None:
    """Raise appropriate exception for HTTP error status codes"""
    if response.is_success:
        return

    error_data = _parse_error_response(response)
    message = error_data.get("message", f"HTTP {response.status_code} error")

    if response.status_code == 401:
        raise AuthenticationError(message, response.status_code, error_data)
    elif response.status_code == 429:
        raise RateLimitError(message, response.status_code, error_data)
    else:
        raise APIError(message, response.status_code, error_data)


def get_default_headers(api_key: str) -> Dict[str, str]:
    """Get default headers for API requests"""
    return {
        "X-API-Key": api_key,  # Backend requires X-API-Key header (not Authorization: Bearer)
        "Content-Type": "application/json",
    }

