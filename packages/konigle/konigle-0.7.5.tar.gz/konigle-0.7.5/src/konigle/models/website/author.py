"""
Author models for the Konigle SDK.

This module provides models for content authors including creation, update,
and resource representations.
"""

import io
from typing import BinaryIO, Optional, Tuple, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from konigle.models.base import (
    CreateModel,
    Resource,
    TimestampedResource,
    UpdateModel,
)
from konigle.utils import FileInput
from konigle.validators import validate_image


class AuthorReference(BaseModel):
    """
    Lightweight author reference for foreign key relationships.

    Used when APIs return minimal author data in list responses or
    when only basic author information is needed.
    """

    id: str = Field(
        ...,
        title="Author ID",
        description="Unique identifier for the author",
    )
    """Unique identifier for the author."""

    name: Optional[str] = Field(
        None,
        title="Name",
        description="Name of the author",
    )
    """Name of the author."""

    model_config = ConfigDict(extra="ignore")


class SocialLinks(BaseModel):

    website: Optional[str] = Field(
        None,
        title="Website",
        description="Author's personal or professional website URL",
    )
    """Author's personal or professional website URL."""

    twitter: Optional[str] = Field(
        None,
        title="Twitter",
        description="Author's Twitter profile URL",
    )
    """Author's Twitter profile URL."""

    facebook: Optional[str] = Field(
        None,
        title="Facebook",
        description="Author's Facebook profile URL",
    )
    """Author's Facebook profile URL."""

    linkedin: Optional[str] = Field(
        None,
        title="LinkedIn",
        description="Author's LinkedIn profile URL",
    )
    """Author's LinkedIn profile URL."""


class BaseAuthor(BaseModel):
    """
    Base class for author models with common editable fields.

    Contains fields that can be set during creation/update.
    """

    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="Name of the author",
    )
    """Name of the author."""

    handle: str = Field(
        ...,
        max_length=50,
        title="Handle",
        description="URL handle for the author",
    )
    """URL handle for the author."""

    tagline: str = Field(
        default="",
        max_length=255,
        title="Tagline",
        description="Author tagline. Ex. Marketing Head",
    )
    """Author tagline. Ex. Marketing Head."""

    bio: str = Field(
        default="",
        title="Bio",
        description="Brief bio of the author",
    )
    """Brief bio of the author."""

    email: str = Field(
        default="",
        title="Email",
        description="Email of the author",
    )
    """Email of the author."""

    social_links: Optional[SocialLinks] = Field(
        default=None,
        title="Social Links",
        description="Social links of the author. Ex. Twitter, Facebook",
    )
    """Social links of the author. Ex. Twitter, Facebook, LinkedIn."""


class Author(BaseAuthor, Resource):
    """
    Author resource model.

    Represents a content author with profile information and social links.
    """

    avatar_width: Optional[int] = Field(
        None,
        title="Avatar Width",
        description="Original width of the author avatar",
    )
    """Original width of the author avatar."""

    avatar_height: Optional[int] = Field(
        None,
        title="Avatar Height",
        description="Original height of the author avatar",
    )
    """Original height of the author avatar."""

    avatar: Optional[str] = Field(
        None,
        title="Avatar",
        description="Author avatar URL",
    )
    """Author avatar URL."""

    def __str__(self) -> str:
        return (
            f"Author(id = {self.id}, name={self.name}, handle={self.handle})"
        )


class AvatarMixin:

    avatar: Optional[
        Union[
            str,
            bytes,
            io.BytesIO,
            BinaryIO,
            Tuple[Union[bytes, io.BytesIO, BinaryIO], str],
        ]
    ] = Field(
        None,
        title="Avatar",
        description="Avatar to upload. Can be file path, bytes, BytesIO, "
        "BinaryIO, or tuple of (file_data, filename)",
    )
    """Avatar file to upload. Can be file path, bytes, BytesIO, BinaryIO, or
    tuple of (file_data, filename)"""

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, v):
        """Ensure we're uploading an image file."""
        return validate_image(v)

    @model_validator(mode="after")
    def normalize_file(self):
        """Convert file paths or bytes to FileInput."""
        if self.avatar:
            self.avatar = FileInput.normalize(self.avatar)
        return self


class CreateAuthor(AvatarMixin, BaseAuthor, CreateModel):
    """
    Model for creating a new author.

    Contains all required and optional fields for author creation.
    """


class UpdateAuthor(AvatarMixin, UpdateModel):
    """
    Model for updating an existing author.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(
        None,
        max_length=255,
        title="Name",
        description="Name of the author",
    )
    """Name of the author."""

    handle: Optional[str] = Field(
        None,
        max_length=50,
        title="Handle",
        description="URL handle for the author",
    )
    """URL handle for the author."""

    tagline: Optional[str] = Field(
        None,
        max_length=255,
        title="Tagline",
        description="Author tagline. Ex. Marketing Head",
    )
    """Author tagline. Ex. Marketing Head."""

    bio: Optional[str] = Field(
        None,
        title="Bio",
        description="Brief bio of the author",
    )
    """Brief bio of the author."""

    email: Optional[str] = Field(
        None,
        title="Email",
        description="Email of the author",
    )
    """Email of the author."""

    social_links: Optional[SocialLinks] = Field(
        None,
        title="Social Links",
        description="Social links of the author. Ex. Twitter, Facebook",
    )
    """Social links of the author. Ex. Twitter, Facebook, LinkedIn."""
