"""
Communication managers for the Konigle SDK.

This module provides manager classes for email, SMS, WhatsApp, and other
communication channels supported by the Konigle platform.
"""

from .email import *

__all__ = [
    # Email managers
    "EmailAccountManager", 
    "AsyncEmailAccountManager",
    "EmailChannelManager",
    "AsyncEmailChannelManager",
    "EmailIdentityManager",
    "AsyncEmailIdentityManager",
]