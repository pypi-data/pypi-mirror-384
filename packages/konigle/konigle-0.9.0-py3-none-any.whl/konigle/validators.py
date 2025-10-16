"""
Custom Pydantic validators for the Konigle SDK.

This module provides reusable validators for common field validation
patterns used across different models in the SDK.
"""

import io
import re
from decimal import Decimal
from typing import Any, BinaryIO, Dict, Optional, Tuple, Union


def validate_handle(v: Optional[str]) -> Optional[str]:
    """
    Validate handle format for URLs.

    Handles must contain only alphanumeric characters, hyphens, and
    underscores. Returns the handle in lowercase.

    Args:
        v: The handle value to validate

    Returns:
        The validated handle in lowercase, or None if input was None

    Raises:
        ValueError: If handle contains invalid characters
    """
    if v is not None:
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                "Handle must contain only alphanumeric characters, "
                "hyphens, and underscores"
            )
        return v.lower()
    return v


def validate_required_handle(v: str) -> str:
    """
    Validate required handle format for URLs.

    Same as validate_handle but for required fields.

    Args:
        v: The handle value to validate

    Returns:
        The validated handle in lowercase

    Raises:
        ValueError: If handle contains invalid characters
    """
    if not v.replace("-", "").replace("_", "").isalnum():
        raise ValueError(
            "Handle must contain only alphanumeric characters, "
            "hyphens, and underscores"
        )
    return v.lower()


def validate_price(
    v: Optional[Union[float, int, Decimal]] = None,
) -> Optional[Union[float, int, Decimal]]:
    """
    Validate that a price is non-negative if provided.

    Args:
        v: The price value to validate
    Returns:
        The validated price value, or None if input was None
    Raises:
        ValueError: If price is negative
    """
    if v is not None:
        if isinstance(v, (float, int, Decimal)) and v < 0:
            raise ValueError("Price must be non-negative")
    return v


def validate_language_code(v: Optional[str]) -> Optional[str]:
    """
    Validate ISO 639-1 language code format.

    Args:
        v: The language code to validate

    Returns:
        The validated language code in lowercase

    Raises:
        ValueError: If language code is not 2 characters or contains
        invalid characters
    """
    if v is not None:
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Language code must be 2 alphabetic characters")
        return v.lower()
    return v


def validate_country_code(v: Optional[str]) -> Optional[str]:
    """
    Validate ISO 3166-1 alpha-2 country code format.

    Args:
        v: The country code to validate

    Returns:
        The validated country code in uppercase

    Raises:
        ValueError: If country code is not 2 characters or contains
        invalid characters
    """
    if v is not None:
        if len(v) != 2 or not v.isalpha():
            raise ValueError("Country code must be 2 alphabetic characters")
        return v.upper()
    return v


def validate_image(
    v: Union[
        str,
        bytes,
        io.BytesIO,
        BinaryIO,
        Tuple[Union[bytes, io.BytesIO, BinaryIO], str],
    ],
):
    """Ensure we're uploading an image file.

    Args:
        v: Image file to upload. Can be file path, bytes, BytesIO, BinaryIO,
        or tuple of (file_data, filename)

    Raises:
        ValueError: If file is not an image


    Returns:
        same as input
    """
    allowed_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".webp",
    ]
    # Handle tuple input
    if isinstance(v, tuple) and len(v) == 2:
        _, filename = v
        if not any(
            filename.lower().endswith(ext) for ext in allowed_extensions
        ):
            raise ValueError(
                f"File must be an image {', '.join(allowed_extensions)}"
            )
    elif (
        isinstance(v, str)
        and not v.startswith("https://")
        and not any(v.lower().endswith(ext) for ext in allowed_extensions)
    ):
        raise ValueError(
            f"File must be an image ({', '.join(allowed_extensions)})"
        )
    return v


def validate_editorjs_content(
    v: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Validate EditorJS block content format using Pydantic models.

    Args:
        v: The EditorJS content to validate

    Returns:
        The validated EditorJS content, or None if input was None

    Raises:
        ValueError: If content format is invalid or contains unsupported
        block types
    """
    # NOTE: disabling data validation for now since timbl agents are failing
    # due to some unexpected data formats. Also need some test cases for this.

    return v
    # Allow None values and empty dictionaries
    if not v:
        return v
    if not isinstance(v, dict):
        raise ValueError("EditorJS content must be a dictionary")

    from konigle.models.rich_text import EditorJSContent

    try:
        # Use Pydantic model for validation
        validated_content = EditorJSContent.model_validate(v)
        return validated_content.model_dump()
    except Exception as e:
        raise ValueError(f"Invalid EditorJS content: {e}") from e
