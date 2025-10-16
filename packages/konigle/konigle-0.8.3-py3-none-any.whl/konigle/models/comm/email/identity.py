"""
Email identity models for the Konigle SDK.

Email identities represent domains or email addresses that have been
verified for sending emails, including DKIM and SPF configuration.
"""

from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field

from konigle.models.base import CreateModel, TimestampedResource, UpdateModel


class EmailIdentityType(str, Enum):
    """Types of email identities."""

    DOMAIN = "domain"
    """Domain identity (e.g., example.com)."""

    EMAIL = "email"
    """Email address identity (e.g., noreply@example.com)."""


class EmailVerificationStatus(str, Enum):
    """Email verification status."""

    PENDING = "pending"
    """Verification is pending."""

    SUCCESS = "success"
    """Verification successful."""

    FAILED = "failed"
    """Verification failed."""


class EmailIdentity(TimestampedResource):
    """
    Identities (domains or email addresses) for sending emails.

    Identities must be verified before they can be used to send emails.
    This includes DKIM and SPF verification for domains.
    """

    account: str = Field(
        title="Account ID",
        description="ID of the email account this identity belongs to.",
    )
    """Email account this identity belongs to."""

    identity_type: EmailIdentityType = Field(
        title="Identity Type",
        description="Type of identity (domain or email).",
    )
    """Type of identity (domain or email)."""

    identity_value: str = Field(
        title="Identity Value",
        description="The domain or email address value.",
        max_length=255,
    )
    """The domain or email address value."""

    verified: bool = Field(
        default=False,
        title="Verified",
        description="Whether the identity is verified for sending emails.",
    )
    """Whether the identity is verified for sending emails."""

    dkim_verification_status: EmailVerificationStatus = Field(
        default=EmailVerificationStatus.PENDING,
        title="DKIM Verification Status",
        description="DKIM verification status.",
    )
    """DKIM verification status."""

    dkim_verified: bool = Field(
        default=False,
        title="DKIM Verified",
        description="Whether DKIM is verified.",
    )
    """Whether DKIM is verified."""

    mail_from_domain: Optional[str] = Field(
        default=None,
        title="MAIL FROM Domain",
        description="Custom MAIL FROM domain used for envelope sender.",
        max_length=255,
    )
    """Custom MAIL FROM domain used for envelope sender."""

    mail_from_verification_status: EmailVerificationStatus = Field(
        default=EmailVerificationStatus.PENDING,
        title="MAIL FROM Verification Status",
        description="MAIL FROM domain verification status. "
        "This is SPF verification status.",
    )
    """MAIL FROM domain verification status. This is SPF verification status."""

    mail_from_verified: bool = Field(
        default=False,
        title="MAIL FROM Verified",
        description="Whether MAIL FROM domain is verified.",
    )
    """Whether MAIL FROM domain is verified."""

    use_custom_mail_from: bool = Field(
        default=False,
        title="Use Custom MAIL FROM",
        description="Whether to use custom MAIL FROM domain.",
    )
    """Whether to use custom MAIL FROM domain."""

    dkim_records: List[Dict[str, str]] = Field(
        default_factory=list,
        title="DKIM Records",
        description="DKIM DNS records to be added for verification.",
    )
    """DKIM DNS records to be added for verification."""

    mail_from_records: List[Dict[str, str]] = Field(
        default_factory=list,
        title="MAIL FROM Records",
        description="MAIL FROM DNS records to be added for verification.",
    )
    """MAIL FROM DNS records to be added for verification."""

    def __str__(self) -> str:
        return (
            f"EmailIdentity(id = {self.id} type={self.identity_type} "
            f"value={self.identity_value} verified={self.verified})"
        )


class EmailIdentityCreate(CreateModel):
    """Model for creating a new email identity."""

    identity_value: str = Field(
        title="Identity Value",
        description="The domain or email address value.",
        max_length=255,
    )
    """The domain or email address value."""


class EmailIdentityUpdate(UpdateModel):
    """Model for updating an existing email identity."""

    use_custom_mail_from: Optional[bool] = Field(
        default=None,
        title="Use Custom MAIL FROM",
        description="Whether to use custom MAIL FROM domain.",
    )
    """Whether to use custom MAIL FROM domain."""
