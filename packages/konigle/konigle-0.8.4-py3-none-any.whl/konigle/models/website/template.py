"""
Template models for the Konigle SDK.

This module provides models for template resources including creation,
update, and resource representations.
"""

import re
from typing import Annotated, Any, ClassVar, Dict, List, Optional, Set

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from konigle.models.base import CreateModel, TimestampedResource, UpdateModel
from konigle.validators import validate_handle


def _validate_block_key(key: str) -> str:
    pattern = r"^[a-z0-9_]+\Z"
    if not re.search(pattern, key):
        raise ValueError("keys must only contain lowercase, numbers and _")
    return key


BlockKey = Annotated[str, AfterValidator(_validate_block_key)]


class Block(BaseModel):
    """Block represents a section of the page."""

    type: str = "component"
    """Type of the block. Currently only 'component' is supported."""

    component_id: Optional[str] = Field(
        default=None,
        title="Component ID",
        description="ID of the component used in this block",
    )
    """ID of the component used in this block."""

    name: Optional[str] = Field(
        default="",
        title="Block Name",
        description="Optional name for the block",
    )
    # Allow extra so that updating the layout does not exclude the unsupported
    # fields.
    model_config = ConfigDict(extra="allow")


class Segment(BaseModel):
    """Segment represents a collection of blocks."""

    blocks: Dict[BlockKey, Block] = Field(
        default_factory=dict,
        title="Blocks",
        description="Blocks within this segment",
    )

    order: List[BlockKey] = Field(
        default_factory=list,
        title="Block Order",
        description="Order of blocks in this segment",
    )
    """Order of blocks in this segment. Must match keys in blocks."""

    # Allow extra so that updating the layout does not exclude the unsupported
    # fields.
    model_config = ConfigDict(extra="allow")


class TemplateLayout(BaseModel):
    """Layout configuration for site templates."""

    version: str = "2"

    header: Optional[Segment] = Field(
        default=None,
        title="Header",
        description="Header segment of the layout",
    )

    main: Optional[Segment] = Field(
        default=None,
        title="Main",
        description="Main content segment of the layout",
    )

    footer: Optional[Segment] = Field(
        default=None,
        title="Footer",
        description="Footer segment of the layout",
    )

    css_assets: List[Any] = Field(
        default_factory=list,
    )
    """CSS included in this layout. Not supported in SDK yet."""

    js_assets: List[Any] = Field(
        default_factory=list,
    )
    """JS included in this layout. Not supported in SDK yet."""

    template_id: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the template this layout belongs to",
    )
    """This is same as the template ID on the main model. Must not change."""

    # Allow extra so that updating the layout does not exclude the unsupported
    # fields.
    model_config = ConfigDict(extra="allow")


class BaseTemplate(BaseModel):
    """
    Base class for template models with common editable fields.

    Contains fields that can be set during creation/update.
    """

    name: str = Field(
        ...,
        max_length=255,
        title="Name",
        description="Name of the template for identification",
    )
    """Name of the template for identification."""

    handle: Annotated[str, AfterValidator(validate_handle)] = Field(
        ...,
        max_length=255,
        title="Handle",
        description="Handle to identify template",
    )
    """Handle to identify template"""

    layout: Optional[TemplateLayout] = Field(
        default=None,
        title="Layout",
        description="Layout containing header, footer, main",
    )
    """Layout containing header, footer, main etc."""

    is_base: bool = Field(
        default=False,
        title="Is Base Template",
        description="Whether this is a base template for common layout",
    )
    """Whether this is a base template for common layout."""

    base: Optional[str] = Field(
        default=None,
        title="Base Template",
        description="Base template ID for this template",
    )
    """Base template ID for this template."""


class Template(BaseTemplate, TimestampedResource):
    """
    Template resource model.

    Represents a template for building landing pages with components.
    """

    # Metadata for field loading behavior
    _detail_only_fields: ClassVar[Set[str]] = {
        "layout",
        "included_component_ids",
    }
    _foreign_key_fields: ClassVar[Set[str]] = {"base"}

    handle: str = Field(
        ...,
        max_length=255,
        title="Handle",
        description="Handle to identify template",
    )
    """Handle to identify template"""

    included_component_ids: List[str] = Field(
        default_factory=list,
        title="Included Component IDs",
        description="List of component IDs included in the template",
    )
    """List of component IDs included in the template. This is a computed
    field."""

    def __str__(self) -> str:
        return (
            f"Template(id = {self.id}, name = {self.name}, "
            f"handle = {self.handle}), is_base = {self.is_base}"
        )


class TemplateCreate(BaseTemplate, CreateModel):
    """
    Model for creating a new template.

    Contains all required and optional fields for template creation.
    """

    pass


class TemplateUpdate(UpdateModel):
    """
    Model for updating an existing template.

    All fields are optional for partial updates.
    """

    name: Optional[str] = Field(
        default=None,
        max_length=255,
        title="Name",
        description="Name of the template for identification",
    )
    """Name of the template for identification."""

    handle: Optional[Annotated[str, AfterValidator(validate_handle)]] = Field(
        default=None,
        max_length=255,
        title="Handle",
        description="Handle to identify template",
    )
    """Handle to identify template"""

    layout: Optional[TemplateLayout] = Field(
        default=None,
        title="Layout",
        description="Layout containing header, footer, main etc.",
    )
    """Layout containing header, footer, main etc."""

    is_base: Optional[bool] = Field(
        default=None,
        title="Is Base Template",
        description="Whether this is a base template for common layout",
    )
    """Whether this is a base template for common layout."""

    base: Optional[str] = Field(
        default=None,
        title="Base Template",
        description="Base template ID for this template",
    )
    """Base template ID for this template."""


__all__ = [
    "Template",
    "TemplateCreate",
    "TemplateUpdate",
]
