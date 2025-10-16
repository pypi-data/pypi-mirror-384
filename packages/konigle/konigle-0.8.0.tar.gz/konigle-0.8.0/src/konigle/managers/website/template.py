"""
Template managers for the Konigle SDK.

This module provides managers for template resources, enabling template
management and operations for building landing pages.
"""

from typing import cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.template import (
    Template,
    TemplateCreate,
    TemplateUpdate,
)


class BaseTemplateManager:
    resource_class = Template
    """The resource model class this manager handles."""

    resource_update_class = TemplateUpdate
    """The model class used for updating resources."""

    base_path = "/admin/api/site-templates"
    """The API base path for this resource type."""


class TemplateManager(BaseTemplateManager, BaseSyncManager):
    """Manager for template resources."""

    def create(self, data: TemplateCreate) -> Template:
        """Create a new template."""
        return cast(Template, super().create(data))

    def update(self, id_: str, data: TemplateUpdate) -> Template:
        """Update an existing template."""
        return cast(Template, super().update(id_, data))

    def get(self, id_: str) -> Template:
        return cast(Template, super().get(id_))


class AsyncTemplateManager(BaseTemplateManager, BaseAsyncManager):
    """Async manager for template resources."""

    async def create(self, data: TemplateCreate) -> Template:
        """Create a new template."""
        return cast(Template, await super().create(data))

    async def update(self, id_: str, data: TemplateUpdate) -> Template:
        """Update an existing template."""
        return cast(Template, await super().update(id_, data))
