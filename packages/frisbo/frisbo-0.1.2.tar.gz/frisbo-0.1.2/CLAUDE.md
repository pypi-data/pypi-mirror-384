# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Python SDK for the Frisbo API (frisbo.ro). The SDK provides a clean, Pythonic interface to manage orders, products, inventory, invoices, and inbound requests through the Frisbo fulfillment platform.

**Package name**: `frisbo`
**Version**: 0.1.0
**API Documentation**: https://developers.frisbo.ro/

## Architecture

### Core Components

**FrisboClient** (frisbo/client.py:17-103)
- Main client class for interacting with the Frisbo API
- Handles automatic authentication with token expiry management
- Provides access to all resource endpoints through properties
- Key features:
  - Automatic authentication on initialization
  - Token expiry tracking and refresh
  - Resource-based API organization
  - Context: `client.orders`, `client.products`, `client.organizations`, etc.

**BaseResource** (frisbo/resources/base.py:10-125)
- Abstract base class for all API resource classes
- Provides common HTTP methods (`_get`, `_post`, `_put`, `_delete`)
- Automatic pagination support via `_paginate()` generator
- Centralized error handling

**Resource Classes** (frisbo/resources/)
Each resource handles a specific API domain:
- **AuthResource** (auth.py): Login, logout, user info
- **OrganizationsResource** (organizations.py): Organizations, warehouses, channels, users
- **ProductsResource** (products.py): Product CRUD, inventory management
- **OrdersResource** (orders.py): Order CRUD, order actions (ship, cancel, deliver, etc.)
- **InvoicesResource** (invoices.py): Invoice listing, series management
- **InboundResource** (inbound.py): Inbound inventory requests and actions

**Data Models** (frisbo/models.py)
- Pydantic models for request/response validation
- Key models: `Organization`, `Product`, `Order`, `User`, `Invoice`, `InventoryItem`
- Type-safe data structures with automatic validation

**Custom Exceptions** (frisbo/exceptions.py)
- `FrisboError`: Base exception
- `AuthenticationError`: Authentication failures
- `APIError`: General API errors (with status code)
- `NotFoundError`: 404 errors
- `RateLimitError`: 429 rate limit errors
- `ValidationError`: Request validation failures

### External Dependencies

- **requests** (>=2.31.0): HTTP client for API calls
- **pydantic** (>=2.0.0): Data validation and serialization
- **typing-extensions**: Type hint support for older Python versions

### API Structure

Frisbo API base URL: `https://api.frisbo.ro/v1/`
- **Authentication**: Bearer token obtained via `/auth/login` (24-hour expiry)
- **Pagination**: Uses `page` parameter, response includes `current_page`, `last_page`, `per_page`
- **Organization ID**: Default is 921 (configurable per request)

## Common Development Tasks

### Installation

```bash
# Create virtual environment
uv venv

# Install SDK in development mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Basic Usage

```python
from frisbo import FrisboClient

# Initialize client (auto-authenticates)
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

# List orders
for order in client.orders.list(organization_id=921):
    print(order['order_reference'])

# Create an order
order = client.orders.create(
    organization_id=921,
    order_reference="ORD-001",
    shipping_customer={...},
    shipping_address={...},
    products=[...]
)

# Logout
client.logout()
```

### Running Examples

```bash
# Basic SDK usage
uv run python examples/basic_usage.py

# Order management
uv run python examples/orders_management.py

# Inventory sync
uv run python examples/inventory_sync.py

# Product management
uv run python examples/product_management.py
```

### Testing Authentication

```python
from frisbo import FrisboClient

client = FrisboClient(
    email="test@example.com",
    password="password",
    auto_authenticate=False
)
client.authenticate()
print(f"Token: {client.access_token}")
print(f"Expires: {client.token_expires_at}")
```

### Testing API Endpoints

```python
from frisbo import FrisboClient

client = FrisboClient(email="...", password="...")

# Test organizations
orgs = list(client.organizations.list())
print(f"Found {len(orgs)} organizations")

# Test products with pagination
products = []
for i, product in enumerate(client.products.list(organization_id=921)):
    products.append(product)
    if i >= 9:  # Get first 10
        break
```

## Project Structure

```
frisbo/
├── __init__.py              # Main exports and package metadata
├── client.py                # FrisboClient class
├── exceptions.py            # Custom exceptions
├── models.py                # Pydantic models for data validation
├── types.py                 # Type definitions (statuses, enums)
└── resources/
    ├── __init__.py
    ├── base.py              # BaseResource with common functionality
    ├── auth.py              # Authentication endpoints
    ├── organizations.py     # Organization management
    ├── products.py          # Product and inventory management
    ├── orders.py            # Order management and actions
    ├── invoices.py          # Invoice operations
    └── inbound.py           # Inbound inventory requests

examples/
├── basic_usage.py           # Getting started guide
├── orders_management.py     # Order operations
├── inventory_sync.py        # Inventory management
└── product_management.py    # Product CRUD operations

Legacy:
├── frisbo.py                # Old integration script (deprecated)
```

## Important Notes

### Migration from Old Script

The repository contains an old `frisbo.py` script that has been superseded by the SDK. For migration guidance, see `examples/migrate_from_old.py`.

**Key differences:**
- Old: `Frisbo()` class → New: `FrisboClient()`
- Old: `f.orders()` → New: `client.orders.list(organization_id=921)`
- Old: `f.inventory()` → New: `client.products.list_inventory(organization_id=921)`
- New: Full CRUD operations, type safety, better error handling

### Credentials Management

- **Never commit credentials** to the repository
- Use environment variables via `.env` file (see `.env.example`)
- The SDK supports both email/password and pre-existing access tokens

### Pagination

The SDK handles pagination automatically via Python generators:
```python
# This will fetch ALL orders across all pages
for order in client.orders.list(organization_id=921):
    process(order)
```

### Error Handling

```python
from frisbo import FrisboClient, APIError, NotFoundError

try:
    order = client.orders.get(organization_id=921, order_id=99999)
except NotFoundError:
    print("Order not found")
except APIError as e:
    print(f"API Error {e.status_code}: {e}")
```

### Type Safety

The SDK includes full type hints and Pydantic models for IDE autocomplete and type checking:
```python
from frisbo import FrisboClient, Organization

client = FrisboClient(email="...", password="...")
org: Organization = client.organizations.get(921)  # Type-safe
```

### Development Workflow

1. Make changes to SDK code
2. Reinstall: `uv pip install -e .`
3. Test with examples or custom scripts
4. Run type checking: `mypy frisbo/`
5. Format code: `black frisbo/`

## API Resources Quick Reference

- **client.auth**: `login()`, `logout()`, `me()`
- **client.organizations**: `list()`, `get()`, `list_warehouses()`, `list_channels()`, `list_users()`, `create_user()`
- **client.products**: `list()`, `create()`, `update()`, `list_inventory()`, `sync_inventory()`
- **client.orders**: `list()`, `get()`, `create()`, `update()`, `cancel()`, `confirm_fulfillment()`, `ship_order()`, `deliver_order()`, `return_order()`
- **client.invoices**: `list()`, `list_series()`
- **client.inbound**: `list()`, `create()`, `send_to_wms()`, `approve()`, `complete()`, `confirm()`

## Testing

```bash
# Run tests (when implemented)
uv run pytest

# Run with coverage
uv run pytest --cov=frisbo

# Type checking
uv run mypy frisbo/

# Linting
uv run ruff check frisbo/
```
