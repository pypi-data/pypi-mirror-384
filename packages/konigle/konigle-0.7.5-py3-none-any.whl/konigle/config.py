"""
Configuration management for the Konigle SDK.

This module provides configuration classes and utilities for managing
SDK settings, environment variables, and client configuration options.
"""

import os
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

BASE_URL = "https://tim.konigle.com"


class ClientConfig(BaseModel):
    """
    Client configuration schema with validation and defaults.

    This class defines all configuration options available for the Konigle SDK
    clients, with sensible defaults and environment variable support.

    Args:
        api_key: Konigle API key for authentication
        base_url: Base URL for the Konigle API
        timeout: Request timeout in seconds
        retry_count: Number of retries for failed requests
        retry_backoff: Base backoff time for exponential retry
        max_connections: Maximum number of HTTP connections in pool
        keepalive_connections: Number of connections to keep alive
        user_agent: Custom user agent string
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_requests: Whether to log HTTP requests
        log_responses: Whether to log HTTP responses
        enable_retry: Whether to enable automatic retries
    """

    api_key: str = Field(...)
    """Konigle API key for authentication."""

    base_url: str = Field(default=BASE_URL)
    """Base URL for the Konigle API."""

    timeout: float = Field(default=30.0, gt=0)
    """Request timeout in seconds."""

    retry_count: int = Field(default=3, ge=0, le=10)
    """Number of retries for failed requests."""

    retry_backoff: float = Field(default=0.5, ge=0)
    """Base backoff time for exponential retry."""

    max_connections: int = Field(default=100, gt=0, le=1000)
    """Maximum number of HTTP connections in pool."""

    keepalive_connections: int = Field(default=20, gt=0, le=100)
    """Number of connections to keep alive."""

    user_agent: Optional[str] = Field(default=None)
    """Custom user agent string."""

    log_level: str = Field(default="WARNING")
    """Logging level (DEBUG, INFO, WARNING, ERROR)."""

    log_requests: bool = Field(default=False)
    """Whether to log HTTP requests."""

    log_responses: bool = Field(default=False)
    """Whether to log HTTP responses."""

    enable_retry: bool = Field(default=True)
    """Whether to enable automatic retries."""

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v: str) -> str:
        """Normalize base URL by removing trailing slash."""
        return v.rstrip("/")

    @model_validator(mode="after")
    def validate_keepalive_connections(self):
        """Ensure keepalive connections doesn't exceed max connections."""
        if self.keepalive_connections > self.max_connections:
            raise ValueError(
                f"keepalive_connections ({self.keepalive_connections}) cannot "
                f"exceed max_connections ({self.max_connections})"
            )
        return self

    @classmethod
    def from_env(cls) -> "ClientConfig":
        """
        Create configuration from environment variables.

        Environment variables should be prefixed with KONIQ_ and follow
        the field names. For example: KONIQ_API_KEY, KONIQ_BASE_URL, etc.

        Returns:
            ClientConfig instance populated from environment variables

        Raises:
            ValidationError: If required fields are missing or invalid
        """
        env_vars = {}

        # Collect all KONIQ_ prefixed environment variables
        for key, value in os.environ.items():
            if key.startswith("KONIQ_"):
                field_name = key[6:].lower()  # Remove KONIQ_ prefix
                env_vars[field_name] = value

        return cls(**env_vars)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ClientConfig":
        """
        Create configuration from a dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            ClientConfig instance
        """
        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Export configuration as a dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return self.model_dump()

    def get_user_agent(self) -> str:
        """
        Get the user agent string for HTTP requests.

        Returns:
            User agent string, either custom or default
        """
        from . import __version__

        if self.user_agent:
            return f"{self.user_agent} konigle-python/{__version__}"
        else:
            return f"konigle-python/{__version__}"

    def get_http_limits(self) -> Dict[str, Any]:
        """
        Get HTTPX limits configuration.

        Returns:
            Dictionary with HTTPX limits configuration
        """
        return {
            "max_keepalive_connections": self.keepalive_connections,
            "max_connections": self.max_connections,
            "keepalive_expiry": 30.0,  # Fixed at 30 seconds
        }

    def should_retry_status_code(self, status_code: int) -> bool:
        """
        Determine if a status code should trigger a retry.

        Args:
            status_code: HTTP status code

        Returns:
            True if the status code indicates a retriable error
        """
        if not self.enable_retry:
            return False

        # Retry on server errors (5xx) and some client errors
        retriable_codes = {
            408,  # Request Timeout
            429,  # Too Many Requests
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        }

        return status_code in retriable_codes or 500 <= status_code < 600


# Default configuration instance
DEFAULT_CONFIG = ClientConfig(
    api_key="",  # Must be provided by user
    base_url=BASE_URL,
    timeout=30.0,
    retry_count=3,
    retry_backoff=0.5,
    max_connections=100,
    keepalive_connections=20,
    log_level="WARNING",
    log_requests=False,
    log_responses=False,
    enable_retry=True,
)
