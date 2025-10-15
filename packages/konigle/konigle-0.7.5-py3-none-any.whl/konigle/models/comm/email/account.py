"""
Email account models for the Konigle SDK.

Email accounts represent the main account container for a website's email
configuration, containing default settings and serving as the parent for
email channels and identities.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from konigle.models.base import CreateModel, TimestampedResource, UpdateModel


class BaseEmailAccount(BaseModel):

    name: str = Field(
        title="Account Name",
        description="Name of the email account.",
        max_length=255,
    )
    """Name of the email account."""

    default_from_email: Optional[EmailStr] = Field(
        default="",
        title="Default From Email",
        description="Default from email address for this account.",
    )
    """Default from email address."""

    default_from_name: Optional[str] = Field(
        default="",
        title="Default From Name",
        description="Default from name for email headers.",
        max_length=255,
    )
    """Default from name."""

    default_reply_to_email: Optional[str] = Field(
        default="",
        title="Default Reply-To Email",
        description="Default reply-to email address.",
    )
    """Default reply-to email address."""

    default_reply_to_name: Optional[str] = Field(
        default="",
        title="Default Reply-To Name",
        description="Default reply-to name for email headers.",
        max_length=255,
    )
    """Default reply-to name."""


class EmailAccount(BaseEmailAccount, TimestampedResource):
    """
    Email account for a website.

    Each website gets one email account that contains the default email
    configuration and serves as the parent for email channels and identities.
    """

    is_active: bool = Field(
        default=True,
        title="Is Active",
        description="Whether the email account is active and can be used.",
    )
    """Whether the email account is active."""

    def __str__(self) -> str:
        return (
            f"EmailAccount(id = {self.id} name={self.name} "
            f"is_active={self.is_active})"
        )


class EmailAccountCreate(BaseEmailAccount, CreateModel):
    """Model for creating a new email account."""


class EmailAccountSetup(BaseModel):
    """Model for setting up an email account with initial configuration."""

    account_name: str = Field(
        title="Account Name",
        description="Name of the email account.",
        max_length=255,
    )
    """Name of the email account."""

    default_from_email: EmailStr = Field(
        title="Default From Email",
        description="Default from email address for this account.",
    )
    """Default from email address."""

    default_reply_to_email: Optional[EmailStr] = Field(
        default=None,
        title="Default Reply-To Email",
        description="Default reply-to email address.",
    )
    """Default reply-to email address."""

    identity_value: str = Field(
        title="Identity Value",
        description="Email address or domain to verify as an identity.",
        max_length=255,
    )
    """Email address or domain to verify as an identity."""


class EmailAccountUpdate(UpdateModel):
    """Model for updating an existing email account."""

    name: Optional[str] = Field(
        default=None,
        title="Account Name",
        description="Name of the email account.",
        max_length=255,
    )
    """Name of the email account."""

    default_from_email: Optional[EmailStr] = Field(
        default=None,
        title="Default From Email",
        description="Default from email address for this account.",
    )
    """Default from email address."""

    default_from_name: Optional[str] = Field(
        default=None,
        title="Default From Name",
        description="Default from name for email headers.",
        max_length=255,
    )
    """Default from name."""

    default_reply_to_email: Optional[EmailStr] = Field(
        default=None,
        title="Default Reply-To Email",
        description="Default reply-to email address.",
    )
    """Default reply-to email address."""

    default_reply_to_name: Optional[str] = Field(
        default=None,
        title="Default Reply-To Name",
        description="Default reply-to name for email headers.",
        max_length=255,
    )
    """Default reply-to name."""
