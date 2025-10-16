"""
Page models for the Konigle SDK.

This module provides models for general pages including creation, update,
and resource representations.
"""

from datetime import datetime
from enum import Enum
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    ClassVar,
    Dict,
    List,
    Optional,
    Set,
    Union,
    cast,
)

from pydantic import AfterValidator, BaseModel, Field

from konigle.models.base import (
    CreateModel,
    SEOMeta,
    TimestampedResource,
    UpdateModel,
)
from konigle.models.website.folder import FolderReference
from konigle.validators import validate_editorjs_content, validate_handle

from .author import Author, AuthorReference

if TYPE_CHECKING:
    from konigle.managers.website.page import PageManager


class PageType(str, Enum):
    """Page type enumeration."""

    TERMS = "terms"
    ABOUT = "about"
    PRIVACY = "privacy"
    FAQ = "faq"
    CONTACT = "contact"
    ROBOTS = "robots"
    FAVICON = "favicon"
    GENERAL = "general"
    LANDING = "landing"
    CAROUSEL = "carousel"
    SITE_VERIFICATION = "site_verification"


class DataSource(str, Enum):
    """Data source enumeration for pages."""

    DATA_TABLE = "data_table"
    SELF = "self"
    FILE = "file"


class BasePage(BaseModel):
    """
    Base class for page models with common editable fields.

    Contains fields that can be set during creation/update.
    Excludes publication status which is managed through separate API calls.
    """

    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="Name for display and search purposes",
    )
    """Name for display and search purposes."""

    handle: Optional[Annotated[str, AfterValidator(validate_handle)]] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="Page handle that is part of the URL",
    )
    """Page handle that is part of the URL."""

    title: str = Field(
        ...,
        max_length=255,
        title="Title",
        description="User facing title of the page",
    )
    """User facing title of the page."""

    subtitle: str = Field(
        default="",
        max_length=255,
        title="Subtitle",
        description="Subtitle of the page",
    )
    """Subtitle of the page."""

    page_type: PageType = Field(
        default=PageType.GENERAL,
        title="Page Type",
        description="Type of the page",
    )
    """Type of the page."""

    folder: Union[str, FolderReference] = Field(
        ...,
        title="Folder",
        description="ID of the folder this page belongs to",
    )
    """ID of the folder this page belongs to."""

    content: Annotated[
        Optional[Dict[str, Any]], AfterValidator(validate_editorjs_content)
    ] = Field(
        default_factory=dict,
        title="Content",
        description="Rich text blocks for the page in EditorJS format",
    )
    """Rich text blocks for the page in EditorJS format."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO meta information for the page",
    )
    """SEO meta information for the page."""

    json_ld: Dict[str, Any] = Field(
        default_factory=dict,
        title="JSON-LD",
        description="Manual override for JSON-LD structured data",
    )
    """Manual override for JSON-LD structured data."""

    exclude_from_sitemap: bool = Field(
        default=False,
        title="Exclude From Sitemap",
        description="Whether the page is excluded from sitemap",
    )
    """Whether the page is excluded from sitemap."""

    author: Optional[Union[str, AuthorReference, Author]] = Field(
        default=None,
        title="Author",
        description="Primary author of the page",
    )
    """Primary author of the page"""

    contributor_ids: Optional[List[str]] = Field(
        default_factory=list,
        title="Contributor IDs",
        description="List of contributor IDs for the page",
    )
    """List of contributor IDs for the page."""

    reviewer_ids: Optional[List[str]] = Field(
        default_factory=list,
        title="Reviewer IDs",
        description="List of reviewer IDs for the page",
    )
    """List of reviewer IDs for the page."""

    show_author: bool = Field(
        default=True,
        title="Show Author",
        description="Whether to show contributors and reviewers on the page",
    )
    """Whether to show contributors and reviewers on the page."""

    template: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the page design template.",
    )
    """ID of the page design template."""


class Page(BasePage, TimestampedResource):
    """
    General purpose page resource model.

    Represents a page with content, type, and publication status.
    """

    contributors: List[Union[str, AuthorReference, Author]] = Field(
        default_factory=list,
        title="Contributors",
        description="List of contributors for the page",
    )
    """List of contributors for the page."""

    reviewers: List[Union[str, AuthorReference, Author]] = Field(
        default_factory=list,
        title="Reviewers",
        description="List of reviewers for the page",
    )
    """List of reviewers for the page."""

    published: bool = Field(
        default=False,
        title="Published",
        description="Whether the page is published",
    )
    """Whether the page is published."""

    published_at: Optional[datetime] = Field(
        None,
        title="Published At",
        description="Date and time when the page was published",
    )
    """Date and time when the page was published."""

    pathname: Optional[str] = Field(
        default=None,
        title="Pathname",
        description="Full pathname of the page",
    )
    """Full pathname of the page"""

    preview_url: Optional[str] = Field(
        default=None,
        title="Preview URL",
        description="Preview URL of the page",
    )
    """Preview URL of the page"""

    url: Optional[str] = Field(
        default=None,
        title="URL",
        description="Public URL of the page",
    )
    """Public URL of the page. Results in 404 if the page is not published."""

    # Metadata for field loading behavior
    _detail_only_fields: ClassVar[Set[str]] = {
        "content",
        "contributors",
        "reviewers",
    }
    _foreign_key_fields: ClassVar[Set[str]] = {"author"}

    def __str__(self) -> str:
        return (
            f"Page(id = {self.id}, title = {self.title}, "
            f"handle = {self.handle})"
        )

    def publish(self):
        """Publish the page."""
        return cast("PageManager", self._manager).publish(self.id)

    def unpublish(self):
        """Unpublish the page."""
        return cast("PageManager", self._manager).unpublish(self.id)

    def change_handle(self, new_handle: str, redirect: bool = False):
        """Change the handle of the page.

        Args:
            new_handle (str): The new handle to set for the page.
            redirect (bool): Whether to create a redirect from the old handle.
        Raises:
            ValueError: If the new handle is invalid.
        """
        handle = validate_handle(new_handle)
        if not handle:
            raise ValueError(f"Invalid handle: {new_handle}")
        return cast("PageManager", self._manager).change_handle(
            self.id, new_handle=handle, redirect=redirect
        )


class PageCreate(BasePage, CreateModel):
    """
    Model for creating a new page.

    Contains all required and optional fields for page creation.
    """

    pass


class PageUpdate(UpdateModel):
    """
    Model for updating an existing page.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(
        None,
        max_length=255,
        title="Name",
        description="Name for display and search purposes",
    )
    """Name for display and search purposes."""

    title: Optional[str] = Field(
        None,
        max_length=255,
        title="Title",
        description="User facing title of the page",
    )
    """User facing title of the page."""

    subtitle: Optional[str] = Field(
        None,
        max_length=255,
        title="Subtitle",
        description="Subtitle of the page",
    )
    """Subtitle of the page."""

    content: Optional[Dict[str, Any]] = Field(
        None,
        title="Content",
        description="Rich text blocks for the page in EditorJS format",
    )
    """Rich text blocks for the page in EditorJS format."""

    seo_meta: Optional[SEOMeta] = Field(
        None,
        title="SEO Meta",
        description="SEO meta information for the page",
    )
    """SEO meta information for the page."""

    json_ld: Optional[Dict[str, Any]] = Field(
        None,
        title="JSON-LD",
        description="Manual override for JSON-LD structured data",
    )
    """Manual override for JSON-LD structured data."""

    exclude_from_sitemap: Optional[bool] = Field(
        None,
        title="Exclude From Sitemap",
        description="Whether the page is excluded from sitemap",
    )
    """Whether the page is excluded from sitemap."""

    show_author: Optional[bool] = Field(
        None,
        title="Show Author",
        description="Whether to show contributors and reviewers on the page",
    )
    """Whether to show contributors and reviewers on the page."""

    author: Optional[Union[str, AuthorReference, Author]] = Field(
        None,
        title="Author",
        description="Primary author of the page",
    )
    """Primary author of the page."""

    contributor_ids: Optional[List[str]] = Field(
        None,
        title="Contributor IDs",
        description="List of contributor IDs for the page",
    )
    """List of contributor IDs for the page."""

    reviewer_ids: Optional[List[str]] = Field(
        None,
        title="Reviewer IDs",
        description="List of reviewer IDs for the page",
    )
    """List of reviewer IDs for the page."""

    template: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the page design template.",
    )
    """ID of the page design template."""


__all__ = [
    "Page",
    "PageCreate",
    "PageUpdate",
]
