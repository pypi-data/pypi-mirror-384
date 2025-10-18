"""Products resource."""

from typing import Iterator, Dict, Optional, Any
from .base import BaseResource
from ..models import Product, InventoryItem


class ProductsResource(BaseResource):
    """Handle product operations."""

    def list(self, organization_id: int, page: int = 1, **params) -> Iterator[Product]:
        """List all products with pagination.

        Args:
            organization_id: Organization ID
            page: Starting page number
            **params: Additional query parameters

        Yields:
            Product objects

        Example:
            >>> for product in client.products.list(organization_id=921):
            ...     print(product.name, product.sku)
        """
        endpoint = f"/v1/organizations/{organization_id}/products"
        for item in self._paginate(endpoint, params=params, page=page):
            yield Product(**item)

    def create(
        self,
        organization_id: int,
        name: str,
        sku: str,
        vat: int = 0,
        **kwargs
    ) -> Product:
        """Create a new product.

        Args:
            organization_id: Organization ID
            name: Product name
            sku: Product SKU
            vat: VAT percentage (default: 0)
            **kwargs: Additional product parameters (ean, upc, dimensions, etc.)

        Returns:
            Created Product object

        Example:
            >>> product = client.products.create(
            ...     organization_id=921,
            ...     name="T-Shirt",
            ...     sku="TSHIRT-001",
            ...     vat=19,
            ...     ean="1234567890123"
            ... )
        """
        data = {"name": name, "sku": sku, "vat": vat, **kwargs}
        response = self._post(
            f"/v1/organizations/{organization_id}/products",
            json=data
        )
        return Product(**response.json())

    def update(
        self,
        organization_id: int,
        product_id: int,
        **kwargs
    ) -> Product:
        """Update an existing product.

        Args:
            organization_id: Organization ID
            product_id: Product ID
            **kwargs: Product fields to update

        Returns:
            Updated Product object

        Example:
            >>> product = client.products.update(
            ...     organization_id=921,
            ...     product_id=123,
            ...     name="Updated Name",
            ...     vat=19
            ... )
        """
        response = self._put(
            f"/v1/organizations/{organization_id}/products/{product_id}",
            json=kwargs
        )
        return Product(**response.json())

    def list_inventory(
        self,
        organization_id: int,
        page: int = 1,
        **params
    ) -> Iterator[Dict[str, Any]]:
        """List inventory with pagination.

        Args:
            organization_id: Organization ID
            page: Starting page number
            **params: Additional query parameters

        Yields:
            Inventory item dictionaries

        Example:
            >>> for item in client.products.list_inventory(organization_id=921):
            ...     print(item)
        """
        endpoint = f"/v1/organizations/{organization_id}/inventory"
        yield from self._paginate(endpoint, params=params, page=page)

    def sync_inventory(
        self,
        organization_id: int,
        products: list,
        **kwargs
    ) -> Dict[str, Any]:
        """Sync inventory levels.

        Args:
            organization_id: Organization ID
            products: List of products with inventory data
            **kwargs: Additional parameters

        Returns:
            API response

        Example:
            >>> response = client.products.sync_inventory(
            ...     organization_id=921,
            ...     products=[
            ...         {"sku": "PROD-001", "quantity": 100},
            ...         {"sku": "PROD-002", "quantity": 50}
            ...     ]
            ... )
        """
        data = {"products": products, **kwargs}
        response = self._post(
            f"/v1/organizations/{organization_id}/inventory",
            json=data
        )
        return response.json()
