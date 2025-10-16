"""
Product variant managers for the Konigle SDK.

This module provides managers for product variant resources, enabling
variant management operations for products including pricing, inventory,
and option management.
"""

from typing import Any, Dict, cast

from konigle.exceptions import KonigleError
from konigle.filters.commerce import ProductVariantFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.base import BaseResource, CreateModel
from konigle.models.commerce.product_variant import (
    ProductVariant,
    ProductVariantUpdate,
)


class BaseProductVariantManager:
    """Base class for product variant managers with shared configuration."""

    resource_class = ProductVariant
    """The resource model class this manager handles."""

    resource_update_class = ProductVariantUpdate
    """The model class used for updating resources."""

    filter_class = ProductVariantFilters
    """The filter model class for this resource type."""

    base_path = "/admin/api/product-variants"
    """The API base path for this resource type."""


class ProductVariantManager(BaseProductVariantManager, BaseSyncManager):
    """Synchronous manager for product variant resources."""

    def create(self, data: CreateModel | Dict[str, Any]) -> BaseResource:
        raise KonigleError(
            "Cannot create variants via this endpoint. Use product update"
            "to specify variant options and variants to create variants."
        )

    def update(self, id_: str, data: ProductVariantUpdate) -> ProductVariant:
        """
        Update an existing product variant.

        Args:
            id_: Product variant ID (UUID)
            data: Product variant update data with partial fields

        Returns:
            Updated product variant instance
        """
        return cast(ProductVariant, super().update(id_, data))

    def get(self, id_: str) -> ProductVariant:
        """
        Get a specific product variant by ID.

        Args:
            id_: Product variant ID (UUID)

        Returns:
            Product variant instance with full detail data
        """
        return cast(ProductVariant, super().get(id_))


class AsyncProductVariantManager(BaseProductVariantManager, BaseAsyncManager):
    """Asynchronous manager for product variant resources."""

    async def create(self, data: CreateModel | Dict[str, Any]) -> BaseResource:
        raise KonigleError(
            "Cannot create variants via this endpoint. Use product update"
            "to specify variant options and variants to create variants."
        )

    async def update(
        self, id_: str, data: ProductVariantUpdate
    ) -> ProductVariant:
        """
        Update an existing product variant.

        Args:
            id_: Product variant ID (UUID)
            data: Product variant update data with partial fields

        Returns:
            Updated product variant instance
        """
        return cast(ProductVariant, await super().update(id_, data))

    async def get(self, id_: str) -> ProductVariant:
        """
        Get a specific product variant by ID.

        Args:
            id_: Product variant ID (UUID)

        Returns:
            Product variant instance with full detail data
        """
        return cast(ProductVariant, await super().get(id_))
