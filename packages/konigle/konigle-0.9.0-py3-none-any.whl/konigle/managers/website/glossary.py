"""
Glossary term managers for the Konigle SDK.

This module provides managers for glossary term resources, enabling glossary
content management and operations.
"""

from typing import cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.glossary import (
    GlossaryTerm,
    GlossaryTermCreate,
    GlossaryTermUpdate,
)


class BaseGlossaryTermManager:
    resource_class = GlossaryTerm
    """The resource model class this manager handles."""

    resource_update_class = GlossaryTermUpdate
    """The model class used for updating resources."""

    base_path = "/admin/api/glossary-terms"
    """The API base path for this resource type."""


class GlossaryTermManager(BaseGlossaryTermManager, BaseSyncManager):
    """Manager for glossary term resources."""

    def create(self, data: GlossaryTermCreate) -> GlossaryTerm:
        """Create a new glossary term."""
        return cast(GlossaryTerm, super().create(data))

    def update(self, id_: str, data: GlossaryTermUpdate) -> GlossaryTerm:
        """Update an existing glossary term."""
        return cast(GlossaryTerm, super().update(id_, data))

    def get(self, id_: str) -> GlossaryTerm:
        return cast(GlossaryTerm, super().get(id_))

    def publish(self, id_: str) -> GlossaryTerm:
        """Publish a glossary term."""
        path = f"{self.base_path}/{id_}/publish"
        response = self._session.post(path)
        return cast(
            GlossaryTerm,
            self.create_resource(response.json(), is_partial=False),
        )

    def unpublish(self, id_: str) -> GlossaryTerm:
        """Unpublish a glossary term."""
        path = f"{self.base_path}/{id_}/unpublish"
        response = self._session.post(path)
        return cast(
            GlossaryTerm,
            self.create_resource(response.json(), is_partial=False),
        )

    def change_handle(
        self, id_: str, new_handle: str, redirect: bool = False
    ) -> GlossaryTerm:
        """Change the handle of a glossary term."""

        path = f"{self.base_path}/{id_}/change-handle"
        response = self._session.post(
            path, json={"handle": new_handle, "redirect": redirect}
        )
        return cast(
            GlossaryTerm,
            self.create_resource(response.json(), is_partial=False),
        )


class AsyncGlossaryTermManager(BaseGlossaryTermManager, BaseAsyncManager):
    """Async manager for glossary term resources."""

    async def create(self, data: GlossaryTermCreate) -> GlossaryTerm:
        """Create a new glossary term."""
        return cast(GlossaryTerm, await super().create(data))

    async def update(self, id_: str, data: GlossaryTermUpdate) -> GlossaryTerm:
        """Update an existing glossary term."""
        return cast(GlossaryTerm, await super().update(id_, data))

    async def get(self, id_: str) -> GlossaryTerm:
        return cast(GlossaryTerm, await super().get(id_))

    async def publish(self, id_: str) -> GlossaryTerm:
        """Publish a glossary term."""
        path = f"{self.base_path}/{id_}/publish"
        response = await self._session.post(path)
        return cast(
            GlossaryTerm,
            self.create_resource(response.json(), is_partial=False),
        )

    async def unpublish(self, id_: str) -> GlossaryTerm:
        """Unpublish a glossary term."""
        path = f"{self.base_path}/{id_}/unpublish"
        response = await self._session.post(path)
        return cast(
            GlossaryTerm,
            self.create_resource(response.json(), is_partial=False),
        )

    async def change_handle(
        self, id_: str, new_handle: str, redirect: bool = False
    ) -> GlossaryTerm:
        """Change the handle of a glossary term."""

        path = f"{self.base_path}/{id_}/change-handle"
        response = await self._session.post(
            path, json={"handle": new_handle, "redirect": redirect}
        )
        return cast(
            GlossaryTerm,
            self.create_resource(response.json(), is_partial=False),
        )
