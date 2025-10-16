"""
Product variant models for the Konigle SDK.

This module provides Pydantic models for product variant resources including
creation, update, and response models with comprehensive pricing and inventory
validation.
"""

from decimal import Decimal
from typing import Annotated, Any, ClassVar, Dict, List, Optional, Set, Union

from pydantic import AfterValidator, BaseModel, Field

from konigle.models.base import BaseResource, CreateModel, SEOMeta, UpdateModel
from konigle.validators import validate_editorjs_content, validate_price

from .base import IDMixin, TimestampedResource
from .product_image import ProductImageReference


class ProductReference(IDMixin):
    """
    Reference model for a product.

    Contains only the ID field for lightweight references.
    """

    title: str = Field(
        title="Title",
        description="Product title or name.",
    )
    """Product title or name."""

    handle: str = Field(
        title="Handle",
        description="URL-friendly product identifier.",
    )
    """URL-friendly product identifier."""


class ProductVariantBase(BaseModel):
    """
    Base product variant model with truly shared fields.

    Contains only fields that have the same optionality and validation
    requirements in both creation and response contexts.
    """

    price: Annotated[Decimal, AfterValidator(validate_price)] = Field(
        ...,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Price",
        description="Variant selling price.",
    )
    """Variant selling price."""

    content: Annotated[
        Optional[Dict[str, Any]], AfterValidator(validate_editorjs_content)
    ] = Field(
        default_factory=dict,
        title="Content",
        description="Variant-specific content blocks in EditorJS format.",
    )
    """Variant-specific content blocks in EditorJS format."""


class ProductVariantCreate(CreateModel, ProductVariantBase):
    """
    Model for creating a new product variant.

    All fields required for creation are included.
    Supports setting all variant fields including pricing, inventory, and images.
    """

    title: Optional[str] = Field(
        default=None,
        title="Title",
        description="Variant title or name.",
    )
    """Variant title or name."""

    barcode: Optional[str] = Field(
        default=None,
        title="Barcode",
        description="Product barcode or UPC.",
    )
    """Product barcode or UPC."""

    sku: Optional[str] = Field(
        default=None,
        title="SKU",
        description="Stock Keeping Unit identifier.",
    )
    """Stock Keeping Unit identifier."""

    compare_at_price: Optional[
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

    cost: Optional[Annotated[Decimal, AfterValidator(validate_price)]] = Field(
        default=None,
        ge=0,
        max_digits=19,
        decimal_places=2,
        title="Cost",
        description="Cost of goods sold for this variant.",
    )
    """Cost of goods sold for this variant."""

    currency: Optional[str] = Field(
        default=None,
        max_length=3,
        title="Currency",
        description="Currency code for price fields.",
    )
    """Currency code for price fields."""

    option1: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Option 1",
        description="First product option value (e.g., Size).",
    )
    """First product option value (e.g., Size)."""

    option2: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Option 2",
        description="Second product option value (e.g., Color).",
    )
    """Second product option value (e.g., Color)."""

    option3: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Option 3",
        description="Third product option value (e.g., Material).",
    )
    """Third product option value (e.g., Material)."""

    position: Optional[int] = Field(
        default=1,
        ge=1,
        title="Position",
        description="Display position in product variant list.",
    )
    """Display position in product variant list."""

    weight: Optional[float] = Field(
        default=None,
        ge=0,
        title="Weight",
        description="Variant weight for shipping calculations.",
    )
    """Variant weight for shipping calculations."""

    weight_unit: Optional[str] = Field(
        default=None,
        max_length=31,
        title="Weight Unit",
        description="Unit of measurement for weight.",
    )
    """Unit of measurement for weight."""

    grams: Optional[int] = Field(
        default=None,
        ge=0,
        title="Grams",
        description="Weight in grams.",
    )
    """Weight in grams."""

    taxable: Optional[bool] = Field(
        default=True,
        title="Taxable",
        description="Whether this variant is subject to taxes.",
    )
    """Whether this variant is subject to taxes."""

    inventory_policy: str = Field(
        default="deny",
        title="Inventory Policy",
        description="Policy for handling out-of-stock variants.",
    )
    """Policy for handling out-of-stock variants."""

    inventory_quantity: int = Field(
        default=1,
        ge=0,
        title="Inventory Quantity",
        description="Available stock quantity.",
    )
    """Available stock quantity."""

    seo_meta: Optional[SEOMeta] = Field(
        default_factory=lambda: SEOMeta(),
        title="SEO Meta",
        description="SEO metadata for this variant.",
    )
    """SEO metadata for this variant."""

    image: Optional[str] = Field(
        default=None,
        title="Image ID",
        description="ID of the main cover image of the variant.",
    )
    """ID of the variant-specific image."""

    def model_post_init(self, context: Any) -> None:
        if self.title is None:
            options: List[str] = []
            if self.option1:
                options.append(self.option1)
            if self.option2:
                options.append(self.option2)
            if self.option3:
                options.append(self.option3)
            self.title = " / ".join(options) if options else "Default Title"


