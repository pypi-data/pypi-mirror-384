# Frisbo SDK Quick Reference

## Installation

```bash
uv venv
uv pip install -e .
```

## Project Structure

```
frisbo/
├── __init__.py              # Main exports
├── client.py                # FrisboClient class
├── exceptions.py            # Custom exceptions
├── models.py                # Pydantic models
├── types.py                 # Type definitions
└── resources/
    ├── __init__.py
    ├── base.py              # Base resource class
    ├── auth.py              # Authentication
    ├── organizations.py     # Organizations
    ├── products.py          # Products & inventory
    ├── orders.py            # Orders
    ├── invoices.py          # Invoices
    └── inbound.py           # Inbound requests

examples/
├── basic_usage.py           # Basic SDK usage
├── orders_management.py     # Order operations
├── inventory_sync.py        # Inventory management
└── product_management.py    # Product CRUD
```

## Quick Start

```python
from frisbo import FrisboClient

# Initialize
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

# List organizations
for org in client.organizations.list():
    print(org.name)

# List orders
for order in client.orders.list(organization_id=921):
    print(order['order_reference'])
```

## API Resources

### Authentication
```python
# Login
auth = client.auth.login("email", "password")

# Get current user
user = client.auth.me()

# Logout
client.logout()
```

### Organizations
```python
# List all
for org in client.organizations.list():
    print(org)

# Get details
org = client.organizations.get(921)

# List warehouses
warehouses = client.organizations.list_warehouses(921)

# List channels
channels = client.organizations.list_channels(921)
```

### Products
```python
# List products
for product in client.products.list(organization_id=921):
    print(product.name, product.sku)

# Create product
product = client.products.create(
    organization_id=921,
    name="Product Name",
    sku="SKU-001",
    vat=19
)

# Update product
updated = client.products.update(
    organization_id=921,
    product_id=123,
    name="Updated Name"
)

# List inventory
for item in client.products.list_inventory(organization_id=921):
    print(item)
```

### Orders
```python
# List orders
for order in client.orders.list(organization_id=921):
    print(order['order_reference'])

# Get order
order = client.orders.get(organization_id=921, order_id=123)

# Create order
order = client.orders.create(
    organization_id=921,
    order_reference="ORD-001",
    shipping_customer={...},
    shipping_address={...},
    products=[...]
)

# Order actions
client.orders.cancel(921, order_id)
client.orders.confirm_fulfillment(921, order_id)
client.orders.ship_order(921, order_id, awb="AWB123")
client.orders.deliver_order(921, order_id)
```

### Inbound
```python
# List inbound requests
for inbound in client.inbound.list(organization_id=921):
    print(inbound['status'])

# Create inbound
inbound = client.inbound.create(
    organization_id=921,
    warehouse_id=1,
    products=[...]
)

# Inbound actions
client.inbound.send_to_wms(921, inventory_request_id)
client.inbound.approve(921, inventory_request_id)
client.inbound.complete(921, inventory_request_id)
```

### Invoices
```python
# List invoices
for invoice in client.invoices.list(organization_id=921):
    print(invoice['invoice_number'])

# List series
series = client.invoices.list_series(organization_id=921)
```

## Error Handling

```python
from frisbo import APIError, AuthenticationError, NotFoundError

try:
    order = client.orders.get(921, 99999)
except NotFoundError:
    print("Order not found")
except APIError as e:
    print(f"API Error {e.status_code}: {e}")
```

## Type Safety

The SDK includes full type hints and Pydantic models:

```python
from frisbo import Organization, Product, Order

org: Organization = client.organizations.get(921)
product: Product = client.products.create(...)
```

## Running Examples

```bash
# Basic usage
uv run python examples/basic_usage.py

# Order management
uv run python examples/orders_management.py

# Inventory sync
uv run python examples/inventory_sync.py

# Product management
uv run python examples/product_management.py

# Migration guide
uv run python examples/migrate_from_old.py
```

## Key Features

✅ **Automatic Authentication**: Token management with auto-refresh
✅ **Resource-based API**: Intuitive organization of endpoints
✅ **Type Safety**: Full type hints and Pydantic validation
✅ **Automatic Pagination**: Seamless iteration over results
✅ **Comprehensive Coverage**: All Frisbo API endpoints
✅ **Error Handling**: Custom exceptions for different error types

## API Documentation

Full API docs: https://developers.frisbo.ro/
