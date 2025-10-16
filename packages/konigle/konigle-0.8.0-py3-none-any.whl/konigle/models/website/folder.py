"""
Folder models for the Konigle SDK.

This module defines models for content folder management including
hierarchical folder structure, folder types, and folder configurations.
"""

from enum import Enum
from typing import (
    TYPE_CHECKING,
    Annotated,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    cast,
)

from pydantic import AfterValidator, BaseModel, Field

from konigle.models.base import CreateModel, Resource, SEOMeta, UpdateModel
from konigle.validators import (
    validate_country_code,
    validate_handle,
    validate_language_code,
)

if TYPE_CHECKING:
    from konigle.managers.website.folder import FolderManager


class FolderType(str, Enum):
    """Folder type enumeration."""

    PAGES = "pages"
    BLOG = "blog"
    GLOSSARY = "glossary"
    COLLECTION = "collection"
    HOME = "home"
    OTHERS = "others"
    CUSTOM = "custom"


class FolderReference(Resource):
    """Lightweight folder reference for foreign key relationships."""

    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="Folder name for display and search purposes",
    )
    """Folder name for display and search purposes."""

    handle: str = Field(
        ...,
        max_length=255,
        title="Handle",
        description="Unique identifier for the folder used in URLs",
    )


class BaseFolder(BaseModel):
    """
    Base class for folder models with common editable fields.

    Contains fields that can be set during creation/update.
    """

    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="Folder name for display and search purposes",
    )
    """Folder name for display and search purposes."""

    handle: Annotated[str, AfterValidator(validate_handle)] = Field(
        ...,
        max_length=255,
        title="Handle",
        description="Unique identifier for the folder used in URLs",
    )
    """Unique identifier for the folder used in URLs."""

    folder_type: FolderType = Field(
        FolderType.CUSTOM,
        title="Folder Type",
        description="Type of the folder for behavior control",
    )
    """Type of the folder for behavior control."""

    parent: Optional[str] = Field(
        None,
        title="Parent ID",
        description="ID of the parent folder, NULL for root folders",
    )
    """ID of the parent folder, NULL for root folders."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO meta information for folder pages",
    )
    """SEO meta information for folder pages."""

    json_ld: Optional[Dict] = Field(
        default_factory=dict,
        title="JSON-LD",
        description="Manual JSON-LD override for the folder",
    )
    """Manual JSON-LD override for the folder."""

    template: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the page design template.",
    )
    """ID of the page design template."""

    exclude_from_sitemap: Optional[bool] = Field(
        default=False,
        title="Exclude From Sitemap",
        description="Whether to exclude folder from sitemap",
    )
    """Whether to exclude folder from sitemap."""

    tags: Optional[List[str]] = Field(
        default_factory=list,
        title="Tags",
        description="Tags for categorization",
    )
    """Tags for categorization."""

    language: Annotated[
        Optional[str], AfterValidator(validate_language_code)
    ] = Field(
        default="en",
        title="Language",
        description="Language code for the folder",
        max_length=2,
    )
    """Language code for the folder."""

    country_code: Annotated[
        Optional[str], AfterValidator(validate_country_code)
    ] = Field(
        default="US",
        title="Country Code",
        description="Country code for the folder",
        max_length=2,
    )
    """Country code for the folder."""

    canonical_page: Optional[str] = Field(
        default=None,
        title="Canonical Page ID",
        description="ID of the canonical page for SEO purposes. Must be a "
        "valid folder id",
    )
    """ID of the canonical page for SEO purposes. Must be a valid folder id."""


class Folder(BaseFolder, Resource):
    """
    Content folder model for hierarchical organization.

    Represents a folder with metadata, versioning, and publication status.
    """

    published: bool = Field(
        True,
        title="Published",
        description="Whether the folder is visible on the website",
    )
    """Whether the folder is visible on the website."""

    managed: bool = Field(
        False,
        title="Managed",
        description="Whether the folder is system-managed",
    )
    """Whether the folder is system-managed."""

    version: str = Field(
        ...,
        title="Version",
        description="Version of the folder for A/B testing",
    )
    """Version of the folder for A/B testing."""

    is_original_version: bool = Field(
        True,
        title="Is Original Version",
        description="Whether this is the original version of the folder. "
        "Only original versions can have children.",
    )
    """Whether this is the original version of the folder. Only original
    versions can have children."""

    is_default_version: bool = Field(
        False,
        title="Is Default Version",
        description="Whether this is the default version of the folder",
    )
    """Whether this is the default version of the folder."""

    preview_url: Optional[str] = Field(
        None,
        title="Preview URL",
        description="URL to preview the folder before publishing",
    )
    """URL to preview the folder before publishing."""

    # Metadata for field loading behavior
    _detail_only_fields: ClassVar[Set[str]] = set()
    _foreign_key_fields: ClassVar[Set[str]] = {"parent"}

    def __str__(self) -> str:
        return (
            f"Folder(id = {self.id}, name = {self.name}, "
            f"handle = {self.handle})"
        )

    def publish(self):
        """Publish the folder."""

        return cast("FolderManager", self._manager).publish(self.id)

    def unpublish(self):
        """Unpublish the folder."""

        return cast("FolderManager", self._manager).unpublish(self.id)

    def change_handle(self, new_handle: str, redirect: bool = False):
        """Change the handle of the folder.

        Args:
            new_handle (str): The new handle to set for the folder.
            redirect (bool): Whether to create a redirect from the old handle.
        Raises:
            ValueError: If the new handle is invalid.
        """
        handle = validate_handle(new_handle)
        if not handle:
            raise ValueError(f"Invalid handle: {new_handle}")

        return cast("FolderManager", self._manager).change_handle(
            self.id, new_handle=handle, redirect=redirect
        )


class FolderCreate(BaseFolder, CreateModel):
    """
    Model for creating a new folder.

    Contains all required and optional fields for folder creation.
    """

    handle: Annotated[Optional[str], AfterValidator(validate_handle)] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="Unique identifier for the folder used in URLs",
    )
    """Unique identifier for the folder used in URLs."""


class FolderUpdate(UpdateModel):
    """
    Model for updating an existing folder.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(
        None,
        max_length=255,
        title="Name",
        description="Folder name for display and search purposes",
    )
    """Folder name for display and search purposes."""

    seo_meta: Optional[SEOMeta] = Field(
        None,
        title="SEO Meta",
        description="SEO meta information for folder pages",
    )
    """SEO meta information for folder pages."""

    json_ld: Optional[Dict] = Field(
        None,
        title="JSON-LD",
        description="Manual JSON-LD override for the folder",
    )
    """Manual JSON-LD override for the folder."""

    exclude_from_sitemap: Optional[bool] = Field(
        None,
        title="Exclude From Sitemap",
        description="Whether to exclude folder from sitemap",
    )
    """Whether to exclude folder from sitemap."""

    tags: Optional[List[str]] = Field(
        None,
        title="Tags",
        description="Tags for categorization",
    )
    """Tags for categorization."""

    language: Annotated[
        Optional[str], AfterValidator(validate_language_code)
    ] = Field(
        None,
        title="Language",
        description="Language code for the folder",
        max_length=2,
    )
    """Language code for the folder."""

    country_code: Annotated[
        Optional[str], AfterValidator(validate_country_code)
    ] = Field(
        None,
        title="Country Code",
        description="Country code for the folder",
        max_length=2,
    )
    """Country code for the folder."""

    canonical_page: Optional[str] = Field(
        None,
        title="Canonical Page ID",
        description="ID of the canonical page for SEO purposes",
    )
    """ID of the canonical page for SEO purposes."""

    template: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the page design template.",
    )
    """ID of the page design template."""


__all__ = [
    "FolderType",
    "FolderReference",
    "Folder",
    "FolderCreate",
    "FolderUpdate",
]
