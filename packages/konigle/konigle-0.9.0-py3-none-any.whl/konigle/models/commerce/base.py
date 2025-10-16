"""
Base models and mixins for commerce resources.

This module provides the foundation for all commerce resource models,
including common timestamp patterns and shared field definitions.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class IDMixin(BaseModel):
    """
    Mixin for models that include an ID field.

    Provides a common ID field that many resources include.
    """

    uid: str = Field(
        ..., title="ID", description="Unique identifier of the resource."
    )
    """Unique identifier of the resource."""

    @property
    def id(self) -> str:
        """Alias for uid to provide uniform interface as with other models."""
        return self.uid


class TimestampedResource(BaseModel):
    """
    Timestamped resource model for commerce resources.

    Provides the djshopify timestamp fields that are common
    across products, variants, and images.
    """

    djshopify_created: datetime = Field(
        ...,
        title="Created At",
        description="Timestamp when the resource was created.",
    )
    """Created timestamp of the resource."""

    djshopify_updated: datetime = Field(
        ...,
        title="Updated At",
        description="Timestamp when the resource was last updated in the source system.",
    )
    """Last updated timestamp of the resource."""
