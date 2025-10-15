"""
Logging configuration and utilities for the Konigle SDK.

This module provides centralized logging setup with support for both
development and production environments, structured logging, and
integration with the SDK's configuration system.
"""

import json
import logging
import sys
from typing import Optional, Union


class KonigleLogger:
    """Centralized logging configuration for the SDK."""

    _logger: Optional[logging.Logger] = None
    _handler: Optional[logging.Handler] = None

    @classmethod
    def get_logger(cls) -> logging.Logger:
        """
        Get configured logger instance.

        Returns:
            Configured logger instance for the SDK
        """
        if cls._logger is None:
            cls._logger = logging.getLogger("konigle")
            cls._logger.setLevel(logging.WARNING)  # Default level

            if not cls._logger.handlers:
                cls._setup_default_handler()

        return cls._logger

    @classmethod
    def _setup_default_handler(cls):
        """Setup default console handler with structured formatting."""
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger = cls.get_logger()
        logger.addHandler(handler)
        cls._handler = handler

    @classmethod
    def set_level(cls, level: Union[str, int]):
        """
        Set logging level.

        Args:
            level: Logging level as string or integer constant
        """
        logger = cls.get_logger()
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        logger.setLevel(level)

    @classmethod
    def add_handler(cls, handler: logging.Handler):
        """
        Add custom logging handler.

        Args:
            handler: Custom logging handler to add
        """
        logger = cls.get_logger()
        logger.addHandler(handler)

    @classmethod
    def configure_for_development(cls):
        """Configure logging for development with detailed output."""
        cls.set_level(logging.DEBUG)

        # Add detailed formatter for development
        if cls._handler:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - "
                "[%(filename)s:%(lineno)d] - %(message)s"
            )
            cls._handler.setFormatter(formatter)

    @classmethod
    def configure_for_production(cls):
        """Configure logging for production with structured JSON output."""

        class JSONFormatter(logging.Formatter):
            """JSON formatter for structured logging in production."""

            def format(self, record):
                """Format log record as JSON."""
                log_data = {
                    "timestamp": self.formatTime(record),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno,
                }

                # Add extra fields if present
                if hasattr(record, "http_method"):
                    log_data["http_method"] = record.http_method
                if hasattr(record, "url"):
                    log_data["url"] = record.url
                if hasattr(record, "status_code"):
                    log_data["status_code"] = record.status_code
                if hasattr(record, "response_time"):
                    log_data["response_time"] = record.response_time

                return json.dumps(log_data)

        if cls._handler:
            cls._handler.setFormatter(JSONFormatter())


# Module-level convenience functions
def get_logger() -> logging.Logger:
    """
    Get the main Konigle logger.

    Returns:
        Main logger instance for the SDK
    """
    return KonigleLogger.get_logger()


def set_log_level(level: Union[str, int]):
    """
    Set SDK logging level.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
               as string or integer constant
    """
    KonigleLogger.set_level(level)


def configure_logging(development: bool = False):
    """
    Configure logging for environment.

    Args:
        development: If True, configure for development with detailed output.
                    If False, configure for production with JSON structured logs.
    """
    if development:
        KonigleLogger.configure_for_development()
    else:
        KonigleLogger.configure_for_production()


def add_handler(handler: logging.Handler):
    """
    Add a custom logging handler.

    Args:
        handler: Custom logging handler to add to the SDK logger
    """
    KonigleLogger.add_handler(handler)
