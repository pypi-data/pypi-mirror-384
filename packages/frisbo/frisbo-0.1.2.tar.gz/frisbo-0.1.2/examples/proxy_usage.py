"""Example showing how to use proxy support with the Frisbo SDK.

This example demonstrates various proxy configurations including HTTP and SOCKS proxies.
"""

import os
from frisbo import FrisboClient

# Get credentials from environment variables
EMAIL = os.getenv("FRISBO_EMAIL", "your-email@example.com")
PASSWORD = os.getenv("FRISBO_PASSWORD", "your-password")
ORGANIZATION_ID = int(os.getenv("FRISBO_ORG_ID", "921"))


def example_http_proxy():
    """Example using HTTP/HTTPS proxy."""
    print("\n=== HTTP/HTTPS Proxy Example ===\n")

    client = FrisboClient(
        email=EMAIL,
        password=PASSWORD,
        proxy='http://proxy.example.com:8080'
    )

    # Make API calls - they will go through the proxy
    user = client.auth.me()
    print(f"Authenticated as: {user.email}")

    client.logout()


def example_socks5_proxy():
    """Example using SOCKS5 proxy."""
    print("\n=== SOCKS5 Proxy Example ===\n")

    client = FrisboClient(
        email=EMAIL,
        password=PASSWORD,
        proxy='socks5://proxy.example.com:1080'
    )

    # Make API calls through SOCKS5 proxy
    orgs = list(client.organizations.list())
    print(f"Found {len(orgs)} organizations")

    client.logout()


def example_socks5_with_auth():
    """Example using SOCKS5 proxy with authentication and DNS resolution."""
    print("\n=== SOCKS5 Proxy with Authentication ===\n")

    # socks5h:// means DNS resolution happens on the proxy side
    client = FrisboClient(
        email=EMAIL,
        password=PASSWORD,
        proxy='socks5h://username:password@proxy.example.com:1080'
    )

    # Make API calls through authenticated SOCKS5 proxy
    user = client.auth.me()
    print(f"Authenticated as: {user.email}")

    # List first 5 orders
    print("\nFetching orders through proxy...")
    for i, order in enumerate(client.orders.list(organization_id=ORGANIZATION_ID)):
        print(f"  Order {i+1}: {order.get('order_reference', 'N/A')}")
        if i >= 4:  # Get first 5
            break

    client.logout()


def example_socks4_proxy():
    """Example using SOCKS4 proxy."""
    print("\n=== SOCKS4 Proxy Example ===\n")

    client = FrisboClient(
        email=EMAIL,
        password=PASSWORD,
        proxy='socks4://proxy.example.com:1080'
    )

    # Make API calls through SOCKS4 proxy
    user = client.auth.me()
    print(f"Authenticated as: {user.email}")

    client.logout()


def example_proxy_from_environment():
    """Example using proxy from environment variable."""
    print("\n=== Proxy from Environment Variable ===\n")

    # Read proxy from environment
    proxy_url = os.getenv('HTTPS_PROXY') or os.getenv('https_proxy')

    if proxy_url:
        print(f"Using proxy from environment: {proxy_url}")
        client = FrisboClient(
            email=EMAIL,
            password=PASSWORD,
            proxy=proxy_url
        )

        user = client.auth.me()
        print(f"Authenticated as: {user.email}")

        client.logout()
    else:
        print("No proxy configured in environment (HTTPS_PROXY or https_proxy)")


def example_no_proxy():
    """Example without proxy (direct connection)."""
    print("\n=== Direct Connection (No Proxy) ===\n")

    # No proxy parameter = direct connection
    client = FrisboClient(
        email=EMAIL,
        password=PASSWORD
    )

    user = client.auth.me()
    print(f"Authenticated as: {user.email}")

    client.logout()


if __name__ == "__main__":
    print("Frisbo SDK - Proxy Usage Examples")
    print("==================================")

    print("\nNOTE: Replace proxy URLs with your actual proxy server details.")
    print("For testing without a real proxy, the examples will fail to connect.")

    # Uncomment the examples you want to run:

    # example_no_proxy()
    # example_http_proxy()
    # example_socks5_proxy()
    # example_socks5_with_auth()
    # example_socks4_proxy()
    # example_proxy_from_environment()

    print("\n" + "="*50)
    print("Supported proxy formats:")
    print("  - HTTP/HTTPS: 'http://proxy:8080'")
    print("  - SOCKS4:     'socks4://proxy:1080'")
    print("  - SOCKS5:     'socks5://proxy:1080'")
    print("  - SOCKS5h:    'socks5h://user:pass@proxy:1080' (DNS on proxy)")
    print("="*50)
