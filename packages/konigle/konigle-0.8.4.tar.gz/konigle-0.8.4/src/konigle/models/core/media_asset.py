"""
Media asset models for the Konigle SDK.

This module defines models for Image, Video, and Document assets.
All three types map to the same backend StorefrontAsset table but are
differentiated by mime_type for user-friendly separate interfaces.
"""

from enum import Enum
from typing import List, Optional

from pydantic import ConfigDict, Field, field_validator, model_validator

from konigle.models.base import CreateModel, TimestampedResource, UpdateModel
from konigle.types.common import FileInputT
from konigle.utils import FileInput


class AssetType(str, Enum):
    """Asset type enumeration."""

    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class BaseAsset(TimestampedResource):
    """Base class for all media assets with common fields."""

    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="User-friendly name for searching",
    )
    """User-friendly name for searching"""

    mime_type: str = Field(
        ...,
        max_length=100,
        title="MIME Type",
        description="MIME type of the file",
    )
    """MIME type of the file"""

    alt_text: str = Field(
        default="", title="Alt Text", description="Alt text for accessibility"
    )
    """Alt text for accessibility"""

    size: int = Field(
        default=0, ge=0, title="Size", description="Total size in bytes"
    )
    """Total size in bytes"""

    asset_url: Optional[str] = Field(
        None, title="Asset URL", description="URL to access the asset"
    )
    """URL to access the asset"""

    tags: List[str] = Field(
        default_factory=list,
        title="Tags",
        description="Tags for categorization",
    )
    """Tags for categorization"""


class BaseAssetCreate(CreateModel):
    """Base create model for assets."""

    name: str = Field(
        ..., max_length=255, title="Name", description="User-friendly name"
    )
    """User-friendly name"""

    alt_text: str = Field(
        default="", title="Alt Text", description="Alt text for accessibility"
    )
    """Alt text for accessibility"""

    tags: str = Field(
        default="",
        title="Tags",
        description="Tags for categorization. Comma-separated string.",
    )
    """Tags for categorization. Comma-separated string."""


class BaseAssetUpdate(UpdateModel):
    """Base update model for assets - only mutable fields."""

    name: Optional[str] = Field(
        None, max_length=255, title="Name", description="User-friendly name"
    )
    """User-friendly name"""

    alt_text: Optional[str] = Field(
        None, title="Alt Text", description="Alt text for accessibility"
    )
    """Alt text for accessibility"""

    tags: Optional[List[str]] = Field(
        None, title="Tags", description="Tags for categorization"
    )
    """Tags for categorization"""

    model_config = ConfigDict(arbitrary_types_allowed=True)


# Image-specific models
class Image(BaseAsset):
    """Image asset model."""

    image_width: Optional[int] = Field(
        None, ge=0, title="Image Width", description="Image width in pixels"
    )
    """Image width in pixels"""

    image_height: Optional[int] = Field(
        None, ge=0, title="Image Height", description="Image height in pixels"
    )
    """Image height in pixels"""

    def __str__(self) -> str:
        return f"Image(id = {self.id}, name = {self.name}, url = {self.asset_url})"


class ImageCreate(BaseAssetCreate):
    """Create model for image assets."""

    image: FileInputT = Field(
        ...,
        title="Image",
        description="Image file to upload. Can be file path, bytes, "
        "BytesIO, BinaryIO, or tuple of (file_data, filename)",
    )
    """Image file to upload. Can be file path, bytes, BytesIO, BinaryIO, or
    tuple of (file_data, filename)"""

    @field_validator("image")
    @classmethod
    def validate_image_file(cls, v):
        """Ensure we're uploading an image file."""
        allowed_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
        ]
        # Handle tuple input
        if isinstance(v, tuple) and len(v) == 2:
            _, filename = v
            if not any(
                filename.lower().endswith(ext) for ext in allowed_extensions
            ):
                raise ValueError(
                    f"File must be an image {', '.join(allowed_extensions)}"
                )
        elif (
            isinstance(v, str)
            and not v.startswith("https://")
            and not any(v.lower().endswith(ext) for ext in allowed_extensions)
        ):
            raise ValueError(
                f"File must be an image ({', '.join(allowed_extensions)})"
            )
        return v

    @model_validator(mode="after")
    def normalize_file(self):
        """Convert file paths or bytes to FileInput."""
        self.image = FileInput.normalize(self.image)
        return self


