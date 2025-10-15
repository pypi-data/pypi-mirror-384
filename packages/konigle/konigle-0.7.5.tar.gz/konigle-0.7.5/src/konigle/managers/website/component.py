"""
Component managers for the Konigle SDK.

This module provides managers for component resources, enabling component
management and operations for building landing pages.
"""

import uuid
from typing import Literal, cast

from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.website.component import (
    Component,
    ComponentCreate,
    ComponentUpdate,
)


class BaseComponentManager:
    resource_class = Component
    """The resource model class this manager handles."""

    resource_update_class = ComponentUpdate
    """The model class used for updating resources."""

    base_path = "/admin/api/components"
    """The API base path for this resource type."""

    def _get_component_context(
        self,
        data: ComponentCreate,
        component_type: Literal["component", "widget"],
    ):
        slug: str = data.name.lower().replace(" ", "-")
        template_code = f"{slug}-{str(uuid.uuid4())[:8]}"
        return {
            "name_": data.name,
            "is_custom_": True,
            "template_": template_code,
            "editor_support_": False,
            "component_type_": (
                "fluid" if component_type == "component" else "widget"
            ),
            "version_": data.version,
            "type_": "component",
        }


class ComponentManager(BaseComponentManager, BaseSyncManager):
    """Manager for component resources."""

    def create(
        self,
        data: ComponentCreate,
        type_: Literal["component", "widget"] = "component",
    ) -> Component:
        """Create a new component."""
        create_data = {
            **data.model_dump(exclude_none=True),
            "type": "fluid" if type_ == "component" else "widget",
            "context": self._get_component_context(data, type_),
        }
        return cast(Component, super().create(create_data))

    def update(self, id_: str, data: ComponentUpdate) -> Component:
        """Update an existing component."""
        return cast(Component, super().update(id_, data))

    def get(self, id_: str) -> Component:
        return cast(Component, super().get(id_))


class AsyncComponentManager(BaseComponentManager, BaseAsyncManager):
    """Async manager for component resources."""

    async def create(
        self,
        data: ComponentCreate,
        type_: Literal["component", "widget"] = "component",
    ) -> Component:
        """Create a new component."""
        create_data = {
            **data.model_dump(exclude_none=True),
            "type": "fluid" if type_ == "component" else "widget",
            "context": self._get_component_context(data, type_),
        }
        return cast(Component, await super().create(create_data))

    async def update(self, id_: str, data: ComponentUpdate) -> Component:
        """Update an existing component."""
        return cast(Component, await super().update(id_, data))
