"""
Product models for the Konigle SDK.

This module provides Pydantic models for product resources including
creation, update, and response models with comprehensive validation.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated, Any, ClassVar, Dict, List, Optional, Set

from pydantic import AfterValidator, BaseModel, Field

from konigle.models.base import BaseResource, CreateModel, SEOMeta, UpdateModel
from konigle.validators import validate_editorjs_content, validate_price

from .base import IDMixin, TimestampedResource
from .product_variant import ProductVariantCreate, ProductVariantUpdate


class ProductOption(BaseModel):
    """
    Model representing a product option.

    Each option can have multiple values, such as size or color.
    """

    name: str = Field(
        ...,
        max_length=255,
        title="Option Name",
        description="Name of the product option (e.g., Size, Color).",
    )
    """Name of the product option (e.g., Size, Color)."""

    values: List[str] = Field(
        ...,
        title="Option Values",
        description="List of possible values for this option.",
    )
    """List of possible values for this option."""


class ProductStatus(str, Enum):
    """Product publication status."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    DRAFT = "draft"


class ProductBase(BaseModel):
    """
    Base product model with truly shared fields.

    Contains only fields that have the same optionality and validation
    requirements in both creation and response contexts.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        title="Title",
        description="Product title or name.",
    )
    """Product title or name."""

    content: Annotated[
        Optional[Dict[str, Any]], AfterValidator(validate_editorjs_content)
    ] = Field(
        default_factory=dict,
        title="Content",
        description="Body content blocks in EditorJS JSON format.",
    )
    """Body content blocks in EditorJS JSON format."""

    options: Optional[List[ProductOption]] = Field(
        default_factory=list,
        title="Options",
        description="List of product option names.",
    )
    """List of product option names."""


class ProductCreate(ProductBase, CreateModel):
    """
    Model for creating a new product.

    Includes all fields required for product creation plus
    optional file upload for the main product image.
    """

    handle: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="URL-friendly product identifier.",
    )
    """URL-friendly product identifier. Will be auto-generated from title 
    if not provided."""

    status: ProductStatus = Field(
        default=ProductStatus.DRAFT,
        title="Status",
        description="Product publication status.",
    )
    """Product publication status."""

    product_type: Optional[str] = Field(
        default="",
        max_length=255,
        title="Product Type",
        description="Product category or type.",
    )
    """Product category or type."""

    vendor: Optional[str] = Field(
        default="",
        max_length=255,
        title="Vendor",
        description="Product vendor or manufacturer.",
    )
    """Product vendor or manufacturer."""

    tags: Optional[str] = Field(
        default="",
        title="Tags",
        description="Comma-separated list of product tags.",
    )
    """Comma-separated list of product tags."""

    price: Optional[Annotated[Decimal, AfterValidator(validate_price)]] = (
        Field(
            default=None,
            gt=0,
            max_digits=19,
            decimal_places=2,
            title="Price",
            description="Product price for single variant products.",
        )
    )
    """Product price for single variant products."""

    original_price: Optional[
        Annotated[Decimal, AfterValidator(validate_price)]
    ] = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Original Price",
        description="Original price before discount.",
    )
    """Original price before discount."""

    currency: Optional[str] = Field(
        default=None,
        max_length=3,
        title="Currency",
        description="Currency code for price fields.",
    )
    """Currency code for price fields."""

    seo_meta: Optional[SEOMeta] = Field(
        default_factory=lambda: SEOMeta(),
        title="SEO Meta",
        description="SEO metadata including title, description, keywords.",
    )
    """SEO metadata including title, description, keywords."""

    variants: Optional[List[ProductVariantCreate]] = Field(
        default_factory=list,
        title="Variants",
        description="List of product variants to create with the product.",
    )
    """List of product variants to create with the product. The options must
    match the product options defined above."""


class Product(ProductBase, TimestampedResource, IDMixin, BaseResource):
    """
    Complete product resource model.

    Represents a product from the API with all fields including
    computed values, relationships, and Active Record capabilities.
    """

    handle: str = Field(
        ...,
        title="Handle",
        description="URL-friendly product identifier.",
    )
    """URL-friendly product identifier."""

    status: ProductStatus = Field(
        ...,
        title="Status",
        description="Product publication status.",
    )
    """Product publication status."""

    product_type: str = Field(
        ...,
        title="Product Type",
        description="Product category or type.",
    )
    """Product category or type."""

    vendor: str = Field(
        ...,
        title="Vendor",
        description="Product vendor or manufacturer.",
    )
    """Product vendor or manufacturer."""

    tags: str = Field(
        ...,
        title="Tags",
        description="Comma-separated list of product tags.",
    )
    """Comma-separated list of product tags."""

    price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Price",
        description="Product price for single variant products.",
    )
    """Product price for single variant products."""

    original_price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Original Price",
        description="Original price before discount.",
    )
    """Original price before discount."""

    currency: Optional[str] = Field(
        default=None,
        max_length=3,
        title="Currency",
        description="Currency code for price fields.",
    )
    """Currency code for price fields."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO metadata including title, description, keywords.",
    )
    """SEO metadata including title, description, keywords."""

    djcom_tags: List[str] = Field(
        default_factory=list,
        title="Parsed Tags",
        description="List of tags parsed from tags field.",
    )
    """List of tags parsed from tags field."""

    has_variants: bool = Field(
        ...,
        title="Has Variants",
        description="Whether product has multiple variants.",
    )
    """Whether product has multiple variants."""

    published_at: Optional[datetime] = Field(
        default=None,
        title="Published At",
        description="Product publication timestamp.",
    )
    """Product publication timestamp."""

    _detail_only_fields: ClassVar[Set[str]] = {"seo_meta", "content"}

    def __str__(self) -> str:
        return (
            f"Product(id = {self.id}, title={self.title}, "
            f"handle={self.handle})"
        )


class ProductUpdate(UpdateModel):
    """
    Model for updating an existing product.

    All fields are optional for partial updates.
    Supports updating any product field including status and image.
    """

    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=255,
        title="Title",
        description="Product title or name.",
    )
    """Product title or name."""

    handle: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="URL-friendly product identifier.",
    )
    """URL-friendly product identifier."""

    content: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Content",
        description="Body content blocks in EditrJS JSON format.",
    )
    """Body content blocks in EditorJS JSON format."""

    product_type: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Product Type",
        description="Product category or type.",
    )
    """Product category or type."""

    status: Optional[ProductStatus] = Field(
        default=None,
        title="Status",
        description="Product publication status.",
    )
    """Product publication status."""

    vendor: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Vendor",
        description="Product vendor or manufacturer.",
    )
    """Product vendor or manufacturer."""

    tags: Optional[str] = Field(
        default=None,
        title="Tags",
        description="Comma-separated list of product tags.",
    )
    """Comma-separated list of product tags."""

    currency: Optional[str] = Field(
        default=None,
        max_length=3,
        title="Currency",
        description="Currency code for price fields.",
    )
    """Currency code for price fields."""

    options: Optional[List[ProductOption]] = Field(
        default=None,
        title="Options",
        description="List of product option names.",
    )
    """List of product option names."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO metadata including title, description, keywords.",
    )
    """SEO metadata including title, description, keywords."""

    image: Optional[str] = Field(
        default=None,
        title="Image ID",
        description="ID of the product image to set as the main image.",
    )
    """ID of the product image to set as the main image."""

    variants: Optional[List[ProductVariantUpdate]] = Field(
        default=None,
        title="Variants",
        description="List of product variants to update.",
    )
    """List of product variants to update. Specify the right options to
    match existing variants. """
