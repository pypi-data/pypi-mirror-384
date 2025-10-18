"""Organizations resource."""

from typing import Iterator, List, Dict, Optional
from .base import BaseResource
from ..models import Organization, Warehouse, Channel, User


class OrganizationsResource(BaseResource):
    """Handle organization operations."""

    def list(self, page: int = 1) -> Iterator[Organization]:
        """List all organizations with pagination.

        Args:
            page: Starting page number

        Yields:
            Organization objects

        Example:
            >>> for org in client.organizations.list():
            ...     print(org.name)
        """
        for item in self._paginate("/v1/organizations", page=page):
            yield Organization(**item)

    def get(self, organization_id: int) -> Organization:
        """Get organization details.

        Args:
            organization_id: Organization ID

        Returns:
            Organization object

        Example:
            >>> org = client.organizations.get(921)
            >>> print(org.name)
        """
        response = self._get(f"/v1/organizations/{organization_id}")
        return Organization(**response.json())

    def list_warehouses(self, organization_id: int) -> List[Warehouse]:
        """List organization warehouses.

        Args:
            organization_id: Organization ID

        Returns:
            List of Warehouse objects

        Example:
            >>> warehouses = client.organizations.list_warehouses(921)
            >>> for warehouse in warehouses:
            ...     print(warehouse.name)
        """
        response = self._get(f"/v1/organizations/{organization_id}/warehouses")
        return [Warehouse(**item) for item in response.json()]

    def list_channels(self, organization_id: int) -> List[Channel]:
        """List organization sales channels.

        Args:
            organization_id: Organization ID

        Returns:
            List of Channel objects

        Example:
            >>> channels = client.organizations.list_channels(921)
            >>> for channel in channels:
            ...     print(channel.name)
        """
        response = self._get(f"/v1/organizations/{organization_id}/channels")
        return [Channel(**item) for item in response.json()]

    def create_channel(
        self,
        organization_id: int,
        name: str,
        type: str,
        **kwargs
    ) -> Channel:
        """Create a new sales channel.

        Args:
            organization_id: Organization ID
            name: Channel name
            type: Channel type
            **kwargs: Additional channel parameters

        Returns:
            Created Channel object

        Example:
            >>> channel = client.organizations.create_channel(
            ...     organization_id=921,
            ...     name="My Store",
            ...     type="shopify"
            ... )
        """
        data = {"name": name, "type": type, **kwargs}
        response = self._post(
            f"/v1/organizations/{organization_id}/channels",
            json=data
        )
        return Channel(**response.json())

    def list_users(self, organization_id: int) -> List[User]:
        """List organization users.

        Args:
            organization_id: Organization ID

        Returns:
            List of User objects

        Example:
            >>> users = client.organizations.list_users(921)
            >>> for user in users:
            ...     print(user.email)
        """
        response = self._get(f"/v1/organizations/{organization_id}/users")
        return [User(**item) for item in response.json()]

    def create_user(
        self,
        organization_id: int,
        first_name: str,
        last_name: str,
        email: str,
        **kwargs
    ) -> User:
        """Create a new organization user.

        Args:
            organization_id: Organization ID
            first_name: User first name
            last_name: User last name
            email: User email
            **kwargs: Additional user parameters

        Returns:
            Created User object

        Example:
            >>> user = client.organizations.create_user(
            ...     organization_id=921,
            ...     first_name="John",
            ...     last_name="Doe",
            ...     email="john@example.com"
            ... )
        """
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            **kwargs
        }
        response = self._post(
            f"/v1/organizations/{organization_id}/users",
            json=data
        )
        return User(**response.json())
