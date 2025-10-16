"""
Custom exception hierarchy for structured error handling in the Konigle SDK.

This module defines a comprehensive set of exceptions that map to specific
HTTP status codes and error conditions, providing clear context for error
handling in client applications.
"""

from typing import Any, Dict, Optional


class KonigleError(Exception):
    """
    Base exception for all SDK errors.

    All Konigle SDK exceptions inherit from this base class, making it easy
    to catch any SDK-related error.
    """


class APIError(KonigleError):
    """
    Base class for API-related errors with structured information.

    Args:
        message: Human-readable error message
        status_code: HTTP status code from the API response
        response: Full response data from the API
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.response = response or {}
        super().__init__(message)

    def __str__(self) -> str:
        """Enhanced string representation with context."""
        base_msg = super().__str__()
        if self.status_code:
            base_msg = f"HTTP {self.status_code}: {base_msg}"
        return base_msg


class AuthenticationError(APIError):
    """
    Invalid API key or authentication failure (HTTP 401).

    This error indicates that the provided API key is invalid, expired,
    or missing from the request.
    """


class AuthorizationError(APIError):
    """
    Insufficient permissions for the requested operation (HTTP 403).

    The API key is valid but doesn't have permission to perform the
    requested action on the specified resource.
    """


class ValidationError(APIError):
    """
    Request validation failed (HTTP 400).

    This error includes detailed information about which fields failed
    validation and why.

    Args:
        message: General validation error message
        field_errors: Dictionary mapping field names to error messages
        **kwargs: Additional arguments passed to APIError
    """

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        self.field_errors = field_errors or {}
        super().__init__(message, **kwargs)

    def __str__(self) -> str:
        """Enhanced representation including field-specific errors."""
        base_msg = super().__str__()
        if self.field_errors:
            field_details = []
            for field, errors in self.field_errors.items():
                if isinstance(errors, list):
                    field_details.append(
                        f"{field}: {', '.join(str(e) for e in errors)}"
                    )
                else:
                    field_details.append(f"{field}: {errors}")
            if field_details:
                base_msg = (
                    f"{base_msg} | Field errors: {'; '.join(field_details)}"
                )
        return base_msg


class NotFoundError(APIError):
    """
    Resource not found (HTTP 404).

    The requested resource does not exist or has been deleted.
    """


class ConflictError(APIError):
    """
    Resource conflict (HTTP 409).

    The request conflicts with the current state of the resource.
    Common causes include duplicate unique values or concurrent modifications.
    """


class RateLimitError(APIError):
    """
    Rate limit exceeded (HTTP 429).

    Too many requests have been made in a short time period.

    Args:
        message: Rate limit error message
        retry_after: Number of seconds to wait before retrying
        **kwargs: Additional arguments passed to APIError
    """

    def __init__(
        self, message: str, retry_after: Optional[int] = None, **kwargs
    ):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)

    def __str__(self) -> str:
        """Enhanced representation including retry timing."""
        base_msg = super().__str__()
        if self.retry_after:
            base_msg = f"{base_msg} (Retry after {self.retry_after} seconds)"
        return base_msg


class ServerError(APIError):
    """
    Server-side errors (HTTP 5xx).

    An error occurred on the server side. These errors are typically
    temporary and may be resolved by retrying the request.
    """


class NetworkError(KonigleError):
    """
    Network connectivity issues.

    This error is raised when network-level problems prevent
    communication with the API server.
    """


class KonigleTimeoutError(KonigleError):
    """
    Request timeout.

    The request took longer than the configured timeout period.
    """


def map_http_error(
    status_code: int,
    message: str,
    response_data: Optional[Dict[str, Any]] = None,
) -> APIError:
    """
    Map HTTP status codes to appropriate exception classes.

    Args:
        status_code: HTTP status code from the response
        message: Error message from the API or generated
        response_data: Full response data from the API

    Returns:
        Appropriate APIError subclass instance
    """
    error_kwargs = {
        "status_code": status_code,
        "response": response_data,
    }

    if status_code == 400:
        return ValidationError(
            message, field_errors=response_data, **error_kwargs
        )

    elif status_code == 401:
        return AuthenticationError(message, **error_kwargs)

    elif status_code == 403:
        return AuthorizationError(message, **error_kwargs)

    elif status_code == 404:
        return NotFoundError(message, **error_kwargs)

    elif status_code == 409:
        return ConflictError(message, **error_kwargs)

    elif status_code == 429:
        retry_after = None
        if response_data:
            retry_after = response_data.get("retry_after")
        return RateLimitError(message, retry_after=retry_after, **error_kwargs)

    elif 500 <= status_code < 600:
        return ServerError(message, **error_kwargs)

    else:
        # Fallback for any other status codes
        return APIError(message, **error_kwargs)
