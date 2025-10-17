"""Sync Freddy client"""

from typing import Optional
import httpx
from ._base_client import get_default_headers
from .responses import ResponsesAPI
from .files import FilesAPI
from .vector_stores import VectorStoresAPI
from .images import ImagesAPI


class FreddyClient:
    """
    Freddy AI Assistant API Client (Synchronous)

    Example:
        >>> with FreddyClient(api_key="your-api-key") as client:
        ...     response = client.responses.create(
        ...         model="gpt-4.1",
        ...         inputs=[{"role": "user", "texts": [{"text": "Hello!"}]}]
        ...     )
        ...     print(response.output[0].content[0].text)
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://freddy-api.aitronos.com",
        timeout: float = 30.0,
    ):
        """
        Initialize Freddy client

        Args:
            api_key: Your Freddy API key
            base_url: API base URL (default: https://freddy-api.aitronos.com)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=get_default_headers(api_key),
            timeout=timeout,
        )

        # Initialize API modules
        self.responses = ResponsesAPI(self._client)
        self.files = FilesAPI(self._client)
        self.vector_stores = VectorStoresAPI(self._client)
        self.images = ImagesAPI(self._client)

    def close(self) -> None:
        """Close the HTTP client"""
        self._client.close()

    def __enter__(self) -> "FreddyClient":
        """Context manager entry"""
        return self

    def __exit__(self, *args) -> None:
        """Context manager exit"""
        self.close()

