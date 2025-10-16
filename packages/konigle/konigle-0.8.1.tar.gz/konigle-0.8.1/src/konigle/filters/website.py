from typing import Literal, Optional

from pydantic import Field

from .base import BaseFilters


class AuthorFilters(BaseFilters):
    """Filters for author resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches name and handle fields"""

    handle: Optional[str] = Field(default=None)
    """Filter by author handle"""

    ordering: Optional[
        Literal[
            "name",
            "-name",
            "handle",
            "-handle",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(default=None)
    """Ordering options for author results"""


class FolderFilters(BaseFilters):
    """Filters for folder resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches name and handle fields"""

    folder_type: Optional[str] = Field(default=None)
    """Filter by folder type"""

    parent: Optional[str] = Field(default=None)
    """Filter by parent folder ID"""

    ordering: Optional[
        Literal[
            "name",
            "-name",
            "position",
            "-position",
        ]
    ] = Field(default=None)
    """Ordering options for folder results"""


class PageFilters(BaseFilters):
    """Filters for page resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches title and name fields"""

    page_type: Optional[str] = Field(default=None)
    """Filter by page type"""

    folder: Optional[str] = Field(default=None)
    """Filter by folder ID"""

    published: Optional[bool] = Field(default=None)
    """Filter by publication status"""

    ordering: Optional[
        Literal[
            "title",
            "-title",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(default=None)
    """Ordering options for page results"""


class BlogFilters(BaseFilters):
    """Filters for blog post resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches title and name fields"""

    folder: Optional[str] = Field(default=None)
    """Filter by folder ID"""

    published: Optional[bool] = Field(default=None)
    """Filter by publication status"""

    handle: Optional[str] = Field(default=None)
    """Filter by blog post handle"""

    ordering: Optional[
        Literal[
            "title",
            "-title",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
            "published_at",
            "-published_at",
        ]
    ] = Field(default=None)
    """Ordering options for blog results"""


class GlossaryTermFilters(BaseFilters):
    """Filters for glossary term resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches title and name fields"""

    published: Optional[bool] = Field(default=None)
    """Filter by publication status"""

    ordering: Optional[
        Literal[
            "title",
            "-title",
            "name",
            "-name",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(default=None)
    """Ordering options for glossary term results"""


class ComponentFilters(BaseFilters):
    """Filters for component resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches name and description fields"""

    type: Optional[str] = Field(default=None)
    """Filter by component type. use comma to separate multiple types"""

    ordering: Optional[
        Literal[
            "name",
            "-name",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(default=None)
    """Ordering options for component results"""


class TemplateFilters(BaseFilters):
    """Filters for template resources."""

    q: Optional[str] = Field(default=None)
    """Search query that matches name and handle fields"""

    handle: Optional[str] = Field(default=None)
    """Filter by template handle"""

    is_base: Optional[bool] = Field(default=None)
    """Filter by base template status"""

    base: Optional[str] = Field(default=None)
    """Filter by base template ID"""

    ordering: Optional[
        Literal[
            "name",
            "-name",
            "handle",
            "-handle",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(default=None)
    """Ordering options for site template results"""


__all__ = [
    "AuthorFilters",
    "FolderFilters",
    "PageFilters",
    "BlogFilters",
    "GlossaryTermFilters",
    "ComponentFilters",
    "TemplateFilters",
]
