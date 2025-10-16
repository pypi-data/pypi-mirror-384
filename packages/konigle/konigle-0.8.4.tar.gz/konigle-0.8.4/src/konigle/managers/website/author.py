"""
Author managers for the Konigle SDK.

This module provides managers for author resources, enabling content author
management and operations.
"""

from typing import cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.author import Author, CreateAuthor, UpdateAuthor


class BaseAuthorManager:
    resource_class = Author
    """The resource model class this manager handles."""

    resource_update_class = UpdateAuthor
    """The model class used for updating resources."""

    base_path = "/admin/api/content-authors"
    """The API base path for this resource type."""


class AuthorManager(BaseAuthorManager, BaseSyncManager):
    """Manager for author resources."""

    def create(self, data: CreateAuthor) -> Author:
        """Create a new author."""
        return cast(Author, super().create(data))

    def update(self, id_: str, data: UpdateAuthor) -> Author:
        """Update an existing author."""
        return cast(Author, super().update(id_, data))


class AsyncAuthorManager(BaseAuthorManager, BaseAsyncManager):
    """Async manager for author resources."""

    async def create(self, data: CreateAuthor) -> Author:
        """Create a new author."""
        return cast(Author, await super().create(data))

    async def update(self, id_: str, data: UpdateAuthor) -> Author:
        """Update an existing author."""
        return cast(Author, await super().update(id_, data))
