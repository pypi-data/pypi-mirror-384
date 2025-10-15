"""
Product image models for the Konigle SDK.

This module provides Pydantic models for product image resources including
creation, update, and response models with file upload validation.
"""

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from konigle.models.base import BaseResource, CreateModel, UpdateModel
from konigle.types.common import FileInputT
from konigle.utils import FileInput

from .base import IDMixin, TimestampedResource


class ProductImageReference(IDMixin):
    """
    Reference model for a product image.

    Contains only the ID field for lightweight references.
    """

    url: Optional[str] = Field(
        default=None,
        title="URL",
        description="The URL of the image.",
    )
    """The URL of the image."""


class ProductImageBase(BaseModel):
    """
    Base product image model with truly shared fields.

    Contains only fields that have the same optionality and validation
    requirements in both creation and response contexts.
    """

    product: str = Field(
        ...,
        title="Product ID",
        description="ID of the parent product.",
    )
    """ID of the parent product."""

    alt: Optional[str] = Field(
        default="",
        title="Alt Text",
        description="Alternative text for accessibility.",
    )
    """Alternative text for accessibility."""

    variant_ids: Optional[List[str]] = Field(
        default_factory=list,
        title="Variant IDs",
        description="List of variant IDs this image is associated with.",
    )
    """List of variant IDs this image is associated with."""


class ProductImageCreate(ProductImageBase, CreateModel):
    """
    Model for creating a new product image.

    Requires either a file upload or a source URL.
    Must specify the parent product ID.
    """

    position: Optional[int] = Field(
        default=1,
        ge=1,
        title="Position",
        description="Display position of the image.",
    )
    """Display position of the image."""

    file: FileInputT = Field(
        ...,
        title="Image File",
        description="Image file to upload.",
    )
    """Image file to upload."""

    @field_validator("file")
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
        self.file = FileInput.normalize(self.file)
        return self


class ProductImage(
    ProductImageBase, TimestampedResource, IDMixin, BaseResource
):
    """
    Complete product image resource model.

    Represents a product image from the API with all fields including
    computed values, file metadata, and Active Record capabilities.
    """

    position: int = Field(
        ...,
        ge=1,
        title="Position",
        description="Display position of the image.",
    )
    """Display position of the image."""

    width: Optional[int] = Field(
        None,
        ge=1,
        title="Width",
        description="Image width in pixels.",
    )
    """Image width in pixels."""

    height: Optional[int] = Field(
        None,
        ge=1,
        title="Height",
        description="Image height in pixels.",
    )
    """Image height in pixels."""

    url: Optional[str] = Field(
        default=None,
        title="URL",
        description="The URL of the image.",
    )
    """URL of the image after upload."""

    def __str__(self) -> str:
        return (
            f"ProductImage(id = {self.id}, position={self.position}, "
            f"url={self.url})"
        )


class ProductImageUpdate(UpdateModel):
    """
    Model for updating an existing product image.

    All fields are optional for partial updates.
    Supports updating position, alt text, variant associations, and the image file.
    """

    position: Optional[int] = Field(
        default=None,
        ge=1,
        title="Position",
        description="Display position of the image.",
    )
    """Display position of the image."""

    alt: Optional[str] = Field(
        default=None,
        title="Alt Text",
        description="Alternative text for accessibility.",
    )
    """Alternative text for accessibility."""

    variant_ids: Optional[List[str]] = Field(
        default=None,
        title="Variant IDs",
        description="List of variant IDs this image is associated with.",
    )
    """List of variant IDs this image is associated with."""
