"""
Email channel models for the Konigle SDK.

Email channels represent different types of email flows within an account,
such as transactional, marketing, or broadcast emails, each with their
own configuration and quotas.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import AfterValidator, BaseModel, Field

from konigle.models.base import CreateModel, TimestampedResource, UpdateModel
from konigle.validators import validate_handle


class EmailChannelType(str, Enum):
    """Types of email channels available."""

    TRANSACTIONAL = "transactional"
    """Transactional emails like order confirmations, password resets."""

    MARKETING = "marketing"
    """Marketing emails like newsletters, promotions."""

    BROADCAST = "broadcast"
    """Broadcast emails like announcements, updates."""


class EmailChannelStatus(str, Enum):
    """Status of an email channel."""

    ACTIVE = "active"
    """Channel is active and can send emails."""

    SUSPENDED = "suspended"
    """Channel is suspended and cannot send emails."""

    PENDING = "pending"
    """Channel is pending setup or verification."""


class BaseEmailChannel(BaseModel):

    code: Annotated[str, AfterValidator(validate_handle)] = Field(
        title="Channel Code",
        description="Unique code for the channel used when sending emails.",
        max_length=50,
    )
    """Unique code for the channel given by the user that is used to 
    refer to when sending the emails."""

    channel_type: EmailChannelType = Field(
        title="Channel Type",
        description="Type of email channel (transactional, marketing, "
        "broadcast).",
    )
    """Type of email channel."""


class EmailChannel(BaseEmailChannel, TimestampedResource):
    """
    Email channel for different types of emails within an account.

    Channels separate different email flows (transactional, marketing, etc.)
    and provide individual configuration and rate limiting.
    """

    account: str = Field(
        title="Account ID",
        description="ID of the email account this channel belongs to.",
    )
    """Email account this channel belongs to."""

    status: EmailChannelStatus = Field(
        default=EmailChannelStatus.ACTIVE,
        title="Channel Status",
        description="Current status of the channel.",
    )
    """Current status of the channel."""

    suspension_reason: Optional[str] = Field(
        default=None,
        title="Suspension Reason",
        description="Reason for suspension if applicable.",
        max_length=255,
    )
    """Reason for suspension if applicable."""

    suspended_at: Optional[datetime] = Field(
        default=None,
        title="Suspended At",
        description="When the channel was suspended.",
    )
    """When the channel was suspended."""

    daily_quota: int = Field(
        default=1000,
        title="Daily Quota",
        description="Daily email quota for this channel.",
        ge=1,
    )
    """Daily email quota for this channel."""

    rate_limit: int = Field(
        default=10,
        title="Rate Limit",
        description="Rate limit (emails per second) for this channel.",
        ge=1,
    )
    """Rate limit (emails per second) for this channel."""

    def __str__(self) -> str:
        return (
            f"EmailChannel(id = {self.id} code={self.code} "
            f"type={self.channel_type} status={self.status})"
        )


class EmailChannelCreate(BaseEmailChannel, CreateModel):
    """Model for creating a new email channel."""


class EmailChannelUpdate(UpdateModel):
    """Model for updating an existing email channel."""

    code: Optional[str] = Field(
        default=None,
        title="Channel Code",
        description="Unique code for the channel used when sending emails.",
        max_length=50,
    )
    """Unique code for the channel given by the user that is used to refer
    to when sending the emails."""
