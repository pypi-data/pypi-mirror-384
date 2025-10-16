"""
Email channel managers for the Konigle SDK.

This module provides managers for email channel resources, enabling
email channel management operations including CRUD operations.
"""

from typing import cast

from konigle.filters.comm import EmailChannelFilters
from konigle.managers.base import BaseAsyncManager, BaseSyncManager
from konigle.models.comm.email.channel import (
    EmailChannel,
    EmailChannelCreate,
    EmailChannelUpdate,
)


class BaseEmailChannelManager:
    """Base class for email channel managers with shared configuration."""

    resource_class = EmailChannel
    """The resource model class this manager handles."""

    resource_update_class = EmailChannelUpdate
    """The model class used for updating resources."""

    filter_class = EmailChannelFilters
    """The filter model class for this resource type."""

    base_path = "/reachout/api/v1/channels"
    """The API base path for this resource type."""


class EmailChannelManager(BaseEmailChannelManager, BaseSyncManager):
    """Synchronous manager for email channel resources."""

    def create(self, data: EmailChannelCreate) -> EmailChannel:
        """
        Create a new email channel.

        Args:
            data: Email channel creation data including all required fields

        Returns:
            Created email channel instance with Active Record capabilities

        Example:
            ```python
            channel_data = EmailChannelCreate(
                code="transactional",
                channel_type=EmailChannelType.TRANSACTIONAL,
            )
            channel = client.email_channels.create(channel_data)
            print(f"Created channel: {channel.code}")
            ```
        """
        return cast(EmailChannel, super().create(data))


class AsyncEmailChannelManager(BaseEmailChannelManager, BaseAsyncManager):
    """Asynchronous manager for email channel resources."""

    async def create(self, data: EmailChannelCreate) -> EmailChannel:
        """
        Create a new email channel.

        Args:
            data: Email channel creation data including all required fields

        Returns:
            Created email channel instance with Active Record capabilities

        Example:
            ```python
            channel_data = EmailChannelCreate(
                code="transactional",
                channel_type=EmailChannelType.TRANSACTIONAL,
            )
            channel = await client.email_channels.create(channel_data)
            print(f"Created channel: {channel.code}")
            ```
        """
        return cast(EmailChannel, await super().create(data))
