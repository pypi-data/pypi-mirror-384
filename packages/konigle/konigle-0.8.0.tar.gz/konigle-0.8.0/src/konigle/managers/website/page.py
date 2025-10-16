"""
Page managers for the Konigle SDK.

This module provides managers for page resources, enabling general page
content management and operations.
"""

from typing import Literal, cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.page import Page, PageCreate, PageUpdate


class BasePageManager:
    resource_class = Page
    """The resource model class this manager handles."""

    resource_update_class = PageUpdate
    """The model class used for updating resources."""

    base_path = "/admin/api/pages"
    """The API base path for this resource type."""


class PageManager(BasePageManager, BaseSyncManager):
    """Manager for page resources."""

    def create(self, data: PageCreate) -> Page:
        """Create a new page."""
        return cast(Page, super().create(data))

    def update(self, id_: str, data: PageUpdate) -> Page:
        """Update an existing page."""
        return cast(Page, super().update(id_, data))

    def get(self, id_: str) -> Page:
        return cast(Page, super().get(id_))

    def publish(self, id_: str) -> Page:
        """Publish a page."""
        path = f"{self.base_path}/{id_}/publish"
        response = self._session.post(path)
        return cast(
            Page, self.create_resource(response.json(), is_partial=False)
        )

    def unpublish(self, id_: str) -> Page:
        """Unpublish a page."""
        path = f"{self.base_path}/{id_}/unpublish"
        response = self._session.post(path)
        return cast(
            Page, self.create_resource(response.json(), is_partial=False)
        )

    def change_handle(
        self, id_: str, new_handle: str, redirect: bool = False
    ) -> Page:
        """Change the handle of a page."""

        path = f"{self.base_path}/{id_}/change-handle"
        response = self._session.post(
            path, json={"handle": new_handle, "redirect": redirect}
        )
        return cast(
            Page, self.create_resource(response.json(), is_partial=False)
        )


class AsyncPageManager(BasePageManager, BaseAsyncManager):
    """Async manager for page resources."""

    async def create(self, data: PageCreate) -> Page:
        """Create a new page."""
        return cast(Page, await super().create(data))

    async def update(self, id_: str, data: PageUpdate) -> Page:
        """Update an existing page."""
        return cast(Page, await super().update(id_, data))

    async def get(self, id_: str) -> Page:
        return cast(Page, await super().get(id_))

    async def publish(self, id_: str) -> Page:
        """Publish a page."""
        path = f"{self.base_path}/{id_}/publish"
        response = await self._session.post(path)
        return cast(
            Page, self.create_resource(response.json(), is_partial=False)
        )

    async def unpublish(self, id_: str) -> Page:
        """Unpublish a page."""
        path = f"{self.base_path}/{id_}/unpublish"
        response = await self._session.post(path)
        return cast(
            Page, self.create_resource(response.json(), is_partial=False)
        )

    async def change_handle(
        self, id_: str, new_handle: str, redirect: bool = False
    ) -> Page:
        """Change the handle of a page."""

        path = f"{self.base_path}/{id_}/change-handle"
        response = await self._session.post(
            path, json={"handle": new_handle, "redirect": redirect}
        )
        return cast(
            Page, self.create_resource(response.json(), is_partial=False)
        )
