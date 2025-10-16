"""
Product managers for the Konigle SDK.

This module provides managers for product resources, enabling e-commerce
product management operations including CRUD operations and nested resource
management for variants and images.
"""

from typing import cast

from konigle.filters.commerce import ProductFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.commerce.product import (
    Product,
    ProductCreate,
    ProductUpdate,
)


class BaseProductManager:
    """Base class for product managers with shared configuration."""

    resource_class = Product
    """The resource model class this manager handles."""

    resource_update_class = ProductUpdate
    """The model class used for updating resources."""

    filter_class = ProductFilters
    """The filter model class for this resource type."""

    base_path = "/admin/api/products"
    """The API base path for this resource type."""


class ProductManager(BaseProductManager, BaseSyncManager):
    """Synchronous manager for product resources."""

    def create(self, data: ProductCreate) -> Product:
        """
        Create a new product.

        Args:
            data: Product creation data including all required fields

        Returns:
            Created product instance with Active Record capabilities
        """
        return cast(Product, super().create(data))

    def update(self, id_: str, data: ProductUpdate) -> Product:
        """
        Update an existing product.

        Args:
            id_: Product ID (UUID)
            data: Product update data with partial fields

        Returns:
            Updated product instance
        """
        return cast(Product, super().update(id_, data))

    def get(self, id_: str) -> Product:
        """
        Get a specific product by ID.

        Args:
            id_: Product ID (UUID)

        Returns:
            Product instance with full detail data and nested managers
        """
        return cast(Product, super().get(id_))


class AsyncProductManager(BaseProductManager, BaseAsyncManager):
    """Asynchronous manager for product resources."""

    async def create(self, data: ProductCreate) -> Product:
        """
        Create a new product.

        Args:
            data: Product creation data including all required fields

        Returns:
            Created product instance with Active Record capabilities
        """
        return cast(Product, await super().create(data))

    async def update(self, id_: str, data: ProductUpdate) -> Product:
        """
        Update an existing product.

        Args:
            id_: Product ID (UUID)
            data: Product update data with partial fields

        Returns:
            Updated product instance
        """
        return cast(Product, await super().update(id_, data))

    async def get(self, id_: str) -> Product:
        """
        Get a specific product by ID.

        Args:
            id_: Product ID (UUID)

        Returns:
            Product instance with full detail data and nested managers
        """
        return cast(Product, await super().get(id_))
