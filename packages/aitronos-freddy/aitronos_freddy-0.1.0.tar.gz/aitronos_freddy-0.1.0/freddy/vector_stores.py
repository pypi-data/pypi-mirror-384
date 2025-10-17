"""Vector Stores API - Knowledge base management"""

from typing import Any, Dict, List, Optional
import httpx
from .models import VectorStoreResponse, VectorStoreListResponse
from ._base_client import _raise_for_status


class VectorStoresAPI:
    """Sync Vector Stores API client"""

    def __init__(self, client: httpx.Client):
        self._client = client

    def create(
        self,
        organization_id: str,
        name: str,
        description: Optional[str] = None,
        access_mode: str = "organization",
        **kwargs: Any,
    ) -> VectorStoreResponse:
        """
        Create a vector store

        Args:
            organization_id: Organization ID
            name: Vector store name
            description: Optional description
            access_mode: Access mode (public, organization, department, private)
            **kwargs: Additional parameters

        Returns:
            VectorStoreResponse with store details

        Example:
            >>> client = FreddyClient(api_key="...")
            >>> store = client.vector_stores.create(
            ...     organization_id="org_123",
            ...     name="Company Knowledge Base",
            ...     description="Internal documentation"
            ... )
            >>> print(store.id)
        """
        payload = {
            "name": name,
            "accessMode": access_mode,
            **kwargs,
        }
        if description:
            payload["description"] = description

        response = self._client.post(
            f"/v1/organizations/{organization_id}/vector-stores", json=payload
        )
        _raise_for_status(response)
        return VectorStoreResponse(**response.json())

    def list(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> VectorStoreListResponse:
        """
        List vector stores

        Args:
            organization_id: Organization ID
            page: Page number
            page_size: Items per page
            search: Search query

        Returns:
            VectorStoreListResponse with list of stores

        Example:
            >>> stores = client.vector_stores.list(organization_id="org_123")
            >>> for store in stores.data:
            ...     print(f"{store.name}: {store.file_count} files")
        """
        params: Dict[str, Any] = {"page": page, "pageSize": page_size}
        if search:
            params["search"] = search

        response = self._client.get(
            f"/v1/organizations/{organization_id}/vector-stores", params=params
        )
        _raise_for_status(response)
        return VectorStoreListResponse(**response.json())

    def retrieve(self, organization_id: str, vector_store_id: str) -> VectorStoreResponse:
        """
        Get vector store details

        Args:
            organization_id: Organization ID
            vector_store_id: Vector store ID

        Returns:
            VectorStoreResponse with store details

        Example:
            >>> store = client.vector_stores.retrieve("org_123", "vs_abc")
            >>> print(f"Files: {store.file_count}, Size: {store.data_size}")
        """
        response = self._client.get(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}"
        )
        _raise_for_status(response)
        return VectorStoreResponse(**response.json())

    def update(
        self,
        organization_id: str,
        vector_store_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> VectorStoreResponse:
        """
        Update vector store

        Args:
            organization_id: Organization ID
            vector_store_id: Vector store ID
            name: New name
            description: New description
            **kwargs: Additional parameters

        Returns:
            Updated VectorStoreResponse

        Example:
            >>> store = client.vector_stores.update(
            ...     "org_123", "vs_abc",
            ...     description="Updated description"
            ... )
        """
        payload: Dict[str, Any] = {**kwargs}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description

        response = self._client.patch(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}", json=payload
        )
        _raise_for_status(response)
        return VectorStoreResponse(**response.json())

    def delete(self, organization_id: str, vector_store_id: str) -> Dict[str, Any]:
        """
        Delete a vector store

        Args:
            organization_id: Organization ID
            vector_store_id: Vector store ID

        Returns:
            Deletion confirmation

        Example:
            >>> result = client.vector_stores.delete("org_123", "vs_abc")
        """
        response = self._client.delete(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}"
        )
        _raise_for_status(response)
        return response.json()

    def add_file(
        self, organization_id: str, vector_store_id: str, file_id: str
    ) -> Dict[str, Any]:
        """
        Add a file to vector store

        Args:
            organization_id: Organization ID
            vector_store_id: Vector store ID
            file_id: File ID to add

        Returns:
            Success confirmation

        Example:
            >>> result = client.vector_stores.add_file("org_123", "vs_abc", "file_xyz")
        """
        payload = {"fileId": file_id}
        response = self._client.post(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}/files",
            json=payload,
        )
        _raise_for_status(response)
        return response.json()

    def remove_file(
        self, organization_id: str, vector_store_id: str, file_id: str
    ) -> Dict[str, Any]:
        """
        Remove a file from vector store

        Args:
            organization_id: Organization ID
            vector_store_id: Vector store ID
            file_id: File ID to remove

        Returns:
            Success confirmation

        Example:
            >>> result = client.vector_stores.remove_file("org_123", "vs_abc", "file_xyz")
        """
        response = self._client.delete(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}/files/{file_id}"
        )
        _raise_for_status(response)
        return response.json()


class AsyncVectorStoresAPI:
    """Async Vector Stores API client"""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def create(
        self,
        organization_id: str,
        name: str,
        description: Optional[str] = None,
        access_mode: str = "organization",
        **kwargs: Any,
    ) -> VectorStoreResponse:
        """Create a vector store (async)"""
        payload = {
            "name": name,
            "accessMode": access_mode,
            **kwargs,
        }
        if description:
            payload["description"] = description

        response = await self._client.post(
            f"/v1/organizations/{organization_id}/vector-stores", json=payload
        )
        _raise_for_status(response)
        return VectorStoreResponse(**response.json())

    async def list(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> VectorStoreListResponse:
        """List vector stores (async)"""
        params: Dict[str, Any] = {"page": page, "pageSize": page_size}
        if search:
            params["search"] = search

        response = await self._client.get(
            f"/v1/organizations/{organization_id}/vector-stores", params=params
        )
        _raise_for_status(response)
        return VectorStoreListResponse(**response.json())

    async def retrieve(self, organization_id: str, vector_store_id: str) -> VectorStoreResponse:
        """Get vector store details (async)"""
        response = await self._client.get(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}"
        )
        _raise_for_status(response)
        return VectorStoreResponse(**response.json())

    async def update(
        self,
        organization_id: str,
        vector_store_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        **kwargs: Any,
    ) -> VectorStoreResponse:
        """Update vector store (async)"""
        payload: Dict[str, Any] = {**kwargs}
        if name:
            payload["name"] = name
        if description:
            payload["description"] = description

        response = await self._client.patch(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}", json=payload
        )
        _raise_for_status(response)
        return VectorStoreResponse(**response.json())

    async def delete(self, organization_id: str, vector_store_id: str) -> Dict[str, Any]:
        """Delete a vector store (async)"""
        response = await self._client.delete(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}"
        )
        _raise_for_status(response)
        return response.json()

    async def add_file(
        self, organization_id: str, vector_store_id: str, file_id: str
    ) -> Dict[str, Any]:
        """Add a file to vector store (async)"""
        payload = {"fileId": file_id}
        response = await self._client.post(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}/files",
            json=payload,
        )
        _raise_for_status(response)
        return response.json()

    async def remove_file(
        self, organization_id: str, vector_store_id: str, file_id: str
    ) -> Dict[str, Any]:
        """Remove a file from vector store (async)"""
        response = await self._client.delete(
            f"/v1/organizations/{organization_id}/vector-stores/{vector_store_id}/files/{file_id}"
        )
        _raise_for_status(response)
        return response.json()

