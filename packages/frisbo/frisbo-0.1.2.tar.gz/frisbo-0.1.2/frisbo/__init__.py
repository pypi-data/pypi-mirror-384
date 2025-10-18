"""
Frisbo Python SDK

A comprehensive Python SDK for interacting with the Frisbo API.

Basic usage:
    >>> from frisbo import FrisboClient
    >>>
    >>> client = FrisboClient(email="user@example.com", password="password")
    >>>
    >>> # List organizations
    >>> for org in client.organizations.list():
    ...     print(org.name)
    >>>
    >>> # Get orders
    >>> for order in client.orders.list(organization_id=921):
    ...     print(order['order_reference'])
"""

from .client import FrisboClient
from .exceptions import (
    FrisboError,
    AuthenticationError,
    APIError,
    ValidationError,
    NotFoundError,
    RateLimitError
)
from .models import (
    Authorization,
    User,
    Organization,
    Channel,
    Warehouse,
    Product,
    ProductDimensions,
    Order,
    OrderProduct,
    Customer,
    Address,
    Invoice,
    InvoiceProduct,
    InvoiceSeries,
    InventoryItem,
    PaginatedResponse
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "FrisboClient",

    # Exceptions
    "FrisboError",
    "AuthenticationError",
    "APIError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",

    # Models
    "Authorization",
    "User",
    "Organization",
    "Channel",
    "Warehouse",
    "Product",
    "ProductDimensions",
    "Order",
    "OrderProduct",
    "Customer",
    "Address",
    "Invoice",
    "InvoiceProduct",
    "InvoiceSeries",
    "InventoryItem",
    "PaginatedResponse",
]
