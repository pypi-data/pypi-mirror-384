"""
Shared enumerations for the Konigle SDK.

This module defines common enums used across the SDK infrastructure,
not model-specific enums which should be defined in their respective models.
"""

from enum import Enum


class SortOrder(str, Enum):
    """Common sort order options."""

    ASC = "asc"
    DESC = "desc"


class HTTPMethod(str, Enum):
    """HTTP methods for API requests."""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
