"""
Core resource filters for the Konigle SDK.

This module defines filter models for core platform resources like media
assets.
"""

from typing import Literal, Optional

from pydantic import Field

from .base import BaseFilters


class MediaAssetFilters(BaseFilters):
    """Base filters for all media assets."""

    q: Optional[str] = Field(None)
    """Search query that matches name and alt_text fields"""

    mime_type: Optional[str] = Field(None)
    """Filter by MIME type. Can be 'image', 'video', 'font', 'document' or
    comma-separated specific MIME types"""

    min_size: Optional[int] = Field(None, ge=0)
    """Minimum file size in bytes"""

    max_size: Optional[int] = Field(None, ge=0)
    """Maximum file size in bytes"""

    tags: Optional[str] = Field(None)
    """Comma-separated tags to filter by (matches any of the tags)"""

    ordering: Optional[
        Literal["created_at", "-created_at", "updated_at", "-updated_at"]
    ] = Field(None)


class ImageFilters(MediaAssetFilters):
    """Filters specific to image assets."""

    mime_type: Optional[Literal["image"]] = Field("image")
    """Automatically set to 'image' for image filters"""


class VideoFilters(MediaAssetFilters):
    """Filters specific to video assets."""

    mime_type: Optional[Literal["video"]] = Field("video")
    """Automatically set to 'video' for video filters"""


class DocumentFilters(MediaAssetFilters):
    """Filters specific to document assets."""

    mime_type: Optional[Literal["document"]] = Field("document")
    """Automatically set to 'document' for document filters"""


__all__ = [
    "MediaAssetFilters",
    "ImageFilters",
    "VideoFilters",
    "DocumentFilters",
]
