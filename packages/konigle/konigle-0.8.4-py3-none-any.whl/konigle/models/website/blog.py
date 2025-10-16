"""
Blog models for the Konigle SDK.

This module provides models for blog posts including creation, update,
and resource representations.
"""

from datetime import datetime
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
from konigle.validators import validate_editorjs_content, validate_handle

from .author import Author, AuthorReference
from .folder import FolderReference

if TYPE_CHECKING:
    from konigle.managers.website.blog import BlogManager


class BaseBlog(BaseModel):
    """
    Base class for blog models with common editable fields.

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

    handle: Annotated[str, AfterValidator(validate_handle)] = Field(
        ...,
        max_length=255,
        title="Handle",
        description="Blog handle that is part of the URL",
    )
    """Blog handle that is part of the URL."""

    title: str = Field(
        ...,
        max_length=255,
        title="Title",
        description="User facing title of the blog post",
    )
    """User facing title of the blog post."""

    subtitle: str = Field(
        default="",
        max_length=255,
        title="Subtitle",
        description="Subtitle of the blog post",
    )
    """Subtitle of the blog post."""

    summary: str = Field(
        default="",
        title="Summary",
        description="Blog summary - used for SEO meta description",
    )
    """Blog summary - used for SEO meta description if not provided."""

    content: Annotated[
        Optional[Dict[str, Any]], AfterValidator(validate_editorjs_content)
    ] = Field(
        default=None,
        title="Content",
        description="Rich text blocks for the blog post in EditorJS format",
    )
    """Rich text blocks for the blog post in EditorJS format."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO meta information for the blog post",
    )
    """SEO meta information for the blog post."""

    json_ld: Dict[str, Any] = Field(
        default_factory=dict,
        title="JSON-LD",
        description="Manual override for JSON-LD structured data",
    )
    """Manual override for JSON-LD structured data."""

    exclude_from_sitemap: bool = Field(
        default=False,
        title="Exclude From Sitemap",
        description="Whether the blog post is excluded from sitemap",
    )
    """Whether the blog post is excluded from sitemap."""

    folder: Optional[Union[str, FolderReference]] = Field(
        default=None,
        title="Folder ID",
        description="ID of the folder where the blog post is stored",
    )
    """ID of the folder where the blog post is stored."""

    author: Optional[Union[str, AuthorReference, Author]] = Field(
        default=None,
        title="Author",
        description="Primary author of the blog post",
    )
    """Primary author of the blog post."""

    show_author: bool = Field(
        default=True,
        title="Show Author",
        description="Whether to show contributors and reviewers on the page",
    )
    """Whether to show contributors and reviewers on the page."""

    contributor_ids: List[str] = Field(
        default_factory=list,
        title="Contributor IDs",
        description="List of contributor IDs for the blog post",
    )
    """List of contributor IDs for the blog post."""

    reviewer_ids: List[str] = Field(
        default_factory=list,
        title="Reviewer IDs",
        description="List of reviewer IDs for the blog post",
    )
    """List of reviewer IDs for the blog post."""

    template: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the blog page design template.",
    )
    """ID of the blog page design template. If template is set, default rich
    text of the blog post will be ignored. The template must render the blog
    or use dynamic component in the template"""


