"""Orders resource."""

from typing import Iterator, Dict, Optional, Any, List
from .base import BaseResource
from ..models import Order, OrderProduct, Customer, Address


class OrdersResource(BaseResource):
    """Handle order operations."""

    def list(
        self,
        organization_id: int,
        page: int = 1,
        **params
    ) -> Iterator[Dict[str, Any]]:
        """List all orders with pagination.

        Args:
            organization_id: Organization ID
            page: Starting page number
            **params: Additional query parameters (filters, sorting, etc.)

        Yields:
            Order dictionaries

        Example:
            >>> for order in client.orders.list(organization_id=921):
            ...     print(order['order_reference'])
        """
        endpoint = f"/v1/organizations/{organization_id}/orders"
        yield from self._paginate(endpoint, params=params, page=page)

    def get(self, organization_id: int, order_id: int) -> Dict[str, Any]:
        """Get order details.

        Args:
            organization_id: Organization ID
            order_id: Order ID

        Returns:
            Order dictionary

        Example:
            >>> order = client.orders.get(organization_id=921, order_id=12345)
            >>> print(order['order_reference'])
        """
        response = self._get(
            f"/v1/organizations/{organization_id}/orders/{order_id}"
        )
        return response.json()

    def create(
        self,
        organization_id: int,
        order_reference: str,
        shipping_customer: Dict[str, str],
        shipping_address: Dict[str, str],
        products: List[Dict[str, Any]],
        channel_id: Optional[int] = None,
        warehouse_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new order.

        Args:
            organization_id: Organization ID
            order_reference: Unique order reference
            shipping_customer: Customer information (email, first_name, last_name, phone)
            shipping_address: Shipping address (street, city, country, zip)
            products: List of products (sku, name, price, quantity, vat)
            channel_id: Sales channel ID (optional)
            warehouse_id: Warehouse ID (optional)
            **kwargs: Additional order parameters

        Returns:
            Created order dictionary

        Example:
            >>> order = client.orders.create(
            ...     organization_id=921,
            ...     order_reference="ORD-12345",
            ...     shipping_customer={
            ...         "email": "customer@example.com",
            ...         "first_name": "John",
            ...         "last_name": "Doe",
            ...         "phone": "+1234567890"
            ...     },
            ...     shipping_address={
            ...         "street": "123 Main St",
            ...         "city": "New York",
            ...         "country": "US",
            ...         "zip": "10001"
            ...     },
            ...     products=[
            ...         {
            ...             "sku": "PROD-001",
            ...             "name": "Product 1",
            ...             "price": "99.99",
            ...             "quantity": 2,
            ...             "vat": "19"
            ...         }
            ...     ]
            ... )
        """
        data = {
            "order_reference": order_reference,
            "shipping_customer": shipping_customer,
            "shipping_address": shipping_address,
            "products": products,
            **kwargs
        }

        if channel_id:
            data["channel_id"] = channel_id
        if warehouse_id:
            data["warehouse_id"] = warehouse_id

        response = self._post(
            f"/v1/organizations/{organization_id}/orders",
            json=data
        )
        return response.json()

    def update(
        self,
        organization_id: int,
        order_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Update an existing order.

        Args:
            organization_id: Organization ID
            order_id: Order ID
            **kwargs: Order fields to update

        Returns:
            Updated order dictionary

        Example:
            >>> order = client.orders.update(
            ...     organization_id=921,
            ...     order_id=12345,
            ...     notes="Updated notes"
            ... )
        """
        response = self._put(
            f"/v1/organizations/{organization_id}/orders/{order_id}",
            json=kwargs
        )
        return response.json()

    def cancel(self, organization_id: int, order_id: int) -> Dict[str, Any]:
        """Cancel an order.

        Args:
            organization_id: Organization ID
            order_id: Order ID

        Returns:
            API response

        Example:
            >>> response = client.orders.cancel(organization_id=921, order_id=12345)
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/orders/{order_id}/actions/cancel"
        )
        return response.json()

    def reprocess(self, organization_id: int, order_id: int) -> Dict[str, Any]:
        """Reprocess an order.

        Args:
            organization_id: Organization ID
            order_id: Order ID

        Returns:
            API response

        Example:
            >>> response = client.orders.reprocess(organization_id=921, order_id=12345)
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/orders/{order_id}/actions/reprocess"
        )
        return response.json()

    def confirm_fulfillment(
        self,
        organization_id: int,
        order_id: int
    ) -> Dict[str, Any]:
        """Confirm order fulfillment.

        Args:
            organization_id: Organization ID
            order_id: Order ID

        Returns:
            API response

        Example:
            >>> response = client.orders.confirm_fulfillment(
            ...     organization_id=921,
            ...     order_id=12345
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/orders/{order_id}/actions/confirmFulfillment"
        )
        return response.json()

    def ship_order(
        self,
        organization_id: int,
        order_id: int,
        awb: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark order as shipped.

        Args:
            organization_id: Organization ID
            order_id: Order ID
            awb: Air Waybill number (optional)

        Returns:
            API response

        Example:
            >>> response = client.orders.ship_order(
            ...     organization_id=921,
            ...     order_id=12345,
            ...     awb="AWB123456"
            ... )
        """
        data = {"awb": awb} if awb else {}
        response = self._post(
            f"/v1/organizations/{organization_id}/orders/{order_id}/actions/shipOrder",
            json=data
        )
        return response.json()

    def deliver_order(self, organization_id: int, order_id: int) -> Dict[str, Any]:
        """Mark order as delivered.

        Args:
            organization_id: Organization ID
            order_id: Order ID

        Returns:
            API response

        Example:
            >>> response = client.orders.deliver_order(
            ...     organization_id=921,
            ...     order_id=12345
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/orders/{order_id}/actions/deliverOrder"
        )
        return response.json()

    def return_order(self, organization_id: int, order_id: int) -> Dict[str, Any]:
        """Mark order as returned.

        Args:
            organization_id: Organization ID
            order_id: Order ID

        Returns:
            API response

        Example:
            >>> response = client.orders.return_order(
            ...     organization_id=921,
            ...     order_id=12345
            ... )
        """
        response = self._post(
            f"/v1/organizations/{organization_id}/orders/{order_id}/actions/returnOrder"
        )
        return response.json()
