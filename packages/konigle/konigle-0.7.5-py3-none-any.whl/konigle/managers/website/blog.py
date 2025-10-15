"""
Blog managers for the Konigle SDK.

This module provides managers for blog resources, enabling blog post
content management and operations.
"""

from typing import cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.blog import Blog, BlogCreate, BlogUpdate


class BaseBlogManager:
    resource_class = Blog
    """The resource model class this manager handles."""

    resource_update_class = BlogUpdate
    """The model class used for updating resources."""

    base_path = "/admin/api/blogs"
    """The API base path for this resource type."""


class BlogManager(BaseBlogManager, BaseSyncManager):
    """Manager for blog resources."""

    def create(self, data: BlogCreate) -> Blog:
        """Create a new blog post."""
        return cast(Blog, super().create(data))

    def update(self, id_: str, data: BlogUpdate) -> Blog:
        """Update an existing blog post."""
        return cast(Blog, super().update(id_, data))

    def get(self, id_: str) -> Blog:
        return cast(Blog, super().get(id_))

    def publish(self, id_: str) -> Blog:
        """Publish a blog post."""
        path = f"{self.base_path}/{id_}/publish"
        response = self._session.post(path)
        return cast(
            Blog, self.create_resource(response.json(), is_partial=False)
        )

    def unpublish(self, id_: str) -> Blog:
        """Unpublish a blog post."""
        path = f"{self.base_path}/{id_}/unpublish"
        response = self._session.post(path)
        return cast(
            Blog, self.create_resource(response.json(), is_partial=False)
        )

    def change_handle(
        self, id_: str, new_handle: str, redirect: bool = False
    ) -> Blog:
        """Change the handle of a blog post."""

        path = f"{self.base_path}/{id_}/change-handle"
        response = self._session.post(
            path, json={"handle": new_handle, "redirect": redirect}
        )
        return cast(
            Blog, self.create_resource(response.json(), is_partial=False)
        )


class AsyncBlogManager(BaseBlogManager, BaseAsyncManager):
    """Async manager for blog resources."""

    async def create(self, data: BlogCreate) -> Blog:
        """Create a new blog post."""
        return cast(Blog, await super().create(data))

    async def update(self, id_: str, data: BlogUpdate) -> Blog:
        """Update an existing blog post."""
        return cast(Blog, await super().update(id_, data))

    async def get(self, id_: str) -> Blog:
        return cast(Blog, await super().get(id_))

    async def publish(self, id_: str) -> Blog:
        """Publish a blog post."""
        path = f"{self.base_path}/{id_}/publish"
        response = await self._session.post(path)
        return cast(
            Blog, self.create_resource(response.json(), is_partial=False)
        )

    async def unpublish(self, id_: str) -> Blog:
        """Unpublish a blog post."""
        path = f"{self.base_path}/{id_}/unpublish"
        response = await self._session.post(path)
        return cast(
            Blog, self.create_resource(response.json(), is_partial=False)
        )

    async def change_handle(
        self, id_: str, new_handle: str, redirect: bool = False
    ) -> Blog:
        """Change the handle of a blog post."""

        path = f"{self.base_path}/{id_}/change-handle"
        response = await self._session.post(
            path, json={"handle": new_handle, "redirect": redirect}
        )
        return cast(
            Blog, self.create_resource(response.json(), is_partial=False)
        )
