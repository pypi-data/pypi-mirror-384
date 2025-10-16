"""
Email template models for the Konigle SDK.

Email templates allow users to create reusable email content with variable
placeholders for dynamic content insertion. Templates belong to an email
account and can be used for sending consistent, branded communications.

Templates do not support any context as of now except for built in context
`unsubscribe_link` if the email is sent to a single recipient.
"""

from typing import List, Optional

from pydantic import BaseModel, Field

from konigle.models.base import CreateModel, TimestampedResource, UpdateModel


class BaseEmailTemplate(BaseModel):

    name: str = Field(
        title="Template Name",
        description="Name of the email template.",
        max_length=255,
    )
    """Name of the email template."""

    code: str = Field(
        title="Template Code",
        description="Unique code for the template.",
        max_length=100,
    )
    """Unique code for the template."""

    subject: str = Field(
        title="Subject Template",
        description="Subject line template with variable placeholders.",
    )
    """Subject line template with variable placeholders."""

    body_html: str = Field(
        title="HTML Body Template",
        description="HTML body template with variable placeholders.",
    )
    """HTML body template with variable placeholders."""

    body_text: Optional[str] = Field(
        default="",
        title="Text Body Template",
        description="Plain text body template (optional).",
    )
    """Plain text body template (optional)."""

    tags: List[str] = Field(
        default_factory=list,
        title="Tags",
        description="List of tags for categorizing the template.",
    )
    """List of tags for categorizing the template."""


class EmailTemplate(BaseEmailTemplate, TimestampedResource):
    """
    Email template for reusable email content.

    Templates do not support any context as of now except for built in context
    `unsubscribe_link` if the email is sent to a single recipient.

    The template must be in valid Jinja2 format.
    """

    account: str = Field(
        title="Account ID",
        description="ID of the email account this template belongs to.",
    )
    """ID of the email account this template belongs to."""

    def __str__(self) -> str:
        return (
            f"EmailTemplate(id={self.id} name={self.name} "
            f"code={self.code})"
        )


class EmailTemplateCreate(BaseEmailTemplate, CreateModel):
    """Model for creating a new email template."""


class EmailTemplateUpdate(UpdateModel):
    """Model for updating an existing email template."""

    name: Optional[str] = Field(
        default=None,
        title="Template Name",
        description="Name of the email template.",
        max_length=255,
    )
    """Name of the email template."""

    code: Optional[str] = Field(
        default=None,
        title="Template Code",
        description="Unique code for the template.",
        max_length=100,
    )
    """Unique code for the template."""

    subject: Optional[str] = Field(
        default=None,
        title="Subject Template",
        description="Subject line template with variable placeholders.",
    )
    """Subject line template with variable placeholders."""

    body_html: Optional[str] = Field(
        default=None,
        title="HTML Body Template",
        description="HTML body template with variable placeholders.",
    )
    """HTML body template with variable placeholders."""

    body_text: Optional[str] = Field(
        default=None,
        title="Text Body Template",
        description="Plain text body template (optional).",
    )
    """Plain text body template (optional)."""

    tags: Optional[List[str]] = Field(
        default=None,
        title="Tags",
        description="List of tags for categorizing the template.",
    )
    """List of tags for categorizing the template."""
