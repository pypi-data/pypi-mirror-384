"""Images API - Image generation and manipulation"""

from typing import Any, BinaryIO, Dict, Optional, Union
from pathlib import Path
import httpx
from .models import ImageResponse
from ._base_client import _raise_for_status


class ImagesAPI:
    """Sync Images API client"""

    def __init__(self, client: httpx.Client):
        self._client = client

    def generate(
        self,
        organization_id: str,
        prompt: str,
        model: str = "dall-e-3",
        amount: int = 1,
        response_format: str = "b64_json",
        size: str = "1024x1024",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """
        Generate images from text

        Args:
            organization_id: Organization ID
            prompt: Text description of desired image
            model: Model to use (dall-e-2, dall-e-3, clipdrop-text-to-image)
            amount: Number of images (1-10)
            response_format: Format (url or b64_json)
            size: Image size (256x256, 512x512, 1024x1024, 1024x1792, 1792x1024)
            uid: Optional unique identifier for end user

        Returns:
            ImageResponse with generated images

        Example:
            >>> client = FreddyClient(api_key="...")
            >>> result = client.images.generate(
            ...     organization_id="org_123",
            ...     prompt="A serene mountain landscape at sunset",
            ...     model="dall-e-3",
            ...     size="1024x1024"
            ... )
            >>> result.save_all("./images")
        """
        payload = {
            "organizationId": organization_id,
            "prompt": prompt,
            "model": model,
            "amount": amount,
            "responseFormat": response_format,
            "size": size,
        }
        if uid:
            payload["uid"] = uid

        response = self._client.post("/v1/images/generate", json=payload)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    def upscale(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        target_width: int,
        target_height: int,
        model: str = "clipdrop-upscale",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """
        Upscale an image

        Args:
            organization_id: Organization ID
            image: Image file path or file-like object
            target_width: Target width (1-4096)
            target_height: Target height (1-4096)
            model: Model to use (clipdrop-upscale)
            response_format: Format (url or b64_json)
            uid: Optional unique identifier for end user

        Returns:
            ImageResponse with upscaled image

        Example:
            >>> result = client.images.upscale(
            ...     organization_id="org_123",
            ...     image="photo.jpg",
            ...     target_width=2048,
            ...     target_height=2048
            ... )
        """
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            filename = Path(image).name
        else:
            image_data = image.read()
            filename = getattr(image, "name", "image.jpg")

        files = {"image": (filename, image_data)}
        data = {
            "organization_id": organization_id,
            "target_width": str(target_width),
            "target_height": str(target_height),
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = self._client.post("/v1/images/upscale", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    def cleanup(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        mask: Union[str, Path, BinaryIO],
        model: str = "clipdrop-cleanup",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """
        Remove objects from image using mask

        Args:
            organization_id: Organization ID
            image: Image file
            mask: Mask file (white areas will be removed)
            model: Model to use (clipdrop-cleanup)
            response_format: Format (url or b64_json)
            uid: Optional unique identifier for end user

        Returns:
            ImageResponse with cleaned image

        Example:
            >>> result = client.images.cleanup(
            ...     organization_id="org_123",
            ...     image="photo.jpg",
            ...     mask="mask.png"
            ... )
        """
        # Load image
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            image_filename = Path(image).name
        else:
            image_data = image.read()
            image_filename = getattr(image, "name", "image.jpg")

        # Load mask
        if isinstance(mask, (str, Path)):
            with open(mask, "rb") as f:
                mask_data = f.read()
            mask_filename = Path(mask).name
        else:
            mask_data = mask.read()
            mask_filename = getattr(mask, "name", "mask.png")

        files = {
            "image": (image_filename, image_data),
            "mask": (mask_filename, mask_data),
        }
        data = {
            "organization_id": organization_id,
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = self._client.post("/v1/images/cleanup", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    def remove_background(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        model: str = "clipdrop-remove-background",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """
        Remove background from image

        Args:
            organization_id: Organization ID
            image: Image file
            model: Model to use (clipdrop-remove-background)
            response_format: Format (url or b64_json)
            uid: Optional unique identifier for end user

        Returns:
            ImageResponse with transparent background

        Example:
            >>> result = client.images.remove_background(
            ...     organization_id="org_123",
            ...     image="photo.jpg"
            ... )
        """
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            filename = Path(image).name
        else:
            image_data = image.read()
            filename = getattr(image, "name", "image.jpg")

        files = {"image": (filename, image_data)}
        data = {
            "organization_id": organization_id,
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = self._client.post("/v1/images/remove-background", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    def replace_background(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        prompt: str,
        model: str = "clipdrop-replace-background",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """
        Replace background with AI-generated background

        Args:
            organization_id: Organization ID
            image: Image file
            prompt: Description of new background
            model: Model to use (clipdrop-replace-background)
            response_format: Format (url or b64_json)
            uid: Optional unique identifier for end user

        Returns:
            ImageResponse with new background

        Example:
            >>> result = client.images.replace_background(
            ...     organization_id="org_123",
            ...     image="photo.jpg",
            ...     prompt="tropical beach with palm trees"
            ... )
        """
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            filename = Path(image).name
        else:
            image_data = image.read()
            filename = getattr(image, "name", "image.jpg")

        files = {"image": (filename, image_data)}
        data = {
            "organization_id": organization_id,
            "prompt": prompt,
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = self._client.post("/v1/images/replace-background", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())


class AsyncImagesAPI:
    """Async Images API client"""

    def __init__(self, client: httpx.AsyncClient):
        self._client = client

    async def generate(
        self,
        organization_id: str,
        prompt: str,
        model: str = "dall-e-3",
        amount: int = 1,
        response_format: str = "b64_json",
        size: str = "1024x1024",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """Generate images from text (async)"""
        payload = {
            "organizationId": organization_id,
            "prompt": prompt,
            "model": model,
            "amount": amount,
            "responseFormat": response_format,
            "size": size,
        }
        if uid:
            payload["uid"] = uid

        response = await self._client.post("/v1/images/generate", json=payload)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    async def upscale(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        target_width: int,
        target_height: int,
        model: str = "clipdrop-upscale",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """Upscale an image (async)"""
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            filename = Path(image).name
        else:
            image_data = image.read()
            filename = getattr(image, "name", "image.jpg")

        files = {"image": (filename, image_data)}
        data = {
            "organization_id": organization_id,
            "target_width": str(target_width),
            "target_height": str(target_height),
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = await self._client.post("/v1/images/upscale", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    async def cleanup(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        mask: Union[str, Path, BinaryIO],
        model: str = "clipdrop-cleanup",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """Remove objects from image (async)"""
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            image_filename = Path(image).name
        else:
            image_data = image.read()
            image_filename = getattr(image, "name", "image.jpg")

        if isinstance(mask, (str, Path)):
            with open(mask, "rb") as f:
                mask_data = f.read()
            mask_filename = Path(mask).name
        else:
            mask_data = mask.read()
            mask_filename = getattr(mask, "name", "mask.png")

        files = {
            "image": (image_filename, image_data),
            "mask": (mask_filename, mask_data),
        }
        data = {
            "organization_id": organization_id,
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = await self._client.post("/v1/images/cleanup", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    async def remove_background(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        model: str = "clipdrop-remove-background",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """Remove background from image (async)"""
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            filename = Path(image).name
        else:
            image_data = image.read()
            filename = getattr(image, "name", "image.jpg")

        files = {"image": (filename, image_data)}
        data = {
            "organization_id": organization_id,
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = await self._client.post("/v1/images/remove-background", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

    async def replace_background(
        self,
        organization_id: str,
        image: Union[str, Path, BinaryIO],
        prompt: str,
        model: str = "clipdrop-replace-background",
        response_format: str = "b64_json",
        uid: Optional[str] = None,
    ) -> ImageResponse:
        """Replace background (async)"""
        if isinstance(image, (str, Path)):
            with open(image, "rb") as f:
                image_data = f.read()
            filename = Path(image).name
        else:
            image_data = image.read()
            filename = getattr(image, "name", "image.jpg")

        files = {"image": (filename, image_data)}
        data = {
            "organization_id": organization_id,
            "prompt": prompt,
            "model": model,
            "response_format": response_format,
        }
        if uid:
            data["uid"] = uid

        response = await self._client.post("/v1/images/replace-background", files=files, data=data)
        _raise_for_status(response)
        return ImageResponse(**response.json())

