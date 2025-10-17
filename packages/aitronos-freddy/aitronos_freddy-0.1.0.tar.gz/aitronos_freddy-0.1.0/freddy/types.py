"""Type definitions for Freddy SDK"""

from typing import Any, Dict, List, Literal, Optional, Union
from typing_extensions import TypedDict


# Response types
class TextContent(TypedDict, total=False):
    """Text content in a message"""

    text: str


class ImageContent(TypedDict, total=False):
    """Image content in a message"""

    type: Literal["image_url"]
    imageUrl: Dict[str, str]


MessageContent = Union[str, TextContent, ImageContent]


class Message(TypedDict, total=False):
    """Message structure"""

    role: Literal["user", "assistant", "system"]
    content: Union[str, List[MessageContent]]
    texts: Optional[List[TextContent]]
    images: Optional[List[ImageContent]]


# Image types
ImageSize = Literal["256x256", "512x512", "1024x1024", "1024x1792", "1792x1024"]
ImageFormat = Literal["url", "b64_json"]


# File purposes
FilePurpose = Literal["vector_store", "user_upload", "assistant"]


# Vector store access modes
AccessMode = Literal["public", "organization", "department", "private"]

