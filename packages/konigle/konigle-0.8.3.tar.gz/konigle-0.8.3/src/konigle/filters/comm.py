"""
Communication filter models for the Konigle SDK.

This module provides type-safe filter models for communication resources
including email accounts, channels, and identities.
"""

from typing import Literal, Optional

from pydantic import Field

from konigle.filters.base import BaseFilters

__all__ = [
    "EmailAccountFilters",
    "EmailChannelFilters",
    "EmailIdentityFilters",
    "EmailTemplateFilters",
]


class EmailAccountFilters(BaseFilters):
    """Type-safe filters for email account queries.

    Currently there is only one email account per website, so filters
    are irrelevant. This class is provided for consistency.
    """


class EmailChannelFilters(BaseFilters):
    """Type-safe filters for email channel queries."""

    q: Optional[str] = Field(
        default=None,
        title="Search Query",
        description="Search in channel code and type.",
    )
    """Search in channel code and type."""

    channel_type: Optional[str] = Field(
        default=None,
        title="Channel Type",
        description="Filter by channel type (transactional, marketing, broadcast).",
    )
    """Filter by channel type (transactional, marketing, broadcast)."""

    status: Optional[str] = Field(
        default=None,
        title="Status",
        description="Filter by channel status (active, suspended, pending).",
    )
    """Filter by channel status (active, suspended, pending)."""

    ordering: Optional[
        Literal[
            "code",
            "-code",
            "channel_type",
            "-channel_type",
            "status",
            "-status",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(
        default=None,
        title="Ordering",
        description="Field to order results by. Prefix with '-' for descending order.",
    )
    """Field to order results by. Prefix with '-' for descending order."""


class EmailIdentityFilters(BaseFilters):
    """Type-safe filters for email identity queries."""

    q: Optional[str] = Field(
        default=None,
        title="Search Query",
        description="Search in identity value.",
    )
    """Search in identity value."""

    identity_type: Optional[Literal["domain", "email"]] = Field(
        default=None,
        title="Identity Type",
        description="Filter by identity type (domain, email).",
    )
    """Filter by identity type (domain, email)."""

    ordering: Optional[
        Literal[
            "identity_value",
            "-identity_value",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(
        default=None,
        title="Ordering",
        description="Field to order results by. Prefix with '-' for "
        "descending order.",
    )
    """Field to order results by. Prefix with '-' for descending order."""


class EmailTemplateFilters(BaseFilters):
    """Type-safe filters for email template queries."""

    q: Optional[str] = Field(
        default=None,
        title="Search Query",
        description="Search in template name, code, and tags.",
    )
    """Search in template name, code, and tags."""

    tags: Optional[str] = Field(
        default=None,
        title="Tags",
        description="Filter by tags (comma-separated for multiple tags).",
    )
    """Filter by tags (comma-separated for multiple tags)."""

    ordering: Optional[
        Literal[
            "name",
            "-name",
            "code",
            "-code",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(
        default=None,
        title="Ordering",
        description="Field to order results by. Prefix with '-' for "
        "descending order.",
    )
    """Field to order results by. Prefix with '-' for descending order."""
