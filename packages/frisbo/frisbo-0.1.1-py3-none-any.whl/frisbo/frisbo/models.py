"""Pydantic models for Frisbo API data structures."""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field, ConfigDict

from .types import FulfillmentStatus, InboundStatus, Courier


class Authorization(BaseModel):
    """Authentication response model."""
    access_token: str = Field(..., description="Bearer token for API authentication")
    id_token: Optional[str] = None
    expires_in: int = Field(..., description="Token expiry time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")


class User(BaseModel):
    """User model."""
    id: int
    name: str
    email: str
    status: bool
    roles: Optional[str] = None
    avatar: Optional[str] = None
    confirmed: Optional[int] = None
    confirmation_code: Optional[str] = None


class Organization(BaseModel):
    """Organization model."""
    organization_id: int
    is_active: bool
    name: str
    first_run_flag: Optional[bool] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    vat_registration_number: Optional[str] = None
    trade_register_registration_number: Optional[str] = None
    description: Optional[str] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    address_id: Optional[int] = None
    contact_id: Optional[int] = None


class Channel(BaseModel):
    """Sales channel model."""
    id: int
    name: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Warehouse(BaseModel):
    """Warehouse model."""
    id: int
    name: str


class ProductDimensions(BaseModel):
    """Product dimensions model."""
    width: Optional[int] = Field(None, description="Width in cm")
    height: Optional[int] = Field(None, description="Height in cm")
    length: Optional[int] = Field(None, description="Length in cm")
    weight: Optional[int] = Field(None, description="Weight in kg")


class Product(BaseModel):
    """Product model."""
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[int] = None
    name: str
    sku: str
    upc: Optional[str] = None
    external_code: Optional[str] = None
    ean: Optional[str] = None
    vat: int = Field(default=0, description="VAT as percentage")
    dimensions: Optional[ProductDimensions] = None
    has_serial_number: Optional[bool] = None


class Address(BaseModel):
    """Address model."""
    street: str
    city: str
    county: Optional[str] = None
    country: str
    zip: str


class Customer(BaseModel):
    """Customer model."""
    email: str
    first_name: str
    last_name: str
    phone: str


class OrderProduct(BaseModel):
    """Order product model."""
    sku: str
    name: str
    price: str
    quantity: int
    vat: str = Field(description="VAT as percentage")
    discount: Optional[str] = Field(None, description="Fixed or percentage (e.g., '10%')")
    product_id: Optional[int] = None
    order_id: Optional[int] = None
    total: Optional[str] = None
    status: Optional[str] = None
    is_virtual: Optional[bool] = None
    price_with_vat: Optional[str] = None
    product: Optional[Product] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Order(BaseModel):
    """Order model."""
    model_config = ConfigDict(populate_by_name=True)

    order_reference: str = Field(..., description="Unique order reference")
    organization_id: Optional[int] = None
    channel_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[str] = None
    fulfillment_status: Optional[FulfillmentStatus] = None
    reason_status: Optional[str] = None
    ordered_date: Optional[str] = None
    delivery_date: Optional[str] = None
    returned_date: Optional[str] = None
    canceled_date: Optional[str] = None
    notes: Optional[str] = None
    shipped_with: Optional[Courier] = None
    shipped_date: Optional[str] = None
    preferred_delivery_time: Optional[str] = None
    shipping_customer: Customer
    shipping_address: Address
    billing_customer: Optional[Customer] = None
    billing_address: Optional[Address] = None
    discount: Optional[str] = Field(None, description="Fixed or percentage (e.g., '10%')")
    products: List[OrderProduct]
    currency: Optional[str] = None
    order_id: Optional[int] = Field(None, alias="_id")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    attachments: Optional[List[dict]] = None


class InvoiceProduct(BaseModel):
    """Invoice product model."""
    product_id: str
    name: str
    price: str
    quantity: int
    vat: str
    discount: Optional[str] = None


class Invoice(BaseModel):
    """Invoice model."""
    id: int
    channel_id: Optional[str] = None
    invoice_number: str
    invoice_date: str
    order_number: str
    products: List[InvoiceProduct]


class InvoiceSeries(BaseModel):
    """Invoice series model."""
    id: int
    organization_id: str
    series: str
    number: str


class InventoryItem(BaseModel):
    """Inventory/Inbound item model."""
    inventory_request_id: Optional[int] = Field(None, alias="_id")
    organization_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[InboundStatus] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    products: Optional[List[dict]] = None


class PaginatedResponse(BaseModel):
    """Paginated API response model."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: List[Any]
    current_page: int
    last_page: int
    per_page: int
    total: Optional[int] = None
