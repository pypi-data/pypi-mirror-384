"""
Email communication models for the Konigle SDK.

This module provides Pydantic models for email accounts, channels,
identities, and send operations with complete CRUD support.
"""

from .account import (
    EmailAccount,
    EmailAccountCreate,
    EmailAccountSetup,
    EmailAccountUpdate,
)
from .channel import (
    EmailChannel,
    EmailChannelCreate,
    EmailChannelStatus,
    EmailChannelType,
    EmailChannelUpdate,
)
from .identity import (
    EmailIdentity,
    EmailIdentityCreate,
    EmailIdentityType,
    EmailIdentityUpdate,
    EmailVerificationStatus,
)
from .send import Email, EmailResponse
from .template import EmailTemplate, EmailTemplateCreate, EmailTemplateUpdate

__all__ = [
    # Account models
    "EmailAccount",
    "EmailAccountCreate",
    "EmailAccountUpdate",
    "EmailAccountSetup",
    # Channel models
    "EmailChannel",
    "EmailChannelCreate",
    "EmailChannelUpdate",
    "EmailChannelType",
    "EmailChannelStatus",
    # Identity models
    "EmailIdentity",
    "EmailIdentityCreate",
    "EmailIdentityUpdate",
    "EmailIdentityType",
    "EmailVerificationStatus",
    # Send models
    "Email",
    "EmailResponse",
    # Template models
    "EmailTemplate",
    "EmailTemplateCreate",
    "EmailTemplateUpdate",
]
