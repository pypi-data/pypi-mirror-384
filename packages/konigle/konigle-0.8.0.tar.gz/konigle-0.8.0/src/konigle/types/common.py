"""
Common type definitions for the Konigle SDK.

This module defines common types, type aliases, and generic types
used throughout the SDK.
"""

import io
from datetime import datetime
from typing import (
    Any,
    BinaryIO,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field

# Type aliases for common data structures
JSONDict = Dict[str, Any]
Headers = Dict[str, str]
QueryParams = Dict[str, Union[str, int, float, bool]]

# File input types. The file input can be a file path (str),
# raw bytes, a binary file-like object, or a tuple of
# (file-like object, filename).
FileInputT = Union[
    str,
    bytes,
    BinaryIO,
    io.BytesIO,
    Tuple[Union[bytes, io.BytesIO, BinaryIO], str],
]

# Generic type variable for resources
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standardized pagination response wrapper.

    This generic class wraps paginated API responses with metadata
    about the pagination state and navigation.
    """

    payload: List[T] = Field(
        ..., title="Payload", description="List of resources in this page."
    )
    """List of resources in this page."""

    count: int = Field(
        ..., ge=0, title="Count", description="Total number of resources."
    )
    """Total number of resources."""

    next: Optional[str] = Field(
        None, title="Next", description="URL for next page."
    )
    """URL for next page."""

    previous: Optional[str] = Field(
        None, title="Previous", description="URL for previous page."
    )
    """URL for previous page."""

    page_size: int = Field(
        ..., gt=0, title="Page Size", description="Number of items per page."
    )
    """Number of items per page."""

    current_page: int = Field(
        ..., ge=1, title="Current Page", description="Current page number."
    )
    """Current page number."""

    num_pages: int = Field(
        ...,
        ge=0,
        title="Number of Pages",
        description="Total number of pages.",
    )
    """Total number of pages."""

    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.next is not None

    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.previous is not None

    @property
    def is_first_page(self) -> bool:
        """Check if this is the first page."""
        return self.current_page == 1

    @property
    def is_last_page(self) -> bool:
        """Check if this is the last page."""
        return self.current_page == self.num_pages


class PaginationParams(BaseModel):
    """
    Pagination parameter validation and defaults.

    Used to validate and normalize pagination parameters
    across all list operations.
    """

    page: int = Field(1, ge=1, title="Page", description="Page number.")
    """Page number."""

    page_size: int = Field(
        20, ge=1, le=200, title="Page Size", description="Items per page."
    )
    """Items per page."""


class TimestampMixin(BaseModel):
    """
    Mixin for models that include timestamp fields.

    Provides common timestamp fields that many resources include.
    """

    created_at: datetime = Field(
        ..., title="Created At", description="Creation timestamp."
    )
    """Creation timestamp."""

    updated_at: datetime = Field(
        ..., title="Updated At", description="Last update timestamp."
    )
    """Last update timestamp."""


class IDMixin(BaseModel):
    """
    Mixin for models that include an ID field.

    Provides the standard ID field that most resources include.
    Default type is string to handle UUIDs and large integers from API.
    Resource models can override the type if needed.
    """

    id: str = Field(..., title="ID", description="Unique identifier.")
    """Unique identifier."""
