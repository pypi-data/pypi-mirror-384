"""
Email managers for the Konigle SDK.

This module provides manager classes for email accounts, channels,
identities, and email operations with complete CRUD support.
"""

from .account import AsyncEmailAccountManager, EmailAccountManager
from .channel import AsyncEmailChannelManager, EmailChannelManager
from .email import AsyncEmailManager, EmailManager
from .identity import AsyncEmailIdentityManager, EmailIdentityManager
from .template import AsyncEmailTemplateManager, EmailTemplateManager

__all__ = [
    # Account managers
    "EmailAccountManager",
    "AsyncEmailAccountManager",
    # Channel managers
    "EmailChannelManager",
    "AsyncEmailChannelManager",
    # Identity managers
    "EmailIdentityManager",
    "AsyncEmailIdentityManager",
    # Email operation managers
    "EmailManager",
    "AsyncEmailManager",
    # Template managers
    "EmailTemplateManager",
    "AsyncEmailTemplateManager",
]