class ImageUpdate(BaseAssetUpdate):
    """Update model for image assets - file cannot be updated."""


# Video-specific models
class Video(BaseAsset):
    """Video asset model."""

    def __str__(self) -> str:
        return (
            f"Video(id = {self.id}, name = {self.name}, "
            "url = {self.asset_url})"
        )


class VideoCreate(BaseAssetCreate):
    """Create model for video assets."""

    file: FileInputT = Field(
        ...,
        title="File",
        description="Video file to upload. Can be file path, bytes, "
        "BytesIO, BinaryIO, or tuple of (file_data, filename)",
    )
    """Video file to upload. Can be file path, bytes, BytesIO, BinaryIO,
    or tuple of (file_data, filename)"""

    @field_validator("file")
    @classmethod
    def validate_video_file(cls, v):
        """Ensure we're uploading a video file."""
        supported_formats = [".mp4", ".webm"]
        # Handle tuple input
        if isinstance(v, tuple) and len(v) == 2:
            _, filename = v
            if not any(
                filename.lower().endswith(ext) for ext in supported_formats
            ):
                raise ValueError(
                    f"File must be a video {', '.join(supported_formats)}"
                )
        elif (
            isinstance(v, str)
            and not v.startswith("https://")
            and not any(v.lower().endswith(ext) for ext in supported_formats)
        ):
            raise ValueError(
                f"File must be a video ({', '.join(supported_formats)})"
            )
        return v

    @model_validator(mode="after")
    def normalize_file(self):
        """Convert file paths or bytes to FileInput."""
        self.file = FileInput.normalize(self.file)
        return self


class VideoUpdate(BaseAssetUpdate):
    """Update model for video assets - file cannot be updated."""


# Document-specific models
class Document(BaseAsset):
    """Document asset model."""

    def __str__(self) -> str:
        return (
            f"Document(id = {self.id}, name = {self.name}, "
            "url = {self.asset_url})"
        )


class DocumentCreate(BaseAssetCreate):
    """Create model for document assets."""

    file: FileInputT = Field(
        ...,
        title="File",
        description="Document file to upload. Can be file path, bytes, "
        "BytesIO, BinaryIO, or tuple of (file_data, filename)",
    )
    """Document file to upload. Can be file path, bytes, BytesIO, BinaryIO,
    or tuple of (file_data, filename)"""

    @field_validator("file")
    @classmethod
    def validate_document_file(cls, v):
        """Ensure we're uploading a supported document file."""
        supported_extensions = [
            ".pdf",
            ".csv",
            ".txt",
            ".docx",
            ".xlsx",
            ".doc",
            ".xls",
        ]

        # Handle tuple input
        if isinstance(v, tuple) and len(v) == 2:
            _, filename = v
            if not any(
                filename.lower().endswith(ext) for ext in supported_extensions
            ):
                raise ValueError(
                    f"File must be a supported document: "
                    f"{', '.join(supported_extensions)}"
                )
        elif isinstance(v, str) and not v.startswith("https://"):
            if not any(
                v.lower().endswith(ext) for ext in supported_extensions
            ):
                raise ValueError(
                    f"File must be a supported document: "
                    f"{', '.join(supported_extensions)}"
                )
        return v

    @model_validator(mode="after")
    def normalize_file(self):
        """Convert file paths or bytes to FileInput."""
        self.file = FileInput.normalize(self.file)
        return self


class DocumentUpdate(BaseAssetUpdate):
    """Update model for document assets - file cannot be updated."""


__all__ = [
    "Image",
    "ImageCreate",
    "ImageUpdate",
    "Video",
    "VideoCreate",
    "VideoUpdate",
    "Document",
    "DocumentCreate",
    "DocumentUpdate",
]
