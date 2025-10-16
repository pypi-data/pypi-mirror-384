"""
Konigle Integration Quickstart  Python SDK

A comprehensive Python SDK for the Konigle platform APIs, providing type-safe,
thread-safe, and async-capable access to CMS, commerce, and marketing resources.

Basic usage:
    import konigle

    client = konigle.Client(api_key="your-api-key")
    products = client.products.list(status='published')

Async usage:
    import konigle

    async with konigle.AsyncClient(api_key="your-api-key") as client:
        products = await client.products.list(status='published')
"""

__version__ = "0.1.0"

# Main modules for lazy loading
from . import filters, models, types

# Core client classes
from .client import AsyncClient, Client

# Configuration utilities
from .config import ClientConfig

# Exception hierarchy for structured error handling
from .exceptions import (
    APIError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    KonigleError,
    KonigleTimeoutError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    ValidationError,
)

# Logging utilities
from .logging import configure_logging, get_logger, set_log_level

__all__ = [
    # Version
    "__version__",
    # Core clients
    "Client",
    "AsyncClient",
    # Exceptions
    "KonigleError",
    "APIError",
    "AuthenticationError",
    "AuthorizationError",
    "ValidationError",
    "NotFoundError",
    "ConflictError",
    "RateLimitError",
    "ServerError",
    "NetworkError",
    "KonigleTimeoutError",
    # Configuration
    "ClientConfig",
    # Logging
    "get_logger",
    "set_log_level",
    "configure_logging",
    # Modules
    "models",
    "filters",
    "types",
]
