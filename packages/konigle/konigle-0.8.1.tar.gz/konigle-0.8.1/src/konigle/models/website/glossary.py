"""
Glossary term models for the Konigle SDK.

This module provides models for glossary terms including creation, update,
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

if TYPE_CHECKING:
    from konigle.managers.website.glossary import GlossaryTermManager


class BaseGlossaryTerm(BaseModel):
    """
    Base class for glossary term models with common editable fields.

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
        description="Term handle that is part of the URL",
    )
    """Term handle that is part of the URL."""

    title: str = Field(
        ...,
        max_length=255,
        title="Title",
        description="User facing title of the glossary term",
    )
    """User facing title of the glossary term."""

    subtitle: str = Field(
        default="",
        max_length=255,
        title="Subtitle",
        description="Subtitle of the glossary term",
    )
    """Subtitle of the glossary term."""

    summary: str = Field(
        default="",
        title="Summary",
        description="Term summary - used for SEO meta description",
    )
    """Term summary - used for SEO meta description if not provided."""

    content: Annotated[
        Optional[Dict[str, Any]], AfterValidator(validate_editorjs_content)
    ] = Field(
        default_factory=dict,
        title="Content",
        description="Rich text blocks for the term in EditorJS format",
    )
    """Rich text blocks for the term in EditorJS format."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO meta information for the term",
    )
    """SEO meta information for the term."""

    json_ld: Dict[str, Any] = Field(
        default_factory=dict,
        title="JSON-LD",
        description="Manual override for JSON-LD structured data",
    )
    """Manual override for JSON-LD structured data."""

    exclude_from_sitemap: bool = Field(
        default=False,
        title="Exclude From Sitemap",
        description="Whether the term is excluded from sitemap",
    )
    """Whether the term is excluded from sitemap."""

    author: Optional[Union[str, AuthorReference, Author]] = Field(
        default=None,
        title="Author",
        description="Primary author of the term",
    )
    """Primary author of the term."""

    show_author: bool = Field(
        default=True,
        title="Show Author",
        description="Whether to show contributors and reviewers on the page",
    )
    """Whether to show contributors and reviewers on the page."""

    contributor_ids: List[str] = Field(
        default_factory=list,
        title="Contributor IDs",
        description="List of contributor IDs for the term",
    )
    """List of contributor IDs for the term."""

    reviewer_ids: List[str] = Field(
        default_factory=list,
        title="Reviewer IDs",
        description="List of reviewer IDs for the term",
    )
    """List of reviewer IDs for the term."""


class GlossaryTerm(BaseGlossaryTerm, TimestampedResource):
    """
    Store glossary term resource model.

    Represents a glossary term with content, hierarchy, and publication status.
    """

    contributors: List[Union[str, AuthorReference, Author]] = Field(
        default_factory=list,
        title="Contributors",
        description="List of contributors for the term",
    )
    """List of contributors for the term."""

    reviewers: List[Union[str, AuthorReference, Author]] = Field(
        default_factory=list,
        title="Reviewers",
        description="List of reviewers for the term",
    )
    """List of reviewers for the term."""

    published: bool = Field(
        default=False,
        title="Published",
        description="Whether the term is published",
    )
    """Whether the term is published."""

    published_at: Optional[datetime] = Field(
        None,
        title="Published At",
        description="Date and time when the term was published",
    )
    """Date and time when the term was published."""

    # Metadata for field loading behavior
    _detail_only_fields: ClassVar[Set[str]] = {
        "content",
        "contributors",
        "reviewers",
    }
    _foreign_key_fields: ClassVar[Set[str]] = {
        "author",
    }

    def __str__(self) -> str:
        return f"GlossaryTerm(id = {self.id}, name = {self.name}, title = {self.title})"

    def publish(self):
        """Publish the glossary term."""

        return cast("GlossaryTermManager", self._manager).publish(self.id)

    def unpublish(self):
        """Unpublish the glossary term."""

        return cast("GlossaryTermManager", self._manager).unpublish(self.id)

    def change_handle(self, new_handle: str, redirect: bool = False):
        """Change the handle of the glossary term.

        Args:
            new_handle (str): The new handle to set for the term.
            redirect (bool): Whether to create a redirect from the old handle.
        Raises:
            ValueError: If the new handle is invalid.
        """
        handle = validate_handle(new_handle)
        if not handle:
            raise ValueError(f"Invalid handle: {new_handle}")

        return cast("GlossaryTermManager", self._manager).change_handle(
            self.id, new_handle=handle, redirect=redirect
        )


class GlossaryTermCreate(BaseGlossaryTerm, CreateModel):
    """
    Model for creating a new glossary term.

    Contains all required and optional fields for term creation.
    """


class GlossaryTermUpdate(UpdateModel):
    """
    Model for updating an existing glossary term.

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
        description="User facing title of the glossary term",
    )
    """User facing title of the glossary term."""

    subtitle: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Subtitle",
        description="Subtitle of the glossary term",
    )
    """Subtitle of the glossary term."""

    summary: Optional[str] = Field(
        default=None,
        title="Summary",
        description="Term summary - used for SEO meta description",
    )
    """Term summary - used for SEO meta description."""

    content: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Content",
        description="Rich text blocks for the term in EditorJS format",
    )
    """Rich text blocks for the term in EditorJS format."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO meta information for the term",
    )
    """SEO meta information for the term."""

    json_ld: Optional[Dict[str, Any]] = Field(
        default=None,
        title="JSON-LD",
        description="Manual override for JSON-LD structured data",
    )
    """Manual override for JSON-LD structured data."""

    exclude_from_sitemap: Optional[bool] = Field(
        default=None,
        title="Exclude From Sitemap",
        description="Whether the term is excluded from sitemap",
    )
    """Whether the term is excluded from sitemap."""

    show_author: Optional[bool] = Field(
        default=None,
        title="Show Author",
        description="Whether to show contributors and reviewers on the page",
    )
    """Whether to show contributors and reviewers on the page."""

    author: Optional[Union[str, AuthorReference, Author]] = Field(
        default=None,
        title="Author",
        description="Primary author of the term",
    )
    """Primary author of the term."""

    contributor_ids: Optional[List[str]] = Field(
        default=None,
        title="Contributor IDs",
        description="List of contributor IDs for the term",
    )
    """List of contributor IDs for the term."""

    reviewer_ids: Optional[List[str]] = Field(
        default=None,
        title="Reviewer IDs",
        description="List of reviewer IDs for the term",
    )
    """List of reviewer IDs for the term."""


__all__ = [
    "GlossaryTerm",
    "GlossaryTermCreate",
    "GlossaryTermUpdate",
]
