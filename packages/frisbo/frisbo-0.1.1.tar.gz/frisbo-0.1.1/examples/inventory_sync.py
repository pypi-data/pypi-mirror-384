"""Inventory and inbound management examples for Frisbo SDK."""

from frisbo import FrisboClient

# Initialize client
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

org_id = 921  # Replace with your organization ID

# List all inventory items
print("=== Current Inventory ===")
for item in client.products.list_inventory(org_id):
    print(f"Inventory Request ID: {item.get('inventory_request_id')} | Status: {item.get('status')}")

# Sync inventory levels
print("\n=== Syncing Inventory ===")
sync_response = client.products.sync_inventory(
    organization_id=org_id,
    products=[
        {"sku": "PROD-001", "quantity": 100},
        {"sku": "PROD-002", "quantity": 50},
        {"sku": "PROD-003", "quantity": 75}
    ]
)
print(f"Inventory sync response: {sync_response}")

# Create inbound request
print("\n=== Creating Inbound Request ===")
warehouse_id = 1  # Replace with your warehouse ID
inbound = client.inbound.create(
    organization_id=org_id,
    warehouse_id=warehouse_id,
    products=[
        {
            "sku": "PROD-001",
            "quantity": 100,
            "price": "10.00"
        },
        {
            "sku": "PROD-002",
            "quantity": 50,
            "price": "20.00"
        }
    ]
)
print(f"Created inbound request: {inbound.get('inventory_request_id')}")

# List all inbound requests
print("\n=== Inbound Requests ===")
for inbound in client.inbound.list(org_id):
    print(f"ID: {inbound.get('inventory_request_id')} | Status: {inbound.get('status')}")

# Inbound actions
inventory_request_id = 123  # Replace with actual ID

try:
    # Send to WMS
    response = client.inbound.send_to_wms(org_id, inventory_request_id)
    print(f"\nSent to WMS: {response}")
except Exception as e:
    print(f"Send to WMS failed: {e}")

try:
    # Approve inbound
    response = client.inbound.approve(org_id, inventory_request_id)
    print(f"Approved: {response}")
except Exception as e:
    print(f"Approval failed: {e}")

try:
    # Complete inbound
    response = client.inbound.complete(org_id, inventory_request_id)
    print(f"Completed: {response}")
except Exception as e:
    print(f"Completion failed: {e}")

try:
    # Confirm inbound
    response = client.inbound.confirm(org_id, inventory_request_id)
    print(f"Confirmed: {response}")
except Exception as e:
    print(f"Confirmation failed: {e}")

print("\nDone!")
