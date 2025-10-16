"""Invoices resource."""

from typing import Iterator, Dict, List, Any
from .base import BaseResource
from ..models import Invoice, InvoiceSeries


class InvoicesResource(BaseResource):
    """Handle invoice operations."""

    def list(
        self,
        organization_id: int,
        page: int = 1,
        **params
    ) -> Iterator[Dict[str, Any]]:
        """List all invoices with pagination.

        Args:
            organization_id: Organization ID
            page: Starting page number
            **params: Additional query parameters

        Yields:
            Invoice dictionaries

        Example:
            >>> for invoice in client.invoices.list(organization_id=921):
            ...     print(invoice['invoice_number'])
        """
        endpoint = f"/v1/organizations/{organization_id}/invoices"
        yield from self._paginate(endpoint, params=params, page=page)

    def list_series(self, organization_id: int) -> List[InvoiceSeries]:
        """List invoice series.

        Args:
            organization_id: Organization ID

        Returns:
            List of InvoiceSeries objects

        Example:
            >>> series = client.invoices.list_series(organization_id=921)
            >>> for s in series:
            ...     print(s.series, s.number)
        """
        response = self._get(
            f"/v1/organizations/{organization_id}/invoices/series"
        )
        return [InvoiceSeries(**item) for item in response.json()]
