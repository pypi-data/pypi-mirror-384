"""
Email template managers for the Konigle SDK.

This module provides managers for email template resources, enabling
email template management operations including CRUD operations.
"""

from typing import cast

from konigle.filters.comm import EmailTemplateFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.comm.email.template import (
    EmailTemplate,
    EmailTemplateCreate,
    EmailTemplateUpdate,
)


class BaseEmailTemplateManager:
    """Base class for email template managers with shared configuration."""

    resource_class = EmailTemplate
    """The resource model class this manager handles."""

    resource_update_class = EmailTemplateUpdate
    """The model class used for updating resources."""

    filter_class = EmailTemplateFilters
    """The filter model class for this resource type."""

    base_path = "/reachout/api/v1/email-templates"
    """The API base path for this resource type."""


class EmailTemplateManager(BaseEmailTemplateManager, BaseSyncManager):
    """Synchronous manager for email template resources."""

    def create(self, data: EmailTemplateCreate) -> EmailTemplate:
        """
        Create a new email template.

        Args:
            data: Email template creation data including all required fields

        Returns:
            Created email template instance with Active Record capabilities

        Example:
            ```python
            template_data = EmailTemplateCreate(
                name="Welcome Email",
                code="welcome-email",
                subject="Welcome to {{company_name}}!",
                body_html="<h1>Welcome!</h1><p>Thanks for joining.</p>",
                body_text="Welcome! Thanks for joining.",
                tags=["welcome", "onboarding"]
            )
            template = client.email_templates.create(template_data)
            print(f"Created template: {template.name}")
            ```
        """
        return cast(EmailTemplate, super().create(data))


class AsyncEmailTemplateManager(BaseEmailTemplateManager, BaseAsyncManager):
    """Asynchronous manager for email template resources."""

    async def create(self, data: EmailTemplateCreate) -> EmailTemplate:
        """
        Create a new email template.

        Args:
            data: Email template creation data including all required fields

        Returns:
            Created email template instance with Active Record capabilities

        Example:
            ```python
            template_data = EmailTemplateCreate(
                name="Welcome Email",
                code="welcome-email",
                subject="Welcome to {{company_name}}!",
                body_html="<h1>Welcome!</h1><p>Thanks for joining.</p>",
                body_text="Welcome! Thanks for joining.",
                tags=["welcome", "onboarding"]
            )
            template = await client.email_templates.create(template_data)
            print(f"Created template: {template.name}")
            ```
        """
        return cast(EmailTemplate, await super().create(data))
