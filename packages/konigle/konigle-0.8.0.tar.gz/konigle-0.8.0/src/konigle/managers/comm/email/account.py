"""
Email account managers for the Konigle SDK.

This module provides managers for email account resources, enabling
email account management operations including CRUD operations.
"""

from typing import Any, Dict, cast

from konigle.filters.comm import EmailAccountFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.comm.email.account import (
    EmailAccount,
    EmailAccountCreate,
    EmailAccountSetup,
    EmailAccountUpdate,
)


class BaseEmailAccountManager:
    """Base class for email account managers with shared configuration."""

    resource_class = EmailAccount
    """The resource model class this manager handles."""

    resource_update_class = EmailAccountUpdate
    """The model class used for updating resources."""

    filter_class = EmailAccountFilters
    """The filter model class for this resource type."""

    base_path = "/reachout/api/v1/accounts"
    """The API base path for this resource type."""


class EmailAccountManager(BaseEmailAccountManager, BaseSyncManager):
    """Synchronous manager for email account resources."""

    def setup(self, data: EmailAccountSetup) -> Dict[str, Any]:
        """
        Set up a new email account along with its default channel and identity.
        Args:
            data: Email account setup data including all required fields
        Returns:
            A dictionary containing the created email account, its default
            channel, and identity.
        Example:
            ```python
            setup_data = EmailAccountSetup(
                name="Marketing Account",
                default_from_email=""
                default_reply_to_email=""
                identity_value="example.com",
            )
            setup_result = client.email_accounts.setup(setup_data)
            account = setup_result["account"]
            channel = setup_result["channels"][0]
            identity = setup_result["identity"]
            ```
        """
        from .channel import EmailChannelManager
        from .identity import EmailIdentityManager

        url = f"{self.base_path}/setup"
        response = self._session.post(
            url, json=data.model_dump(exclude_none=True, exclude_unset=True)
        )
        account_info = response.json()
        account = self.create_resource(account_info["account"])
        channels = [
            EmailChannelManager(self._session).create_resource(ch)
            for ch in account_info.get("channels", [])
        ]
        identity = EmailIdentityManager(self._session).create_resource(
            account_info["identity"]
        )
        return {
            "account": account,
            "channels": channels,
            "identity": identity,
        }

    def create(self, data: EmailAccountCreate) -> EmailAccount:
        """
        Create a new email account.

        Args:
            data: Email account creation data including all required fields

        Returns:
            Created email account instance with Active Record capabilities

        Example:
            ```python
            account_data = EmailAccountCreate(
                name="Marketing Account",
                default_from_email="noreply@example.com",
                default_from_name="Example Team",
            )
            account = client.email_accounts.create(account_data)
            print(f"Created account: {account.name}")
            ```
        """
        return cast(EmailAccount, super().create(data))


class AsyncEmailAccountManager(BaseEmailAccountManager, BaseAsyncManager):
    """Asynchronous manager for email account resources."""

    async def setup(self, data: EmailAccountSetup) -> Dict[str, Any]:
        """
        Set up a new email account along with its default channel and identity.
        Args:
            data: Email account setup data including all required fields
        Returns:
            A dictionary containing the created email account, its default
            channel, and identity.
        Example:
            ```python
            setup_data = EmailAccountSetup(
                name="Marketing Account",
                default_from_email=""
                default_reply_to_email=""
                identity_value="example.com",
            )
            setup_result = await client.email_accounts.setup(setup_data)
            account = setup_result["account"]
            channel = setup_result["channels"][0]
            identity = setup_result["identity"]
            ```
        """
        from .channel import AsyncEmailChannelManager
        from .identity import AsyncEmailIdentityManager

        url = f"{self.base_path}/setup"
        response = await self._session.post(
            url, json=data.model_dump(exclude_none=True, exclude_unset=True)
        )
        account_info = response.json()
        account = self.create_resource(account_info["account"])
        channels = [
            AsyncEmailChannelManager(self._session).create_resource(ch)
            for ch in account_info.get("channels", [])
        ]
        identity = AsyncEmailIdentityManager(self._session).create_resource(
            account_info["identity"]
        )
        return {
            "account": account,
            "channels": channels,
            "identity": identity,
        }

    async def create(self, data: EmailAccountCreate) -> EmailAccount:
        """
        Create a new email account.

        Args:
            data: Email account creation data including all required fields

        Returns:
            Created email account instance with Active Record capabilities

        Example:
            ```python
            account_data = EmailAccountCreate(
                name="Marketing Account",
                default_from_email="noreply@example.com",
                default_from_name="Example Team",
            )
            account = await client.email_accounts.create(account_data)
            print(f"Created account: {account.name}")
            ```
        """
        return cast(EmailAccount, await super().create(data))
