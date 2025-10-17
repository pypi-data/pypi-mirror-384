"""Enhanced Pydantic models for Freddy SDK"""

import base64
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, ConfigDict


# Response Models
class OutputText(BaseModel):
    """Text output from AI response"""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["output_text"] = "output_text"
    text: str
    annotations: List[Any] = Field(default_factory=list)


class MessageOutput(BaseModel):
    """Message output from AI response"""

    model_config = ConfigDict(populate_by_name=True)

    type: Literal["message"] = "message"
    id: str
    status: str
    role: str
    content: List[OutputText]


class ModelResponse(BaseModel):
    """Response from model/response endpoint"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    object: Literal["response"] = "response"
    created_at: int = Field(alias="createdAt")
    status: str
    model: str
    output: List[MessageOutput]
    error: Optional[str] = None
    incomplete_details: Optional[Dict[str, Any]] = Field(None, alias="incompleteDetails")
    instructions: Optional[str] = None
    max_output_tokens: Optional[int] = Field(None, alias="maxOutputTokens")
    parallel_tool_calls: Optional[bool] = Field(None, alias="parallelToolCalls")
    previous_response_id: Optional[str] = Field(None, alias="previousResponseId")
    reasoning: Optional[Dict[str, Any]] = None


# File Models
class FileObject(BaseModel):
    """File object"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    size: int
    mime_type: str = Field(alias="mimeType")
    purpose: Optional[str] = None
    created_at: str = Field(alias="createdAt")
    created_by: str = Field(alias="createdBy")
    is_active: bool = Field(default=True, alias="isActive")
    vector_stores: List[str] = Field(default_factory=list, alias="vectorStores")


class FileListResponse(BaseModel):
    """List of files with pagination"""

    model_config = ConfigDict(populate_by_name=True)

    data: List[FileObject]
    total: int
    page: int
    page_size: int = Field(alias="pageSize")
    has_more: bool = Field(alias="hasMore")


# Vector Store Models
class VectorStoreFileInfo(BaseModel):
    """File information in a vector store"""

    model_config = ConfigDict(populate_by_name=True)

    file_id: str = Field(alias="fileId")
    filename: str
    original_size: Optional[int] = Field(None, alias="originalSize")
    processed_size: Optional[int] = Field(None, alias="processedSize")
    size: Optional[int] = None
    compression_ratio: Optional[float] = Field(None, alias="compressionRatio")
    mime_type: Optional[str] = Field(None, alias="mimeType")
    uploaded_at: Optional[datetime] = Field(None, alias="uploadedAt")
    processed_at: Optional[datetime] = Field(None, alias="processedAt")
    chunk_count: Optional[int] = Field(None, alias="chunkCount")
    processing_status: Optional[Literal["pending", "processing", "completed", "failed"]] = Field(
        "pending", alias="processingStatus"
    )
    processing_error: Optional[str] = Field(None, alias="processingError")
    processing_progress: Optional[int] = Field(None, alias="processingProgress")


class VectorStoreResponse(BaseModel):
    """Vector store information"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    description: Optional[str] = None
    organization_id: str = Field(alias="organizationId")
    is_active: Optional[bool] = Field(True, alias="isActive")
    created_at: datetime = Field(alias="createdAt")
    updated_at: Optional[datetime] = Field(None, alias="updatedAt")
    created_by: Optional[str] = Field(None, alias="createdBy")
    access_mode: Optional[str] = Field(None, alias="accessMode")
    access_departments: Optional[List[str]] = Field(None, alias="accessDepartments")
    access_users: Optional[List[str]] = Field(None, alias="accessUsers")
    file_count: Optional[int] = Field(0, alias="fileCount")
    data_size: Optional[int] = Field(0, alias="dataSize")
    last_active: Optional[datetime] = Field(None, alias="lastActive")


class VectorStoreListResponse(BaseModel):
    """List of vector stores"""

    model_config = ConfigDict(populate_by_name=True)

    data: List[VectorStoreResponse]
    total: int


# Image Models
class ImageData(BaseModel):
    """Individual image data in response"""

    model_config = ConfigDict(populate_by_name=True)

    url: Optional[str] = None
    b64_json: Optional[str] = Field(None, alias="b64Json")
    revised_prompt: Optional[str] = Field(None, alias="revisedPrompt")

    def save_to_file(self, path: Union[str, Path]) -> None:
        """Save base64 image to file"""
        if not self.b64_json:
            raise ValueError("No base64 image data available")

        path = Path(path)
        image_bytes = base64.b64decode(self.b64_json)
        path.write_bytes(image_bytes)


class ImageResponse(BaseModel):
    """Response from image operations"""

    model_config = ConfigDict(populate_by_name=True)

    created: int
    data: List[ImageData]
    model: str
    provider: str

    def save_all(self, directory: Union[str, Path], prefix: str = "image") -> List[Path]:
        """Save all images to directory"""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        saved_paths = []
        for i, image_data in enumerate(self.data):
            if image_data.b64_json:
                path = directory / f"{prefix}_{i}.png"
                image_data.save_to_file(path)
                saved_paths.append(path)

        return saved_paths

