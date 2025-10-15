"""
Email managers for the Konigle SDK.

This module provides managers for email operations such as sending emails.
Unlike resource managers, these managers handle action-based operations
rather than CRUD operations on resources.
"""

from typing import TYPE_CHECKING, Union

from konigle.logging import get_logger
from konigle.models.comm.email.send import Email, EmailResponse
from konigle.utils import model_to_dict

if TYPE_CHECKING:
    from konigle.session import AsyncSession, SyncSession


class BaseEmailManager:
    resource_class = Email
    """The resource model class this manager handles."""

    base_path = "/reachout/api/v1/send-email"
    """The API base path for email operations."""

    def _prepare_request_data(self, data: Union[Email, dict]) -> dict:
        if isinstance(data, dict):
            data = Email(**data)

        # Convert to dict for API request
        data_dict = model_to_dict(data)

        # Check if we have file attachments
        has_files = data.attachments is not None and len(data.attachments) > 0

        if has_files:
            # Use multipart form data for file uploads
            form_data = {}
            files_data = []

            # Separate file data from regular data
            for key, value in data_dict.items():
                if key == "attachments":
                    # Add all attachments with the same field name
                    for attachment in value:
                        files_data.append(("attachments", attachment))
                else:
                    form_data[key] = value

            return {"data": form_data, "files": files_data}
        else:
            return {"json": data_dict}


class EmailManager(BaseEmailManager):
    """
    Synchronous manager for email operations.

    Provides functionality for sending emails and other email-related
    actions that don't involve resource management.
    """

    def __init__(self, session: "SyncSession"):
        self._session = session
        self.logger = get_logger()

    def send(self, data: Union[Email, dict]) -> EmailResponse:
        """
        Send an email through the Konigle email service.

        Args:
            data: Email data model instance or dict containing email details

        Returns:
            SendEmailResponse with success message and optional IDs

        Example:
            ```python
            from konigle.models.comm import Email

            email_data = Email(
                to_email=["recipient@example.com"],
                subject="Welcome to Konigle",
                body_html="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
                body_text="Welcome! Thanks for signing up.",
                channel="welcome-emails",
                save_as_template=False
            )

            response = client.emails.send(email_data)
            print(f"Email sent: {response.message}")
            ```
        """
        request_data = self._prepare_request_data(data)
        response = self._session.post(self.base_path, **request_data)
        response_data = response.json()
        return EmailResponse(**response_data)


class AsyncEmailManager(BaseEmailManager):
    """
    Asynchronous manager for email operations.

    Provides async functionality for sending emails and other email-related
    actions that don't involve resource management.
    """

    def __init__(self, session: "AsyncSession"):
        self._session = session
        self.logger = get_logger()

    async def send(self, data: Union[Email, dict]) -> EmailResponse:
        """
        Send an email through the Konigle email service.

        Args:
            data: Email data model instance or dict containing email details

        Returns:
            SendEmailResponse with success message and optional IDs

        Example:
            ```python
            from konigle.models.comm import Email

            email_data = Email(
                to_email=["recipient@example.com"],
                subject="Welcome to Konigle",
                body_html="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
                body_text="Welcome! Thanks for signing up.",
                channel="welcome-emails",
                save_as_template=False
            )

            response = await client.emails.send(email_data)
            print(f"Email sent: {response.message}")
            ```
        """
        request_data = self._prepare_request_data(data)
        response = await self._session.post(self.base_path, **request_data)
        response_data = response.json()
        return EmailResponse(**response_data)
