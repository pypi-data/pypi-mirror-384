"""
Commerce filter models for the Konigle SDK.

This module provides type-safe filter models for commerce resources
including products, product variants, and product images.
"""

from typing import Literal, Optional

from pydantic import Field

from konigle.filters.base import BaseFilters


class ProductFilters(BaseFilters):
    """Type-safe filters for product queries."""

    q: Optional[str] = Field(
        None,
        title="Search Query",
        description="Search in title, handle, and tags.",
    )
    """Search in title, handle, and tags."""

    status: Optional[str] = Field(
        None,
        title="Status",
        description="Filter by product status (active, archived, draft).",
    )
    """Filter by product status (active, archived, draft)."""

    product_type: Optional[str] = Field(
        None,
        title="Product Type",
        description="Filter by product type.",
    )
    """Filter by product type."""

    vendor: Optional[str] = Field(
        None,
        title="Vendor",
        description="Filter by vendor name.",
    )
    """Filter by vendor name."""

    ordering: Optional[
        Literal[
            "title",
            "-title",
            "status",
            "-status",
            "vendor",
            "-vendor",
            "product_type",
            "-product_type",
        ]
    ] = Field(
        None,
        title="Ordering",
        description="Sort order for results.",
    )
    """Sort order for results."""


class ProductVariantFilters(BaseFilters):
    """Type-safe filters for product variant queries."""

    q: Optional[str] = Field(
        None,
        title="Search Query",
        description="Search in title, sku, and barcode.",
    )
    """Search in title, sku, and barcode."""

    product_id: Optional[str] = Field(
        None,
        title="Product ID",
        description="Filter by parent product ID.",
    )
    """Filter by parent product ID."""

    ordering: Optional[
        Literal[
            "title",
            "-title",
            "sku",
            "-sku",
            "position",
            "-position",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(
        None,
        title="Ordering",
        description="Sort order for results.",
    )
    """Sort order for results."""


class ProductImageFilters(BaseFilters):
    """Type-safe filters for product image queries."""

    product_id: Optional[str] = Field(
        None,
        title="Product ID",
        description="Filter by parent product ID.",
    )
    """Filter by parent product ID."""

    ordering: Optional[
        Literal[
            "position",
            "-position",
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
        ]
    ] = Field(
        None,
        title="Ordering",
        description="Sort order for results.",
    )
    """Sort order for results."""


__all__ = [
    "ProductFilters",
    "ProductVariantFilters",
    "ProductImageFilters",
]