class Blog(BaseBlog, TimestampedResource):
    """
    Blog post resource model.

    Represents a blog post with content, SEO metadata, and publication status.
    """

    contributors: List[Union[str, AuthorReference, Author]] = Field(
        default_factory=list,
        title="Contributors",
        description="List of contributors for the blog post",
    )
    """List of contributors for the blog post."""

    reviewers: List[Union[str, AuthorReference, Author]] = Field(
        default_factory=list,
        title="Reviewers",
        description="List of reviewers for the blog post",
    )
    """List of reviewers for the blog post."""

    published: bool = Field(
        default=False,
        title="Published",
        description="Whether the blog post is published",
    )
    """Whether the blog post is published."""

    published_at: Optional[datetime] = Field(
        None,
        title="Published At",
        description="Date and time when the blog post was published",
    )
    """Date and time when the blog post was published."""

    pathname: Optional[str] = Field(
        default=None,
        title="Pathname",
        description="Full pathname of the blog post",
    )
    """Full pathname of the blog post."""

    preview_url: Optional[str] = Field(
        default=None,
        title="Preview URL",
        description="Preview URL of the blog post",
    )
    """Preview URL of the blog post."""

    url: Optional[str] = Field(
        default=None,
        title="URL",
        description="Public URL of the blog post",
    )
    """Public URL of the blog post. Results in 404 if the blog is not 
    published."""

    # Metadata for field loading behavior
    _detail_only_fields: ClassVar[Set[str]] = {
        "content",
        "contributors",
        "reviewers",
    }
    _foreign_key_fields: ClassVar[Set[str]] = {
        "author",
        "folder",
    }

    def __str__(self) -> str:
        return (
            f"Blog(id = {self.id}, title = {self.title}, "
            f"handle = {self.handle}, published = {self.published})"
        )

    def publish(self):
        """Publish the blog post."""

        return cast("BlogManager", self._manager).publish(self.id)

    def unpublish(self):
        """Unpublish the blog post."""

        return cast("BlogManager", self._manager).unpublish(self.id)

    def change_handle(self, new_handle: str, redirect: bool = False):
        """Change the handle of the blog post.

        Args:
            new_handle (str): The new handle to set for the blog post.
            redirect (bool): Whether to create a redirect from the old handle.
        Raises:
            ValueError: If the new handle is invalid.
        """
        handle = validate_handle(new_handle)
        if not handle:
            raise ValueError(f"Invalid handle: {new_handle}")

        return cast("BlogManager", self._manager).change_handle(
            self.id, new_handle=handle, redirect=redirect
        )


class BlogCreate(BaseBlog, CreateModel):
    """
    Model for creating a new blog post.

    Contains all required and optional fields for blog post creation.
    """

    handle: Annotated[Optional[str], AfterValidator(validate_handle)] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="Blog handle that is part of the URL",
    )
    """Blog handle that is part of the URL."""


class BlogUpdate(UpdateModel):
    """
    Model for updating an existing blog post.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Name",
        description="Name for display and search purposes",
    )
    """Name for display and search purposes."""

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Title",
        description="User facing title of the blog post",
    )
    """User facing title of the blog post."""

    subtitle: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Subtitle",
        description="Subtitle of the blog post",
    )
    """Subtitle of the blog post."""

    summary: Optional[str] = Field(
        default=None,
        title="Summary",
        description="Blog summary - used for SEO meta description",
    )
    """Blog summary - used for SEO meta description."""

    content: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Content",
        description="Rich text blocks for the blog post in EditorJS format",
    )
    """Rich text blocks for the blog post in EditorJS format."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO meta information for the blog post",
    )
    """SEO meta information for the blog post."""

    json_ld: Optional[Dict[str, Any]] = Field(
        default=None,
        title="JSON-LD",
        description="Manual override for JSON-LD structured data",
    )
    """Manual override for JSON-LD structured data."""

    exclude_from_sitemap: Optional[bool] = Field(
        default=None,
        title="Exclude From Sitemap",
        description="Whether the blog post is excluded from sitemap",
    )
    """Whether the blog post is excluded from sitemap."""

    show_author: Optional[bool] = Field(
        default=None,
        title="Show Author",
        description="Whether to show contributors and reviewers on the page",
    )
    """Whether to show contributors and reviewers on the page."""

    contributor_ids: Optional[List[str]] = Field(
        default_factory=list,
        title="Contributor IDs",
        description="List of contributor IDs for the page",
    )
    """List of contributor IDs for the page."""

    reviewer_ids: Optional[List[str]] = Field(
        default_factory=list,
        title="Reviewer IDs",
        description="List of reviewer IDs for the blog post",
    )
    """List of reviewer IDs for the blog post."""

    template: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the blog page design template.",
    )
    """ID of the blog page design template."""


__all__ = [
    "Blog",
    "BlogCreate",
    "BlogUpdate",
]
