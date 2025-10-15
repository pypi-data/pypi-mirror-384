"""
Communication models for the Konigle SDK.

This module provides models for email, SMS, WhatsApp, and other
communication channels supported by the Konigle platform.
"""

from .email import *

__all__ = [
    # Email models
    "EmailAccount",
    "EmailAccountCreate",
    "EmailAccountUpdate",
    "EmailAccountSetup",
    "EmailChannel",
    "EmailChannelCreate",
    "EmailChannelUpdate",
    "EmailIdentity",
    "EmailIdentityCreate",
    "EmailIdentityUpdate",
    "EmailTemplate",
    "EmailTemplateCreate",
    "EmailTemplateUpdate",
    # Enums
    "EmailChannelType",
    "EmailChannelStatus",
    "EmailIdentityType",
    "EmailVerificationStatus",
    # Send models
    "Email",
    "EmailResponse",
]
