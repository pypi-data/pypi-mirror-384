"""
Base model classes and mixins for the Konigle SDK.

This module provides the foundation for all resource models,
including Active Record functionality, state tracking, and
common model patterns.
"""

from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Set

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from konigle.types.common import IDMixin, TimestampMixin

if TYPE_CHECKING:
    from konigle.managers.base import BaseAsyncManager, BaseSyncManager


class SEOMeta(BaseModel):
    """
    SEO metadata model for all resource types.

    Provides comprehensive SEO and social media metadata fields
    that can be used across website, commerce, and marketing resources.
    """

    title: Optional[str] = Field(
        default=None,
        title="SEO Title",
        description="Title for SEO purposes, max 70 characters.",
    )
    """Title for SEO purposes, max 70 characters."""

    description: Optional[str] = Field(
        default="",
        title="SEO Description",
        description="Description for SEO purposes, max 160 characters.",
    )
    """Description for SEO purposes, max 160 characters."""

    keywords: Optional[str] = Field(
        default=None,
        title="SEO Keywords",
        description="Comma-separated keywords for SEO.",
    )
    """Comma-separated keywords for SEO."""

    og_title: Optional[str] = Field(
        default=None,
        title="Open Graph Title",
        description="Title for social sharing, max 70 characters.",
    )
    """Title for social sharing, max 70 characters."""

    og_description: Optional[str] = Field(
        default=None,
        title="Open Graph Description",
        description="Description for social sharing, max 160 characters.",
    )
    """Description for social sharing, max 160 characters."""

    og_image: Optional[str] = Field(
        default=None,
        title="Open Graph Image URL",
        description="URL of the image for social sharing.",
    )
    """URL of the image for social sharing."""

    model_config = ConfigDict(extra="ignore")


