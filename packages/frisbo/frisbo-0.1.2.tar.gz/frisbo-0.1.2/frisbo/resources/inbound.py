"""Inbound/Inventory requests resource."""

from typing import Iterator, Dict, List, Any, Optional
from .base import BaseResource


class InboundResource(BaseResource):
    """Handle inbound inventory requests."""

    def list(
        self,
        organization_id: int,
        page: int = 1,
        **params
    ) -> Iterator[Dict[str, Any]]:
        """List all inbound requests with pagination.

        Args:
            organization_id: Organization ID
            page: Starting page number
            **params: Additional query parameters

        Yields:
            Inbound request dictionaries

        Example:
            >>> for inbound in client.inbound.list(organization_id=921):
            ...     print(inbound['status'])
        """
        endpoint = f"/v1/organizations/{organization_id}/inventory"
        yield from self._paginate(endpoint, params=params, page=page)

    def create(
        self,
        organization_id: int,
        warehouse_id: int,
        products: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new inbound inventory request.

        Args:
            organization_id: Organization ID
            warehouse_id: Warehouse ID
            products: List of products to receive
            **kwargs: Additional parameters

        Returns:
            Created inbound request dictionary

        Example:
            >>> inbound = client.inbound.create(
            ...     organization_id=921,
            ...     warehouse_id=1,
            ...     products=[
            ...         {
            ...             "sku": "PROD-001",
            ...             "quantity": 100,
            ...             "price": "10.00"
            ...         }
            ...     ]
            ... )
        """
        data = {
            "warehouse_id": warehouse_id,
            "products": products,
            **kwargs
        }
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory",
            json=data
        )
        return response.json()

    def send_to_wms(
        self,
        organization_id: int,
        inventory_request_id: int
    ) -> Dict[str, Any]:
        """Send inbound request to WMS.

        Args:
            organization_id: Organization ID
            inventory_request_id: Inventory request ID

        Returns:
            API response

        Example:
            >>> response = client.inbound.send_to_wms(
            ...     organization_id=921,
            ...     inventory_request_id=123
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory/{inventory_request_id}/actions/sendToWms"
        )
        return response.json()

    def approve(
        self,
        organization_id: int,
        inventory_request_id: int
    ) -> Dict[str, Any]:
        """Approve inbound request.

        Args:
            organization_id: Organization ID
            inventory_request_id: Inventory request ID

        Returns:
            API response

        Example:
            >>> response = client.inbound.approve(
            ...     organization_id=921,
            ...     inventory_request_id=123
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory/{inventory_request_id}/actions/approve"
        )
        return response.json()

    def complete(
        self,
        organization_id: int,
        inventory_request_id: int
    ) -> Dict[str, Any]:
        """Complete inbound request.

        Args:
            organization_id: Organization ID
            inventory_request_id: Inventory request ID

        Returns:
            API response

        Example:
            >>> response = client.inbound.complete(
            ...     organization_id=921,
            ...     inventory_request_id=123
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory/{inventory_request_id}/actions/complete"
        )
        return response.json()

    def confirm(
        self,
        organization_id: int,
        inventory_request_id: int
    ) -> Dict[str, Any]:
        """Confirm inbound request.

        Args:
            organization_id: Organization ID
            inventory_request_id: Inventory request ID

        Returns:
            API response

        Example:
            >>> response = client.inbound.confirm(
            ...     organization_id=921,
            ...     inventory_request_id=123
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory/{inventory_request_id}/actions/confirm"
        )
        return response.json()

    def reprocess(
        self,
        organization_id: int,
        inventory_request_id: int
    ) -> Dict[str, Any]:
        """Reprocess inbound request.

        Args:
            organization_id: Organization ID
            inventory_request_id: Inventory request ID

        Returns:
            API response

        Example:
            >>> response = client.inbound.reprocess(
            ...     organization_id=921,
            ...     inventory_request_id=123
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory/{inventory_request_id}/actions/reprocess"
        )
        return response.json()
