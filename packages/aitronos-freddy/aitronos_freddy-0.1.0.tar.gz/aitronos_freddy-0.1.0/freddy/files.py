"""Files API - File management and uploads"""

from typing import Any, BinaryIO, Dict, Optional, Union
from pathlib import Path
import httpx
from .models import FileObject, FileListResponse
from ._base_client import _raise_for_status


class FilesAPI:
    """Sync Files API client"""

    def __init__(self, client: httpx.Client):
        self._client = client

    def upload(
        self,
        organization_id: str,
        file: Union[str, Path, BinaryIO],
        purpose: str = "vector_store",
        filename: Optional[str] = None,
    ) -> FileObject:
        """
        Upload a file

        Args:
            organization_id: Organization ID
            file: File path or file-like object
            purpose: Purpose of the file (e.g., "vector_store", "user_upload")
            filename: Optional filename override

        Returns:
            FileObject with file details

        Example:
            >>> client = FreddyClient(api_key="...")
            >>> file = client.files.upload(
            ...     organization_id="org_123",
            ...     file="document.pdf",
            ...     purpose="vector_store"
            ... )
            >>> print(file.id)
        """
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not filename:
                filename = file_path.name
            with open(file_path, "rb") as f:
                file_data = f.read()
        else:
            file_data = file.read()
            if not filename:
                filename = getattr(file, "name", "uploaded_file")

        files = {"file": (filename, file_data)}
        data = {"purpose": purpose}

        response = self._client.post(
            f"/v1/organizations/{organization_id}/files", files=files, data=data
        )
        _raise_for_status(response)
        return FileObject(**response.json())

    def list(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        purpose: Optional[str] = None,
        search: Optional[str] = None,
    ) -> FileListResponse:
        """
        List files

        Args:
            organization_id: Organization ID
            page: Page number (1-indexed)
            page_size: Items per page
            purpose: Filter by purpose
            search: Search query for filename

        Returns:
            FileListResponse with list of files

        Example:
            >>> files = client.files.list(organization_id="org_123", page_size=10)
            >>> for file in files.data:
            ...     print(file.name)
        """
        params: Dict[str, Any] = {"page": page, "pageSize": page_size}
        if purpose:
            params["purpose"] = purpose
        if search:
            params["search"] = search

        response = self._client.get(f"/v1/organizations/{organization_id}/files", params=params)
        _raise_for_status(response)
        return FileListResponse(**response.json())

    def retrieve(self, organization_id: str, file_id: str) -> FileObject:
        """
        Get file details

        Args:
            organization_id: Organization ID
            file_id: File ID

        Returns:
            FileObject with file details

        Example:
            >>> file = client.files.retrieve("org_123", "file_abc")
            >>> print(f"{file.name}: {file.size} bytes")
        """
        response = self._client.get(f"/v1/organizations/{organization_id}/files/{file_id}")
        _raise_for_status(response)
        return FileObject(**response.json())

    def delete(self, organization_id: str, file_id: str) -> Dict[str, Any]:
        """
        Delete a file

        Args:
            organization_id: Organization ID
            file_id: File ID

        Returns:
            Deletion confirmation

        Example:
            >>> result = client.files.delete("org_123", "file_abc")
            >>> print(result["deleted"])
        """
        response = self._client.delete(f"/v1/organizations/{organization_id}/files/{file_id}")
        _raise_for_status(response)
        return response.json()


class AsyncFilesAPI:
    """Async Files API client"""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def upload(
        self,
        organization_id: str,
        file: Union[str, Path, BinaryIO],
        purpose: str = "vector_store",
        filename: Optional[str] = None,
    ) -> FileObject:
        """Upload a file (async)"""
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not filename:
                filename = file_path.name
            with open(file_path, "rb") as f:
                file_data = f.read()
        else:
            file_data = file.read()
            if not filename:
                filename = getattr(file, "name", "uploaded_file")

        files = {"file": (filename, file_data)}
        data = {"purpose": purpose}

        response = await self._client.post(
            f"/v1/organizations/{organization_id}/files", files=files, data=data
        )
        _raise_for_status(response)
        return FileObject(**response.json())

    async def list(
        self,
        organization_id: str,
        page: int = 1,
        page_size: int = 20,
        purpose: Optional[str] = None,
        search: Optional[str] = None,
    ) -> FileListResponse:
        """List files (async)"""
        params: Dict[str, Any] = {"page": page, "pageSize": page_size}
        if purpose:
            params["purpose"] = purpose
        if search:
            params["search"] = search

        response = await self._client.get(
            f"/v1/organizations/{organization_id}/files", params=params
        )
        _raise_for_status(response)
        return FileListResponse(**response.json())

    async def retrieve(self, organization_id: str, file_id: str) -> FileObject:
        """Get file details (async)"""
        response = await self._client.get(f"/v1/organizations/{organization_id}/files/{file_id}")
        _raise_for_status(response)
        return FileObject(**response.json())

    async def delete(self, organization_id: str, file_id: str) -> Dict[str, Any]:
        """Delete a file (async)"""
        response = await self._client.delete(
            f"/v1/organizations/{organization_id}/files/{file_id}"
        )
        _raise_for_status(response)
        return response.json()

