"""Async Freddy client"""

from typing import Optional
import httpx
from ._base_client import get_default_headers
from .responses import AsyncResponsesAPI
from .files import AsyncFilesAPI
from .vector_stores import AsyncVectorStoresAPI
from .images import AsyncImagesAPI


class AsyncFreddyClient:
    """
    Freddy AI Assistant API Client (Asynchronous)

    Example:
        >>> async with AsyncFreddyClient(api_key="your-api-key") as client:
        ...     response = await client.responses.create(
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
        Initialize async Freddy client

        Args:
            api_key: Your Freddy API key
            base_url: API base URL (default: https://freddy-api.aitronos.com)
            timeout: Request timeout in seconds (default: 30.0)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=get_default_headers(api_key),
            timeout=timeout,
        )

        # Initialize API modules
        self.responses = AsyncResponsesAPI(self._client)
        self.files = AsyncFilesAPI(self._client)
        self.vector_stores = AsyncVectorStoresAPI(self._client)
        self.images = AsyncImagesAPI(self._client)

    async def close(self) -> None:
        """Close the HTTP client"""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncFreddyClient":
        """Async context manager entry"""
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit"""
        await self.close()

