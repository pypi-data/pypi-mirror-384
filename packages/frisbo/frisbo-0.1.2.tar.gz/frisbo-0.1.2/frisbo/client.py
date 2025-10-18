"""Main Frisbo API client."""

from typing import Optional
import logging
import requests
from datetime import datetime, timedelta

from .exceptions import AuthenticationError
from .resources.auth import AuthResource
from .resources.organizations import OrganizationsResource
from .resources.products import ProductsResource
from .resources.orders import OrdersResource
from .resources.invoices import InvoicesResource
from .resources.inbound import InboundResource

logger = logging.getLogger(__name__)


class FrisboClient:
    """Main client for interacting with the Frisbo API.

    Example:
        >>> client = FrisboClient(email="user@example.com", password="secret")
        >>> # List organizations
        >>> for org in client.organizations.list():
        ...     print(org)
        >>> # Get orders for an organization
        >>> for order in client.orders.list(organization_id=921):
        ...     print(order)
    """

    def __init__(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
        access_token: Optional[str] = None,
        base_url: str = "https://api.frisbo.ro",
        auto_authenticate: bool = True,
        proxy: Optional[str] = None
    ):
        """Initialize the Frisbo client.

        Args:
            email: User email for authentication
            password: User password for authentication
            access_token: Pre-existing access token (optional)
            base_url: Base URL for the API
            auto_authenticate: Automatically authenticate on initialization
            proxy: Proxy URL (supports http, https, socks4, socks5, socks5h)
                   Examples: 'http://proxy:8080', 'socks5h://user:pass@proxy:1080'
        """
        self.email = email
        self.password = password
        self.access_token = access_token
        self.base_url = base_url.rstrip("/")
        self.token_expires_at: Optional[datetime] = None

        # Convert proxy string to dict format for requests library
        self.proxies = {'http': proxy, 'https': proxy} if proxy else None

        # Log client initialization
        logger.info(
            f"Initializing FrisboClient (base_url={base_url}, proxy={'configured' if proxy else 'none'})",
            extra={
                "base_url": base_url,
                "proxy": proxy,
                "auto_authenticate": auto_authenticate
            }
        )

        # Initialize resources
        self.auth = AuthResource(self)
        self.organizations = OrganizationsResource(self)
        self.products = ProductsResource(self)
        self.orders = OrdersResource(self)
        self.invoices = InvoicesResource(self)
        self.inbound = InboundResource(self)

        # Auto-authenticate if credentials provided
        if auto_authenticate and email and password and not access_token:
            self.authenticate()

    def authenticate(self) -> str:
        """Authenticate with the API and store the access token.

        Returns:
            Access token

        Raises:
            AuthenticationError: If authentication fails
        """
        if not self.email or not self.password:
            raise AuthenticationError("Email and password are required for authentication")

        logger.info(f"Authenticating user: {self.email}")

        try:
            auth_response = self.auth.login(self.email, self.password)
            self.access_token = auth_response.access_token

            # Calculate token expiry
            if auth_response.expires_in:
                self.token_expires_at = datetime.now() + timedelta(seconds=auth_response.expires_in)
                logger.info(
                    f"Authentication successful (token expires at {self.token_expires_at.isoformat()})",
                    extra={
                        "email": self.email,
                        "expires_at": self.token_expires_at.isoformat(),
                        "expires_in": auth_response.expires_in
                    }
                )
            else:
                logger.info(f"Authentication successful", extra={"email": self.email})

            return self.access_token
        except Exception as e:
            logger.error(f"Authentication failed for {self.email}: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if the client has a valid access token.

        Returns:
            True if authenticated, False otherwise
        """
        if not self.access_token:
            return False

        # Check if token is expired
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            logger.warning("Access token has expired")
            return False

        return True

    def ensure_authenticated(self) -> None:
        """Ensure the client is authenticated, re-authenticate if needed."""
        if not self.is_authenticated():
            if self.email and self.password:
                logger.info("Re-authenticating due to expired or missing token")
                self.authenticate()
            else:
                logger.error("Not authenticated and no credentials available")
                raise AuthenticationError("Not authenticated and no credentials available")

    def logout(self) -> None:
        """Logout and invalidate the current session."""
        if self.access_token:
            logger.info(f"Logging out user: {self.email}")
            try:
                self.auth.logout()
                logger.info("Logout successful")
            finally:
                self.access_token = None
                self.token_expires_at = None
