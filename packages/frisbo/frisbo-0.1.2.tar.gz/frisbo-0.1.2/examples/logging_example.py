"""Example showing how to configure logging with the Frisbo SDK.

This example demonstrates various logging configurations and how to use
them to debug and monitor API interactions.
"""

import os
import logging
import sys
from frisbo import FrisboClient

# Get credentials from environment variables
EMAIL = os.getenv("FRISBO_EMAIL", "your-email@example.com")
PASSWORD = os.getenv("FRISBO_PASSWORD", "your-password")
ORGANIZATION_ID = int(os.getenv("FRISBO_ORG_ID", "921"))


def basic_logging_example():
    """Basic logging configuration - logs to console."""
    print("\n=== Basic Logging Example ===\n")

    # Configure basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create client and perform operations
    client = FrisboClient(email=EMAIL, password=PASSWORD)

    # Get user info
    user = client.auth.me()
    print(f"User: {user.email}")

    # List first few organizations
    orgs = list(client.organizations.list())
    print(f"Found {len(orgs)} organizations")

    client.logout()


def debug_logging_example():
    """Debug logging - shows all API requests and responses."""
    print("\n=== Debug Logging Example ===\n")

    # Configure debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True  # Override previous config
    )

    # Create client with proxy to see proxy logging
    client = FrisboClient(
        email=EMAIL,
        password=PASSWORD,
        proxy='socks5://localhost:1080'  # Example proxy (will fail if not running)
    )

    # Perform operations - you'll see detailed request/response logs
    try:
        user = client.auth.me()
        print(f"User: {user.email}")
    except Exception as e:
        print(f"Error (expected if proxy not configured): {e}")


def selective_logging_example():
    """Selective logging - only log specific components."""
    print("\n=== Selective Logging Example ===\n")

    # Configure root logger to WARNING
    logging.basicConfig(level=logging.WARNING, force=True)

    # Enable INFO logging only for Frisbo SDK
    frisbo_logger = logging.getLogger('frisbo')
    frisbo_logger.setLevel(logging.INFO)

    # Enable DEBUG logging only for authentication
    auth_logger = logging.getLogger('frisbo.resources.auth')
    auth_logger.setLevel(logging.DEBUG)

    # Create client
    client = FrisboClient(email=EMAIL, password=PASSWORD)

    # You'll see:
    # - DEBUG logs for authentication operations
    # - INFO logs for other SDK operations
    # - WARNING and higher for everything else

    user = client.auth.me()
    print(f"User: {user.email}")

    client.logout()


def file_logging_example():
    """Log to file instead of console."""
    print("\n=== File Logging Example ===\n")

    # Create logger
    logger = logging.getLogger('frisbo')
    logger.setLevel(logging.DEBUG)

    # Create file handler
    file_handler = logging.FileHandler('frisbo_sdk.log')
    file_handler.setLevel(logging.DEBUG)

    # Create console handler with higher level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    print("Logging to both console (INFO) and file (DEBUG): frisbo_sdk.log")

    # Create client
    client = FrisboClient(email=EMAIL, password=PASSWORD)

    # Perform operations
    user = client.auth.me()
    print(f"User: {user.email}")

    # List orders (will log pagination info to file)
    order_count = 0
    for i, order in enumerate(client.orders.list(organization_id=ORGANIZATION_ID)):
        order_count += 1
        if i >= 4:  # Get first 5
            break

    print(f"Retrieved {order_count} orders")
    print("\nCheck 'frisbo_sdk.log' for detailed DEBUG logs")

    client.logout()


def json_logging_example():
    """JSON structured logging for production."""
    print("\n=== JSON Structured Logging Example ===\n")

    # Custom formatter for JSON output
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            import json
            log_data = {
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
            }
            # Add extra fields if present
            if hasattr(record, 'method'):
                log_data['method'] = record.method
            if hasattr(record, 'endpoint'):
                log_data['endpoint'] = record.endpoint
            if hasattr(record, 'status_code'):
                log_data['status_code'] = record.status_code
            if hasattr(record, 'elapsed'):
                log_data['elapsed'] = record.elapsed

            return json.dumps(log_data)

    # Configure logger
    logger = logging.getLogger('frisbo')
    logger.setLevel(logging.INFO)
    logger.handlers = []  # Clear existing handlers

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.propagate = False

    print("Logging in JSON format (useful for log aggregation):\n")

    # Create client
    client = FrisboClient(email=EMAIL, password=PASSWORD)

    # Perform operations
    user = client.auth.me()

    client.logout()


def performance_logging_example():
    """Focus on performance metrics."""
    print("\n=== Performance Logging Example ===\n")

    # Configure to show only INFO and WARNING
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        force=True
    )

    # Filter to show only response logs with timing
    class PerformanceFilter(logging.Filter):
        def filter(self, record):
            return 'API Response' in record.getMessage() and hasattr(record, 'elapsed')

    # Apply filter to base resource logger
    base_logger = logging.getLogger('frisbo.resources.base')
    handler = logging.StreamHandler()
    handler.addFilter(PerformanceFilter())
    handler.setFormatter(logging.Formatter('%(message)s'))
    base_logger.addHandler(handler)
    base_logger.propagate = False

    print("Showing only API response times:\n")

    # Create client
    client = FrisboClient(email=EMAIL, password=PASSWORD)

    # Perform various operations
    user = client.auth.me()
    orgs = list(client.organizations.list())

    # Get first few orders
    for i, order in enumerate(client.orders.list(organization_id=ORGANIZATION_ID)):
        if i >= 4:
            break

    client.logout()


def disable_logging_example():
    """Disable all SDK logging."""
    print("\n=== Disable Logging Example ===\n")

    # Disable all frisbo logging
    logging.getLogger('frisbo').setLevel(logging.CRITICAL + 1)

    print("All SDK logging disabled\n")

    # Create client
    client = FrisboClient(email=EMAIL, password=PASSWORD)

    # Perform operations - no logs will appear
    user = client.auth.me()
    print(f"User: {user.email} (no logs shown)")

    client.logout()


if __name__ == "__main__":
    print("Frisbo SDK - Logging Examples")
    print("=" * 60)

    print("\nThese examples show different logging configurations.")
    print("Uncomment the examples you want to run:\n")

    # Uncomment the examples you want to run:

    # basic_logging_example()
    # debug_logging_example()
    # selective_logging_example()
    # file_logging_example()
    # json_logging_example()
    # performance_logging_example()
    # disable_logging_example()

    print("\n" + "=" * 60)
    print("\nLogging Levels Guide:")
    print("  DEBUG    - Detailed request/response info, token details")
    print("  INFO     - Authentication events, API calls with timing")
    print("  WARNING  - Token expiry, rate limits")
    print("  ERROR    - API errors, authentication failures")
    print("\nLogger Names:")
    print("  frisbo                    - Root logger for all SDK")
    print("  frisbo.client             - Client initialization and auth")
    print("  frisbo.resources.base     - All API requests/responses")
    print("  frisbo.resources.auth     - Authentication operations")
    print("  frisbo.resources.*        - Other resource operations")
    print("=" * 60)