class BaseResource(BaseModel):
    """
    Base class providing Active Record functionality to all resources.

    This class enables resources to have methods like save(), delete(),
    and reload() by maintaining a reference to their manager and tracking
    field modifications.
    """

    _manager: Optional["BaseSyncManager | BaseAsyncManager"] = None
    """Reference to the manager handling this resource."""

    _original_data: Optional[Dict[str, Any]] = None
    """Snapshot of the original data for change tracking."""

    _modified_fields: Set[str] = PrivateAttr(default_factory=set)
    """Set of field names that have been modified since last sync."""

    _is_partial: bool = PrivateAttr(default=False)
    """Whether this resource was loaded from a list endpoint (partial data)."""

    _detail_only_fields: ClassVar[Set[str]] = set()
    """Fields that are only available in detail responses."""

    _foreign_key_fields: ClassVar[Set[str]] = set()
    """Fields that contain foreign key relationships."""

    def model_post_init(self, context: Any) -> None:
        self._original_data = self.model_dump()
        return super().model_post_init(context)

    def __setattr__(self, name: str, value: Any) -> None:
        """Track field modifications for dirty checking."""
        # Only track changes to actual model fields, not private attributes
        if (
            hasattr(self, "_original_data")
            and name in self.__class__.model_fields
            and self._original_data is not None
        ):
            self._modified_fields = self._modified_fields or set()

            original_value = self._original_data.get(name)
            if original_value != value:
                self._modified_fields.add(name)

        super().__setattr__(name, value)

    def save(self) -> "BaseResource":
        """
        Save changes back to the API.

        Returns:
            Updated resource instance with fresh data from the server

        Raises:
            ValueError: If resource is not associated with a manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot save: {self.__class__.__name__} not associated with "
                "a manager"
            )

        # Check if manager is sync
        from konigle.managers.base import BaseAsyncManager

        if isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use save(): {self.__class__.__name__} is "
                "associated with an async manager. Use asave() instead."
            )

        if not self._modified_fields:
            return self  # No changes to save

        # Create update data with only modified fields
        update_data = {
            field: getattr(self, field) for field in self._modified_fields
        }

        # Call manager's update method
        updated_resource = self._manager.update(self._get_id(), update_data)

        # Update self with fresh data from server
        for field, value in updated_resource.model_dump().items():
            if (
                field in self.__class__.model_fields
            ):  # Only update model fields
                setattr(self, field, value)

        # Reset tracking state
        if self._modified_fields:
            self._modified_fields.clear()
        self._original_data = self.model_dump()

        return self

    def delete(self) -> bool:
        """
        Delete this resource from the API.

        Returns:
            True if deletion was successful

        Raises:
            ValueError: If resource is not associated with a manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot delete: {self.__class__.__name__} not associated "
                "with a manager"
            )

        # Check if manager is sync
        from konigle.managers.base import BaseAsyncManager

        if isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use delete(): {self.__class__.__name__} is "
                "associated with an async manager. Use adelete() instead."
            )

        return self._manager.delete(self._get_id())

    def reload(self) -> "BaseResource":
        """
        Reload fresh data from the API.

        Returns:
            Self with updated data from the server

        Raises:
            ValueError: If resource is not associated with a manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot reload: {self.__class__.__name__} not associated "
                "with a manager"
            )

        from konigle.managers.base import BaseAsyncManager

        if isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use reload(): {self.__class__.__name__} is "
                "associated with an async manager. Use areload() instead."
            )

        fresh_resource = self._manager.get(self._get_id())

        # Update self with fresh data
        for field, value in fresh_resource.model_dump().items():
            if field in self.__class__.model_fields:
                setattr(self, field, value)

        # Reset tracking state
        if self._modified_fields:
            self._modified_fields.clear()
        self._original_data = self.model_dump()

        return self

    async def asave(self) -> "BaseResource":
        """
        Async version of save() - Save changes back to the API.

        Returns:
            Updated resource instance with fresh data from the server

        Raises:
            ValueError: If resource is not associated with an async manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot save: {self.__class__.__name__} not associated with "
                "a manager"
            )

        from konigle.managers.base import BaseAsyncManager

        if not isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use asave(): {self.__class__.__name__} is "
                "associated with a sync manager. Use save() instead."
            )

        if not self._modified_fields:
            return self  # No changes to save

        # Create update data with only modified fields
        update_data = {
            field: getattr(self, field) for field in self._modified_fields
        }

        # Call manager's update method
        updated_resource = await self._manager.update(
            self._get_id(), update_data
        )

        # Update self with fresh data from server
        for field, value in updated_resource.model_dump().items():
            if (
                field in self.__class__.model_fields
            ):  # Only update model fields
                setattr(self, field, value)

        # Reset tracking state
        self._modified_fields.clear()
        self._original_data = self.model_dump()

        return self

    async def adelete(self) -> bool:
        """
        Async version of delete() - Delete this resource from the API.

        Returns:
            True if deletion was successful

        Raises:
            ValueError: If resource is not associated with an async manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot delete: {self.__class__.__name__} not associated "
                "with a manager"
            )

        # Check if manager is async
        from konigle.managers.base import BaseAsyncManager

        if not isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use adelete(): {self.__class__.__name__} is "
                "associated with a sync manager. Use delete() instead."
            )

        return await self._manager.delete(self._get_id())

    async def areload(self) -> "BaseResource":
        """
        Async version of reload() - Reload fresh data from the API.

        Returns:
            Self with updated data from the server

        Raises:
            ValueError: If resource is not associated with an async manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot reload: {self.__class__.__name__} not associated "
                "with a manager"
            )

        # Check if manager is async
        from konigle.managers.base import BaseAsyncManager

        if not isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use areload(): {self.__class__.__name__} is "
                "associated with a sync manager. Use reload() instead."
            )

        fresh_resource = await self._manager.get(self._get_id())

        # Update self with fresh data
        for field, value in fresh_resource.model_dump().items():
            if field in self.__class__.model_fields:
                setattr(self, field, value)

        # Reset tracking state
        if self._modified_fields:
            self._modified_fields.clear()
        self._original_data = self.model_dump()

        return self

    @property
    def is_dirty(self) -> bool:
        """Check if the object has unsaved changes."""
        return len(self._modified_fields or set()) > 0

    @property
    def dirty_fields(self) -> Set[str]:
        """Get the names of fields that have been modified."""
        return (self._modified_fields or set()).copy()

    def reset_changes(self) -> None:
        """Reset all changes to original values."""
        if self._original_data and self._modified_fields:
            for field in self._modified_fields:
                if field in self._original_data:
                    setattr(self, field, self._original_data[field])
        if self._modified_fields:
            self._modified_fields.clear()

    def _get_id(self) -> str:
        """Helper to get the ID field if it exists."""
        id_ = getattr(self, "id", None)
        if id_ is None:
            raise ValueError(
                f"Cannot get ID: {self.__class__.__name__} does not have an 'id' field."
            )
        return id_

    def _update_from_full_resource(
        self, full_resource: "BaseResource"
    ) -> None:
        """
        Update this instance with data from a full resource.

        Args:
            full_resource: Resource instance with complete data from detail API
        """
        # Update all fields from the full object
        for field_name, field_value in full_resource.model_dump().items():
            if field_name in self.__class__.model_fields:
                setattr(self, field_name, field_value)

        # Update metadata
        self._is_partial = False
        self._original_data = self.model_dump()
        if self._modified_fields:
            self._modified_fields.clear()

    def load_detail(self) -> "BaseResource":
        """
        Load full detail from API and update this instance.

        Fetches the complete resource from the detail endpoint and updates
        all fields, including detail-only fields and full foreign key objects.

        Returns:
            Self with updated data from the detail API

        Raises:
            ValueError: If resource is not associated with a manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot load detail: {self.__class__.__name__} not associated with a manager"
            )

        # Check if manager is sync
        from konigle.managers.base import BaseAsyncManager

        if isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use load_detail(): {self.__class__.__name__} is "
                "associated with an async manager. Use aload_detail() instead."
            )
        if not self._is_partial:
            return self  # Already has full detail

        # Get full object from detail API
        full_resource = self._manager.get(self._get_id())

        # Update this instance with the full data
        self._update_from_full_resource(full_resource)

        return self

    async def aload_detail(self) -> "BaseResource":
        """
        Async version of load_detail() - Load full detail from API.

        Returns:
            Self with updated data from the detail API

        Raises:
            ValueError: If resource is not associated with an async manager
            APIError: If the API request fails
        """
        if not self._manager:
            raise ValueError(
                f"Cannot load detail: {self.__class__.__name__} not associated with a manager"
            )

        from konigle.managers.base import BaseAsyncManager

        if not isinstance(self._manager, BaseAsyncManager):
            raise ValueError(
                f"Cannot use aload_detail(): {self.__class__.__name__} is "
                "associated with a sync manager. Use load_detail() instead."
            )

        # Get full object from detail API
        full_resource = await self._manager.get(self._get_id())

        # Update this instance with the full data
        self._update_from_full_resource(full_resource)

        return self

    def is_detail_loaded(self) -> bool:
        """
        Check if detail data is loaded.

        Returns:
            True if this resource was loaded from a detail endpoint,
            or if there are no detail-only fields or foreign key fields.
            False if loaded from a list endpoint and has detail-only/foreign key fields.
        """
        # If no detail-only or foreign key fields, always considered loaded
        if not self._detail_only_fields and not self._foreign_key_fields:
            return True

        return not self._is_partial

    def is_foreign_key_loaded(self, field_name: str) -> bool:
        """
        Check if a foreign key field is fully loaded (not just IDs).

        Args:
            field_name: Name of the foreign key field to check

        Returns:
            True if the field contains full objects, False if just IDs

        Raises:
            ValueError: If field_name is not a defined foreign key field
        """
        if field_name not in self._foreign_key_fields:
            raise ValueError(
                f"'{field_name}' is not a foreign key field. "
                f"Valid foreign key fields: {', '.join(self._foreign_key_fields)}"
            )

        value = getattr(self, field_name, None)
        if value is None:
            return True  # Null values are considered "loaded"

        if isinstance(value, list):
            # For lists, check if any items are still strings (IDs)
            return all(not isinstance(item, str) for item in value)

        # For single values, check if it's not a string (ID)
        return not isinstance(value, str)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        validate_assignment=True,
    )


class Resource(BaseResource, IDMixin):
    """
    Standard resource model for resources that have an ID but no timestamps.

    Combines BaseResource (Active Record) with IDMixin (id field).
    Use this for simple resources that don't have created_at/updated_at fields.
    """

    pass


class TimestampedResource(BaseResource, IDMixin, TimestampMixin):
    """
    Resource model for resources that have ID and timestamp fields.

    Combines BaseResource (Active Record), IDMixin (id field),
    and TimestampMixin (created_at, updated_at) for resources
    that include full timestamp tracking.
    """

    pass


class CreateModel(BaseModel):
    """
    Base class for creation models.

    Used for models that define fields required/allowed
    when creating new resources.
    """

    # Allow arbitrary types for file handling
    model_config = ConfigDict(
        arbitrary_types_allowed=True, use_enum_values=True, extra="forbid"
    )


class UpdateModel(BaseModel):
    """
    Base class for update models.

    Used for models that define fields allowed when
    updating existing resources. All fields are optional.
    """

    # Allow arbitrary types for file handling
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )
