"""
Shared utilities for the Konigle SDK.

This module provides essential utility functions used throughout
the SDK for file handling and URL construction.
"""

import io
import mimetypes
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Dict, Tuple, Union
from urllib.parse import urlparse
from urllib.request import urlretrieve

from pydantic import BaseModel

from .logging import get_logger

logger = get_logger()


class FileInput:
    """Utility class for handling various file input types."""

    @staticmethod
    def normalize(
        file_input: Union[
            str,
            Path,
            BinaryIO,
            bytes,
            io.BytesIO,
            Tuple[Union[BinaryIO, bytes, io.BytesIO], str],
        ],
        filename: str | None = None,
    ) -> Union[BinaryIO, io.BytesIO]:
        """
        Normalize various file input types to BytesIO with name attribute.

        Args:
            file_input: File input in various formats (path, bytes, file
            object, URL, or tuple of (file_data, filename))
            filename: Optional filename to use if file_input doesn't have one

        Returns:
            BytesIO object with name attribute set

        Raises:
            FileNotFoundError: If file path doesn't exist
            ValueError: If unsupported file input type
        """
        # Handle tuple input (file_data, filename)
        if isinstance(file_input, tuple) and len(file_input) == 2:
            file_data, provided_filename = file_input
            # Recursively normalize the file_data part with the provided
            # filename
            return FileInput.normalize(file_data, provided_filename)

        if isinstance(file_input, str):
            # Check if it's a URL
            if file_input.startswith("https://"):
                parsed_url = urlparse(file_input)
                url_filename = Path(parsed_url.path).name or "download"

                # Download to temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.close()

                logger.info(f"Downloading file from URL: {file_input}")

                # urlretrieve returns (filename, headers)
                _, headers = urlretrieve(file_input, temp_file.name)

                # Add extension from Content-Type if URL filename has no
                # extension
                if not Path(url_filename).suffix:
                    content_type = headers.get("Content-Type", "").split(";")[
                        0
                    ]
                    extension = mimetypes.guess_extension(content_type) or ""
                    url_filename += extension

                with open(temp_file.name, "rb") as f:
                    file_data = f.read()

                temp_file.unlink()  # Clean up temp file

                file = io.BytesIO(file_data)
                file.name = filename or url_filename
                return file

            # Handle as file path
            file_path = Path(file_input)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            # NOTE: Does httpx close the file after sending? If not we are
            # leaking file handles here.
            return open(file_path, "rb")

        elif isinstance(file_input, Path):
            file_path = file_input
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            return open(file_path, "rb")

        elif isinstance(file_input, bytes):
            # Create BytesIO and add name attribute
            file_obj = io.BytesIO(file_input)
            file_obj.name = filename or "upload.bin"
            return file_obj

        elif isinstance(file_input, io.BytesIO):
            # Add name attribute to existing BytesIO
            if not hasattr(file_input, "name"):
                file_input.name = filename or "upload.bin"
            elif filename:
                # Override with provided filename
                file_input.name = filename
            return file_input

        elif (
            isinstance(file_input, io.IOBase)
            and hasattr(file_input, "read")
            and hasattr(file_input, "name")
        ):
            # Already a proper file-like object with name
            return file_input  # type: ignore

        else:
            raise ValueError(
                f"Unsupported file input type: {type(file_input)}"
            )

    @staticmethod
    def get_content_type(filename: str) -> str:
        """
        Get MIME type for filename.

        Args:
            filename: Name of the file

        Returns:
            MIME type string
        """
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or "application/octet-stream"


def build_url_path(*parts: str) -> str:
    """
    Build URL path from parts, ensuring proper slash handling.

    Args:
        *parts: URL path components

    Returns:
        Properly formatted URL path
    """
    # Filter out None and empty string parts
    clean_parts = [str(part).strip("/") for part in parts if part]

    if not clean_parts:
        return "/"

    return "/" + "/".join(clean_parts) + "/"


def model_to_dict(model: BaseModel) -> Dict[str, Any]:
    """Convert a Pydantic model to a dict, excluding None and unset fields
    and handling file fields appropriately for multipart requests.
    """

    def _is_file_field(value: Any) -> bool:
        return isinstance(value, (io.BytesIO, io.IOBase)) or (
            hasattr(value, "read") and hasattr(value, "name")
        )

    # Get file field names
    file_fields = []
    for field_name in model.__class__.model_fields:
        field_value = getattr(model, field_name, None)
        if _is_file_field(field_value):
            file_fields.append(field_name)
        elif isinstance(field_value, list):
            if any(_is_file_field(item) for item in field_value):
                file_fields.append(field_name)

    # Dump excluding file fields
    data_dict = model.model_dump(
        mode="json",
        exclude_none=True,
        exclude=set(file_fields),
    )
    # Add file fields back for multipart handling
    for field_name in file_fields:
        data_dict[field_name] = getattr(model, field_name)
    return data_dict
