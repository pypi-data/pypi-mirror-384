"""
Send email models for the Konigle SDK.

Models for sending transactional and marketing emails through the Konigle
email service. These models represent the request data for the send-email
API endpoint.
"""

import os
from typing import List, Optional

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from konigle.models.base import CreateModel
from konigle.types.common import FileInputT
from konigle.utils import FileInput


class Email(CreateModel):
    """
    Model for sending direct emails through the Konigle email service.

    Not supporting cc and bcc since they don't represent the use case of
    sending transactional emails and marketing emails.
    """

    from_email: Optional[EmailStr] = Field(
        default=None,
        title="From Email",
        description="From email address to override the "
        "Account.default_from_email.",
    )
    """From email address to override the Account.default_from_email."""

    to_email: List[EmailStr] = Field(
        title="To Email",
        description="Primary recipient email addresses.",
        min_length=1,
    )
    """Primary recipient email addresses."""

    subject: str = Field(
        title="Subject",
        description="Email subject line.",
        max_length=255,
    )
    """Email subject line."""

    body_html: str = Field(
        title="HTML Body",
        description="HTML body content.",
    )
    """HTML body content."""

    body_text: Optional[str] = Field(
        default=None,
        title="Text Body",
        description="Plain text body content (optional).",
    )
    """Plain text body content (optional)."""

    reply_to_email: Optional[EmailStr] = Field(
        default=None,
        title="Reply-To Email",
        description="Optional reply-to email address. Overrides "
        "Account.default_reply_to_email.",
    )
    """Optional reply-to email address. Overrides
    Account.default_reply_to_email."""

    attachments: Optional[List[FileInputT]] = Field(
        default=None,
        title="Attachments",
        description="Optional file attachments (max 10 files). Can be file "
        "paths, bytes, BytesIO, BinaryIO, or tuples of (file_data, "
        "filename).",
        max_length=10,
    )
    """Optional file attachments (max 10 files)."""

    channel: str = Field(
        title="Channel",
        description="Channel code to use for sending the email.",
        max_length=20,
    )
    """Channel code to use for sending the email."""

    category: Optional[str] = Field(
        default=None,
        title="Category",
        description="Notification category code for the email. If present, "
        "the email will not be sent if the to_email is unsubscribed from "
        "the category.",
        max_length=50,
    )
    """Notification category code for the email."""

    save_as_template: bool = Field(
        default=False,
        title="Save as Template",
        description="Whether to save the email as a template for future use.",
    )
    """Whether to save the email as a template for future use."""

    @field_validator("attachments")
    @classmethod
    def validate_attachments(cls, v):
        """Validate attachment files."""
        if v is None:
            return v

        # Basic validation - ensure we have valid file-like objects
        if not isinstance(v, list):
            raise ValueError("Attachments must be a list")

        if len(v) > 10:
            raise ValueError("Maximum 10 attachments allowed")

        return v

    @model_validator(mode="after")
    def normalize_attachments(self):
        """Normalize attachments to FileInputT."""
        if self.attachments is None:
            return self

        normalized = []
        for attachment in self.attachments:
            normalized.append(FileInput.normalize(attachment))

        # make sure that each file size does not exceed 20MB and total size
        # is less than 100MB
        total_size = 0
        for file_input in normalized:
            # find file size
            if hasattr(file_input, "seek") and hasattr(file_input, "tell"):
                # For BytesIO and file objects that support seek/tell
                current_pos = file_input.tell()
                file_input.seek(0, 2)  # Seek to end
                size = file_input.tell()
                file_input.seek(current_pos)  # Restore original position
            else:
                # For other file-like objects, try to get size from stat
                try:
                    size = os.fstat(file_input.fileno()).st_size
                except (AttributeError, OSError):
                    # If we can't determine size, skip validation
                    continue

            filename = getattr(file_input, "name", "attachment")
            if size > 20 * 1024 * 1024:
                raise ValueError(
                    f"Attachment {filename} exceeds the maximum "
                    "file size of 20MB"
                )
            total_size += size
        if total_size > 100 * 1024 * 1024:
            raise ValueError(
                "Total attachment size exceeds the maximum of 100MB"
            )
        self.attachments = normalized

        return self


class EmailResponse(BaseModel):
    """
    Response model for successful email send operations.
    """

    status: str = Field(
        title="Status",
        description="Status code of the email send operation.",
    )
    """Status code of the email send operation."""

    message_id: Optional[str] = Field(
        default=None,
        title="Email Message ID",
        description="Unique identifier for the sent email",
    )
    """Unique identifier for the sent email"""

    template_id: Optional[str] = Field(
        default=None,
        title="Template ID",
        description="ID of the created template (if save_as_template was "
        "True).",
    )
    """ID of the created template (if save_as_template was True)."""
