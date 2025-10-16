"""Product management examples for Frisbo SDK."""

from frisbo import FrisboClient

# Initialize client
client = FrisboClient(
    email="your-email@example.com",
    password="your-password"
)

org_id = 921  # Replace with your organization ID

# List all products
print("=== All Products ===")
for product in client.products.list(org_id):
    print(f"- {product.name}")
    print(f"  SKU: {product.sku}")
    print(f"  EAN: {product.ean}")
    print(f"  VAT: {product.vat}%")
    if product.dimensions:
        print(f"  Dimensions: {product.dimensions.width}x{product.dimensions.height}x{product.dimensions.length} cm")
    print()

# Create a new product
print("=== Creating Product ===")
new_product = client.products.create(
    organization_id=org_id,
    name="Test Product",
    sku="TEST-SKU-001",
    ean="1234567890123",
    upc="123456789012",
    vat=19,
    dimensions={
        "width": 10,
        "height": 15,
        "length": 20,
        "weight": 500  # in grams
    }
)
print(f"Created product: {new_product.name} (ID: {new_product.id})")

# Update product
print("\n=== Updating Product ===")
updated_product = client.products.update(
    organization_id=org_id,
    product_id=new_product.id,
    name="Updated Test Product",
    vat=20
)
print(f"Updated product: {updated_product.name}")

print("\nDone!")
