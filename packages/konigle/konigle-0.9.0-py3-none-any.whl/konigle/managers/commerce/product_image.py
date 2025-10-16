"""
Product image managers for the Konigle SDK.

This module provides managers for product image resources, enabling
image management operations for products including upload, organization,
and variant associations.
"""

from typing import TYPE_CHECKING, cast

from konigle.filters.commerce import ProductImageFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.commerce.product_image import (
    ProductImage,
    ProductImageCreate,
    ProductImageUpdate,
)

if TYPE_CHECKING:
    from konigle.session import AsyncSession, SyncSession


class BaseProductImageManager:
    """Base class for product image managers with shared configuration."""

    resource_class = ProductImage
    """The resource model class this manager handles."""

    resource_update_class = ProductImageUpdate
    """The model class used for updating resources."""

    filter_class = ProductImageFilters
    """The filter model class for this resource type."""

    base_path = "/admin/api/product-images"
    """The API base path for this resource type."""


class ProductImageManager(BaseProductImageManager, BaseSyncManager):
    """Synchronous manager for product image resources."""

    def create(self, data: ProductImageCreate) -> ProductImage:
        """
        Create a new product image.

        Args:
            data: Product image creation data including file or URL

        Returns:
            Created product image instance with Active Record capabilities
        """

        return cast(ProductImage, super().create(data))

    def update(self, id_: str, data: ProductImageUpdate) -> ProductImage:
        """
        Update an existing product image.

        Args:
            id_: Product image ID (UUID)
            data: Product image update data with partial fields

        Returns:
            Updated product image instance
        """
        return cast(ProductImage, super().update(id_, data))

    def get(self, id_: str) -> ProductImage:
        """
        Get a specific product image by ID.

        Args:
            id_: Product image ID (UUID)

        Returns:
            Product image instance with full detail data
        """
        return cast(ProductImage, super().get(id_))


class AsyncProductImageManager(BaseProductImageManager, BaseAsyncManager):
    """Asynchronous manager for product image resources."""

    async def create(self, data: ProductImageCreate) -> ProductImage:
        """
        Create a new product image.

        Args:
            data: Product image creation data including file or URL

        Returns:
            Created product image instance with Active Record capabilities
        """

        return cast(ProductImage, await super().create(data))

    async def update(self, id_: str, data: ProductImageUpdate) -> ProductImage:
        """
        Update an existing product image.

        Args:
            id_: Product image ID (UUID)
            data: Product image update data with partial fields

        Returns:
            Updated product image instance
        """
        return cast(ProductImage, await super().update(id_, data))

    async def get(self, id_: str) -> ProductImage:
        """
        Get a specific product image by ID.

        Args:
            id_: Product image ID (UUID)

        Returns:
            Product image instance with full detail data
        """
        return cast(ProductImage, await super().get(id_))
