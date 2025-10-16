"""
Base filter classes for the Konigle SDK.

This module provides the foundation for all filter models,
implementing common filtering patterns and validation.
"""

from pydantic import BaseModel, ConfigDict


class BaseFilters(BaseModel):
    """
    Base class for filter models.

    Provides common filtering patterns and validation
    for all resource filter classes.
    """

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True,
    )
