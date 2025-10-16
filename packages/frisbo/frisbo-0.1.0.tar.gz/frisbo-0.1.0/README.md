# Frisbo Python SDK

A comprehensive Python SDK for interacting with the [Frisbo API](https://frisbo.ro). This SDK provides a clean, Pythonic interface to manage orders, products, inventory, and more.

## Features

- **Easy Authentication**: Automatic token management with refresh
- **Resource-based API**: Intuitive organization of endpoints
- **Type Safety**: Full type hints and Pydantic models for validation
- **Automatic Pagination**: Seamless iteration over paginated results
- **Comprehensive Coverage**: Support for all Frisbo API endpoints
- **Error Handling**: Custom exceptions for different error types

## Installation

### Using uv (recommended)

```bash
uv pip install -e .
```

### Using pip

```bash
pip install -e .
```

## Quick Start

```python
from frisbo import FrisboClient

# Initialize the client
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

# List organizations
for org in client.organizations.list():
    print(org.name)

# Get orders for an organization
for order in client.orders.list(organization_id=921):
    print(order['order_reference'])
```

## Authentication

### Email and Password

```python
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)
```

### Access Token

```python
client = FrisboClient(access_token="your-access-token")
```

### Manual Authentication

```python
client = FrisboClient(
    email="your-email@example.com",
    password="your-password",
    auto_authenticate=False
)
client.authenticate()
```

## Usage Examples

### Organizations

```python
# List all organizations
for org in client.organizations.list():
    print(f"{org.name} (ID: {org.organization_id})")

# Get organization details
org = client.organizations.get(organization_id=921)

# List warehouses
warehouses = client.organizations.list_warehouses(organization_id=921)

# List channels
channels = client.organizations.list_channels(organization_id=921)
```

### Products

```python
# List products
for product in client.products.list(organization_id=921):
    print(f"{product.name} - SKU: {product.sku}")

# Create product
product = client.products.create(
    organization_id=921,
    name="T-Shirt",
    sku="TSHIRT-001",
    ean="1234567890123",
    vat=19,
    dimensions={"width": 10, "height": 15, "length": 20, "weight": 500}
)

# Update product
updated = client.products.update(
    organization_id=921,
    product_id=123,
    name="Updated Name",
    vat=20
)

# List inventory
for item in client.products.list_inventory(organization_id=921):
    print(item)

# Sync inventory
response = client.products.sync_inventory(
    organization_id=921,
    products=[
        {"sku": "PROD-001", "quantity": 100},
        {"sku": "PROD-002", "quantity": 50}
    ]
)
```

### Orders

```python
# List orders
for order in client.orders.list(organization_id=921):
    print(f"{order['order_reference']} - {order.get('fulfillment_status')}")

# Get order details
order = client.orders.get(organization_id=921, order_id=12345)

# Create order
order = client.orders.create(
    organization_id=921,
    order_reference="ORD-001",
    channel_id=1,
    warehouse_id=1,
    shipping_customer={
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+40123456789"
    },
    shipping_address={
        "street": "Strada Principala 123",
        "city": "Bucharest",
        "country": "Romania",
        "zip": "010101"
    },
    products=[
        {
            "sku": "PROD-001",
            "name": "Product Name",
            "price": "99.99",
            "quantity": 2,
            "vat": "19"
        }
    ],
    discount="10%"
)

# Update order
updated = client.orders.update(
    organization_id=921,
    order_id=12345,
    notes="Updated notes"
)

# Order actions
client.orders.cancel(organization_id=921, order_id=12345)
client.orders.confirm_fulfillment(organization_id=921, order_id=12345)
client.orders.ship_order(organization_id=921, order_id=12345, awb="AWB123")
client.orders.deliver_order(organization_id=921, order_id=12345)
client.orders.return_order(organization_id=921, order_id=12345)
```

### Inbound Inventory

```python
# List inbound requests
for inbound in client.inbound.list(organization_id=921):
    print(f"ID: {inbound['inventory_request_id']} - Status: {inbound['status']}")

# Create inbound request
inbound = client.inbound.create(
    organization_id=921,
    warehouse_id=1,
    products=[
        {"sku": "PROD-001", "quantity": 100, "price": "10.00"},
        {"sku": "PROD-002", "quantity": 50, "price": "20.00"}
    ]
)

# Inbound actions
client.inbound.send_to_wms(organization_id=921, inventory_request_id=123)
client.inbound.approve(organization_id=921, inventory_request_id=123)
client.inbound.complete(organization_id=921, inventory_request_id=123)
client.inbound.confirm(organization_id=921, inventory_request_id=123)
```

### Invoices

```python
# List invoices
for invoice in client.invoices.list(organization_id=921):
    print(f"{invoice['invoice_number']} - {invoice['invoice_date']}")

# List invoice series
series = client.invoices.list_series(organization_id=921)
for s in series:
    print(f"{s.series} - Current: {s.number}")
```

## API Resources

The SDK is organized into the following resources:

- **auth**: Authentication operations (login, logout, me)
- **organizations**: Organization management (list, get, warehouses, channels, users)
- **products**: Product management (list, create, update, inventory)
- **orders**: Order management (list, get, create, update, actions)
- **invoices**: Invoice operations (list, series)
- **inbound**: Inbound inventory requests (list, create, actions)

## Error Handling

```python
from frisbo import FrisboClient, APIError, AuthenticationError, NotFoundError

try:
    client = FrisboClient(email="user@example.com", password="wrong")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")

try:
    order = client.orders.get(organization_id=921, order_id=99999)
except NotFoundError as e:
    print(f"Order not found: {e}")

try:
    # Some API call
    pass
except APIError as e:
    print(f"API Error {e.status_code}: {e}")
```

## Type Support

The SDK includes full type hints and Pydantic models:

```python
from frisbo import FrisboClient, Organization, Product, Order

client = FrisboClient(email="...", password="...")

# Type hints work with IDE autocomplete
org: Organization = client.organizations.get(921)
product: Product = client.products.create(...)
```

## Development

### Running Examples

Check the `examples/` directory for complete usage examples:

```bash
# Basic usage
uv run python examples/basic_usage.py

# Order management
uv run python examples/orders_management.py

# Inventory sync
uv run python examples/inventory_sync.py

# Product management
uv run python examples/product_management.py
```

## API Documentation

For full API documentation, visit: https://developers.frisbo.ro/

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
