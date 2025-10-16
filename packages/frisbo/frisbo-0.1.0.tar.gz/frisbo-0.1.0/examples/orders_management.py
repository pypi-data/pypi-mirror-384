"""Order management examples for Frisbo SDK."""

from frisbo import FrisboClient

# Initialize client
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

org_id = 921  # Replace with your organization ID

# List all orders
print("=== Listing Orders ===")
for order in client.orders.list(org_id):
    print(f"Order: {order['order_reference']} | Status: {order.get('fulfillment_status')}")

# Get specific order details
order_id = 12345  # Replace with actual order ID
order_details = client.orders.get(org_id, order_id)
print(f"\n=== Order Details: {order_details['order_reference']} ===")
print(f"Status: {order_details.get('fulfillment_status')}")
print(f"Customer: {order_details['shipping_customer']['first_name']} {order_details['shipping_customer']['last_name']}")
print(f"Products: {len(order_details['products'])}")

# Create a new order
print("\n=== Creating New Order ===")
new_order = client.orders.create(
    organization_id=org_id,
    order_reference="SDK-TEST-001",
    channel_id=1,  # Replace with your channel ID
    warehouse_id=1,  # Replace with your warehouse ID
    shipping_customer={
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+40123456789"
    },
    shipping_address={
        "street": "Strada Principala 123",
        "city": "Bucharest",
        "county": "Bucuresti",
        "country": "Romania",
        "zip": "010101"
    },
    billing_customer={
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+40123456789"
    },
    billing_address={
        "street": "Strada Principala 123",
        "city": "Bucharest",
        "county": "Bucuresti",
        "country": "Romania",
        "zip": "010101"
    },
    products=[
        {
            "sku": "PROD-001",
            "name": "Test Product",
            "price": "99.99",
            "quantity": 2,
            "vat": "19"
        }
    ],
    notes="Test order created via SDK",
    discount="10%"  # 10% discount
)
print(f"Created order: {new_order['order_reference']}")

# Update order
print("\n=== Updating Order ===")
updated_order = client.orders.update(
    organization_id=org_id,
    order_id=new_order['order_id'],
    notes="Updated notes via SDK"
)
print(f"Updated order: {updated_order['order_reference']}")

# Order actions
print("\n=== Order Actions ===")

# Confirm fulfillment
try:
    response = client.orders.confirm_fulfillment(org_id, order_id)
    print("Fulfillment confirmed")
except Exception as e:
    print(f"Fulfillment confirmation failed: {e}")

# Ship order
try:
    response = client.orders.ship_order(org_id, order_id, awb="AWB123456")
    print("Order shipped")
except Exception as e:
    print(f"Shipping failed: {e}")

# Mark as delivered
try:
    response = client.orders.deliver_order(org_id, order_id)
    print("Order delivered")
except Exception as e:
    print(f"Delivery confirmation failed: {e}")

# Cancel order (if needed)
try:
    response = client.orders.cancel(org_id, order_id)
    print("Order canceled")
except Exception as e:
    print(f"Cancellation failed: {e}")

print("\nDone!")