class ProductVariantUpdate(UpdateModel):
    """
    Model for updating an existing product variant.

    All fields are optional for partial updates.
    """

    handle: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="URL-friendly variant identifier.",
    )
    """URL-friendly variant identifier."""

    title: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Title",
        description="Variant title or name.",
    )
    """Variant title or name."""

    barcode: Optional[str] = Field(
        default=None,
        title="Barcode",
        description="Product barcode or UPC.",
    )
    """Product barcode or UPC."""

    sku: Optional[str] = Field(
        default=None,
        title="SKU",
        description="Stock Keeping Unit identifier.",
    )
    """Stock Keeping Unit identifier."""

    price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Price",
        description="Variant selling price.",
    )
    """Variant selling price."""

    cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=19,
        decimal_places=2,
        title="Cost",
        description="Cost of goods sold for this variant.",
    )
    """Cost of goods sold for this variant."""

    currency: Optional[str] = Field(
        default=None,
        max_length=3,
        title="Currency",
        description="Currency code for price fields.",
    )
    """Currency code for price fields."""

    compare_at_price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Compare At Price",
        description="Compare at price for displaying discounts.",
    )
    """Compare at price for displaying discounts."""

    position: Optional[int] = Field(
        default=None,
        ge=1,
        title="Position",
        description="Display position in product variant list.",
    )
    """Display position in product variant list."""

    weight: Optional[float] = Field(
        default=None,
        ge=0,
        title="Weight",
        description="Variant weight for shipping calculations.",
    )
    """Variant weight for shipping calculations."""

    weight_unit: Optional[str] = Field(
        default=None,
        max_length=31,
        title="Weight Unit",
        description="Unit of measurement for weight.",
    )
    """Unit of measurement for weight."""

    grams: Optional[int] = Field(
        default=None,
        ge=0,
        title="Grams",
        description="Weight in grams.",
    )
    """Weight in grams."""

    taxable: Optional[bool] = Field(
        default=None,
        title="Taxable",
        description="Whether this variant is subject to taxes.",
    )
    """Whether this variant is subject to taxes."""

    tax_code: Optional[str] = Field(
        default=None,
        title="Tax Code",
        description="Tax classification code.",
    )
    """Tax classification code."""

    inventory_policy: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Inventory Policy",
        description="Policy for handling out-of-stock variants.",
    )
    """Policy for handling out-of-stock variants."""

    inventory_quantity: Optional[int] = Field(
        default=None,
        ge=0,
        title="Inventory Quantity",
        description="Available stock quantity.",
    )
    """Available stock quantity."""

    content: Optional[Dict[str, Any]] = Field(
        default=None,
        title="Content",
        description="Variant-specific content blocks in JSON format.",
    )
    """Variant-specific content blocks in JSON format."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO metadata for this variant.",
    )
    """SEO metadata for this variant."""

    image: Optional[str] = Field(
        default=None,
        title="Image ID",
        description="ID of the main image of the variant.",
    )
    """ID of the main image of the variant."""


class ProductVariant(
    ProductVariantBase, TimestampedResource, IDMixin, BaseResource
):
    """
    Complete product variant resource model.

    Represents a product variant from the API with all fields including
    computed values, pricing, inventory, and Active Record capabilities.
    """

    product: Union[str, ProductReference] = Field(
        ...,
        title="Product ID",
        description="ID of the parent product.",
    )
    """ID of the parent product."""

    handle: str = Field(
        ...,
        title="Handle",
        description="URL-friendly variant identifier.",
    )
    """URL-friendly variant identifier."""

    title: str = Field(
        ...,
        title="Title",
        description="Variant title or name.",
    )
    """Variant title or name."""

    barcode: Optional[str] = Field(
        default=None,
        title="Barcode",
        description="Product barcode or UPC.",
    )
    """Product barcode or UPC."""

    sku: Optional[str] = Field(
        default=None,
        title="SKU",
        description="Stock Keeping Unit identifier.",
    )
    """Stock Keeping Unit identifier."""

    compare_at_price: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=19,
        decimal_places=2,
        title="Original Price",
        description="Original price before discount.",
    )
    """Original price before discount."""

    cost: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=19,
        decimal_places=2,
        title="Cost",
        description="Cost of goods sold for this variant.",
    )
    """Cost of goods sold for this variant."""

    currency: Optional[str] = Field(
        default=None,
        max_length=3,
        title="Currency",
        description="Currency code for price fields.",
    )
    """Currency code for price fields."""

    option1: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Option 1",
        description="First product option value (e.g., Size).",
    )
    """First product option value (e.g., Size)."""

    option2: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Option 2",
        description="Second product option value (e.g., Color).",
    )
    """Second product option value (e.g., Color)."""

    option3: Optional[str] = Field(
        default=None,
        max_length=500,
        title="Option 3",
        description="Third product option value (e.g., Material).",
    )
    """Third product option value (e.g., Material)."""

    position: int = Field(
        ...,
        ge=1,
        title="Position",
        description="Display position in product variant list.",
    )
    """Display position in product variant list."""

    weight: Optional[float] = Field(
        default=None,
        ge=0,
        title="Weight",
        description="Variant weight for shipping calculations.",
    )
    """Variant weight for shipping calculations."""

    weight_unit: Optional[str] = Field(
        default=None,
        max_length=31,
        title="Weight Unit",
        description="Unit of measurement for weight.",
    )
    """Unit of measurement for weight."""

    grams: Optional[int] = Field(
        default=None,
        ge=0,
        title="Grams",
        description="Weight in grams.",
    )
    """Weight in grams."""

    taxable: bool = Field(
        ...,
        title="Taxable",
        description="Whether this variant is subject to taxes.",
    )
    """Whether this variant is subject to taxes."""

    inventory_policy: Optional[str] = Field(
        default=None,
        title="Inventory Policy",
        description="Policy for handling out-of-stock variants.",
    )
    """Policy for handling out-of-stock variants."""

    inventory_quantity: int = Field(
        ...,
        ge=0,
        title="Inventory Quantity",
        description="Available stock quantity.",
    )
    """Available stock quantity."""

    seo_meta: Optional[SEOMeta] = Field(
        default=None,
        title="SEO Meta",
        description="SEO metadata for this variant.",
    )
    """SEO metadata for this variant."""

    image: Optional[Union[str, ProductImageReference]] = Field(
        default=None,
        title="Image ID",
        description="ID of the variant-specific image.",
    )
    """ID of the variant-specific image."""

    _detail_only_fields: ClassVar[Set[str]] = {"content", "seo_meta"}

    _foreign_key_fields: ClassVar[Set[str]] = {"product", "image"}

    def __str__(self) -> str:
        product_id = (
            self.product if isinstance(self.product, str) else self.product.id
        )
        return (
            f"ProductVariant(id = {self.id}, product={product_id} "
            f"title={self.title}, handle={self.handle})"
        )
