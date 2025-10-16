"""
Email identity managers for the Konigle SDK.

This module provides managers for email identity resources, enabling
email identity management operations including CRUD operations and
verification handling.
"""

from typing import cast

from konigle.filters.comm import EmailIdentityFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.comm.email.identity import (
    EmailIdentity,
    EmailIdentityCreate,
    EmailIdentityUpdate,
)


class BaseEmailIdentityManager:
    """Base class for email identity managers with shared configuration."""

    resource_class = EmailIdentity
    """The resource model class this manager handles."""

    resource_update_class = EmailIdentityUpdate
    """The model class used for updating resources."""

    filter_class = EmailIdentityFilters
    """The filter model class for this resource type."""

    base_path = "/reachout/api/v1/identities"
    """The API base path for this resource type."""


class EmailIdentityManager(BaseEmailIdentityManager, BaseSyncManager):
    """Synchronous manager for email identity resources."""

    def create(self, data: EmailIdentityCreate) -> EmailIdentity:
        """
        Create a new email identity.

        Args:
            data: Email identity creation data including all required fields

        Returns:
            Created email identity instance with Active Record capabilities

        Example:
            ```python
            identity_data = EmailIdentityCreate(
                identity_value="example.com",
            )
            identity = client.email_identities.create(identity_data)
            print(f"Created identity: {identity.identity_value}")
            ```
        """
        return cast(EmailIdentity, super().create(data))

    def check_verification_status(self, identity_id: str) -> EmailIdentity:
        """
        Check verification status for an email identity.

        Args:
            identity_id: ID of the identity to verify

        Returns:
            Updated identity instance with verification status

        Example:
            ```python
            identity = client.email_identities.check_verification_status("eid_123")
            print(f"Verification status: {identity.verified}")
            ```
        """
        url = f"{self.base_path}/{identity_id}/check-status"
        response = self._session.post(url)
        return cast(
            EmailIdentity,
            self.create_resource(response.json(), is_partial=False),
        )

    def setup_custom_mail_from(
        self, identity_id: str, mail_from_domain: str
    ) -> EmailIdentity:
        """
        Setup custom MAIL FROM domain for an email identity.

        Args:
            identity_id: ID of the identity to setup custom MAIL FROM
            mail_from_domain: Custom MAIL FROM domain to be set
        Returns:
            Updated identity instance with custom MAIL FROM domain that is
            pending verification. The returned instance includes the dns
            records that need to be added for verification.
        """
        url = f"{self.base_path}/{identity_id}/setup-custom-mail-from"
        response = self._session.post(
            url, json={"mail_from_domain": mail_from_domain}
        )
        return cast(
            EmailIdentity,
            self.create_resource(response.json(), is_partial=False),
        )


class AsyncEmailIdentityManager(BaseEmailIdentityManager, BaseAsyncManager):
    """Asynchronous manager for email identity resources."""

    async def create(self, data: EmailIdentityCreate) -> EmailIdentity:
        """
        Create a new email identity.

        Args:
            data: Email identity creation data including all required fields

        Returns:
            Created email identity instance with Active Record capabilities

        Example:
            ```python
            identity_data = EmailIdentityCreate(
                identity_value="example.com",
            )
            identity = await client.email_identities.create(identity_data)
            print(f"Created identity: {identity.identity_value}")
            ```
        """
        return cast(EmailIdentity, await super().create(data))

    async def check_verification_status(
        self, identity_id: str
    ) -> EmailIdentity:
        """
        Check verification status for an email identity.

        Args:
            identity_id: ID of the identity to verify
        Returns:
            Updated identity instance with verification status
        Example:
            ```python
            identity = await client.email_identities.check_verification_status("eid_123")
            print(f"Verification status: {identity.verified}")
            ```
        """
        url = f"{self.base_path}/{identity_id}/check-status"
        response = await self._session.post(url)
        return cast(
            EmailIdentity,
            self.create_resource(response.json(), is_partial=False),
        )

    async def setup_custom_mail_from(
        self, identity_id: str, mail_from_domain: str
    ) -> EmailIdentity:
        """
        Setup custom MAIL FROM domain for an email identity.
        Args:
            identity_id: ID of the identity to setup custom MAIL FROM
            mail_from_domain: Custom MAIL FROM domain to be set
        Returns:
            Updated identity instance with custom MAIL FROM domain that is
            pending verification. The returned instance includes the dns
            records that need to be added for verification.
        """
        url = f"{self.base_path}/{identity_id}/setup-custom-mail-from"
        response = await self._session.post(
            url, json={"mail_from_domain": mail_from_domain}
        )
        return cast(
            EmailIdentity,
            self.create_resource(response.json(), is_partial=False),
        )
