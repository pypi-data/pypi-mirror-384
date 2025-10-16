"""
Base manager classes for the Konigle SDK.

This module provides the foundation for all resource managers,
implementing common CRUD operations, pagination, filtering,
and file upload handling.
"""

import io
import json
from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

import httpx
from pydantic import BaseModel, ValidationError

from konigle.filters.base import BaseFilters
from konigle.logging import get_logger
from konigle.models.base import BaseResource, CreateModel, UpdateModel
from konigle.types.common import PaginatedResponse, PaginationParams
from konigle.utils import model_to_dict

if TYPE_CHECKING:
    from ..session import AsyncSession, SyncSession


class BaseManager:
    """
    Base manager class providing common functionality for both sync and async
    managers.

    Contains shared methods for URL construction, resource creation, filtering,
    and file handling that are identical between sync and async
    implementations.
    """

    resource_class: Type[BaseResource]
    """The resource model class this manager handles."""

    resource_update_class: Optional[Type[UpdateModel]] = None
    """The update model class for this resource type."""

    base_path: str
    """The API base path for this resource type (e.g., '/media-assets')."""

    filter_class: Optional[Type[BaseFilters]] = None
    """The filter model class for this resource type (optional)."""

    def __init__(self):
        self.logger = get_logger()

    def _get_base_url(self) -> str:
        """Get the base URL for this resource type."""
        return self.base_path

    def _get_list_url(self) -> str:
        """Get the URL for listing resources."""
        return self._get_base_url()

    def _get_detail_url(self, id_: str) -> str:
        """Get the URL for a specific resource."""
        return f"{self._get_base_url()}/{id_}"

    def create_resource(
        self, data: Dict[str, Any], is_partial: bool = False
    ) -> BaseResource:
        """
        Create resource instance with Active Record capabilities.

        Args:
            data: Resource data from API response
            is_partial: Whether this resource was loaded from a list endpoint
                       (may be missing detail-only fields)

        Returns:
            Resource instance with manager attached
        """
        resource = self.resource_class.model_validate(data)
        self._attach_manager(resource, is_partial=is_partial)
        return resource

    def _attach_manager(
        self, resource: BaseResource, is_partial: bool = False
    ):
        """
        Attach manager and initialize tracking state.

        Args:
            resource: The resource instance to attach to
            is_partial: Whether this resource was loaded from a list endpoint
        """
        resource._manager = self  # type: ignore
        resource._original_data = resource.model_dump()
        resource._modified_fields = set()
        resource._is_partial = is_partial

    def _process_filters(
        self,
        filters: Optional[BaseFilters] = None,
        filter_kwargs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Process and validate filters."""
        if filters and filter_kwargs:
            raise ValueError(
                "Cannot use both 'filters' object and filter_kwargs"
            )

        if filter_kwargs:
            if self.filter_class:
                try:
                    filters = self.filter_class(**filter_kwargs)
                except ValidationError as e:
                    supported = list(self.filter_class.model_fields.keys())
                    raise ValueError(
                        f"Invalid filter arguments: {e}. "
                        f"Supported filters: {', '.join(supported)}"
                    ) from e
            else:
                # No filter class defined, just pass through kwargs
                return {
                    k: v for k, v in filter_kwargs.items() if v is not None
                }

        # get default filters. Useful for Image, Video, Document managers
        # which add default filter for mime_type on the same table.
        if filters is None and self.filter_class:
            filters = self.filter_class()

        if filters:
            return filters.model_dump(exclude_none=True)

        return {}

    def _has_file_fields(self, data: Dict[str, Any]) -> bool:
        """Check if data contains file fields."""
        for field_value in data.values():
            if isinstance(field_value, (io.BytesIO, io.IOBase)):
                return True
            elif hasattr(field_value, "read") and hasattr(field_value, "name"):
                return True
        return False

    def _prepare_multipart_data(
        self, data: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Separate form data and files for multipart requests."""
        form_data = {}
        files_data = {}

        for field_name, field_value in data.items():
            if isinstance(field_value, (io.BytesIO, io.IOBase)) or (
                hasattr(field_value, "read") and hasattr(field_value, "name")
            ):
                # httpx will use the .name attribute for filename and
                # content-type
                files_data[field_name] = field_value
            elif isinstance(field_value, (dict, list, tuple)):
                # Serialize complex types as JSON strings
                form_data[field_name] = json.dumps(field_value)
            else:
                form_data[field_name] = field_value

        return form_data, files_data

    def _create_paginated_response(
        self, data: Dict[str, Any], pagination: PaginationParams
    ) -> PaginatedResponse[BaseResource]:
        """
        Create a PaginatedResponse from API data.

        Resources in list responses are marked as partial since they may
        be missing detail-only fields.
        """
        payload = (
            data.get("payload", [])
            if "payload" in data
            else data.get("results", [])
        )

        return PaginatedResponse[self.resource_class](
            payload=[
                self.create_resource(item, is_partial=True) for item in payload
            ],
            count=data["count"],
            next=data.get("next"),
            previous=data.get("previous"),
            page_size=pagination.page_size,
            current_page=pagination.page,
            num_pages=data.get("num_pages", 1),
        )


class BaseSyncManager(BaseManager):
    """
    Synchronous manager providing CRUD operations.

    All sync resource managers inherit from this class to get standard
    functionality for listing, creating, updating, and deleting resources.
    """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses define required class attributes."""
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "resource_class") or cls.resource_class is None:
            raise TypeError(f"{cls.__name__} must define 'resource_class'")

        if not hasattr(cls, "base_path") or not isinstance(cls.base_path, str):
            raise TypeError(
                f"{cls.__name__} must define 'base_path' as a string"
            )

    def __init__(self, session: "SyncSession"):
        super().__init__()
        self._session = session

    def _make_multipart_request(
        self, method: str, url: str, data: Dict[str, Any]
    ) -> httpx.Response:
        """Make multipart form data request."""
        form_data, files_data = self._prepare_multipart_data(data)
        kwargs = {}
        if form_data:
            kwargs["data"] = form_data
        if files_data:
            kwargs["files"] = files_data

        if method.upper() == "POST":
            response = self._session.post(url, **kwargs)
        elif method.upper() == "PATCH":

            response = self._session.patch(url, **kwargs)
        elif method.upper() == "PUT":
            response = self._session.put(url, **kwargs)
        else:
            raise ValueError(f"Multipart not supported for {method}")

        return response

    def _model_to_dict(self, model: BaseModel) -> Dict[str, Any]:
        """Convert a Pydantic model to a dict, excluding None and unset fields
        and handling file fields appropriately for multipart requests.
        """
        return model_to_dict(model)

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[BaseFilters] = None,
        **filter_kwargs,
    ) -> PaginatedResponse[BaseResource]:
        """
        List resources with pagination and filtering.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            filters: Filter object for type-safe filtering
            **filter_kwargs: Filter arguments as keyword arguments

        Returns:
            Paginated response containing list of resources
        """
        # Validate pagination parameters
        pagination = PaginationParams(page=page, page_size=page_size)

        # Process filters
        filter_params = self._process_filters(filters, filter_kwargs)

        # Build request parameters
        params = {
            "page": pagination.page,
            "page_size": pagination.page_size,
            **filter_params,
        }

        response = self._session.get(self._get_list_url(), params=params)
        data = response.json()

        return self._create_paginated_response(data, pagination)

    def get(self, id_: str) -> BaseResource:
        """
        Get a specific resource by ID.

        Args:
            id_: Unique identifier for the resource

        Returns:
            Resource instance with full detail data
        """
        response = self._session.get(self._get_detail_url(id_))

        return self.create_resource(response.json(), is_partial=False)

    def create(self, data: Union[CreateModel, Dict[str, Any]]) -> BaseResource:
        """
        Create a new resource.

        Args:
            data: Resource data model instance or dict

        Returns:
            Created resource instance
        """
        if isinstance(data, BaseModel):
            # Extract raw field values to avoid SerializationIterator issues
            # when file-like objects are involved.
            data_dict = self._model_to_dict(data)
        else:
            data_dict = {k: v for k, v in data.items() if v is not None}

        if self._has_file_fields(data_dict):
            response = self._make_multipart_request(
                "POST", self._get_list_url(), data_dict
            )
        else:
            response = self._session.post(self._get_list_url(), json=data_dict)

        return self.create_resource(response.json())

    def update(
        self, id_: str, data: Union[UpdateModel, Dict[str, Any]]
    ) -> BaseResource:
        """
        Update an existing resource.

        Args:
            id_: Unique identifier for the resource
            data: Updated resource data model instance or dict

        Returns:
            Updated resource instance
        """
        if isinstance(data, BaseModel):
            # Assuming the update requests do not include file-like objects
            data_dict = self._model_to_dict(data)
        else:
            if self.resource_update_class:
                data_dict = self._model_to_dict(
                    self.resource_update_class.model_validate(data)
                )
            else:
                # no validation. let the api handle it
                data_dict = {k: v for k, v in data.items() if v is not None}

        if self._has_file_fields(data_dict):
            response = self._make_multipart_request(
                "PATCH", self._get_detail_url(id_), data_dict
            )
        else:
            response = self._session.patch(
                self._get_detail_url(id_), json=data_dict
            )

        return self.create_resource(response.json())

    def delete(self, id_: str) -> bool:
        """
        Delete a resource.

        Args:
            id_: Unique identifier for the resource

        Returns:
            True if deletion was successful
        """
        response = self._session.delete(self._get_detail_url(id_))
        return 200 <= response.status_code < 300

    def iter_all(
        self,
        page_size: int = 100,
        filters: Optional[BaseFilters] = None,
        **filter_kwargs,
    ):
        """
        Memory-efficient iteration over all matching resources.

        Args:
            page_size: Number of items to fetch per page
            filters: Filter object for type-safe filtering
            **filter_kwargs: Filter arguments as keyword arguments

        Yields:
            Resource instances one by one
        """
        page = 1

        while True:
            response = self.list(
                page=page,
                page_size=page_size,
                filters=filters,
                **filter_kwargs,
            )

            for item in response.payload:
                yield item

            if not response.has_next():
                break
            page += 1


class BaseAsyncManager(BaseManager):
    """
    Asynchronous manager providing CRUD operations.

    All async resource managers inherit from this class to get standard
    functionality for listing, creating, updating, and deleting resources.
    """

    def __init_subclass__(cls, **kwargs):
        """Ensure subclasses define required class attributes."""
        super().__init_subclass__(**kwargs)

        if not hasattr(cls, "resource_class") or cls.resource_class is None:
            raise TypeError(f"{cls.__name__} must define 'resource_class'")

        if not hasattr(cls, "base_path") or not isinstance(cls.base_path, str):
            raise TypeError(
                f"{cls.__name__} must define 'base_path' as a string"
            )

    def __init__(self, session: "AsyncSession"):
        super().__init__()
        self._session = session

    async def _make_multipart_request(
        self, method: str, url: str, data: Dict[str, Any]
    ) -> httpx.Response:
        """Make async multipart form data request."""
        form_data, files_data = self._prepare_multipart_data(data)

        try:
            if method.upper() == "POST":
                response = await self._session.post(
                    url, data=form_data, files=files_data
                )
            elif method.upper() == "PATCH":
                response = await self._session.patch(
                    url, data=form_data, files=files_data
                )
            elif method.upper() == "PUT":
                response = await self._session.put(
                    url, data=form_data, files=files_data
                )
            else:
                raise ValueError(f"Multipart not supported for {method}")

            return response
        finally:
            # Clean up opened file handles
            for file_obj in files_data.values():
                if hasattr(file_obj, "close") and hasattr(file_obj, "name"):
                    file_obj.close()

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[BaseFilters] = None,
        **filter_kwargs,
    ) -> PaginatedResponse[BaseResource]:
        """
        List resources with pagination and filtering.

        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            filters: Filter object for type-safe filtering
            **filter_kwargs: Filter arguments as keyword arguments

        Returns:
            Paginated response containing list of resources
        """
        # Validate pagination parameters
        pagination = PaginationParams(page=page, page_size=page_size)

        # Process filters
        filter_params = self._process_filters(filters, filter_kwargs)

        # Build request parameters
        params = {
            "page": pagination.page,
            "page_size": pagination.page_size,
            **filter_params,
        }

        response = await self._session.get(self._get_list_url(), params=params)
        data = response.json()

        return self._create_paginated_response(data, pagination)

    async def get(self, id_: str) -> BaseResource:
        """
        Get a specific resource by ID.

        Args:
            id_: Unique identifier for the resource

        Returns:
            Resource instance with full detail data
        """
        response = await self._session.get(self._get_detail_url(id_))
        return self.create_resource(response.json(), is_partial=False)

    async def create(
        self, data: Union[CreateModel, Dict[str, Any]]
    ) -> BaseResource:
        """
        Create a new resource.

        Args:
            data: Resource data model instance or dict

        Returns:
            Created resource instance
        """
        if isinstance(data, BaseModel):
            # Extract raw field values to avoid SerializationIterator issues
            # when file-like objects are involved.
            data_dict = model_to_dict(data)
        else:
            data_dict = {k: v for k, v in data.items() if v is not None}

        if self._has_file_fields(data_dict):
            response = await self._make_multipart_request(
                "POST", self._get_list_url(), data_dict
            )
        else:
            response = await self._session.post(
                self._get_list_url(), json=data_dict
            )

        return self.create_resource(response.json())

    async def update(
        self, id_: str, data: Union[UpdateModel, Dict[str, Any]]
    ) -> BaseResource:
        """
        Update an existing resource.

        Args:
            id_: Unique identifier for the resource
            data: Updated resource data model instance

        Returns:
            Updated resource instance
        """
        if isinstance(data, BaseModel):
            # Assuming the update requests do not include file-like objects
            data_dict = model_to_dict(data)
        else:
            if self.resource_update_class:
                data_dict = model_to_dict(
                    self.resource_update_class.model_validate(data)
                )
            else:
                # no validation. let the api handle it
                data_dict = {k: v for k, v in data.items() if v is not None}

        if self._has_file_fields(data_dict):
            response = await self._make_multipart_request(
                "PATCH", self._get_detail_url(id_), data_dict
            )
        else:
            response = await self._session.patch(
                self._get_detail_url(id_), json=data_dict
            )

        return self.create_resource(response.json())

    async def delete(self, id_: str) -> bool:
        """
        Delete a resource.

        Args:
            id_: Unique identifier for the resource

        Returns:
            True if deletion was successful
        """
        response = await self._session.delete(self._get_detail_url(id_))
        return response.status_code == 204

    async def iter_all(
        self,
        page_size: int = 100,
        filters: Optional[BaseFilters] = None,
        **filter_kwargs,
    ):
        """
        Memory-efficient iteration over all matching resources.

        Args:
            page_size: Number of items to fetch per page
            filters: Filter object for type-safe filtering
            **filter_kwargs: Filter arguments as keyword arguments

        Yields:
            Resource instances one by one
        """
        page = 1

        while True:
            response = await self.list(
                page=page,
                page_size=page_size,
                filters=filters,
                **filter_kwargs,
            )

            for item in response.payload:
                yield item

            if not response.has_next():
                break
            page += 1
