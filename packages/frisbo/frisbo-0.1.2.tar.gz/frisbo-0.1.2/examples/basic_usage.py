"""Basic usage examples for Frisbo SDK."""

from frisbo import FrisboClient

# Initialize the client with credentials
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

# Or use an existing access token
# client = FrisboClient(access_token="your-token")

# Get current user info
user = client.auth.me()
print(f"Logged in as: {user.name} ({user.email})")

# List all organizations
print("\n=== Organizations ===")
for org in client.organizations.list():
    print(f"- {org.name} (ID: {org.organization_id})")

# Get organization details
org_id = 921  # Replace with your organization ID
organization = client.organizations.get(org_id)
print(f"\nOrganization: {organization.name}")

# List warehouses
print("\n=== Warehouses ===")
warehouses = client.organizations.list_warehouses(org_id)
for warehouse in warehouses:
    print(f"- {warehouse.name} (ID: {warehouse.id})")

# List channels
print("\n=== Channels ===")
channels = client.organizations.list_channels(org_id)
for channel in channels:
    print(f"- {channel.name} (ID: {channel.id})")

# List products (with pagination)
print("\n=== Products (first 5) ===")
for i, product in enumerate(client.products.list(org_id)):
    print(f"- {product.name} | SKU: {product.sku}")
    if i >= 4:  # Only show first 5
        break

# Logout when done
client.logout()
print("\nLogged out successfully")
